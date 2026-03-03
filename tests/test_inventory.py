"""
Tests for inventory routes.
"""
from models import Inventory


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
