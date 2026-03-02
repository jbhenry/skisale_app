"""
Pytest configuration and shared fixtures for SkiSale tests.
"""
import pytest
import sqlalchemy as sa
from sqlalchemy.pool import StaticPool
from app import app as flask_app
from models import db as _db, Vendor, Inventory, Invoice, InvoiceLine


@pytest.fixture()
def app():
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    })

    # Flask-SQLAlchemy creates the production engine during init_app at startup
    # and caches it. We can't call init_app again once Flask has handled its
    # first request (it raises AssertionError), so we directly swap the engine
    # in the internal cache. StaticPool ensures all connections share the same
    # in-memory database so SQLite doesn't create a fresh empty DB per connection.
    test_engine = sa.create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    engine_cache = _db._app_engines[flask_app]
    prod_engine = engine_cache.get(None)
    engine_cache[None] = test_engine

    ctx = flask_app.app_context()
    ctx.push()
    _db.create_all()

    yield flask_app

    _db.session.remove()
    _db.drop_all()
    ctx.pop()

    # Dispose the test engine and restore the production engine so other code
    # that runs after this fixture (e.g. the next test's setup) finds a clean state.
    test_engine.dispose()
    if prod_engine is not None:
        engine_cache[None] = prod_engine
    else:
        engine_cache.pop(None, None)


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
