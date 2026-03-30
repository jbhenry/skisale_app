#!/usr/bin/env python3
"""
Initialize the database for a new swap event.

Deletes all invoices, invoice lines, and inventory.
Sets all vendors to inactive.

Run: source bin/activate && python init_swap.py
"""
import sys
from app import app
from models import db, Vendor, Inventory, Invoice, InvoiceLine

with app.app_context():
    vendors  = Vendor.query.count()
    items    = Inventory.query.count()
    invoices = Invoice.query.count()
    lines    = InvoiceLine.query.count()

    print("=" * 50)
    print("  INITIALIZE FOR NEW SWAP")
    print("=" * 50)
    print(f"  Vendors to deactivate  : {vendors}")
    print(f"  Inventory items to delete: {items}")
    print(f"  Invoices to delete     : {invoices}")
    print(f"  Invoice lines to delete: {lines}")
    print("=" * 50)
    print("This CANNOT be undone.")
    print("Ensure payout reports and checks are complete.")
    print()

    confirm = input("Type YES to proceed: ")
    if confirm != "YES":
        print("Aborted.")
        sys.exit(0)

    try:
        InvoiceLine.query.delete()
        Invoice.query.delete()
        Inventory.query.delete()
        Vendor.query.update({'active': False})
        db.session.commit()
        print("Done. Database initialized for new swap.")
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        sys.exit(1)
