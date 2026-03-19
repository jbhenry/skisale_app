# Administrator Guide

This guide covers the Admin panel and administrative tasks beyond day-to-day sales.

## Accessing the Admin Panel

Navigate to **Admin** in the top navigation bar.

---

## Backup Database

Downloads a copy of the production database (`skisale.db`) to your browser as a timestamped
file (e.g. `skisale_backup_20260315_120000.db`).

**When to back up:**
- Before initializing for a new event
- Before any bulk import or data correction
- At the end of each event day as a precaution

Backups are also saved automatically to the `backups/` directory on the server.

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

Rates are defined as constants in `app.py` and require a code change:

```python
DEFAULT_TAX_RATE = 0.06   # line ~75 — change to new rate
SURCHARGE_RATE   = 0.03   # models.py line ~13
```

After changing, restart the server. Existing invoices retain the rate they were created with.

---

## Discount Rates

The employee/volunteer discount is a fixed 10% applied at invoice creation.
To change the available rates, edit the dropdown options in `templates/invoice_form.html`
and `templates/invoice_edit.html`.
