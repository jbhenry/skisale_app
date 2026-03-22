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
        assert d['sku'] == 1234567
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
                sku=9990000 + i,
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


class TestInvoiceSurchargeModel:
    def test_credit_card_applies_surcharge(self, db, sample_vendor, sample_item, sample_invoice):
        sample_invoice.payment_method = 'Credit Card'
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        db.session.commit()

        sample_invoice.calculate_totals()
        # 3% surcharge on $100 = $3.00
        assert sample_invoice.surcharge_rate == pytest.approx(0.03)
        assert sample_invoice.surcharge_amount == pytest.approx(3.00)
        assert sample_invoice.total == pytest.approx(109.00)  # 100 + 6 tax + 3 surcharge

    def test_venmo_applies_surcharge(self, db, sample_vendor, sample_item, sample_invoice):
        sample_invoice.payment_method = 'Venmo'
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        db.session.commit()

        sample_invoice.calculate_totals()
        assert sample_invoice.surcharge_rate == pytest.approx(0.03)
        assert sample_invoice.surcharge_amount == pytest.approx(3.00)

    def test_cash_no_surcharge(self, db, sample_vendor, sample_item, sample_invoice):
        sample_invoice.payment_method = 'Cash'
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        db.session.commit()

        sample_invoice.calculate_totals()
        assert sample_invoice.surcharge_rate == 0.0
        assert sample_invoice.surcharge_amount == 0.0
        assert sample_invoice.total == pytest.approx(106.00)  # 100 + 6 tax

    def test_check_no_surcharge(self, db, sample_vendor, sample_item, sample_invoice):
        sample_invoice.payment_method = 'Check'
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        db.session.commit()

        sample_invoice.calculate_totals()
        assert sample_invoice.surcharge_rate == 0.0
        assert sample_invoice.surcharge_amount == 0.0

    def test_surcharge_excluded_from_tax_base(self, db, sample_vendor, sample_item, sample_invoice):
        """Tax is calculated on subtotal only, not on the surcharge amount."""
        sample_invoice.payment_method = 'Credit Card'
        sample_invoice.tax_rate = 0.10  # 10% for easy math
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        db.session.commit()

        sample_invoice.calculate_totals()
        # tax = 100 * 0.10 = 10, surcharge = 100 * 0.03 = 3, total = 113
        assert sample_invoice.tax_amount == pytest.approx(10.00)
        assert sample_invoice.surcharge_amount == pytest.approx(3.00)
        assert sample_invoice.total == pytest.approx(113.00)


class TestInvoiceDiscountModel:
    def test_discount_reduces_total(self, db, sample_vendor, sample_item, sample_invoice):
        """Discount is applied to subtotal before tax."""
        sample_invoice.discount_rate = 0.10  # 10%
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        db.session.commit()

        sample_invoice.calculate_totals()
        # discounted = 100 - 10 = 90, tax = 90 * 0.06 = 5.40, total = 95.40
        assert sample_invoice.discount_amount == pytest.approx(10.00)
        assert sample_invoice.tax_amount == pytest.approx(5.40)
        assert sample_invoice.total == pytest.approx(95.40)

    def test_discount_applied_before_surcharge(self, db, sample_vendor, sample_item, sample_invoice):
        """Surcharge is calculated on the discounted amount, not the full subtotal."""
        sample_invoice.payment_method = 'Credit Card'
        sample_invoice.discount_rate = 0.10  # 10%
        sample_invoice.tax_rate = 0.06
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        db.session.commit()

        sample_invoice.calculate_totals()
        # discounted = 90, tax = 90 * 0.06 = 5.40, surcharge = 90 * 0.03 = 2.70, total = 98.10
        assert sample_invoice.discount_amount == pytest.approx(10.00)
        assert sample_invoice.surcharge_amount == pytest.approx(2.70)
        assert sample_invoice.tax_amount == pytest.approx(5.40)
        assert sample_invoice.total == pytest.approx(98.10)

    def test_zero_discount_unchanged(self, db, sample_vendor, sample_item, sample_invoice):
        """A zero discount rate leaves totals unaffected."""
        sample_invoice.discount_rate = 0.0
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        db.session.commit()

        sample_invoice.calculate_totals()
        assert sample_invoice.discount_amount == pytest.approx(0.00)
        assert sample_invoice.total == pytest.approx(106.00)  # 100 + 6% tax

    def test_discount_default_is_zero(self, db):
        """Invoices default to no discount."""
        invoice = Invoice(customer_name='Test', tax_rate=0.06, payment_method='Cash')
        db.session.add(invoice)
        db.session.commit()
        assert invoice.discount_rate == 0.0
        assert invoice.discount_amount == 0.0
