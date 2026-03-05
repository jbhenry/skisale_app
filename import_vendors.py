"""
One-time import of vendors from a CSV file into the Vendors table.

CSV columns expected:
    Last Name, First Name, Email, Address, City, State, Zip, Phone, Active

All imported vendors are set to inactive (active=False).
Existing vendors with the same first+last name are skipped.

Usage:
    source bin/activate && python import_vendors.py vendors.csv
"""
import csv
import sys
from app import app
from models import db, Vendor
from models import utcnow

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <csvfile>")
    sys.exit(1)

csv_path = sys.argv[1]

imported = 0
skipped  = 0
errors   = 0

with app.app_context():
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for lineno, row in enumerate(reader, start=2):  # start=2 accounts for header
            first = row['First Name'].strip()
            last  = row['Last Name'].strip()

            if not first or not last:
                print(f"  Line {lineno}: skipping — missing name ({row})")
                errors += 1
                continue

            # Check for existing vendor with same name
            existing = Vendor.query.filter_by(
                first_name=first, last_name=last
            ).first()
            if existing:
                print(f"  Line {lineno}: SKIP — {first} {last} already exists (ID {existing.id})")
                skipped += 1
                continue

            active_str = row.get('Active', 'No').strip().lower()
            active = active_str in ('yes', 'true', '1')

            vendor = Vendor(
                first_name=first,
                last_name=last,
                email=row.get('Email', '').strip() or None,
                address1=row.get('Address', '').strip() or None,
                city=row.get('City', '').strip() or None,
                state=row.get('State', '').strip() or None,
                zip_code=row.get('Zip', '').strip() or None,
                phone=row.get('Phone', '').strip() or None,
                active=active,
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            db.session.add(vendor)
            imported += 1

        db.session.commit()

print(f"\nDone — {imported} imported, {skipped} skipped (duplicates), {errors} errors.")
