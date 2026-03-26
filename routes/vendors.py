"""
Vendor and dashboard routes.
"""
import csv
import io
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from models import db, Vendor, Inventory, Invoice, InvoiceLine
from constants import EQUIPMENT_TYPES, INVENTORY_STATUSES, PAYMENT_METHODS, EASTERN, COMMISSION_RATES, VENDOR_PAYMENT_METHODS, DEFAULT_VENDOR_COMMISSION_RATE, SKU_MIN, SKU_MAX

vendors_bp = Blueprint('vendors', __name__)


@vendors_bp.before_request
def require_register_for_writes():
    if request.method == 'POST':
        if not session.get('register_id'):
            flash('Please set your register ID before making changes.', 'error')
            return redirect(request.referrer or url_for('vendors.vendors_list'))


@vendors_bp.route('/')
def index():
    """Dashboard - Home page with sales metrics"""
    # Vendor metrics
    active_vendors = Vendor.query.filter_by(active=True).count()

    # Inventory metrics
    total_inventory = Inventory.query.count()
    inventory_by_status = {}
    for status in INVENTORY_STATUSES:
        count = Inventory.query.filter_by(status=status).count()
        inventory_by_status[status] = count

    # Sales metrics
    all_invoices = Invoice.query.all()
    total_sales = sum(invoice.total for invoice in all_invoices)  # Grand total with tax
    total_tax = sum(invoice.tax_amount for invoice in all_invoices)
    total_subtotal = sum(invoice.subtotal for invoice in all_invoices)  # Before tax
    total_discounts = sum(invoice.discount_amount for invoice in all_invoices)

    # Calculate vendor payouts and commissions from INVOICE LINES (not just sold items)
    # This ensures we only count items that were actually sold through invoices
    total_vendor_payout = 0
    total_commission = 0

    # Go through all invoice lines to calculate payouts
    for invoice in all_invoices:
        for line in invoice.lines:
            item = line.inventory_item
            vendor = item.vendor
            item_price = line.price  # Use price from invoice line (price at time of sale)
            commission = item_price * vendor.commission_rate
            payout = item_price - commission
            total_commission += commission
            total_vendor_payout += payout

    # Payment method breakdown
    payment_breakdown = {}
    for invoice in all_invoices:
        method = invoice.payment_method or 'Unknown'
        if method not in payment_breakdown:
            payment_breakdown[method] = {'count': 0, 'total': 0.0}
        payment_breakdown[method]['count'] += 1
        payment_breakdown[method]['total'] += invoice.total
    payment_breakdown = dict(
        sorted(payment_breakdown.items(), key=lambda x: x[1]['total'], reverse=True)
    )

    return render_template('dashboard.html',
                         active_vendors=active_vendors,
                         total_inventory=total_inventory,
                         inventory_by_status=inventory_by_status,
                         total_sales=total_sales,
                         total_tax=total_tax,
                         total_subtotal=total_subtotal,
                         total_discounts=total_discounts,
                         total_vendor_payout=total_vendor_payout,
                         total_commission=total_commission,
                         num_invoices=len(all_invoices),
                         payment_breakdown=payment_breakdown)


@vendors_bp.route('/vendors')
def vendors_list():
    """Display all vendors"""
    # Get filter parameters
    # If active_only is not in request args, default to true
    # If it's present (even as empty), user unchecked it, so set to false
    active_only = request.args.get('active_only', None)
    if active_only is None:
        active_only = False  # Default to showing all vendors
    else:
        active_only = active_only == 'true'

    search = request.args.get('search', '')
    sort = request.args.get('sort', 'name')
    direction = request.args.get('direction', 'asc')

    # Build query
    query = Vendor.query

    if active_only:
        query = query.filter_by(active=True)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Vendor.first_name.ilike(search_term),
                Vendor.last_name.ilike(search_term),
                Vendor.email.ilike(search_term)
            )
        )

    if sort == 'id':
        order = Vendor.id.desc() if direction == 'desc' else Vendor.id
    else:
        if direction == 'desc':
            order = (Vendor.last_name.desc(), Vendor.first_name.desc())
        else:
            order = (Vendor.last_name, Vendor.first_name)

    vendors = query.order_by(*order if isinstance(order, tuple) else (order,)).all()

    return render_template('vendors_list.html',
                         vendors=vendors,
                         active_only=active_only,
                         search=search,
                         sort=sort,
                         direction=direction)


@vendors_bp.route('/vendors/new', methods=['GET', 'POST'])
def vendor_new():
    """Create new vendor"""
    if request.method == 'POST':
        try:
            vendor = Vendor(
                first_name=request.form['first_name'].strip(),
                last_name=request.form['last_name'].strip(),
                phone=request.form.get('phone', '').strip(),
                email=request.form.get('email', '').strip(),
                address1=request.form.get('address1', '').strip(),
                address2=request.form.get('address2', '').strip(),
                city=request.form.get('city', '').strip(),
                state=request.form.get('state', '').strip(),
                zip_code=request.form.get('zip_code', '').strip(),
                commission_rate=float(request.form.get('commission_rate', DEFAULT_VENDOR_COMMISSION_RATE * 100)) / 100,
                payment_method=request.form.get('payment_method', '').strip(),
                notes=request.form.get('notes', '').strip(),
                active=request.form.get('active') == 'on',
                created_by=session.get('register_id'),
                updated_by=session.get('register_id'),
            )

            db.session.add(vendor)
            db.session.commit()

            flash(f'Vendor "{vendor.full_name}" created successfully!', 'success')
            return redirect(url_for('vendors.vendor_view', vendor_id=vendor.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating vendor: {str(e)}', 'error')

    return render_template('vendor_form.html', vendor=None, action='New',
                           commission_rates=COMMISSION_RATES,
                           vendor_payment_methods=VENDOR_PAYMENT_METHODS)


@vendors_bp.route('/vendors/<int:vendor_id>/edit', methods=['GET', 'POST'])
def vendor_edit(vendor_id):
    """Edit existing vendor"""
    vendor = db.get_or_404(Vendor, vendor_id)

    if request.method == 'POST':
        try:
            vendor.first_name = request.form['first_name'].strip()
            vendor.last_name = request.form['last_name'].strip()
            vendor.phone = request.form.get('phone', '').strip()
            vendor.email = request.form.get('email', '').strip()
            vendor.address1 = request.form.get('address1', '').strip()
            vendor.address2 = request.form.get('address2', '').strip()
            vendor.city = request.form.get('city', '').strip()
            vendor.state = request.form.get('state', '').strip()
            vendor.zip_code = request.form.get('zip_code', '').strip()
            vendor.commission_rate = float(request.form.get('commission_rate', DEFAULT_VENDOR_COMMISSION_RATE * 100)) / 100
            vendor.payment_method = request.form.get('payment_method', '').strip()
            vendor.notes = request.form.get('notes', '').strip()
            vendor.active = request.form.get('active') == 'on'
            vendor.updated_by = session.get('register_id')

            db.session.commit()

            flash(f'Vendor "{vendor.full_name}" updated successfully!', 'success')
            return redirect(url_for('vendors.vendor_view', vendor_id=vendor.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating vendor: {str(e)}', 'error')

    return render_template('vendor_form.html', vendor=vendor, action='Edit',
                           commission_rates=COMMISSION_RATES,
                           vendor_payment_methods=VENDOR_PAYMENT_METHODS)


@vendors_bp.route('/vendors/<int:vendor_id>/delete', methods=['POST'])
def vendor_delete(vendor_id):
    """Delete vendor (soft delete by setting active=False)"""
    vendor = db.get_or_404(Vendor, vendor_id)

    try:
        vendor.active = False
        vendor.updated_by = session.get('register_id')
        db.session.commit()
        flash(f'Vendor "{vendor.full_name}" deactivated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deactivating vendor: {str(e)}', 'error')

    return redirect(url_for('vendors.vendors_list',
        search=request.form.get('search', ''),
        active_only=request.form.get('active_only', 'false'),
        sort=request.form.get('sort', 'name'),
        direction=request.form.get('direction', 'asc')))


@vendors_bp.route('/vendors/<int:vendor_id>/reactivate', methods=['POST'])
def vendor_reactivate(vendor_id):
    """Reactivate a previously deactivated vendor"""
    vendor = db.get_or_404(Vendor, vendor_id)

    try:
        vendor.active = True
        vendor.updated_by = session.get('register_id')
        db.session.commit()
        flash(f'Vendor "{vendor.full_name}" reactivated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error reactivating vendor: {str(e)}', 'error')

    return redirect(url_for('vendors.vendors_list',
        search=request.form.get('search', ''),
        active_only=request.form.get('active_only', 'false'),
        sort=request.form.get('sort', 'name'),
        direction=request.form.get('direction', 'asc')))


@vendors_bp.route('/vendors/<int:vendor_id>')
def vendor_view(vendor_id):
    """View vendor details"""
    vendor = db.get_or_404(Vendor, vendor_id)
    return render_template('vendor_view.html', vendor=vendor)


@vendors_bp.route('/vendors/<int:vendor_id>/receipt')
def vendor_receipt(vendor_id):
    """Print a check-in receipt listing all inventory for a vendor."""
    vendor = db.get_or_404(Vendor, vendor_id)
    checkedin_items = (Inventory.query
                       .filter_by(vendor_id=vendor.id)
                       .order_by(Inventory.sku)
                       .all())
    return render_template('vendor_receipt.html', vendor=vendor,
                           checkedin_items=checkedin_items,
                           now=datetime.now(EASTERN))


@vendors_bp.route('/vendors/<int:vendor_id>/checkout-receipt')
def vendor_checkout_receipt(vendor_id):
    """Print a checkout/payout receipt for a vendor."""
    vendor = db.get_or_404(Vendor, vendor_id)
    items = (Inventory.query
             .filter_by(vendor_id=vendor.id)
             .order_by(Inventory.sku)
             .all())
    sold_items = [i for i in items if i.status == 'Sold']
    total_sales = sum(i.price for i in sold_items)
    commission_amt = total_sales * vendor.commission_rate
    payout_amt = total_sales - commission_amt
    return render_template('vendor_checkout_receipt.html', vendor=vendor,
                           items=items, sold_items=sold_items,
                           total_sales=total_sales,
                           commission_amt=commission_amt,
                           payout_amt=payout_amt,
                           now=datetime.now(EASTERN))


@vendors_bp.route('/vendors/<int:vendor_id>/import', methods=['GET', 'POST'])
def vendor_import_csv(vendor_id):
    """Import inventory items from a CSV file for a vendor."""
    vendor = db.get_or_404(Vendor, vendor_id)

    if request.method == 'GET':
        return render_template('vendor_import.html', vendor=vendor)

    # POST: process uploaded file
    uploaded_file = request.files.get('csv_file')
    if not uploaded_file or not uploaded_file.filename:
        flash('Please select a CSV file to upload.', 'error')
        return render_template('vendor_import.html', vendor=vendor)

    if not uploaded_file.filename.lower().endswith('.csv'):
        flash('File must be a .csv file.', 'error')
        return render_template('vendor_import.html', vendor=vendor)

    # Read file as text
    stream = io.StringIO(uploaded_file.stream.read().decode('utf-8-sig'))
    reader = csv.DictReader(stream)

    # Normalise header names to lowercase with no spaces for flexible matching
    if reader.fieldnames is None:
        flash('The CSV file appears to be empty.', 'error')
        return render_template('vendor_import.html', vendor=vendor)

    # Map normalised header → actual header name
    header_map = {h.strip().lower().replace(' ', '_'): h for h in reader.fieldnames}

    def get_col(row, *candidates):
        """Return the first matching column value, or None."""
        for name in candidates:
            if name in header_map:
                return row.get(header_map[name], '').strip()
        return None

    imported, skipped = [], []

    for line_num, row in enumerate(reader, start=2):
        sku         = get_col(row, 'sku', 'barcode', 'item_number', 'upc')
        description = get_col(row, 'description', 'desc', 'item_description', 'name', 'item_name')
        price_raw   = get_col(row, 'price', 'cost', 'amount', 'retail_price', 'retail')
        equip_type  = get_col(row, 'equipment_type', 'type', 'equipment', 'category', 'item_type')

        # Validate required fields
        if not sku:
            skipped.append({'row': line_num, 'sku': '(blank)', 'reason': 'Missing SKU'})
            continue

        try:
            sku = int(sku)
            if not (SKU_MIN <= sku <= SKU_MAX):
                raise ValueError
        except ValueError:
            skipped.append({'row': line_num, 'sku': str(sku), 'reason': f'SKU must be a number {SKU_MIN}–{SKU_MAX}'})
            continue

        if not price_raw:
            skipped.append({'row': line_num, 'sku': sku, 'reason': 'Missing price'})
            continue

        try:
            price = float(price_raw.replace('$', '').replace(',', ''))
        except ValueError:
            skipped.append({'row': line_num, 'sku': sku, 'reason': f'Invalid price: {price_raw!r}'})
            continue

        # Check for duplicate SKU
        if Inventory.query.filter_by(sku=sku).first():
            skipped.append({'row': line_num, 'sku': sku, 'reason': 'SKU already exists'})
            continue

        # Map equipment type to a known value, default to 'Other'
        matched_type = 'Other'
        if equip_type:
            for known in EQUIPMENT_TYPES:
                if equip_type.lower() == known.lower():
                    matched_type = known
                    break

        item = Inventory(
            sku=sku,
            vendor_id=vendor.id,
            equipment_type=matched_type,
            description=description or '',
            price=price,
            status='Not In Stock',
            created_by=session.get('register_id'),
            updated_by=session.get('register_id'),
        )
        db.session.add(item)
        imported.append({'sku': sku, 'description': description or '—',
                         'type': matched_type, 'price': price})

    if imported:
        db.session.commit()

    return render_template('vendor_import.html', vendor=vendor,
                           imported=imported, skipped=skipped)


@vendors_bp.route('/vendors/<int:vendor_id>/checkin', methods=['GET', 'POST'])
def vendor_checkin(vendor_id):
    """Scan SKUs to mark items as In-Stock for a vendor."""
    vendor = db.get_or_404(Vendor, vendor_id)

    # Items still awaiting check-in (owned by this vendor, not yet in stock)
    CHECKIN_STATUSES = ['Not In Stock']
    pending_items = (Inventory.query
                     .filter_by(vendor_id=vendor.id)
                     .filter(Inventory.status.in_(CHECKIN_STATUSES))
                     .order_by(Inventory.sku)
                     .all())

    checked_in_item = None

    if request.method == 'POST':
        sku_raw = request.form.get('sku', '').strip()
        sku = None
        if not sku_raw:
            flash('Please enter or scan a SKU.', 'error')
        else:
            try:
                sku = int(sku_raw)
            except ValueError:
                flash(f'SKU "{sku_raw}" is not a valid number.', 'error')

        if sku is not None:
            item = Inventory.query.filter_by(sku=sku).first()

            if not item:
                flash(f'SKU {sku} not found.', 'error')
            elif item.vendor_id != vendor.id:
                flash(f'SKU {sku} belongs to a different vendor — not checked in.', 'error')
            elif item.status == 'In-Stock':
                flash(f'SKU {sku} ({item.description or item.equipment_type}) is already In-Stock.', 'warning')
            elif item.status not in CHECKIN_STATUSES:
                flash(f'SKU {sku} has status "{item.status}" and cannot be checked in.', 'error')
            else:
                item.status = 'In-Stock'
                item.updated_by = session.get('register_id')
                db.session.commit()
                checked_in_item = item
                # Refresh pending list after change
                pending_items = (Inventory.query
                                 .filter_by(vendor_id=vendor.id)
                                 .filter(Inventory.status.in_(CHECKIN_STATUSES))
                                 .order_by(Inventory.sku)
                                 .all())

    return render_template('vendor_checkin.html', vendor=vendor,
                           pending_items=pending_items,
                           checked_in_item=checked_in_item)


@vendors_bp.route('/vendors/<int:vendor_id>/checkout', methods=['GET', 'POST'])
def vendor_checkout(vendor_id):
    """Scan SKUs or click buttons to return/donate In-Stock or Rejected items for a vendor."""
    vendor = db.get_or_404(Vendor, vendor_id)

    def _refresh_checkout_items():
        return (Inventory.query
                .filter(Inventory.vendor_id == vendor.id,
                        Inventory.status.in_(['In-Stock', 'Rejected']))
                .order_by(Inventory.sku)
                .all())

    checkout_items = _refresh_checkout_items()
    actioned_item = None
    action_label = None

    if request.method == 'POST':
        action = request.form.get('action', 'scan')

        if action in ('return_item', 'donate_item'):
            # Per-row button click — resolve by item ID
            item_id = request.form.get('item_id', type=int)
            item = db.get_or_404(Inventory, item_id)
            if item.vendor_id != vendor.id:
                flash(f'SKU {item.sku} belongs to a different vendor.', 'error')
            elif item.status not in ('In-Stock', 'Rejected'):
                flash(f'SKU {item.sku} has status "{item.status}" and cannot be actioned.', 'warning')
            else:
                if action == 'return_item':
                    item.status = 'Returned to Vendor'
                    action_label = 'Returned'
                else:
                    item.status = 'Donated'
                    action_label = 'Donated'
                item.updated_by = session.get('register_id')
                db.session.commit()
                actioned_item = item
                checkout_items = _refresh_checkout_items()

        else:
            # Barcode scan — resolve by SKU
            sku_raw = request.form.get('sku', '').strip()
            sku = None
            if not sku_raw:
                flash('Please enter or scan a SKU.', 'error')
            else:
                try:
                    sku = int(sku_raw)
                except ValueError:
                    flash(f'SKU "{sku_raw}" is not a valid number.', 'error')

            if sku is not None:
                item = Inventory.query.filter_by(sku=sku).first()
                if not item:
                    flash(f'SKU {sku} not found.', 'error')
                elif item.vendor_id != vendor.id:
                    flash(f'SKU {sku} belongs to a different vendor — not checked out.', 'error')
                elif item.status == 'Returned to Vendor':
                    flash(f'SKU {sku} ({item.description or item.equipment_type}) has already been returned.', 'warning')
                elif item.status not in ('In-Stock', 'Rejected'):
                    flash(f'SKU {sku} has status "{item.status}" and cannot be returned.', 'error')
                else:
                    item.status = 'Returned to Vendor'
                    item.updated_by = session.get('register_id')
                    db.session.commit()
                    actioned_item = item
                    action_label = 'Returned'
                    checkout_items = _refresh_checkout_items()

    return render_template('vendor_checkout.html', vendor=vendor,
                           checkout_items=checkout_items,
                           actioned_item=actioned_item,
                           action_label=action_label)
