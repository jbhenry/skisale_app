"""
SkiSale Flask Application
Main application file with vendor management
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Vendor, Inventory, Invoice, InvoiceLine
from sqlalchemy import text
import os
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skisale.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Equipment types and statuses
EQUIPMENT_TYPES = [
    'Skis',
    'Snowboards',
    'Boots',
    'Poles',
    'Bindings',
    'Helmets',
    'Goggles',
    'Apparel',
    'Accessories',
    'Other'
]

INVENTORY_STATUSES = [
    'In-Stock',
    'Pending',
    'Not In Stock',
    'Donated',
    'Sold',
    'Rejected',
    'Returned to Vendor'
]

PAYMENT_METHODS = [
    'Cash',
    'Credit Card',
    'Debit Card',
    'Check',
    'Other'
]

# Default sales tax rate (can be changed per invoice)
DEFAULT_TAX_RATE = 0.06  # 6%

# Create tables and run lightweight column migrations
with app.app_context():
    db.create_all()
    # Add donate_if_not_sold column if upgrading from an older schema
    try:
        db.session.execute(text(
            'ALTER TABLE inventory ADD COLUMN donate_if_not_sold BOOLEAN NOT NULL DEFAULT 0'
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()  # Column already exists — nothing to do

@app.route('/')
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
    
    return render_template('dashboard.html',
                         active_vendors=active_vendors,
                         total_inventory=total_inventory,
                         inventory_by_status=inventory_by_status,
                         total_sales=total_sales,
                         total_tax=total_tax,
                         total_subtotal=total_subtotal,
                         total_vendor_payout=total_vendor_payout,
                         total_commission=total_commission,
                         num_invoices=len(all_invoices))

@app.route('/vendors')
def vendors_list():
    """Display all vendors"""
    # Get filter parameters
    # If active_only is not in request args, default to true
    # If it's present (even as empty), user unchecked it, so set to false
    active_only = request.args.get('active_only', None)
    if active_only is None:
        active_only = True  # Default to showing only active
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

@app.route('/vendors/new', methods=['GET', 'POST'])
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
                commission_rate=float(request.form.get('commission_rate', 20)) / 100,
                payment_method=request.form.get('payment_method', '').strip(),
                notes=request.form.get('notes', '').strip(),
                active=request.form.get('active') == 'on'
            )
            
            db.session.add(vendor)
            db.session.commit()
            
            flash(f'Consignor "{vendor.full_name}" created successfully!', 'success')
            return redirect(url_for('vendor_view', vendor_id=vendor.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating consignor: {str(e)}', 'error')
    
    return render_template('vendor_form.html', vendor=None, action='New')

@app.route('/vendors/<int:vendor_id>/edit', methods=['GET', 'POST'])
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
            vendor.commission_rate = float(request.form.get('commission_rate', 20)) / 100
            vendor.payment_method = request.form.get('payment_method', '').strip()
            vendor.notes = request.form.get('notes', '').strip()
            vendor.active = request.form.get('active') == 'on'
            
            db.session.commit()
            
            flash(f'Consignor "{vendor.full_name}" updated successfully!', 'success')
            return redirect(url_for('vendors_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating consignor: {str(e)}', 'error')
    
    return render_template('vendor_form.html', vendor=vendor, action='Edit')

@app.route('/vendors/<int:vendor_id>/delete', methods=['POST'])
def vendor_delete(vendor_id):
    """Delete vendor (soft delete by setting active=False)"""
    vendor = db.get_or_404(Vendor, vendor_id)
    
    try:
        vendor.active = False
        db.session.commit()
        flash(f'Consignor "{vendor.full_name}" deactivated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deactivating consignor: {str(e)}', 'error')
    
    return redirect(url_for('vendors_list'))

@app.route('/vendors/<int:vendor_id>')
def vendor_view(vendor_id):
    """View vendor details"""
    vendor = db.get_or_404(Vendor, vendor_id)
    return render_template('vendor_view.html', vendor=vendor)

@app.route('/vendors/<int:vendor_id>/receipt')
def vendor_receipt(vendor_id):
    """Print a check-in receipt listing all inventory for a vendor."""
    from datetime import datetime, timezone
    vendor = db.get_or_404(Vendor, vendor_id)
    checkedin_items = (Inventory.query
                       .filter_by(vendor_id=vendor.id)
                       .order_by(Inventory.sku)
                       .all())
    return render_template('vendor_receipt.html', vendor=vendor,
                           checkedin_items=checkedin_items,
                           now=datetime.now(timezone.utc))

@app.route('/vendors/<int:vendor_id>/checkout-receipt')
def vendor_checkout_receipt(vendor_id):
    """Print a checkout/payout receipt for a vendor."""
    from datetime import datetime, timezone
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
                           now=datetime.now(timezone.utc))

@app.route('/vendors/<int:vendor_id>/import', methods=['GET', 'POST'])
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
        )
        db.session.add(item)
        imported.append({'sku': sku, 'description': description or '—',
                         'type': matched_type, 'price': price})

    if imported:
        db.session.commit()

    return render_template('vendor_import.html', vendor=vendor,
                           imported=imported, skipped=skipped)

@app.route('/vendors/<int:vendor_id>/checkin', methods=['GET', 'POST'])
def vendor_checkin(vendor_id):
    """Scan SKUs to mark items as In-Stock for a vendor."""
    vendor = db.get_or_404(Vendor, vendor_id)

    # Items still awaiting check-in (owned by this vendor, not yet in stock)
    CHECKIN_STATUSES = ['Not In Stock', 'Returned to Vendor']
    pending_items = (Inventory.query
                     .filter_by(vendor_id=vendor.id)
                     .filter(Inventory.status.in_(CHECKIN_STATUSES))
                     .order_by(Inventory.sku)
                     .all())

    checked_in_item = None

    if request.method == 'POST':
        sku = request.form.get('sku', '').strip()

        if not sku:
            flash('Please enter or scan a SKU.', 'error')
        else:
            item = Inventory.query.filter_by(sku=sku).first()

            if not item:
                flash(f'SKU {sku} not found.', 'error')
            elif item.vendor_id != vendor.id:
                flash(f'SKU {sku} belongs to a different consignor — not checked in.', 'error')
            elif item.status == 'In-Stock':
                flash(f'SKU {sku} ({item.description or item.equipment_type}) is already In-Stock.', 'warning')
            elif item.status not in CHECKIN_STATUSES:
                flash(f'SKU {sku} has status "{item.status}" and cannot be checked in.', 'error')
            else:
                item.status = 'In-Stock'
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


@app.route('/vendors/<int:vendor_id>/checkout', methods=['GET', 'POST'])
def vendor_checkout(vendor_id):
    """Scan SKUs to mark items as Returned to Vendor for a vendor."""
    vendor = db.get_or_404(Vendor, vendor_id)

    # Items currently In-Stock for this vendor (eligible for return)
    in_stock_items = (Inventory.query
                      .filter_by(vendor_id=vendor.id, status='In-Stock')
                      .order_by(Inventory.sku)
                      .all())

    checked_out_item = None

    if request.method == 'POST':
        sku = request.form.get('sku', '').strip()

        if not sku:
            flash('Please enter or scan a SKU.', 'error')
        else:
            item = Inventory.query.filter_by(sku=sku).first()

            if not item:
                flash(f'SKU {sku} not found.', 'error')
            elif item.vendor_id != vendor.id:
                flash(f'SKU {sku} belongs to a different consignor — not checked out.', 'error')
            elif item.status == 'Returned to Vendor':
                flash(f'SKU {sku} ({item.description or item.equipment_type}) has already been returned.', 'warning')
            elif item.status != 'In-Stock':
                flash(f'SKU {sku} has status "{item.status}" and cannot be returned.', 'error')
            else:
                item.status = 'Returned to Vendor'
                db.session.commit()
                checked_out_item = item
                # Refresh list after change
                in_stock_items = (Inventory.query
                                  .filter_by(vendor_id=vendor.id, status='In-Stock')
                                  .order_by(Inventory.sku)
                                  .all())

    return render_template('vendor_checkout.html', vendor=vendor,
                           in_stock_items=in_stock_items,
                           checked_out_item=checked_out_item)

# ============================================================================
# INVENTORY ROUTES
# ============================================================================

@app.route('/inventory')
def inventory_list():
    """Display all inventory items"""
    # Get filter parameters
    status_filter = request.args.get('status', '')
    equipment_filter = request.args.get('equipment', '')
    vendor_filter = request.args.get('vendor', '')
    search = request.args.get('search', '')
    
    # Build query
    query = Inventory.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if equipment_filter:
        query = query.filter_by(equipment_type=equipment_filter)
    
    if vendor_filter:
        query = query.filter_by(vendor_id=int(vendor_filter))
    
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Inventory.sku.ilike(search_term),
                Inventory.description.ilike(search_term)
            )
        )
    
    inventory_items = query.order_by(Inventory.sku).all()
    vendors = Vendor.query.filter_by(active=True).order_by(Vendor.last_name, Vendor.first_name).all()
    
    return render_template('inventory_list.html', 
                         inventory_items=inventory_items,
                         vendors=vendors,
                         equipment_types=EQUIPMENT_TYPES,
                         statuses=INVENTORY_STATUSES,
                         status_filter=status_filter,
                         equipment_filter=equipment_filter,
                         vendor_filter=vendor_filter,
                         search=search)

@app.route('/inventory/new', methods=['GET', 'POST'])
def inventory_new():
    """Create new inventory item"""
    if request.method == 'POST':
        try:
            item = Inventory(
                sku=request.form['sku'].strip(),
                vendor_id=int(request.form['vendor_id']),
                equipment_type=request.form['equipment_type'],
                description=request.form.get('description', '').strip(),
                price=float(request.form['price']),
                status=request.form['status'],
                donate_if_not_sold=request.form.get('donate_if_not_sold') == 'on',
                notes=request.form.get('notes', '').strip()
            )
            
            db.session.add(item)
            db.session.commit()
            
            flash(f'Inventory item SKU {item.sku} created successfully!', 'success')
            # Redirect back to add another item for the same vendor
            return redirect(url_for('inventory_new', vendor_id=item.vendor_id))
            
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

@app.route('/inventory/<int:item_id>/edit', methods=['GET', 'POST'])
def inventory_edit(item_id):
    """Edit existing inventory item"""
    item = db.get_or_404(Inventory, item_id)
    
    if request.method == 'POST':
        try:
            item.sku = request.form['sku'].strip()
            item.vendor_id = int(request.form['vendor_id'])
            item.equipment_type = request.form['equipment_type']
            item.description = request.form.get('description', '').strip()
            item.price = float(request.form['price'])
            item.status = request.form['status']
            item.donate_if_not_sold = request.form.get('donate_if_not_sold') == 'on'
            item.notes = request.form.get('notes', '').strip()
            
            db.session.commit()
            
            flash(f'Inventory item SKU {item.sku} updated successfully!', 'success')
            return redirect(url_for('inventory_list'))
            
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

@app.route('/inventory/<int:item_id>/delete', methods=['POST'])
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
    
    return redirect(url_for('inventory_list'))

@app.route('/inventory/<int:item_id>')
def inventory_view(item_id):
    """View inventory item details"""
    item = db.get_or_404(Inventory, item_id)
    return render_template('inventory_view.html', item=item)

# ============================================================================
# INVOICE ROUTES
# ============================================================================

@app.route('/invoices')
def invoices_list():
    """Display all invoices"""
    invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).all()
    return render_template('invoices_list.html', invoices=invoices)

@app.route('/invoices/new', methods=['GET', 'POST'])
def invoice_new():
    """Create new invoice"""
    if request.method == 'POST':
        try:
            # Create invoice
            invoice = Invoice(
                customer_name=request.form.get('customer_name', '').strip(),
                tax_rate=float(request.form.get('tax_rate', DEFAULT_TAX_RATE * 100)) / 100,
                payment_method=request.form.get('payment_method', '').strip(),
                notes=request.form.get('notes', '').strip()
            )
            
            db.session.add(invoice)
            db.session.flush()  # Get invoice ID
            db.session.commit()  # Save to database
            
            flash(f'Invoice #{invoice.id} created! Now add items to the sale.', 'success')
            return redirect(url_for('invoice_edit', invoice_id=invoice.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating invoice: {str(e)}', 'error')
    
    return render_template('invoice_form.html', 
                         invoice=None,
                         payment_methods=PAYMENT_METHODS,
                         default_tax_rate=DEFAULT_TAX_RATE * 100)

@app.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
def invoice_edit(invoice_id):
    """Edit invoice and add/remove items"""
    invoice = db.get_or_404(Invoice, invoice_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_item':
            # Add item by SKU
            sku = request.form.get('sku', '').strip()
            item = Inventory.query.filter_by(sku=sku).first()
            
            if not item:
                flash(f'Item with SKU {sku} not found.', 'error')
            elif item.status != 'In-Stock':
                # Item exists but not available
                flash(f'Item {sku} cannot be added - status is "{item.status}". Only In-Stock items can be sold.', 'error')
            else:
                # Add to invoice
                line = InvoiceLine(
                    invoice_id=invoice.id,
                    inventory_id=item.id,
                    price=item.price
                )
                db.session.add(line)
                
                # Mark item as pending (not sold yet until invoice completed)
                item.status = 'Pending'
                
                # Recalculate totals
                invoice.calculate_totals()
                db.session.commit()
                
                flash(f'Added {item.sku} - {item.description} to invoice.', 'success')
        
        elif action == 'remove_item':
            # Remove item from invoice
            line_id = int(request.form.get('line_id'))
            line = db.get_or_404(InvoiceLine, line_id)
            
            # Mark item back as in-stock
            line.inventory_item.status = 'In-Stock'
            
            db.session.delete(line)
            invoice.calculate_totals()
            db.session.commit()
            
            flash('Item removed from invoice.', 'success')
        
        elif action == 'update_invoice':
            # Update invoice details
            invoice.customer_name = request.form.get('customer_name', '').strip()
            invoice.tax_rate = float(request.form.get('tax_rate', DEFAULT_TAX_RATE)) / 100
            invoice.payment_method = request.form.get('payment_method', '').strip()
            invoice.notes = request.form.get('notes', '').strip()
            invoice.calculate_totals()
            db.session.commit()
            
            flash('Invoice updated successfully!', 'success')
        
        elif action == 'complete':
            # Finalize the invoice
            invoice.customer_name = request.form.get('customer_name', '').strip()
            invoice.tax_rate = float(request.form.get('tax_rate', DEFAULT_TAX_RATE)) / 100
            invoice.payment_method = request.form.get('payment_method', '').strip()
            invoice.notes = request.form.get('notes', '').strip()
            invoice.calculate_totals()
            
            # Mark all items in this invoice as Sold
            for line in invoice.lines:
                line.inventory_item.status = 'Sold'
            
            db.session.commit()
            
            flash(f'Invoice #{invoice.id} completed!', 'success')
            return redirect(url_for('invoice_view', invoice_id=invoice.id))
        
        return redirect(url_for('invoice_edit', invoice_id=invoice.id))
    
    # GET request - show edit form
    available_items = Inventory.query.filter_by(status='In-Stock').order_by(Inventory.sku).all()
    
    return render_template('invoice_edit.html',
                         invoice=invoice,
                         available_items=available_items,
                         payment_methods=PAYMENT_METHODS,
                         default_tax_rate=DEFAULT_TAX_RATE * 100)

@app.route('/invoices/<int:invoice_id>')
def invoice_view(invoice_id):
    """View invoice details"""
    invoice = db.get_or_404(Invoice, invoice_id)
    return render_template('invoice_view.html', invoice=invoice)

@app.route('/invoices/<int:invoice_id>/receipt')
def invoice_receipt(invoice_id):
    """Print receipt for invoice"""
    invoice = db.get_or_404(Invoice, invoice_id)
    return render_template('invoice_receipt.html', invoice=invoice)

@app.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
def invoice_delete(invoice_id):
    """Delete invoice and return items to stock"""
    invoice = db.get_or_404(Invoice, invoice_id)
    
    try:
        # Return all items to stock
        for line in invoice.lines:
            line.inventory_item.status = 'In-Stock'
        
        db.session.delete(invoice)
        db.session.commit()
        flash(f'Invoice #{invoice_id} deleted and items returned to stock.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting invoice: {str(e)}', 'error')
    
    return redirect(url_for('invoices_list'))

# API endpoints for inventory
@app.route('/api/inventory')
def api_inventory_list():
    """API endpoint to get inventory as JSON"""
    items = Inventory.query.order_by(Inventory.created_at.desc()).all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/inventory/<int:item_id>')
def api_inventory_get(item_id):
    """API endpoint to get single inventory item"""
    item = db.get_or_404(Inventory, item_id)
    return jsonify(item.to_dict())

# API endpoints for AJAX calls
@app.route('/api/vendors')
def api_vendors_list():
    """API endpoint to get vendors as JSON"""
    vendors = Vendor.query.filter_by(active=True).order_by(Vendor.last_name, Vendor.first_name).all()
    return jsonify([v.to_dict() for v in vendors])

@app.route('/api/vendors/<int:vendor_id>')
def api_vendor_get(vendor_id):
    """API endpoint to get single vendor"""
    vendor = db.get_or_404(Vendor, vendor_id)
    return jsonify(vendor.to_dict())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
