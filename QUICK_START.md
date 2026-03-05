# SkiSale Manager — Quick Start

## First-Time Setup

```bash
cd skisale_app
source bin/activate          # activate the Python virtualenv
pip install -r requirements.txt
python app.py                # starts on http://localhost:5000
```

To load sample consignors and inventory for testing:

```bash
python init_db.py
```

---

## Sale Day Workflow

### 1. Consignor Drop-Off (Check-In)

1. Open the consignor's record — **Consignors → [Name]**
2. Click **Check In Items**
3. Scan each item's barcode (or type the SKU). Items are marked **In-Stock**.
4. Print the check-in receipt for the consignor.

### 2. Selling Items (Point of Sale)

1. Go to **Invoices → New Invoice**
2. Enter customer name, payment method, and tax rate
3. Scan item barcodes to add them to the cart — items move to **Pending**
4. Click **Complete Invoice** — items move to **Sold**, receipt is available to print

Note: Credit Card and Venmo payments automatically add a 3% surcharge.

### 3. Consignor Pickup (Check-Out)

1. Open the consignor's record — **Consignors → [Name]**
2. Click **Check Out Items**
3. Scan each item being returned. Items are marked **Returned to Vendor**.
   - Items with **Donate if not sold** checked can be marked **Donated** instead.
4. Print the payout receipt for the consignor.

---

## End-of-Sale Reports

All reports are on the **Admin** page under **Close-Out**:

| Report | Description |
|--------|-------------|
| Payout Report | xlsx — one row per consignor: items sold, commission, net payout |
| Print Checks | PDF — 3-up payout checks ready to print on check stock |
| Remaining Inventory | xlsx — all items still In-Stock |
| Donated Items | xlsx — all items marked Donated |
| Sales Tax Report | xlsx — one row per invoice with tax collected |

---

## Database Backup

Go to **Admin → Backup Database** at any time during the sale. Backups are saved to `var/app-instance/backups/skisale_backup_YYYYMMDD_HHMMSS.db`.

---

## Network Access

To let other computers on your network reach the app, share:

```
http://YOUR_IP_ADDRESS:5000
```

Find your IP: run `ip addr` (Linux/Mac) or `ipconfig` (Windows).

For production use, run under Waitress instead of the Flask dev server:

```bash
source bin/activate
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

---

## Common Questions

**How do I add a consignor?**
Consignors → New Consignor. The Vendor ID is assigned automatically.

**How do I change a commission rate?**
Edit the consignor record. Each consignor has their own rate (default 20%).

**An item was scanned into the wrong invoice — how do I fix it?**
Open the invoice, remove the item (it returns to In-Stock), then add it to the correct invoice.

**How do I reset for a new sale event?**
Admin → Initialize for New Swap. This clears all invoices and inventory and sets all consignors to inactive. Download the Payout Report and print checks first.

**How do I run the tests?**
```bash
source bin/activate && python -m pytest tests/ -q
```
