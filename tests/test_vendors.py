"""
Tests for vendor routes.
"""
import io
import pytest
from models import Vendor, Inventory


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

    def test_import_unknown_equipment_type_defaults_to_other(self, client, db, sample_vendor):
        csv_data = b'SKU,Price,Equipment Type\n3004,75.00,Surfboard\n'
        data = {'csv_file': (io.BytesIO(csv_data), 'items.csv')}
        client.post(
            f'/vendors/{sample_vendor.id}/import',
            data=data,
            content_type='multipart/form-data',
        )
        item = Inventory.query.filter_by(sku=3004).first()
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
