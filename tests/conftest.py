"""
Pytest configuration and shared fixtures for SkiSale tests.
"""
import pytest
from app import app as flask_app
from models import db as _db, Vendor, Inventory, Invoice, InvoiceLine


@pytest.fixture()
def app():
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    })
    ctx = flask_app.app_context()
    ctx.push()
    _db.create_all()

    yield flask_app

    _db.session.remove()
    _db.drop_all()
    ctx.pop()


@pytest.fixture()
def client(app):
    return flask_app.test_client()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def sample_vendor(db):
    vendor = Vendor(
        first_name='Jane',
        last_name='Doe',
        phone='555-1234',
        email='jane@example.com',
        commission_rate=0.20,
        payment_method='Cash',
        active=True,
    )
    db.session.add(vendor)
    db.session.commit()
    return vendor


@pytest.fixture()
def sample_item(db, sample_vendor):
    item = Inventory(
        sku='0001234',
        vendor_id=sample_vendor.id,
        equipment_type='Skis',
        description='Fischer RC4 160cm',
        price=150.00,
        status='In-Stock',
    )
    db.session.add(item)
    db.session.commit()
    return item


@pytest.fixture()
def sample_invoice(db):
    invoice = Invoice(
        customer_name='Bob Smith',
        tax_rate=0.06,
        payment_method='Cash',
    )
    db.session.add(invoice)
    db.session.commit()
    return invoice
