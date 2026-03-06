"""
Tests for vendor routes.
"""
from models import Vendor


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
