"""
Database consistency checker for SkiSale.

Runs all sanity checks and prints a summary. Exit code 0 = all clear, 1 = issues found.

Usage:
    source bin/activate && python db_check.py
"""
import sys
from app import app, INVENTORY_STATUSES
from models import db, Vendor, Inventory, Invoice, InvoiceLine
from sqlalchemy import func

TOLERANCE = 0.02  # cents tolerance for float rounding comparisons

issues_found = 0


def section(title):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def ok(msg):
    print(f"  OK  {msg}")


def warn(msg, rows):
    global issues_found
    issues_found += 1
    print(f" WARN {msg}")
    for r in rows:
        print(f"       {r}")


with app.app_context():

    # ── 1. Sold items with no InvoiceLine ───────────────────────────────────
    section("1. Sold items with no InvoiceLine")
    orphans = (
        db.session.query(Inventory)
        .outerjoin(InvoiceLine, InvoiceLine.inventory_id == Inventory.id)
        .filter(Inventory.status == 'Sold')
        .filter(InvoiceLine.id == None)
        .order_by(Inventory.sku)
        .all()
    )
    if orphans:
        warn(f"{len(orphans)} Sold item(s) have no InvoiceLine (manually marked Sold):",
             [f"SKU {i.sku}  {i.vendor.full_name}  ${i.price:.2f}" for i in orphans])
    else:
        ok("No orphaned Sold items.")

    # ── 2. Pending items with no InvoiceLine ────────────────────────────────
    section("2. Pending items with no InvoiceLine")
    stuck = (
        db.session.query(Inventory)
        .outerjoin(InvoiceLine, InvoiceLine.inventory_id == Inventory.id)
        .filter(Inventory.status == 'Pending')
        .filter(InvoiceLine.id == None)
        .order_by(Inventory.sku)
        .all()
    )
    if stuck:
        warn(f"{len(stuck)} Pending item(s) with no InvoiceLine (abandoned cart?):",
             [f"SKU {i.sku}  {i.vendor.full_name}  ${i.price:.2f}" for i in stuck])
    else:
        ok("No stuck Pending items.")

    # ── 3. InvoiceLines whose item is not Sold or Pending ───────────────────
    section("3. InvoiceLines whose inventory status is not Sold or Pending")
    bad_status = (
        db.session.query(InvoiceLine)
        .join(Inventory, InvoiceLine.inventory_id == Inventory.id)
        .filter(~Inventory.status.in_(['Sold', 'Pending']))
        .all()
    )
    if bad_status:
        warn(f"{len(bad_status)} InvoiceLine(s) point to items with unexpected status:",
             [f"Invoice #{l.invoice_id}  SKU {l.inventory_item.sku}  status={l.inventory_item.status}"
              for l in bad_status])
    else:
        ok("All InvoiceLine items are Sold or Pending.")

    # ── 4. Item appearing in more than one InvoiceLine ──────────────────────
    section("4. Same item in multiple InvoiceLines (double-sell)")
    dupes = (
        db.session.query(InvoiceLine.inventory_id, func.count(InvoiceLine.id).label('cnt'))
        .group_by(InvoiceLine.inventory_id)
        .having(func.count(InvoiceLine.id) > 1)
        .all()
    )
    if dupes:
        rows = []
        for inv_id, cnt in dupes:
            item = db.session.get(Inventory, inv_id)
            sku = item.sku if item else '?'
            rows.append(f"inventory_id={inv_id}  SKU {sku}  appears {cnt}x")
        warn(f"{len(dupes)} item(s) appear in more than one InvoiceLine:", rows)
    else:
        ok("No items double-sold.")

    # ── 5. Invoice financial math ────────────────────────────────────────────
    section("5. Invoice financial math (subtotal / tax / surcharge / total)")
    invoices = Invoice.query.all()
    math_errors = []
    for inv in invoices:
        line_sum = sum(l.price for l in inv.lines)
        expected_tax = line_sum * inv.tax_rate
        expected_surcharge = line_sum * inv.surcharge_rate
        expected_total = line_sum + expected_tax + expected_surcharge

        errs = []
        if abs(inv.subtotal - line_sum) > TOLERANCE:
            errs.append(f"subtotal {inv.subtotal:.4f} != line sum {line_sum:.4f}")
        if abs(inv.tax_amount - expected_tax) > TOLERANCE:
            errs.append(f"tax_amount {inv.tax_amount:.4f} != {expected_tax:.4f}")
        if abs(inv.total - expected_total) > TOLERANCE:
            errs.append(f"total {inv.total:.4f} != {expected_total:.4f}")

        if errs:
            math_errors.append(f"Invoice #{inv.id}: " + "; ".join(errs))

    if math_errors:
        warn(f"{len(math_errors)} invoice(s) have math errors:", math_errors)
    else:
        ok(f"All {len(invoices)} invoice(s) pass math check.")

    # ── 6. Inventory with unknown status ────────────────────────────────────
    section("6. Inventory items with unrecognised status")
    valid_statuses = set(INVENTORY_STATUSES)
    bad = Inventory.query.filter(~Inventory.status.in_(valid_statuses)).all()
    if bad:
        warn(f"{len(bad)} item(s) have unrecognised status:",
             [f"SKU {i.sku}  status='{i.status}'" for i in bad])
    else:
        ok("All inventory statuses are valid.")

    # ── 7. Inventory with price <= 0 ────────────────────────────────────────
    section("7. Inventory items with price <= 0")
    zero_price = Inventory.query.filter(Inventory.price <= 0).order_by(Inventory.sku).all()
    if zero_price:
        warn(f"{len(zero_price)} item(s) have price <= 0:",
             [f"SKU {i.sku}  {i.vendor.full_name}  price=${i.price:.2f}" for i in zero_price])
    else:
        ok("All items have a positive price.")

    # ── 8. Inventory referencing nonexistent vendor (FK violation) ───────────
    section("8. Inventory items with no matching vendor (FK violation)")
    vendor_ids = {v.id for v in Vendor.query.all()}
    orphan_items = Inventory.query.filter(~Inventory.vendor_id.in_(vendor_ids)).all()
    if orphan_items:
        warn(f"{len(orphan_items)} item(s) reference a nonexistent vendor:",
             [f"SKU {i.sku}  vendor_id={i.vendor_id}" for i in orphan_items])
    else:
        ok("All inventory items have a valid vendor.")

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    if issues_found == 0:
        print("  ALL CHECKS PASSED — database looks consistent.")
    else:
        print(f"  {issues_found} CHECK(S) FAILED — review warnings above.")
    print(f"{'═' * 60}\n")

sys.exit(1 if issues_found else 0)
