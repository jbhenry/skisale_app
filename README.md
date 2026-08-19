# SkiSale Manager

Flask web application for managing consignment ski sales — consignors, inventory, point-of-sale, and end-of-sale reporting.

## Features

- **Dashboard** — live financial summary: sales, tax collected, commissions, vendor payouts
- **Consignor management** — add/edit consignors, commission rates, payment preferences; soft-delete (inactive flag)
- **Inventory** — track items by SKU (1–9999999), equipment type, price, and status; bulk CSV import; barcode scanner support throughout
- **Check-in / Check-out** — scan consignor items in at drop-off, scan them back out at pickup; printable receipts
- **Point of sale** — invoice workflow with barcode scanning, configurable sales tax, 3% surcharge auto-applied for Credit Card and Venmo
- **Reports (xlsx download)**
  - Payout Report — one row per consignor with items sold, commission withheld, net payout
  - Remaining Inventory — all In-Stock items
  - Donated Items — all items marked Donated
  - Sales Tax Report — one row per invoice with subtotal, tax rate, tax collected, total
  - Employee Discounts Report — all invoices with a non-zero discount amount
  - Sales by Register Report — all invoices grouped by register ID with per-register subtotals
- **Check printing** — print-ready PDF of vendor payout checks, 1 check per page
- **Register ID** — per-session register/cashier identifier stamped on invoices; required before any write operation
- **Admin** — on-demand database backup, new-sale initialization

## Tech Stack

- Python 3 + Flask + SQLAlchemy + SQLite (WAL mode)
- Jinja2 templates + Bootstrap 5
- openpyxl (xlsx reports), ReportLab (PDF checks)
- Recommended production server: [Waitress](https://docs.pylonsproject.org/projects/waitress/)

## Setup

**Linux / macOS**

```bash
# Create and activate virtualenv (first time only)
python3 -m venv .
source bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
python app.py
```

**Windows (PowerShell)**

```powershell
# Create and activate virtualenv (first time only)
python -m venv .
.\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start the development server
python app.py
```

> If activation fails with a script execution policy error, run PowerShell as
> Administrator once and execute:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

App runs at **http://localhost:5000**. The SQLite database is created automatically at first start.

To pre-populate with sample data:

```bash
python init_db.py
```

## Running Tests

```bash
source bin/activate
python -m pytest tests/ -v      # full suite, verbose
python -m pytest tests/ -q      # full suite, quiet
python -m pytest tests/test_admin.py -v   # single file
```

227 tests, all isolated with in-memory SQLite.

## Production Deployment

Run under Waitress instead of the Flask dev server:

**Linux / macOS**

```bash
source bin/activate
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

**Windows (PowerShell)**

```powershell
.\Scripts\Activate.ps1
python serve.py
```

- **Database**: `var/app-instance/skisale.db`
- **Backups**: use the Backup button on the Admin page — saves a timestamped copy to `var/app-instance/backups/`
- **Schema migrations**: handled automatically at startup via `ALTER TABLE` / table-recreate blocks in `app.py` — no Alembic needed

## File Structure

```
skisale_app/
├── app.py                  # Flask app factory, startup migrations, blueprint registration
├── models.py               # SQLAlchemy models: Vendor, Inventory, Invoice, InvoiceLine
├── constants.py            # Shared constants: tax rate, surcharge, commission rates, payment methods
├── init_db.py              # Sample data loader
├── requirements.txt
├── pytest.ini
├── routes/                 # Flask blueprints (one file per domain)
│   ├── vendors.py
│   ├── inventory.py
│   ├── invoices.py
│   └── admin.py
├── tests/
│   ├── conftest.py         # Fixtures: app, client (with register_id), db, sample_vendor, sample_item, sample_invoice
│   ├── test_models.py
│   ├── test_vendors.py
│   ├── test_inventory.py
│   ├── test_invoices.py
│   └── test_admin.py
├── templates/              # Jinja2 + Bootstrap 5
│   ├── base.html           # Navbar with register ID modal
│   ├── dashboard.html
│   ├── admin.html
│   ├── vendors_list.html / vendor_form.html / vendor_view.html
│   ├── vendor_checkin.html / vendor_checkout.html
│   ├── vendor_receipt.html / vendor_checkout_receipt.html
│   ├── vendor_import.html
│   ├── inventory_list.html / inventory_form.html / inventory_view.html
│   ├── invoices_list.html / invoice_form.html / invoice_edit.html
│   ├── invoice_view.html / invoice_receipt.html
├── docs/                   # Documentation
│   ├── admin-guide.md      # Admin panel, reports, rate configuration
│   ├── data-model.md       # Models, business rules, invoice calculation
│   ├── hardwaresetup.md    # Physical hardware and network setup
│   ├── operations.md       # Full event lifecycle (setup through payout)
│   ├── setup.md            # Installation and configuration
│   └── user-guide.md       # Cashier/volunteer reference
└── var/
    └── app-instance/
        ├── skisale.db
        └── backups/        # On-demand backups saved here
```

## Inventory Status Workflow

```
In-Stock → (add to invoice) → Pending → (complete invoice) → Sold
                                ↓
                         (remove from invoice)
                                ↓
                            In-Stock

In-Stock / Rejected → (vendor checkout) → Returned to Vendor
In-Stock            → (vendor checkout) → Donated
```

## Key Conventions

- SKU is an integer, 1–9999999 (up to 7 digits)
- Vendor payout = sale price × (1 − commission_rate), calculated from invoice lines only
- 3% surcharge applied automatically for Credit Card and Venmo payments
- Dashboard payouts are calculated from invoice lines, not from inventory status
- Vendors are soft-deleted (active=False); inventory is hard-deleted
- Register ID (set once per browser session) is stamped on invoices and all vendor/inventory writes; required before any POST operation
- `created_by` / `updated_by` tracked on Vendor and Inventory records using the session register ID
