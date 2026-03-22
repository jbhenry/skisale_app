"""
JSON API endpoints.
"""
from flask import Blueprint, jsonify

from models import db, Vendor, Inventory

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/inventory')
def api_inventory_list():
    """API endpoint to get inventory as JSON"""
    items = Inventory.query.order_by(Inventory.created_at.desc()).all()
    return jsonify([item.to_dict() for item in items])


@api_bp.route('/api/inventory/<int:item_id>')
def api_inventory_get(item_id):
    """API endpoint to get single inventory item"""
    item = db.get_or_404(Inventory, item_id)
    return jsonify(item.to_dict())


@api_bp.route('/api/vendors')
def api_vendors_list():
    """API endpoint to get vendors as JSON"""
    vendors = Vendor.query.filter_by(active=True).order_by(Vendor.last_name, Vendor.first_name).all()
    return jsonify([v.to_dict() for v in vendors])


@api_bp.route('/api/vendors/<int:vendor_id>')
def api_vendor_get(vendor_id):
    """API endpoint to get single vendor"""
    vendor = db.get_or_404(Vendor, vendor_id)
    return jsonify(vendor.to_dict())
