"""
Tests for invoice routes and business logic.
"""
import pytest
from models import Invoice, Inventory, InvoiceLine
from routes.invoices import release_abandoned_invoices


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

    def test_create_invoice_no_name_no_discount_allowed(self, client, db):
        response = client.post('/invoices/new', data={
            'customer_name': '',
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '0',
        }, follow_redirects=True)

        assert response.status_code == 200
        assert Invoice.query.count() == 1  # invoice was created

    def test_discount_without_name_rejected(self, client, db):
        response = client.post('/invoices/new', data={
            'customer_name': '',
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '10',
        }, follow_redirects=True)

        assert response.status_code == 200
        assert Invoice.query.count() == 0  # invoice was NOT created
        assert b'Customer name is required' in response.data

    def test_discount_with_name_allowed(self, client, db):
        response = client.post('/invoices/new', data={
            'customer_name': 'Jane Employee',
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '10',
        }, follow_redirects=True)

        assert response.status_code == 200
        invoice = Invoice.query.first()
        assert invoice is not None
        assert invoice.discount_rate == pytest.approx(0.10)


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

    def test_complete_discount_without_name_rejected(self, client, db, sample_item, sample_invoice):
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
            'customer_name': '',
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '10',
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Customer name is required' in response.data
        db.session.refresh(sample_item)
        assert sample_item.status == 'Pending'  # items NOT marked sold

    def test_complete_saves_customer_name(self, client, db, sample_item, sample_invoice):
        """Name passed directly to complete action is saved (simulates JS-synced hidden field)."""
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=sample_item.price,
        )
        db.session.add(line)
        sample_item.status = 'Pending'
        db.session.commit()

        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'complete',
            'customer_name': 'Alice Buyer',
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '0',
        })

        db.session.refresh(sample_invoice)
        assert sample_invoice.customer_name == 'Alice Buyer'

    def test_complete_discount_with_name_allowed(self, client, db, sample_item, sample_invoice):
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
            'customer_name': 'Jane Employee',
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '10',
        })

        assert response.status_code == 302
        db.session.refresh(sample_item)
        assert sample_item.status == 'Sold'


class TestInvoiceEditGet:
    def test_get_edit_form_returns_200(self, client, sample_invoice):
        response = client.get(f'/invoices/{sample_invoice.id}/edit')
        assert response.status_code == 200

    def test_get_edit_form_shows_customer_name(self, client, sample_invoice):
        response = client.get(f'/invoices/{sample_invoice.id}/edit')
        assert b'Bob Smith' in response.data

    def test_get_edit_form_404_for_missing_invoice(self, client):
        response = client.get('/invoices/9999/edit')
        assert response.status_code == 404


class TestInvoiceUpdate:
    def test_update_invoice_changes_customer_name(self, client, db, sample_invoice):
        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'update_invoice',
            'customer_name': 'New Name',
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '0',
        })

        db.session.refresh(sample_invoice)
        assert sample_invoice.customer_name == 'New Name'

    def test_update_invoice_changes_payment_method(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        sample_item.status = 'Pending'
        db.session.commit()

        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'update_invoice',
            'customer_name': sample_invoice.customer_name,
            'tax_rate': '0',
            'payment_method': 'Credit Card',
            'discount_rate': '0',
        })

        db.session.refresh(sample_invoice)
        assert sample_invoice.payment_method == 'Credit Card'
        assert sample_invoice.surcharge_amount == pytest.approx(3.00)  # 3% of $100

    def test_update_invoice_changes_tax_rate(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        sample_item.status = 'Pending'
        db.session.commit()

        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'update_invoice',
            'customer_name': sample_invoice.customer_name,
            'tax_rate': '10',
            'payment_method': 'Cash',
            'discount_rate': '0',
        })

        db.session.refresh(sample_invoice)
        assert sample_invoice.tax_rate == pytest.approx(0.10)
        assert sample_invoice.tax_amount == pytest.approx(10.00)

    def test_update_discount_without_name_rejected(self, client, db, sample_invoice):
        original_name = sample_invoice.customer_name
        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'update_invoice',
            'customer_name': '',
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '10',
        })

        db.session.refresh(sample_invoice)
        assert sample_invoice.discount_rate == pytest.approx(0.0)  # not updated
        assert sample_invoice.customer_name == original_name

    def test_update_discount_with_name_allowed(self, client, db, sample_invoice):
        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'update_invoice',
            'customer_name': 'Jane Employee',
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '10',
        })

        db.session.refresh(sample_invoice)
        assert sample_invoice.discount_rate == pytest.approx(0.10)
        assert sample_invoice.customer_name == 'Jane Employee'


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

    def test_delete_nonexistent_invoice_returns_404(self, client):
        response = client.post('/invoices/9999/delete')
        assert response.status_code == 404


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

    def test_view_after_returning_all_items_on_cash_invoice_with_tendered(
        self, client, db, sample_item, sample_invoice
    ):
        """Regression: cash invoice with amount_tendered set, all items
        returned -> total becomes 0, change_due must not crash the view."""
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=sample_item.price,
        )
        db.session.add(line)
        sample_item.status = 'Sold'
        sample_invoice.payment_method = 'Cash'
        sample_invoice.amount_tendered = 50.0
        sample_invoice.calculate_totals()
        db.session.commit()

        client.post(f'/invoices/{sample_invoice.id}/return_item', data={'line_id': line.id})

        response = client.get(f'/invoices/{sample_invoice.id}')
        assert response.status_code == 200


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


class TestInvoiceDiscount:
    def test_create_invoice_stores_discount_rate(self, client, db):
        client.post('/invoices/new', data={
            'customer_name': 'Discount Buyer',
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '10',
        }, follow_redirects=True)

        invoice = Invoice.query.filter_by(customer_name='Discount Buyer').first()
        assert invoice is not None
        assert invoice.discount_rate == pytest.approx(0.10)

    def test_update_invoice_applies_discount(self, client, db, sample_item, sample_invoice):
        # Add an item first
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        sample_item.status = 'Pending'
        db.session.commit()

        client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'update_invoice',
            'customer_name': sample_invoice.customer_name,
            'tax_rate': '6',
            'payment_method': 'Cash',
            'discount_rate': '10',
        })

        db.session.refresh(sample_invoice)
        # discounted = 90, tax = 90 * 0.06 = 5.40, total = 95.40
        assert sample_invoice.discount_rate == pytest.approx(0.10)
        assert sample_invoice.discount_amount == pytest.approx(10.00)
        assert sample_invoice.total == pytest.approx(95.40)

    def test_complete_invoice_with_discount(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(
            invoice_id=sample_invoice.id,
            inventory_id=sample_item.id,
            price=100.00,
        )
        db.session.add(line)
        sample_item.status = 'Pending'
        db.session.commit()

        response = client.post(f'/invoices/{sample_invoice.id}/edit', data={
            'action': 'complete',
            'customer_name': 'Bob Smith',
            'tax_rate': '0',
            'payment_method': 'Cash',
            'discount_rate': '20',
        })

        assert response.status_code == 302
        db.session.refresh(sample_invoice)
        # discounted = 80, tax = 0, total = 80
        assert sample_invoice.discount_rate == pytest.approx(0.20)
        assert sample_invoice.discount_amount == pytest.approx(20.00)
        assert sample_invoice.total == pytest.approx(80.00)

    def test_discount_with_surcharge(self, client, db, sample_item):
        """Surcharge applies to the discounted amount, not the full subtotal."""
        client.post('/invoices/new', data={
            'customer_name': 'CC Discount',
            'tax_rate': '0',
            'payment_method': 'Credit Card',
            'discount_rate': '10',
        }, follow_redirects=True)

        invoice = Invoice.query.filter_by(customer_name='CC Discount').first()
        client.post(f'/invoices/{invoice.id}/edit', data={
            'action': 'add_item',
            'sku': sample_item.sku,
        })

        db.session.refresh(invoice)
        # sample_item price = $150, 10% discount = $15, discounted = $135
        # surcharge = 135 * 0.03 = 4.05, total = 139.05
        assert invoice.discount_amount == pytest.approx(15.00)
        assert invoice.surcharge_amount == pytest.approx(4.05)
        assert invoice.total == pytest.approx(139.05)


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


class TestReleaseAbandonedInvoices:
    def test_pending_item_returned_to_stock(self, db, sample_vendor, sample_item, sample_invoice):
        sample_item.status = 'Pending'
        line = InvoiceLine(invoice_id=sample_invoice.id, inventory_id=sample_item.id, price=sample_item.price)
        db.session.add(line)
        db.session.commit()

        release_abandoned_invoices()

        db.session.refresh(sample_item)
        assert sample_item.status == 'In-Stock'

    def test_abandoned_invoice_deleted(self, db, sample_vendor, sample_item, sample_invoice):
        sample_item.status = 'Pending'
        line = InvoiceLine(invoice_id=sample_invoice.id, inventory_id=sample_item.id, price=sample_item.price)
        db.session.add(line)
        db.session.commit()
        invoice_id = sample_invoice.id

        release_abandoned_invoices()

        assert db.session.get(Invoice, invoice_id) is None

    def test_completed_invoice_not_affected(self, db, sample_vendor, sample_item, sample_invoice):
        sample_item.status = 'Sold'
        line = InvoiceLine(invoice_id=sample_invoice.id, inventory_id=sample_item.id, price=sample_item.price)
        db.session.add(line)
        db.session.commit()
        invoice_id = sample_invoice.id

        release_abandoned_invoices()

        assert db.session.get(Invoice, invoice_id) is not None
        db.session.refresh(sample_item)
        assert sample_item.status == 'Sold'

    def test_empty_invoice_not_affected(self, db, sample_invoice):
        invoice_id = sample_invoice.id

        release_abandoned_invoices()

        assert db.session.get(Invoice, invoice_id) is not None

    def test_only_pending_items_reset(self, db, sample_vendor, sample_invoice):
        """An invoice with both Pending and Sold lines: only Pending items are reset."""
        pending_item = Inventory(sku=8000001, vendor_id=sample_vendor.id,
                                 equipment_type='Skis', price=100.00, status='Pending')
        sold_item = Inventory(sku=8000002, vendor_id=sample_vendor.id,
                              equipment_type='Boots', price=50.00, status='Sold')
        db.session.add_all([pending_item, sold_item])
        db.session.flush()
        db.session.add_all([
            InvoiceLine(invoice_id=sample_invoice.id, inventory_id=pending_item.id, price=100.00),
            InvoiceLine(invoice_id=sample_invoice.id, inventory_id=sold_item.id, price=50.00),
        ])
        db.session.commit()

        release_abandoned_invoices()

        db.session.refresh(pending_item)
        db.session.refresh(sold_item)
        assert pending_item.status == 'In-Stock'
        assert sold_item.status == 'Sold'


class TestRegisterID:
    def test_set_register_stores_in_session(self, client):
        response = client.post('/set-register', data={'register_id': 'Register 1'})
        assert response.status_code == 302
        with client.session_transaction() as sess:
            assert sess['register_id'] == 'Register 1'

    def test_set_register_empty_clears_session(self, client):
        with client.session_transaction() as sess:
            sess['register_id'] = 'Register 1'
        client.post('/set-register', data={'register_id': ''})
        with client.session_transaction() as sess:
            assert 'register_id' not in sess

    def test_set_register_redirects(self, client):
        response = client.post('/set-register', data={'register_id': 'R2'})
        assert response.status_code == 302

    def test_new_invoice_stamped_with_session_register_id(self, client, db):
        with client.session_transaction() as sess:
            sess['register_id'] = 'Register 3'
        client.post('/invoices/new', data={
            'customer_name': 'Test',
            'tax_rate': '6',
            'payment_method': 'Cash',
        })
        invoice = Invoice.query.first()
        assert invoice is not None
        assert invoice.register_id == 'Register 3'

    def test_create_invoice_without_register_is_blocked(self, client, db):
        with client.session_transaction() as sess:
            sess.pop('register_id', None)
        response = client.post('/invoices/new', data={
            'customer_name': 'Test',
            'tax_rate': '6',
            'payment_method': 'Cash',
        })
        assert response.status_code == 302
        assert Invoice.query.count() == 0

    def test_register_id_shown_in_invoice_view(self, client, db):
        invoice = Invoice(customer_name='Test', tax_rate=0.06,
                          payment_method='Cash', register_id='Register 2')
        db.session.add(invoice)
        db.session.commit()
        response = client.get(f'/invoices/{invoice.id}')
        assert b'Register 2' in response.data

    def test_register_id_absent_not_shown_in_invoice_view(self, client, db):
        invoice = Invoice(customer_name='Test', tax_rate=0.06,
                          payment_method='Cash', register_id=None)
        db.session.add(invoice)
        db.session.commit()
        response = client.get(f'/invoices/{invoice.id}')
        # "Register:" label should not appear when register_id is None
        assert b'<strong>Register:</strong>' not in response.data

    def test_register_id_shown_in_invoice_list(self, client, db):
        invoice = Invoice(customer_name='Test', tax_rate=0.06,
                          payment_method='Cash', register_id='Cashier Jane')
        db.session.add(invoice)
        db.session.commit()
        response = client.get('/invoices')
        assert b'Cashier Jane' in response.data

    def test_navbar_shows_set_register_when_unset(self, client):
        with client.session_transaction() as sess:
            sess.pop('register_id', None)
        response = client.get('/invoices')
        assert b'Set Register' in response.data

    def test_navbar_shows_register_id_when_set(self, client):
        with client.session_transaction() as sess:
            sess['register_id'] = 'Register 5'
        response = client.get('/invoices')
        assert b'Register 5' in response.data


class TestCancelInvoiceButton:
    def test_cancel_button_present_on_edit_page(self, client, sample_invoice):
        response = client.get(f'/invoices/{sample_invoice.id}/edit')
        assert b'Cancel Invoice' in response.data

    def test_cancel_button_deletes_invoice_and_restores_stock(self, client, db, sample_item, sample_invoice):
        line = InvoiceLine(invoice_id=sample_invoice.id, inventory_id=sample_item.id, price=sample_item.price)
        db.session.add(line)
        sample_item.status = 'Pending'
        db.session.commit()
        invoice_id = sample_invoice.id

        response = client.post(f'/invoices/{invoice_id}/delete', follow_redirects=True)

        assert response.status_code == 200
        assert db.session.get(Invoice, invoice_id) is None
        db.session.refresh(sample_item)
        assert sample_item.status == 'In-Stock'
