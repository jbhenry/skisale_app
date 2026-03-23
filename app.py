"""
SkiSale Flask Application
"""
from datetime import timezone

from flask import Flask
from sqlalchemy import text

from models import db
from constants import EASTERN

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skisale.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.template_filter('localtime')
def to_eastern(dt):
    """Convert a naive UTC datetime to US Eastern time."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(EASTERN)

# Register blueprints
from routes.vendors import vendors_bp
from routes.inventory import inventory_bp
from routes.invoices import invoices_bp
from routes.admin import admin_bp
from routes.api import api_bp

app.register_blueprint(vendors_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(invoices_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)

# Create tables and run lightweight column migrations
from routes.invoices import release_abandoned_invoices

with app.app_context():
    db.create_all()
    # Add donate_if_not_sold column if upgrading from an older schema
    try:
        db.session.execute(text(
            'ALTER TABLE inventory ADD COLUMN donate_if_not_sold BOOLEAN NOT NULL DEFAULT 0'
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()  # Column already exists — nothing to do

    # Add register_id column if upgrading from an older schema
    try:
        db.session.execute(text(
            'ALTER TABLE invoices ADD COLUMN register_id VARCHAR(50)'
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()  # Column already exists — nothing to do

    # Add surcharge/discount columns if upgrading from an older schema
    for col_sql in [
        'ALTER TABLE invoices ADD COLUMN surcharge_rate FLOAT NOT NULL DEFAULT 0.0',
        'ALTER TABLE invoices ADD COLUMN surcharge_amount FLOAT NOT NULL DEFAULT 0.0',
        'ALTER TABLE invoices ADD COLUMN discount_rate FLOAT NOT NULL DEFAULT 0.0',
        'ALTER TABLE invoices ADD COLUMN discount_amount FLOAT NOT NULL DEFAULT 0.0',
    ]:
        try:
            db.session.execute(text(col_sql))
            db.session.commit()
        except Exception:
            db.session.rollback()  # Column already exists — nothing to do

    # Enable WAL mode for better concurrent read performance
    db.session.execute(text('PRAGMA journal_mode=WAL'))
    db.session.execute(text('PRAGMA busy_timeout=5000'))
    db.session.commit()

    release_abandoned_invoices()

    # Migrate sku column from VARCHAR to INTEGER if upgrading from an older schema.
    # SQLite doesn't support ALTER COLUMN, so we rename → recreate → copy → drop.
    try:
        col_info = db.session.execute(text("PRAGMA table_info(inventory)")).fetchall()
        sku_type = next((row[2] for row in col_info if row[1] == 'sku'), None)
        if sku_type and sku_type.upper() != 'INTEGER':
            db.session.execute(text("ALTER TABLE inventory RENAME TO _inventory_old"))
            db.session.commit()
            db.create_all()  # creates inventory with INTEGER sku
            db.session.execute(text("""
                INSERT INTO inventory (id, sku, vendor_id, equipment_type, description,
                    price, status, donate_if_not_sold, notes, created_at, updated_at)
                SELECT id, CAST(sku AS INTEGER), vendor_id, equipment_type, description,
                    price, status, donate_if_not_sold, notes, created_at, updated_at
                FROM _inventory_old
            """))
            db.session.execute(text("DROP TABLE _inventory_old"))
            db.session.commit()
    except Exception:
        db.session.rollback()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
