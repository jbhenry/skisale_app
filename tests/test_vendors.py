"""
Tests for vendor routes.
"""
import io
import pytest
from models import Vendor, Inventory, Invoice, InvoiceLine
from routes.vendors import compute_swap_metrics


class TestVendorList:
    def test_list_shows_active_vendors(self, client, sample_vendor):
        response = client.get('/vendors')
        assert response.status_code == 200
        assert b'Jane' in response.data

    def test_list_shows_inactive_by_default(self, client, db, sample_vendor):
        sample_vendor.active = False
        db.session.commit()

        response = client.get('/vendors')
        assert b'Jane' in response.data

    def test_list_shows_inactive_when_requested(self, client, db, sample_vendor):
        sample_vendor.active = False
        db.session.commit()

        response = client.get('/vendors?active_only=false')
        assert b'Jane' in response.data

    def test_search_by_name(self, client, sample_vendor):
        response = client.get('/vendors?search=Doe')
        assert response.status_code == 200
        assert b'Jane' in response.data

    def test_search_no_match(self, client, sample_vendor):
        response = client.get('/vendors?search=nobody')
        assert b'Jane' not in response.data

    def test_default_sort_is_id_ascending(self, client, db, sample_vendor):
        # Second vendor's name sorts before "Doe" alphabetically but has a
        # higher ID, so ID-ascending and name-ascending disagree.
        second = Vendor(
            first_name='Amy',
            last_name='Adams',
            commission_rate=0.20,
            payment_method='Cash',
            active=True,
        )
        db.session.add(second)
        db.session.commit()

        response = client.get('/vendors')
        assert response.data.index(b'Jane') < response.data.index(b'Amy')


class TestVendorCreate:
    def test_get_new_form(self, client):
        response = client.get('/vendors/new')
        assert response.status_code == 200

    def test_create_vendor(self, client, db):
        response = client.post('/vendors/new', data={
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'phone': '555-9999',
            'email': 'alice@example.com',
            'commission_rate': '25',
            'payment_method': 'Check',
            'active': 'on',
        }, follow_redirects=True)

        assert response.status_code == 200
        vendor = Vendor.query.filter_by(last_name='Johnson').first()
        assert vendor is not None
        assert vendor.commission_rate == 0.25
        assert vendor.active is True

    def test_create_vendor_missing_required_field(self, client, db):
        response = client.post('/vendors/new', data={
            'first_name': 'Alice',
            # last_name missing
        }, follow_redirects=True)

        assert Vendor.query.count() == 0


class TestVendorEdit:
    def test_get_edit_form(self, client, sample_vendor):
        response = client.get(f'/vendors/{sample_vendor.id}/edit')
        assert response.status_code == 200
        assert b'Jane' in response.data

    def test_edit_vendor(self, client, db, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/edit', data={
            'first_name': 'Jane',
            'last_name': 'Updated',
            'commission_rate': '30',
            'active': 'on',
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(sample_vendor)
        assert sample_vendor.last_name == 'Updated'
        assert sample_vendor.commission_rate == 0.30

    def test_edit_nonexistent_vendor(self, client):
        response = client.get('/vendors/9999/edit')
        assert response.status_code == 404

    def test_deactivate_via_edit_blocked_when_vendor_has_inventory(self, client, db, sample_vendor, sample_item):
        response = client.post(f'/vendors/{sample_vendor.id}/edit', data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'commission_rate': '20',
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(sample_vendor)
        assert sample_vendor.active is True
        assert b'Cannot deactivate' in response.data

    def test_edit_without_inventory_can_deactivate(self, client, db, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/edit', data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'commission_rate': '20',
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(sample_vendor)
        assert sample_vendor.active is False


class TestVendorDelete:
    def test_soft_delete_sets_inactive(self, client, db, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/delete',
                               follow_redirects=True)
        assert response.status_code == 200
        db.session.refresh(sample_vendor)
        assert sample_vendor.active is False

    def test_soft_delete_not_removed_from_db(self, client, db, sample_vendor):
        vendor_id = sample_vendor.id
        client.post(f'/vendors/{vendor_id}/delete')
        assert db.session.get(Vendor, vendor_id) is not None

    def test_deactivate_blocked_when_vendor_has_inventory(self, client, db, sample_vendor, sample_item):
        response = client.post(f'/vendors/{sample_vendor.id}/delete', follow_redirects=True)
        assert response.status_code == 200
        db.session.refresh(sample_vendor)
        assert sample_vendor.active is True
        assert b'Cannot deactivate' in response.data


class TestVendorView:
    def test_view_vendor(self, client, sample_vendor):
        response = client.get(f'/vendors/{sample_vendor.id}')
        assert response.status_code == 200
        assert b'Jane' in response.data

    def test_view_nonexistent_vendor(self, client):
        response = client.get('/vendors/9999')
        assert response.status_code == 404


class TestVendorAPI:
    def test_api_returns_active_vendors(self, client, sample_vendor):
        response = client.get('/api/vendors')
        assert response.status_code == 200
        data = response.get_json()
        assert any(v['last_name'] == 'Doe' for v in data)

    def test_api_excludes_inactive(self, client, db, sample_vendor):
        sample_vendor.active = False
        db.session.commit()

        response = client.get('/api/vendors')
        data = response.get_json()
        assert not any(v['last_name'] == 'Doe' for v in data)

    def test_api_get_single_vendor(self, client, sample_vendor):
        response = client.get(f'/api/vendors/{sample_vendor.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['full_name'] == 'Jane Doe'


class TestVendorReceipt:
    def test_receipt_returns_200(self, client, sample_vendor):
        response = client.get(f'/vendors/{sample_vendor.id}/receipt')
        assert response.status_code == 200

    def test_receipt_shows_vendor_name(self, client, sample_vendor):
        response = client.get(f'/vendors/{sample_vendor.id}/receipt')
        assert b'Jane' in response.data

    def test_receipt_shows_items(self, client, sample_item):
        response = client.get(f'/vendors/{sample_item.vendor_id}/receipt')
        assert b'Fischer' in response.data

    def test_receipt_404_for_missing_vendor(self, client):
        response = client.get('/vendors/9999/receipt')
        assert response.status_code == 404

    def test_receipt_shows_disclaimer(self, client, sample_vendor):
        response = client.get(f'/vendors/{sample_vendor.id}/receipt')
        assert b'WINTER SPORTS EQUIPMENT SALE' in response.data


class TestVendorCheckoutReceipt:
    @pytest.fixture()
    def vendor_with_sale(self, db, sample_vendor):
        item = Inventory(
            sku=5000001,
            vendor_id=sample_vendor.id,
            equipment_type='Skis',
            description='Sold Ski',
            price=100.00,
            status='Sold',
        )
        db.session.add(item)
        db.session.commit()
        return sample_vendor

    def test_checkout_receipt_returns_200(self, client, vendor_with_sale):
        response = client.get(f'/vendors/{vendor_with_sale.id}/checkout-receipt')
        assert response.status_code == 200

    def test_checkout_receipt_shows_vendor_name(self, client, vendor_with_sale):
        response = client.get(f'/vendors/{vendor_with_sale.id}/checkout-receipt')
        assert b'Jane' in response.data

    def test_checkout_receipt_404_for_missing_vendor(self, client):
        response = client.get('/vendors/9999/checkout-receipt')
        assert response.status_code == 404

    def test_checkout_receipt_calculates_payout(self, client, db, vendor_with_sale):
        # vendor_with_sale has commission_rate=0.20 and one $100 sold item
        # payout = $100 * (1 - 0.20) = $80
        response = client.get(f'/vendors/{vendor_with_sale.id}/checkout-receipt')
        assert response.status_code == 200
        assert b'80' in response.data  # payout amount appears on page


class TestVendorImportCsv:
    def test_get_form_returns_200(self, client, sample_vendor):
        response = client.get(f'/vendors/{sample_vendor.id}/import')
        assert response.status_code == 200

    def test_get_form_404_for_missing_vendor(self, client):
        response = client.get('/vendors/9999/import')
        assert response.status_code == 404

    def test_import_valid_csv_creates_items(self, client, db, sample_vendor):
        csv_data = b'SKU,Description,Price,Equipment Type\n3001,Test Ski,100.00,Skis\n'
        data = {'csv_file': (io.BytesIO(csv_data), 'items.csv')}
        response = client.post(
            f'/vendors/{sample_vendor.id}/import',
            data=data,
            content_type='multipart/form-data',
        )
        assert response.status_code == 200
        item = Inventory.query.filter_by(sku=3001).first()
        assert item is not None
        assert item.price == pytest.approx(100.00)
        assert item.equipment_type == 'Skis'
        assert item.status == 'Not In Stock'

    def test_import_sets_vendor_id(self, client, db, sample_vendor):
        csv_data = b'SKU,Price\n3002,50.00\n'
        data = {'csv_file': (io.BytesIO(csv_data), 'items.csv')}
        client.post(
            f'/vendors/{sample_vendor.id}/import',
            data=data,
            content_type='multipart/form-data',
        )
        item = Inventory.query.filter_by(sku=3002).first()
        assert item is not None
        assert item.vendor_id == sample_vendor.id

    def test_import_no_file_shows_error(self, client, sample_vendor):
        response = client.post(
            f'/vendors/{sample_vendor.id}/import',
            data={},
            content_type='multipart/form-data',
        )
        assert response.status_code == 200
        assert Inventory.query.count() == 0

    def test_import_non_csv_shows_error(self, client, sample_vendor):
        data = {'csv_file': (io.BytesIO(b'not a csv'), 'items.txt')}
        response = client.post(
            f'/vendors/{sample_vendor.id}/import',
            data=data,
            content_type='multipart/form-data',
        )
        assert response.status_code == 200
        assert Inventory.query.count() == 0

    def test_import_duplicate_sku_skipped(self, client, db, sample_vendor, sample_item):
        # sample_item has sku=1234567
        csv_data = b'SKU,Price\n1234567,99.00\n'
        data = {'csv_file': (io.BytesIO(csv_data), 'items.csv')}
        client.post(
            f'/vendors/{sample_vendor.id}/import',
            data=data,
            content_type='multipart/form-data',
        )
        # Still only one item with that SKU
        assert Inventory.query.filter_by(sku=1234567).count() == 1

    def test_import_missing_price_skipped(self, client, db, sample_vendor):
        csv_data = b'SKU,Description\n3003,No Price Item\n'
        data = {'csv_file': (io.BytesIO(csv_data), 'items.csv')}
        client.post(
            f'/vendors/{sample_vendor.id}/import',
            data=data,
            content_type='multipart/form-data',
        )
        assert Inventory.query.filter_by(sku=3003).first() is None

    def test_import_invalid_sku_skipped(self, client, db, sample_vendor):
        csv_data = b'SKU,Price\nabc,50.00\n'
        data = {'csv_file': (io.BytesIO(csv_data), 'items.csv')}
        client.post(
            f'/vendors/{sample_vendor.id}/import',
            data=data,
            content_type='multipart/form-data',
        )
        assert Inventory.query.count() == 0

    def test_import_unknown_equipment_type_kept_as_is(self, client, db, sample_vendor):
        csv_data = b'SKU,Price,Equipment Type\n3004,75.00,Surfboard\n'
        data = {'csv_file': (io.BytesIO(csv_data), 'items.csv')}
        client.post(
            f'/vendors/{sample_vendor.id}/import',
            data=data,
            content_type='multipart/form-data',
        )
        item = Inventory.query.filter_by(sku=3004).first()
        assert item is not None
        assert item.equipment_type == 'Surfboard'

    def test_import_missing_equipment_type_defaults_to_other(self, client, db, sample_vendor):
        csv_data = b'SKU,Price,Equipment Type\n3006,75.00,\n'
        data = {'csv_file': (io.BytesIO(csv_data), 'items.csv')}
        client.post(
            f'/vendors/{sample_vendor.id}/import',
            data=data,
            content_type='multipart/form-data',
        )
        item = Inventory.query.filter_by(sku=3006).first()
        assert item is not None
        assert item.equipment_type == 'Other'

    def test_import_price_with_dollar_sign(self, client, db, sample_vendor):
        csv_data = b'SKU,Price\n3005,$125.00\n'
        data = {'csv_file': (io.BytesIO(csv_data), 'items.csv')}
        client.post(
            f'/vendors/{sample_vendor.id}/import',
            data=data,
            content_type='multipart/form-data',
        )
        item = Inventory.query.filter_by(sku=3005).first()
        assert item is not None
        assert item.price == pytest.approx(125.00)


class TestVendorCheckin:
    @pytest.fixture()
    def not_in_stock_item(self, db, sample_vendor):
        item = Inventory(
            sku=4001,
            vendor_id=sample_vendor.id,
            equipment_type='Skis',
            description='Pre-registered Ski',
            price=80.00,
            status='Not In Stock',
        )
        db.session.add(item)
        db.session.commit()
        return item

    def test_get_checkin_page_returns_200(self, client, sample_vendor):
        response = client.get(f'/vendors/{sample_vendor.id}/checkin')
        assert response.status_code == 200

    def test_get_checkin_404_for_missing_vendor(self, client):
        response = client.get('/vendors/9999/checkin')
        assert response.status_code == 404

    def test_checkin_valid_sku_sets_in_stock(self, client, db, not_in_stock_item, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/checkin', data={
            'sku': str(not_in_stock_item.sku),
        }, follow_redirects=True)
        assert response.status_code == 200
        db.session.refresh(not_in_stock_item)
        assert not_in_stock_item.status == 'In-Stock'

    def test_checkin_sku_not_found_shows_error(self, client, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/checkin', data={
            'sku': '9999999',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'not found' in response.data.lower()

    def test_checkin_wrong_vendor_shows_error(self, client, db, not_in_stock_item):
        other_vendor = Vendor(first_name='Other', last_name='Vendor', commission_rate=0.20)
        db.session.add(other_vendor)
        db.session.commit()

        response = client.post(f'/vendors/{other_vendor.id}/checkin', data={
            'sku': str(not_in_stock_item.sku),
        }, follow_redirects=True)
        assert response.status_code == 200
        db.session.refresh(not_in_stock_item)
        assert not_in_stock_item.status == 'Not In Stock'

    def test_checkin_already_in_stock_shows_warning(self, client, sample_item, sample_vendor):
        # sample_item is already In-Stock
        response = client.post(f'/vendors/{sample_vendor.id}/checkin', data={
            'sku': str(sample_item.sku),
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'already' in response.data.lower() or b'in-stock' in response.data.lower()

    def test_checkin_invalid_sku_string_shows_error(self, client, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/checkin', data={
            'sku': 'notanumber',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert Inventory.query.filter_by(status='In-Stock').count() == 0

    def test_checkin_empty_sku_shows_error(self, client, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/checkin', data={
            'sku': '',
        }, follow_redirects=True)
        assert response.status_code == 200


class TestVendorCheckout:
    @pytest.fixture()
    def in_stock_item(self, db, sample_vendor):
        item = Inventory(
            sku=6001,
            vendor_id=sample_vendor.id,
            equipment_type='Boots',
            description='Checkout Boot',
            price=60.00,
            status='In-Stock',
        )
        db.session.add(item)
        db.session.commit()
        return item

    def test_get_checkout_page_returns_200(self, client, sample_vendor):
        response = client.get(f'/vendors/{sample_vendor.id}/checkout')
        assert response.status_code == 200

    def test_get_checkout_404_for_missing_vendor(self, client):
        response = client.get('/vendors/9999/checkout')
        assert response.status_code == 404

    def test_scan_sku_returns_to_vendor(self, client, db, in_stock_item, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/checkout', data={
            'action': 'scan',
            'sku': str(in_stock_item.sku),
        }, follow_redirects=True)
        assert response.status_code == 200
        db.session.refresh(in_stock_item)
        assert in_stock_item.status == 'Returned to Vendor'

    def test_button_return_item(self, client, db, in_stock_item, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/checkout', data={
            'action': 'return_item',
            'item_id': str(in_stock_item.id),
        }, follow_redirects=True)
        assert response.status_code == 200
        db.session.refresh(in_stock_item)
        assert in_stock_item.status == 'Returned to Vendor'

    def test_button_donate_item(self, client, db, in_stock_item, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/checkout', data={
            'action': 'donate_item',
            'item_id': str(in_stock_item.id),
        }, follow_redirects=True)
        assert response.status_code == 200
        db.session.refresh(in_stock_item)
        assert in_stock_item.status == 'Donated'

    def test_scan_wrong_vendor_shows_error(self, client, db, in_stock_item):
        other_vendor = Vendor(first_name='Other', last_name='Person', commission_rate=0.20)
        db.session.add(other_vendor)
        db.session.commit()

        response = client.post(f'/vendors/{other_vendor.id}/checkout', data={
            'action': 'scan',
            'sku': str(in_stock_item.sku),
        }, follow_redirects=True)
        assert response.status_code == 200
        db.session.refresh(in_stock_item)
        assert in_stock_item.status == 'In-Stock'

    def test_scan_sku_not_found_shows_error(self, client, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/checkout', data={
            'action': 'scan',
            'sku': '9999999',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'not found' in response.data.lower()

    def test_scan_already_returned_shows_warning(self, client, db, sample_vendor):
        item = Inventory(
            sku=6002,
            vendor_id=sample_vendor.id,
            equipment_type='Poles',
            price=20.00,
            status='Returned to Vendor',
        )
        db.session.add(item)
        db.session.commit()

        response = client.post(f'/vendors/{sample_vendor.id}/checkout', data={
            'action': 'scan',
            'sku': '6002',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_scan_invalid_sku_string_shows_error(self, client, sample_vendor):
        response = client.post(f'/vendors/{sample_vendor.id}/checkout', data={
            'action': 'scan',
            'sku': 'bad',
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_checkout_items_removed_from_list_after_action(self, client, db, in_stock_item, sample_vendor):
        client.post(f'/vendors/{sample_vendor.id}/checkout', data={
            'action': 'return_item',
            'item_id': str(in_stock_item.id),
        })
        response = client.get(f'/vendors/{sample_vendor.id}/checkout')
        # Returned item should no longer appear as actionable
        assert in_stock_item.description.encode() not in response.data or \
               b'Checkout Boot' not in response.data


class TestVendorRegisterStamping:
    def test_create_vendor_stamps_created_by(self, client, db):
        with client.session_transaction() as sess:
            sess['register_id'] = 'Register 1'
        client.post('/vendors/new', data={
            'first_name': 'Tom', 'last_name': 'Test',
            'commission_rate': '20', 'active': 'on',
        })
        vendor = Vendor.query.filter_by(last_name='Test').first()
        assert vendor.created_by == 'Register 1'
        assert vendor.updated_by == 'Register 1'

    def test_create_vendor_without_register_is_blocked(self, client, db):
        with client.session_transaction() as sess:
            sess.pop('register_id', None)
        response = client.post('/vendors/new', data={
            'first_name': 'Tom', 'last_name': 'NoReg',
            'commission_rate': '20', 'active': 'on',
        })
        assert response.status_code == 302
        assert Vendor.query.filter_by(last_name='NoReg').first() is None

    def test_edit_vendor_stamps_updated_by(self, client, db, sample_vendor):
        with client.session_transaction() as sess:
            sess['register_id'] = 'Register 2'
        client.post(f'/vendors/{sample_vendor.id}/edit', data={
            'first_name': sample_vendor.first_name,
            'last_name': sample_vendor.last_name,
            'commission_rate': '20', 'active': 'on',
        })
        db.session.refresh(sample_vendor)
        assert sample_vendor.updated_by == 'Register 2'

    def test_deactivate_vendor_stamps_updated_by(self, client, db, sample_vendor):
        with client.session_transaction() as sess:
            sess['register_id'] = 'Register 3'
        client.post(f'/vendors/{sample_vendor.id}/delete')
        db.session.refresh(sample_vendor)
        assert sample_vendor.updated_by == 'Register 3'

    def test_reactivate_vendor_stamps_updated_by(self, client, db, sample_vendor):
        sample_vendor.active = False
        db.session.commit()
        with client.session_transaction() as sess:
            sess['register_id'] = 'Register 4'
        client.post(f'/vendors/{sample_vendor.id}/reactivate')
        db.session.refresh(sample_vendor)
        assert sample_vendor.updated_by == 'Register 4'


class TestVendorReactivate:
    def test_reactivate_sets_active(self, client, db, sample_vendor):
        sample_vendor.active = False
        db.session.commit()

        client.post(f'/vendors/{sample_vendor.id}/reactivate')

        db.session.refresh(sample_vendor)
        assert sample_vendor.active is True

    def test_reactivate_redirects_to_vendor_list(self, client, db, sample_vendor):
        sample_vendor.active = False
        db.session.commit()

        response = client.post(f'/vendors/{sample_vendor.id}/reactivate')

        assert response.status_code == 302
        assert '/vendors' in response.location

    def test_reactivate_nonexistent_vendor_returns_404(self, client):
        response = client.post('/vendors/9999/reactivate')
        assert response.status_code == 404

    def test_reactivate_with_next_view_redirects_to_vendor_detail(self, client, db, sample_vendor):
        sample_vendor.active = False
        db.session.commit()

        response = client.post(f'/vendors/{sample_vendor.id}/reactivate', data={'next': 'view'})

        assert response.status_code == 302
        assert response.location == f'/vendors/{sample_vendor.id}'


class TestVendorViewActivateButton:
    def test_activate_button_shown_when_inactive(self, client, db, sample_vendor):
        sample_vendor.active = False
        db.session.commit()

        response = client.get(f'/vendors/{sample_vendor.id}')
        assert b'Activate' in response.data

    def test_activate_button_hidden_when_active(self, client, sample_vendor):
        response = client.get(f'/vendors/{sample_vendor.id}')
        assert b'Activate' not in response.data


class TestCheckFeeOnVendorPages:
    """The $1 check processing/mailing fee comes out of every vendor payout
    shown anywhere, so the numbers match the printed check."""

    @pytest.fixture
    def sold(self, db, sample_item, sample_invoice):
        # $150 sold at 20% commission -> $30 commission, $120 - $1 fee = $119
        db.session.add(InvoiceLine(invoice_id=sample_invoice.id,
                                   inventory_id=sample_item.id, price=150.00))
        sample_item.status = 'Sold'
        sample_invoice.calculate_totals()
        db.session.commit()
        return sample_item

    def test_checkout_receipt_shows_fee(self, client, sold):
        html = client.get(f'/vendors/{sold.vendor_id}/checkout-receipt').data
        assert b'Check Processing/Mailing Fee' in html
        assert b'$119.00' in html
        assert b'$120.00' not in html

    def test_checkout_receipt_no_fee_without_sales(self, client, sample_item):
        html = client.get(f'/vendors/{sample_item.vendor_id}/checkout-receipt').data
        assert b'Check Processing/Mailing Fee' not in html

    def test_vendor_view_payout_after_fee(self, client, sold):
        html = client.get(f'/vendors/{sold.vendor_id}').data
        assert b'$119.00' in html
        assert b'$1.00 check fee' in html

    def test_metrics_deduct_fee_once_per_vendor(self, app, db, sold, sample_vendor, sample_invoice):
        # A second item for the same vendor: still only one check, one fee
        item2 = Inventory(sku=7654321, vendor_id=sample_vendor.id, equipment_type='Poles',
                          price=50.00, status='Sold')
        db.session.add(item2)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=sample_invoice.id, inventory_id=item2.id, price=50.00))
        db.session.commit()
        with app.test_request_context():
            m = compute_swap_metrics()
        # $200 sold, $40 commission, $160 - $1 fee
        assert m['total_commission'] == pytest.approx(40.00)
        assert m['total_check_fees'] == pytest.approx(1.00)
        assert m['total_vendor_payout'] == pytest.approx(159.00)

    def test_metrics_parts_add_up_to_subtotal(self, app, sold):
        with app.test_request_context():
            m = compute_swap_metrics()
        parts = m['total_vendor_payout'] + m['total_commission'] + m['total_check_fees']
        assert parts == pytest.approx(m['total_subtotal'])

    def test_dashboard_shows_check_fees(self, client, sold):
        html = client.get('/').data
        assert b'Check Fees' in html
        assert b'$119.00' in html

    def test_swap_summary_shows_check_fees(self, client, sold):
        html = client.get('/admin/summary').data
        assert b'Check Fees' in html
        assert b'$119.00' in html

    def test_dashboard_hides_check_fees_without_sales(self, client, db):
        assert b'Check Fees' not in client.get('/').data


class TestCommissionRateDefault:
    def test_default_is_one_of_the_offered_rates(self):
        from constants import COMMISSION_RATES, DEFAULT_VENDOR_COMMISSION_RATE
        assert round(DEFAULT_VENDOR_COMMISSION_RATE * 100) in [pct for pct, _ in COMMISSION_RATES]

    def test_new_vendor_form_preselects_20_percent(self, client):
        html = client.get('/vendors/new').data.decode()
        assert '<option value="20"\n' in html or '<option value="20"' in html
        selected = html.split('<option value="20"', 1)[1].split('>', 1)[0]
        assert 'selected' in selected

    def test_edit_form_preselects_vendors_rate(self, client, sample_vendor):
        # sample_vendor is at 20%; editing must not fall back to the first option (15%)
        html = client.get(f'/vendors/{sample_vendor.id}/edit').data.decode()
        selected = html.split('<option value="20"', 1)[1].split('>', 1)[0]
        assert 'selected' in selected
        not_selected = html.split('<option value="15"', 1)[1].split('>', 1)[0]
        assert 'selected' not in not_selected


class TestNonStandardCommissionRate:
    """A rate set manually outside COMMISSION_RATES (the MBSP vendor at 100%)
    must survive editing the vendor."""

    @pytest.fixture
    def mbsp_vendor(self, db):
        vendor = Vendor(first_name='MBSP', last_name='Only', commission_rate=1.0,
                        payment_method='Check', active=True)
        db.session.add(vendor)
        db.session.commit()
        return vendor

    def _selected_option(self, html):
        select = html.split('id="commission_rate"', 1)[1].split('</select>', 1)[0]
        for opt in select.split('<option')[1:]:
            tag = opt.split('>', 1)[0]
            if 'selected' in tag:
                return tag.split('value="', 1)[1].split('"', 1)[0]
        return None

    def test_edit_form_keeps_current_rate_selected(self, client, mbsp_vendor):
        html = client.get(f'/vendors/{mbsp_vendor.id}/edit').data.decode()
        assert self._selected_option(html) == '100'
        assert '100% — current rate (not a standard option)' in html

    def test_saving_form_keeps_100_percent(self, client, db, mbsp_vendor):
        html = client.get(f'/vendors/{mbsp_vendor.id}/edit').data.decode()
        client.post(f'/vendors/{mbsp_vendor.id}/edit', data={
            'first_name': 'MBSP', 'last_name': 'Only',
            'commission_rate': self._selected_option(html),
            'payment_method': 'Check', 'active': 'on',
        })
        db.session.refresh(mbsp_vendor)
        assert mbsp_vendor.commission_rate == pytest.approx(1.0)

    def test_standard_rate_has_no_extra_option(self, client, sample_vendor):
        html = client.get(f'/vendors/{sample_vendor.id}/edit').data.decode()
        assert 'not a standard option' not in html
        assert self._selected_option(html) == '20'

    def test_new_vendor_has_no_extra_option(self, client):
        html = client.get('/vendors/new').data.decode()
        assert 'not a standard option' not in html
