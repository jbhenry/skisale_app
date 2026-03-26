# Administrator Guide

This guide covers the Admin panel and administrative tasks beyond day-to-day sales.

## Accessing the Admin Panel

Navigate to **Admin** in the top navigation bar.

---

## Backup Database

Two backup options are available from the **Daily Tasks** section of the Admin panel:

**Backup Database (Server)** — saves a timestamped copy to the `backups/` directory on the
server (e.g. `skisale_backup_20260315_120000.db`). Use this for routine on-site backups.

**Download Database** — sends a copy of the database directly to your browser as a file
download. Use this to take an off-site copy or transfer to another machine.

**When to back up:**
- Before initializing for a new event
- Before any bulk import or data correction
- At the end of each event day as a precaution

---

## Reports

### Inventory Report (In-Stock Items)

Downloads an XLSX spreadsheet of all items currently **In-Stock**.
Useful for end-of-event reconciliation and returning unsold items to vendors.

Columns: SKU, Vendor #, Vendor Name, Equipment Type, Description, Price

### Sales Report

Downloads an XLSX spreadsheet of all completed sales (sold invoice lines).

### Payout Report

Downloads an XLSX spreadsheet with one row per vendor showing:
- Items consigned, items sold
- Total sales, commission withheld, net payout

Use this to prepare vendor checks.

### Sales Tax Report

Downloads an XLSX report of sales tax collected, broken out by invoice.

### Employee Discounts Report

Downloads an XLSX list of every invoice with a non-zero discount amount, including customer name, payment method, discount percentage, and totals.

### Sales by Register Report

Downloads an XLSX list of all invoices grouped by register ID, with per-register subtotals and a grand total. Invoices with no register set appear under "(No Register)".

---

## Initialize for New Event

> ⚠️ **Destructive — cannot be undone.** Always back up first.

This action:
- Deletes all invoices and invoice lines
- Deletes all inventory items
- Sets all vendors to **inactive**

Vendors are preserved (not deleted) so returning vendors can be reactivated rather than
re-entered. Their IDs remain stable across events.

---

## Managing Vendors

See [operations.md](operations.md) for the full vendor lifecycle.

- **Reactivate** an inactive vendor from the Vendors list (green button)
- **Deactivate** an active vendor from the vendor detail page or vendor list
- Vendors with sold items cannot be fully removed without clearing sales data

---

## Changing Tax or Surcharge Rates

Rates are defined as constants in `constants.py` and require a code change:

```python
DEFAULT_TAX_RATE = 0.06   # sales tax applied to all new invoices
SURCHARGE_RATE   = 0.03   # applied automatically for Credit Card and Venmo (in models.py)
```

After changing, restart the server. Existing invoices retain the rate they were created with.

---

## Discount Rates

The employee/volunteer discount rate is defined as `EMPLOYEE_DISCOUNT_RATE` in `constants.py`
(currently 10%). Changing it there updates the invoice form dropdown and all calculations
automatically.

---

## Commission Rates

Available commission rate tiers are defined as `COMMISSION_RATES` in `constants.py`:

```python
COMMISSION_RATES = [
    (15,  '15% — Employees'),
    (23,  '23% — General Public'),
    (100, '100% — MBSP Only'),
]
```

Each entry is `(integer_pct, display_label)`. The vendor form dropdown is populated from
this list. New vendors default to 23% (General Public).
