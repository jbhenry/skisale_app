"""
Tests for invoice routes and business logic.
"""
import pytest
from models import Invoice, Inventory, InvoiceLine


class TestInvoiceCreate:
    def test_get_new_form(self, client):
        response = client.get('/invoices/new')
        assert response.status_code == 200

    def test_create_invoice(self, client, db):
        response = client.post('/invoices/new', data={
            'customer_name': 'Test Customer',
            'tax_rate': '6',
            'payment_method': 'Cash',
        }, follow_redirects=True)

        assert response.status_code == 200
        invoice = Invoice.query.first()
        assert invoice is not None
        assert invoice.customer_name == 'Test Customer'
        assert invoice.tax_rate == pytest.approx(0.06)


class TestInvoiceAddItem:
    def test_add_in_stock_item_sets_pending(self, client, db, sample_item, sample_invoice):
        response = client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'add_item',
            'sku': sample_item.sku,
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(sample_item)
        assert sample_item.status == 'Pending'
        assert InvoiceLine.query.filter_by(invoice_id=sample_invoice.id).count() == 1

    def test_add_item_updates_invoice_total(self, client, db, sample_item, sample_invoice):
        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'add_item',
            'sku': sample_item.sku,
        })

        db.session.refresh(sample_invoice)
        assert sample_invoice.subtotal == pytest.approx(150.00)
        assert sample_invoice.total == pytest.approx(159.00)  # 150 + 6% tax

    def test_add_nonexistent_sku_shows_error(self, client, sample_invoice):
        response = client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'add_item',
            'sku': 'XXXXXXX',
        }, follow_redirects=True)

        assert response.status_code == 200
        assert InvoiceLine.query.count() == 0

    def test_cannot_add_already_sold_item(self, client, db, sample_item, sample_invoice):
        sample_item.status = 'Sold'
        db.session.commit()

        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'add_item',
            'sku': sample_item.sku,
        })

        assert InvoiceLine.query.count() == 0

    def test_cannot_add_pending_item(self, client, db, sample_item, sample_invoice):
        sample_item.status = 'Pending'
        db.session.commit()

        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'add_item',
            'sku': sample_item.sku,
        })

        assert InvoiceLine.query.count() == 0


class TestInvoiceRemoveItem:
    def test_remove_item_returns_to_stock(self, client, db, sample_item, sample_invoice):
        # First add the item
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=sample_item.price,
        )
        db.session.add(line)
        sample_item.status = 'Pending'
        db.session.commit()

        response = client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'remove_item',
            'line_id': line.id,
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(sample_item)
        assert sample_item.status == 'In-Stock'
        assert InvoiceLine.query.filter_by(invoice_id=sample_invoice.id).count() == 0

    def test_remove_item_updates_total(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=sample_item.price,
        )
        db.session.add(line)
        sample_item.status = 'Pending'
        sample_invoice.subtotal = 150.00
        sample_invoice.total = 159.00
        db.session.commit()

        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'remove_item',
            'line_id': line.id,
        })

        db.session.refresh(sample_invoice)
        assert sample_invoice.subtotal == 0.0
        assert sample_invoice.total == 0.0


class TestInvoiceComplete:
    def test_complete_marks_items_sold(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=sample_item.price,
        )
        db.session.add(line)
        sample_item.status = 'Pending'
        db.session.commit()

        response = client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'complete',
            'customer_name': 'Bob Smith',
            'tax_rate': '6',
            'payment_method': 'Cash',
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(sample_item)
        assert sample_item.status == 'Sold'

    def test_complete_redirects_to_view(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=sample_item.price,
        )
        db.session.add(line)
        sample_item.status = 'Pending'
        db.session.commit()

        response = client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'complete',
            'customer_name': 'Bob',
            'tax_rate': '6',
            'payment_method': 'Cash',
        })

        assert response.status_code == 302
        assert f'/invoices/{sample_invoice.id}' in response.location


class TestInvoiceDelete:
    def test_delete_returns_items_to_stock(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=sample_item.price,
        )
        db.session.add(line)
        sample_item.status = 'Pending'
        db.session.commit()

        invoice_id = sample_invoice.id
        response = client.post(f'/invoices/{invoice_id}/delete',
                               follow_redirects=True)

        assert response.status_code == 200
        assert db.session.get(Invoice, invoice_id) is None
        db.session.refresh(sample_item)
        assert sample_item.status == 'In-Stock'


class TestInvoiceList:
    def test_invoice_list_returns_200(self, client):
        response = client.get('/invoices')
        assert response.status_code == 200

    def test_invoice_list_shows_invoices(self, client, sample_invoice):
        response = client.get('/invoices')
        assert response.status_code == 200
        assert b'Bob Smith' in response.data

    def test_invoice_list_empty_db(self, client, db):
        response = client.get('/invoices')
        assert response.status_code == 200


class TestInvoiceView:
    def test_view_invoice_returns_200(self, client, sample_invoice):
        response = client.get(f'/invoices/{sample_invoice.id}')
        assert response.status_code == 200

    def test_view_invoice_shows_customer_name(self, client, sample_invoice):
        response = client.get(f'/invoices/{sample_invoice.id}')
        assert b'Bob Smith' in response.data

    def test_view_nonexistent_invoice_returns_404(self, client):
        response = client.get('/invoices/9999')
        assert response.status_code == 404

    def test_view_invoice_returns_mode(self, client, sample_invoice):
        response = client.get(f'/invoices/{sample_invoice.id}?returns=1')
        assert response.status_code == 200


class TestInvoiceReceipt:
    def test_receipt_returns_200(self, client, sample_invoice):
        response = client.get(f'/invoices/{sample_invoice.id}/receipt')
        assert response.status_code == 200

    def test_receipt_shows_customer_name(self, client, sample_invoice):
        response = client.get(f'/invoices/{sample_invoice.id}/receipt')
        assert b'Bob Smith' in response.data

    def test_receipt_404_for_missing_invoice(self, client):
        response = client.get('/invoices/9999/receipt')
        assert response.status_code == 404


class TestInvoiceReturnItem:
    def test_return_item_sets_in_stock(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=sample_item.price,
        )
        db.session.add(line)
        sample_item.status = 'Sold'
        db.session.commit()

        response = client.post(f'/invoices/{sample_invoice.id}/return_item', data={
            'line_id': line.id,
        })
        assert response.status_code == 302
        db.session.refresh(sample_item)
        assert sample_item.status == 'In-Stock'

    def test_return_item_removes_invoice_line(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=sample_item.price,
        )
        db.session.add(line)
        sample_item.status = 'Sold'
        db.session.commit()
        line_id = line.id

        client.post(f'/invoices/{sample_invoice.id}/return_item', data={'line_id': line_id})
        assert db.session.get(InvoiceLine, line_id) is None

    def test_return_item_redirects_to_invoice_view(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=sample_item.price,
        )
        db.session.add(line)
        sample_item.status = 'Sold'
        db.session.commit()

        response = client.post(f'/invoices/{sample_invoice.id}/return_item', data={
            'line_id': line.id,
        })
        assert f'/invoices/{sample_invoice.id}' in response.location


class TestInvoiceSurcharge:
    def test_credit_card_adds_surcharge(self, client, db, sample_item):
        # Create an invoice with Credit Card payment
        response = client.post('/invoices/new', data={
            'customer_name': 'CC Buyer',
            'tax_rate': '0',
            'payment_method': 'Credit Card',
        }, follow_redirects=True)
        assert response.status_code == 200

        invoice = Invoice.query.filter_by(customer_name='CC Buyer').first()
        assert invoice is not None

        # Add the item
        client.post(f'/invoices/{invoice.id}/edit', data={
            'action': 'add_item',
            'sku': sample_item.sku,
        })

        db.session.refresh(invoice)
        # 3% surcharge on $150 = $4.50
        assert invoice.surcharge_rate == pytest.approx(0.03)
        assert invoice.surcharge_amount == pytest.approx(4.50)
        assert invoice.total == pytest.approx(154.50)

    def test_venmo_adds_surcharge(self, client, db, sample_item):
        response = client.post('/invoices/new', data={
            'customer_name': 'Venmo Buyer',
            'tax_rate': '0',
            'payment_method': 'Venmo',
        }, follow_redirects=True)
        assert response.status_code == 200

        invoice = Invoice.query.filter_by(customer_name='Venmo Buyer').first()
        client.post(f'/invoices/{invoice.id}/edit', data={
            'action': 'add_item',
            'sku': sample_item.sku,
        })

        db.session.refresh(invoice)
        assert invoice.surcharge_rate == pytest.approx(0.03)
        assert invoice.surcharge_amount == pytest.approx(4.50)

    def test_cash_no_surcharge(self, client, db, sample_item):
        response = client.post('/invoices/new', data={
            'customer_name': 'Cash Buyer',
            'tax_rate': '0',
            'payment_method': 'Cash',
        }, follow_redirects=True)
        assert response.status_code == 200

        invoice = Invoice.query.filter_by(customer_name='Cash Buyer').first()
        client.post(f'/invoices/{invoice.id}/edit', data={
            'action': 'add_item',
            'sku': sample_item.sku,
        })

        db.session.refresh(invoice)
        assert invoice.surcharge_rate == 0.0
        assert invoice.surcharge_amount == 0.0
        assert invoice.total == pytest.approx(150.00)

    def test_check_no_surcharge(self, client, db, sample_item):
        response = client.post('/invoices/new', data={
            'customer_name': 'Check Buyer',
            'tax_rate': '0',
            'payment_method': 'Check',
        }, follow_redirects=True)
        assert response.status_code == 200

        invoice = Invoice.query.filter_by(customer_name='Check Buyer').first()
        client.post(f'/invoices/{invoice.id}/edit', data={
            'action': 'add_item',
            'sku': sample_item.sku,
        })

        db.session.refresh(invoice)
        assert invoice.surcharge_rate == 0.0
        assert invoice.surcharge_amount == 0.0


class TestDashboard:
    def test_dashboard_loads(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_dashboard_totals_with_sale(self, client, db, sample_vendor, sample_item, sample_invoice):
        # Complete a sale
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=150.00,
        )
        db.session.add(line)
        sample_item.status = 'Sold'
        sample_invoice.subtotal = 150.00
        sample_invoice.tax_amount = 9.00
        sample_invoice.total = 159.00
        db.session.commit()

        response = client.get('/')
        assert response.status_code == 200
        # $150 sale * 20% commission = $30 commission, $120 vendor payout
        assert b'159' in response.data or b'150' in response.data
