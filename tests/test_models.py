"""
Unit tests for database models.
"""
from models import Vendor, Inventory, Invoice, InvoiceLine


class TestVendorModel:
    def test_full_name(self, db):
        vendor = Vendor(first_name='John', last_name='Smith', commission_rate=0.20)
        assert vendor.full_name == 'John Smith'

    def test_default_commission_rate(self, db):
        vendor = Vendor(first_name='A', last_name='B')
        db.session.add(vendor)
        db.session.commit()
        assert vendor.commission_rate == 0.20

    def test_default_active(self, db):
        vendor = Vendor(first_name='A', last_name='B')
        db.session.add(vendor)
        db.session.commit()
        assert vendor.active is True

    def test_to_dict(self, sample_vendor):
        d = sample_vendor.to_dict()
        assert d['first_name'] == 'Jane'
        assert d['last_name'] == 'Doe'
        assert d['full_name'] == 'Jane Doe'
        assert d['commission_rate'] == 0.20
        assert d['active'] is True


class TestInventoryModel:
    def test_to_dict(self, sample_item):
        d = sample_item.to_dict()
        assert d['sku'] == '0001234'
        assert d['equipment_type'] == 'Skis'
        assert d['price'] == 150.00
        assert d['status'] == 'In-Stock'
        assert d['vendor_name'] == 'Jane Doe'


class TestInvoiceModel:
    def test_calculate_totals_no_lines(self, sample_invoice):
        sample_invoice.calculate_totals()
        assert sample_invoice.subtotal == 0.0
        assert sample_invoice.tax_amount == 0.0
        assert sample_invoice.total == 0.0

    def test_calculate_totals_with_lines(self, db, sample_vendor, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        db.session.commit()

        sample_invoice.calculate_totals()
        assert sample_invoice.subtotal == 100.00
        assert sample_invoice.tax_amount == pytest.approx(6.00)
        assert sample_invoice.total == pytest.approx(106.00)

    def test_calculate_totals_multiple_lines(self, db, sample_vendor, sample_invoice):
        items = []
        for i, price in enumerate([50.00, 75.00, 25.00], start=1):
            item = Inventory(
                sku=f'999000{i}',
                vendor_id=sample_vendor.id,
                equipment_type='Boots',
                price=price,
                status='In-Stock',
            )
            db.session.add(item)
            db.session.flush()
            line = InvoiceLine(invoice_id=sample_invoice.id, inventory_id=item.id, price=price)
            db.session.add(line)

        db.session.commit()
        sample_invoice.calculate_totals()

        assert sample_invoice.subtotal == pytest.approx(150.00)
        assert sample_invoice.tax_amount == pytest.approx(9.00)
        assert sample_invoice.total == pytest.approx(159.00)


import pytest
