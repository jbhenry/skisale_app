"""
Inventory routes.
"""
from sqlalchemy import cast, String
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from models import db, Vendor, Inventory
from constants import EQUIPMENT_TYPES, INVENTORY_STATUSES

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.before_request
def require_register_for_writes():
    if request.method == 'POST':
        if not session.get('register_id'):
            flash('Please set your register ID before making changes.', 'error')
            return redirect(request.referrer or url_for('inventory.inventory_list'))


@inventory_bp.route('/inventory')
def inventory_list():
    """Display all inventory items"""
    # Get filter parameters
    status_filter = request.args.get('status', '')
    equipment_filter = request.args.get('equipment', '')
    vendor_filter = request.args.get('vendor', '')
    donate_filter = request.args.get('donate', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'sku')
    direction = request.args.get('direction', 'asc')

    # Build query
    query = Inventory.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    if equipment_filter:
        query = query.filter_by(equipment_type=equipment_filter)

    if vendor_filter:
        query = query.filter_by(vendor_id=int(vendor_filter))

    if donate_filter == 'yes':
        query = query.filter_by(donate_if_not_sold=True)
    elif donate_filter == 'no':
        query = query.filter_by(donate_if_not_sold=False)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                cast(Inventory.sku, String).like(search_term),
                Inventory.description.ilike(search_term)
            )
        )

    if sort == 'vendor':
        query = query.join(Vendor, Inventory.vendor_id == Vendor.id)
        if direction == 'desc':
            order = (Vendor.last_name.desc(), Vendor.first_name.desc())
        else:
            order = (Vendor.last_name, Vendor.first_name)
    elif sort == 'equipment':
        order = (Inventory.equipment_type.desc(),) if direction == 'desc' else (Inventory.equipment_type,)
    elif sort == 'status':
        order = (Inventory.status.desc(),) if direction == 'desc' else (Inventory.status,)
    else:
        sort = 'sku'
        order = (Inventory.sku.desc(),) if direction == 'desc' else (Inventory.sku,)

    inventory_items = query.order_by(*order).all()
    vendors = Vendor.query.filter_by(active=True).order_by(Vendor.last_name, Vendor.first_name).all()

    return render_template('inventory_list.html',
                         inventory_items=inventory_items,
                         vendors=vendors,
                         equipment_types=EQUIPMENT_TYPES,
                         statuses=INVENTORY_STATUSES,
                         status_filter=status_filter,
                         equipment_filter=equipment_filter,
                         vendor_filter=vendor_filter,
                         donate_filter=donate_filter,
                         search=search,
                         sort=sort,
                         direction=direction)


@inventory_bp.route('/inventory/new', methods=['GET', 'POST'])
def inventory_new():
    """Create new inventory item"""
    if request.method == 'POST':
        try:
            item = Inventory(
                sku=int(request.form['sku']),
                vendor_id=int(request.form['vendor_id']),
                equipment_type=request.form['equipment_type'],
                description=request.form.get('description', '').strip(),
                price=float(request.form['price']),
                status=request.form['status'],
                donate_if_not_sold=request.form.get('donate_if_not_sold') == 'on',
                notes=request.form.get('notes', '').strip(),
                created_by=session.get('register_id'),
                updated_by=session.get('register_id'),
            )

            db.session.add(item)
            db.session.commit()

            flash(f'Inventory item SKU {item.sku} created successfully!', 'success')
            # Redirect back to add another item for the same vendor
            return redirect(url_for('inventory.inventory_new', vendor_id=item.vendor_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating inventory item: {str(e)}', 'error')

    # Get vendor_id from URL parameter if present
    preselect_vendor_id = request.args.get('vendor_id', type=int)

    vendors = Vendor.query.filter_by(active=True).order_by(Vendor.last_name, Vendor.first_name).all()
    return render_template('inventory_form.html',
                         item=None,
                         action='New',
                         vendors=vendors,
                         equipment_types=EQUIPMENT_TYPES,
                         statuses=INVENTORY_STATUSES,
                         preselect_vendor_id=preselect_vendor_id)


@inventory_bp.route('/inventory/<int:item_id>/edit', methods=['GET', 'POST'])
def inventory_edit(item_id):
    """Edit existing inventory item"""
    item = db.get_or_404(Inventory, item_id)

    if request.method == 'POST':
        try:
            item.sku = int(request.form['sku'])
            item.vendor_id = int(request.form['vendor_id'])
            item.equipment_type = request.form['equipment_type']
            item.description = request.form.get('description', '').strip()
            item.price = float(request.form['price'])
            item.status = request.form['status']
            item.donate_if_not_sold = request.form.get('donate_if_not_sold') == 'on'
            item.notes = request.form.get('notes', '').strip()
            item.updated_by = session.get('register_id')

            db.session.commit()

            flash(f'Inventory item SKU {item.sku} updated successfully!', 'success')
            return redirect(url_for('inventory.inventory_view', item_id=item.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating inventory item: {str(e)}', 'error')

    vendors = Vendor.query.filter_by(active=True).order_by(Vendor.last_name, Vendor.first_name).all()
    return render_template('inventory_form.html',
                         item=item,
                         action='Edit',
                         vendors=vendors,
                         equipment_types=EQUIPMENT_TYPES,
                         statuses=INVENTORY_STATUSES)


@inventory_bp.route('/inventory/<int:item_id>/delete', methods=['POST'])
def inventory_delete(item_id):
    """Delete inventory item"""
    item = db.get_or_404(Inventory, item_id)

    try:
        sku = item.sku
        db.session.delete(item)
        db.session.commit()
        flash(f'Inventory item SKU {sku} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting inventory item: {str(e)}', 'error')

    return redirect(url_for('inventory.inventory_list'))


@inventory_bp.route('/inventory/<int:item_id>')
def inventory_view(item_id):
    """View inventory item details"""
    item = db.get_or_404(Inventory, item_id)
    return render_template('inventory_view.html', item=item)
