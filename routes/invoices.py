"""
Invoice routes and abandoned-invoice cleanup.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from models import db, Inventory, Invoice, InvoiceLine
from constants import PAYMENT_METHODS, DEFAULT_TAX_RATE, EMPLOYEE_DISCOUNT_RATE

invoices_bp = Blueprint('invoices', __name__)


@invoices_bp.before_request
def require_register_for_writes():
    if request.method == 'POST' and request.endpoint != 'invoices.set_register':
        if not session.get('register_id'):
            flash('Please set your register ID before making changes.', 'error')
            return redirect(request.referrer or url_for('invoices.invoices_list'))


def release_abandoned_invoices():
    """Release any items left in Pending status from a previous session.

    This happens when a user starts an invoice then navigates away without
    completing or cancelling it. The abandoned invoice is deleted and all
    its Pending items are returned to In-Stock.
    """
    abandoned = (Invoice.query
                 .join(InvoiceLine)
                 .join(Inventory, InvoiceLine.inventory_id == Inventory.id)
                 .filter(Inventory.status == 'Pending')
                 .distinct()
                 .all())
    for invoice in abandoned:
        for line in invoice.lines:
            if line.inventory_item.status == 'Pending':
                line.inventory_item.status = 'In-Stock'
        db.session.delete(invoice)
    if abandoned:
        db.session.commit()


@invoices_bp.route('/set-register', methods=['POST'])
def set_register():
    """Store register/user ID in session for the duration of the session."""
    register_id = request.form.get('register_id', '').strip()
    if register_id:
        session['register_id'] = register_id
    else:
        session.pop('register_id', None)
    return redirect(request.referrer or url_for('invoices.invoices_list'))


@invoices_bp.route('/invoices')
def invoices_list():
    """Display all invoices"""
    invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).all()
    return render_template('invoices_list.html', invoices=invoices)


@invoices_bp.route('/invoices/new', methods=['GET', 'POST'])
def invoice_new():
    """Create new invoice"""
    if request.method == 'POST':
        try:
            customer_name = request.form.get('customer_name', '').strip()
            discount_rate = float(request.form.get('discount_rate', 0)) / 100
            if discount_rate > 0 and not customer_name:
                flash('Customer name is required when a discount is applied.', 'error')
                return render_template('invoice_form.html',
                                       invoice=None,
                                       payment_methods=PAYMENT_METHODS,
                                       default_tax_rate=DEFAULT_TAX_RATE * 100,
                                       employee_discount_pct=int(EMPLOYEE_DISCOUNT_RATE * 100))
            # Create invoice
            invoice = Invoice(
                customer_name=customer_name,
                tax_rate=float(request.form.get('tax_rate', DEFAULT_TAX_RATE * 100)) / 100,
                discount_rate=discount_rate,
                payment_method=request.form.get('payment_method', '').strip(),
                register_id=session.get('register_id'),
                notes=request.form.get('notes', '').strip()
            )

            db.session.add(invoice)
            db.session.flush()  # Get invoice ID
            db.session.commit()  # Save to database

            flash(f'Invoice #{invoice.id} created! Now add items to the sale.', 'success')
            return redirect(url_for('invoices.invoice_edit', invoice_id=invoice.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating invoice: {str(e)}', 'error')

    return render_template('invoice_form.html',
                         invoice=None,
                         payment_methods=PAYMENT_METHODS,
                         default_tax_rate=DEFAULT_TAX_RATE * 100,
                         employee_discount_pct=int(EMPLOYEE_DISCOUNT_RATE * 100))


@invoices_bp.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
def invoice_edit(invoice_id):
    """Edit invoice and add/remove items"""
    invoice = db.get_or_404(Invoice, invoice_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_item':
            # Add item by SKU
            sku_raw = request.form.get('sku', '').strip()
            try:
                sku = int(sku_raw) if sku_raw else None
            except ValueError:
                sku = None
                flash(f'SKU "{sku_raw}" is not a valid number.', 'error')
            item = Inventory.query.filter_by(sku=sku).first() if sku is not None else None

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
            customer_name = request.form.get('customer_name', '').strip()
            discount_rate = float(request.form.get('discount_rate', 0)) / 100
            if discount_rate > 0 and not customer_name:
                flash('Customer name is required when a discount is applied.', 'error')
            else:
                invoice.customer_name = customer_name
                invoice.tax_rate = float(request.form.get('tax_rate', DEFAULT_TAX_RATE)) / 100
                invoice.discount_rate = discount_rate
                invoice.payment_method = request.form.get('payment_method', '').strip()
                invoice.notes = request.form.get('notes', '').strip()
                invoice.calculate_totals()
                db.session.commit()
                flash('Invoice updated successfully!', 'success')

        elif action == 'complete':
            # Finalize the invoice
            customer_name = request.form.get('customer_name', '').strip()
            discount_rate = float(request.form.get('discount_rate', 0)) / 100
            if discount_rate > 0 and not customer_name:
                flash('Customer name is required when a discount is applied.', 'error')
            else:
                invoice.customer_name = customer_name
                invoice.tax_rate = float(request.form.get('tax_rate', DEFAULT_TAX_RATE)) / 100
                invoice.discount_rate = discount_rate
                invoice.payment_method = request.form.get('payment_method', '').strip()
                invoice.notes = request.form.get('notes', '').strip()
                invoice.calculate_totals()

                # Mark all items in this invoice as Sold
                for line in invoice.lines:
                    line.inventory_item.status = 'Sold'

                db.session.commit()

                flash(f'Invoice #{invoice.id} completed!', 'success')
                return redirect(url_for('invoices.invoice_view', invoice_id=invoice.id))

        return redirect(url_for('invoices.invoice_edit', invoice_id=invoice.id))

    # GET request - show edit form
    available_items = Inventory.query.filter_by(status='In-Stock').order_by(Inventory.sku).all()

    return render_template('invoice_edit.html',
                         invoice=invoice,
                         available_items=available_items,
                         payment_methods=PAYMENT_METHODS,
                         default_tax_rate=DEFAULT_TAX_RATE * 100,
                         employee_discount_pct=int(EMPLOYEE_DISCOUNT_RATE * 100))


@invoices_bp.route('/invoices/<int:invoice_id>')
def invoice_view(invoice_id):
    """View invoice details"""
    invoice = db.get_or_404(Invoice, invoice_id)
    returns_mode = request.args.get('returns') == '1'
    return render_template('invoice_view.html', invoice=invoice, returns_mode=returns_mode)


@invoices_bp.route('/invoices/<int:invoice_id>/return_item', methods=['POST'])
def invoice_return_item(invoice_id):
    """Return a single line item: remove from invoice, set inventory back to In-Stock"""
    invoice = db.get_or_404(Invoice, invoice_id)
    line_id = int(request.form.get('line_id'))
    line = db.get_or_404(InvoiceLine, line_id)

    try:
        sku = line.inventory_item.sku
        line.inventory_item.status = 'In-Stock'
        db.session.delete(line)
        invoice.calculate_totals()
        db.session.commit()
        flash(f'Item {sku} returned to stock.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error returning item: {str(e)}', 'error')

    return redirect(url_for('invoices.invoice_view', invoice_id=invoice_id, returns='1'))


@invoices_bp.route('/invoices/<int:invoice_id>/receipt')
def invoice_receipt(invoice_id):
    """Print receipt for invoice"""
    invoice = db.get_or_404(Invoice, invoice_id)
    return render_template('invoice_receipt.html', invoice=invoice)


@invoices_bp.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
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

    return redirect(url_for('invoices.invoices_list'))
