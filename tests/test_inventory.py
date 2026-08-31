"""
Tests for inventory routes.
"""
import pytest

from models import Inventory, Vendor


class TestInventoryList:
    def test_list_shows_items(self, client, sample_item):
        response = client.get('/inventory')
        assert response.status_code == 200
        assert b'1234567' in response.data

    def test_filter_by_status(self, client, sample_item):
        response = client.get('/inventory?status=In-Stock')
        assert b'1234567' in response.data

    def test_filter_by_status_no_match(self, client, sample_item):
        response = client.get('/inventory?status=Sold')
        assert b'1234567' not in response.data

    def test_filter_by_equipment_type(self, client, sample_item):
        response = client.get('/inventory?equipment=Skis')
        assert b'1234567' in response.data

    def test_search_by_sku(self, client, sample_item):
        response = client.get('/inventory?search=1234567')
        assert b'1234567' in response.data

    def test_search_by_description(self, client, sample_item):
        response = client.get('/inventory?search=Fischer')
        assert b'1234567' in response.data


class TestInventorySort:
    @pytest.fixture()
    def second_item(self, db, sample_item):
        vendor = Vendor(
            first_name='Amy',
            last_name='Adams',
            commission_rate=0.20,
            payment_method='Cash',
            active=True,
        )
        db.session.add(vendor)
        db.session.commit()
        item = Inventory(
            sku=1111111,
            vendor_id=vendor.id,
            equipment_type='Boots - Ski',
            description='Salomon boots',
            price=75.00,
            status='Sold',
        )
        db.session.add(item)
        db.session.commit()
        return item

    def test_default_sort_is_sku_ascending(self, client, sample_item, second_item):
        response = client.get('/inventory')
        assert response.data.index(b'1111111') < response.data.index(b'1234567')

    def test_sort_by_sku_descending(self, client, sample_item, second_item):
        response = client.get('/inventory?sort=sku&direction=desc')
        assert response.data.index(b'1234567') < response.data.index(b'1111111')

    def test_sort_by_vendor_ascending(self, client, sample_item, second_item):
        # Amy Adams sorts before Jane Doe
        response = client.get('/inventory?sort=vendor&direction=asc')
        assert response.data.index(b'1111111') < response.data.index(b'1234567')

    def test_sort_by_vendor_descending(self, client, sample_item, second_item):
        response = client.get('/inventory?sort=vendor&direction=desc')
        assert response.data.index(b'1234567') < response.data.index(b'1111111')

    def test_sort_by_equipment_type_ascending(self, client, sample_item, second_item):
        # 'Boots - Ski' sorts before 'Skis'
        response = client.get('/inventory?sort=equipment&direction=asc')
        assert response.data.index(b'1111111') < response.data.index(b'1234567')

    def test_sort_by_equipment_type_descending(self, client, sample_item, second_item):
        response = client.get('/inventory?sort=equipment&direction=desc')
        assert response.data.index(b'1234567') < response.data.index(b'1111111')

    def test_sort_by_status_ascending(self, client, sample_item, second_item):
        # 'In-Stock' sorts before 'Sold'
        response = client.get('/inventory?sort=status&direction=asc')
        assert response.data.index(b'1234567') < response.data.index(b'1111111')

    def test_sort_by_status_descending(self, client, sample_item, second_item):
        response = client.get('/inventory?sort=status&direction=desc')
        assert response.data.index(b'1111111') < response.data.index(b'1234567')

    def test_invalid_sort_falls_back_to_sku(self, client, sample_item, second_item):
        response = client.get('/inventory?sort=bogus')
        assert response.data.index(b'1111111') < response.data.index(b'1234567')


class TestInventoryCreate:
    def test_get_new_form(self, client, sample_vendor):
        response = client.get('/inventory/new')
        assert response.status_code == 200

    def test_create_item(self, client, db, sample_vendor):
        response = client.post('/inventory/new', data={
            'sku': '9999001',
            'vendor_id': sample_vendor.id,
            'equipment_type': 'Boots',
            'description': 'Salomon X-Pro',
            'price': '75.00',
            'status': 'In-Stock',
        }, follow_redirects=True)

        assert response.status_code == 200
        item = Inventory.query.filter_by(sku=9999001).first()
        assert item is not None
        assert item.price == 75.00
        assert item.status == 'In-Stock'

    def test_create_item_preselects_vendor(self, client, sample_vendor):
        response = client.get(f'/inventory/new?vendor_id={sample_vendor.id}')
        assert response.status_code == 200

    def test_duplicate_sku_rejected(self, client, db, sample_vendor, sample_item):
        response = client.post('/inventory/new', data={
            'sku': '1234567',  # already exists
            'vendor_id': sample_vendor.id,
            'equipment_type': 'Skis',
            'price': '100.00',
            'status': 'In-Stock',
        }, follow_redirects=True)

        assert Inventory.query.filter_by(sku=1234567).count() == 1


class TestInventoryEdit:
    def test_get_edit_form(self, client, sample_item):
        response = client.get(f'/inventory/{sample_item.id}/edit')
        assert response.status_code == 200
        assert b'1234567' in response.data

    def test_edit_item(self, client, db, sample_item, sample_vendor):
        response = client.post(f'/inventory/{sample_item.id}/edit', data={
            'sku': '1234567',
            'vendor_id': sample_vendor.id,
            'equipment_type': 'Skis',
            'description': 'Updated description',
            'price': '200.00',
            'status': 'In-Stock',
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(sample_item)
        assert sample_item.price == 200.00
        assert sample_item.description == 'Updated description'

    def test_edit_nonexistent_item(self, client):
        response = client.get('/inventory/9999/edit')
        assert response.status_code == 404


class TestInventoryDelete:
    def test_delete_item(self, client, db, sample_item):
        item_id = sample_item.id
        response = client.post(f'/inventory/{item_id}/delete',
                               follow_redirects=True)
        assert response.status_code == 200
        assert db.session.get(Inventory, item_id) is None

    def test_delete_nonexistent_item(self, client):
        response = client.post('/inventory/9999/delete')
        assert response.status_code == 404


class TestInventoryView:
    def test_view_item(self, client, sample_item):
        response = client.get(f'/inventory/{sample_item.id}')
        assert response.status_code == 200
        assert b'1234567' in response.data


class TestInventoryRegisterStamping:
    def test_create_item_stamps_created_by(self, client, db, sample_vendor):
        with client.session_transaction() as sess:
            sess['register_id'] = 'Register 1'
        client.post('/inventory/new', data={
            'sku': '9000001',
            'vendor_id': str(sample_vendor.id),
            'equipment_type': 'Skis',
            'price': '100',
            'status': 'In-Stock',
        })
        item = Inventory.query.filter_by(sku=9000001).first()
        assert item.created_by == 'Register 1'
        assert item.updated_by == 'Register 1'

    def test_create_item_without_register_is_blocked(self, client, db, sample_vendor):
        with client.session_transaction() as sess:
            sess.pop('register_id', None)
        response = client.post('/inventory/new', data={
            'sku': '9000002',
            'vendor_id': str(sample_vendor.id),
            'equipment_type': 'Skis',
            'price': '100',
            'status': 'In-Stock',
        })
        assert response.status_code == 302
        assert Inventory.query.filter_by(sku=9000002).first() is None

    def test_edit_item_stamps_updated_by(self, client, db, sample_item):
        with client.session_transaction() as sess:
            sess['register_id'] = 'Register 2'
        client.post(f'/inventory/{sample_item.id}/edit', data={
            'sku': str(sample_item.sku),
            'vendor_id': str(sample_item.vendor_id),
            'equipment_type': sample_item.equipment_type,
            'price': str(sample_item.price),
            'status': sample_item.status,
        })
        db.session.refresh(sample_item)
        assert sample_item.updated_by == 'Register 2'

    def test_edit_item_does_not_change_created_by(self, client, db, sample_item):
        sample_item.created_by = 'Register 1'
        db.session.commit()
        with client.session_transaction() as sess:
            sess['register_id'] = 'Register 2'
        client.post(f'/inventory/{sample_item.id}/edit', data={
            'sku': str(sample_item.sku),
            'vendor_id': str(sample_item.vendor_id),
            'equipment_type': sample_item.equipment_type,
            'price': str(sample_item.price),
            'status': sample_item.status,
        })
        db.session.refresh(sample_item)
        assert sample_item.created_by == 'Register 1'
        assert sample_item.updated_by == 'Register 2'


class TestInventoryAPI:
    def test_api_returns_all_items(self, client, sample_item):
        response = client.get('/api/inventory')
        assert response.status_code == 200
        data = response.get_json()
        assert any(item['sku'] == 1234567 for item in data)

    def test_api_get_single_item(self, client, sample_item):
        response = client.get(f'/api/inventory/{sample_item.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['sku'] == 1234567
        assert data['price'] == 150.00
