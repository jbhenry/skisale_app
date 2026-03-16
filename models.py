"""
SkiSale Database Models
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)

db = SQLAlchemy()

SURCHARGE_RATE = 0.03  # 3% surcharge
SURCHARGE_METHODS = {'Credit Card', 'Venmo'}

class Vendor(db.Model):
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address1 = db.Column(db.String(200))
    address2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    
    # Consignment-specific fields
    commission_rate = db.Column(db.Float, default=0.20)  # Default 20% commission
    payment_method = db.Column(db.String(20))  # Cash, Check, PayPal, etc.
    
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationship to inventory
    inventory_items = db.relationship('Inventory', backref='vendor', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def __repr__(self):
        return f'<Vendor #{self.id}: {self.full_name}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'address1': self.address1,
            'address2': self.address2,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'commission_rate': self.commission_rate,
            'payment_method': self.payment_method,
            'notes': self.notes,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.Integer, unique=True, nullable=False)  # up to 7-digit SKU
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    
    # Item details
    equipment_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='In-Stock')
    
    donate_if_not_sold = db.Column(db.Boolean, default=False, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self):
        return f'<Inventory SKU:{self.sku} - {self.equipment_type}>'

    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'sku': self.sku,
            'vendor_id': self.vendor_id,
            'vendor_name': self.vendor.full_name if self.vendor else None,
            'equipment_type': self.equipment_type,
            'description': self.description,
            'price': self.price,
            'status': self.status,
            'donate_if_not_sold': self.donate_if_not_sold,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_date = db.Column(db.DateTime, default=utcnow, nullable=False)
    customer_name = db.Column(db.String(100))
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax_rate = db.Column(db.Float, nullable=False, default=0.0)  # e.g., 0.08 for 8%
    tax_amount = db.Column(db.Float, nullable=False, default=0.0)
    surcharge_rate = db.Column(db.Float, nullable=False, default=0.0)
    surcharge_amount = db.Column(db.Float, nullable=False, default=0.0)
    discount_rate = db.Column(db.Float, nullable=False, default=0.0)
    discount_amount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    payment_method = db.Column(db.String(20))  # Cash, Credit, Check, etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationship to invoice lines
    lines = db.relationship('InvoiceLine', backref='invoice', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Invoice #{self.id} - ${self.total}>'
    
    def calculate_totals(self):
        """Calculate subtotal, discount, tax, surcharge, and total from lines"""
        self.subtotal = sum(line.price for line in self.lines)
        self.discount_amount = round(self.subtotal * self.discount_rate, 2)
        discounted = self.subtotal - self.discount_amount
        self.tax_amount = discounted * self.tax_rate
        if self.payment_method in SURCHARGE_METHODS:
            self.surcharge_rate = SURCHARGE_RATE
            self.surcharge_amount = discounted * SURCHARGE_RATE
        else:
            self.surcharge_rate = 0.0
            self.surcharge_amount = 0.0
        self.total = discounted + self.tax_amount + self.surcharge_amount
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'customer_name': self.customer_name,
            'subtotal': self.subtotal,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'total': self.total,
            'payment_method': self.payment_method,
            'notes': self.notes,
            'line_count': len(self.lines),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class InvoiceLine(db.Model):
    __tablename__ = 'invoice_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of sale
    
    # Relationship to inventory
    inventory_item = db.relationship('Inventory', backref='invoice_line', uselist=False)
    
    def __repr__(self):
        return f'<InvoiceLine Invoice:{self.invoice_id} Item:{self.inventory_id}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'inventory_id': self.inventory_id,
            'sku': self.inventory_item.sku if self.inventory_item else None,
            'description': self.inventory_item.description if self.inventory_item else None,
            'price': self.price
        }

