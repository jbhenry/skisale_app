# Volunteer & Cashier User Guide

This guide covers the tasks a cashier or general volunteer will perform during the sale.

## Logging In

The application does not require a login — anyone with access to the URL can use it.
The app is typically available at **http://\<hostname\>:5000** on the local network. We will have a shortcut for this URL set up on all workstations, so you can connect with one click.

---

## Processing a Sale

1. Click **New Sale** on the Dashboard or the Invoices page
2. Enter the customer's name (optional but helpful for returns/questions)
3. Select the **Payment Method**:
   - Cash, Check — no surcharge
   - Credit Card, Venmo — a 3% surcharge is added automatically
4. Apply a **Discount** if the customer is an employee or volunteer:
   - Select "Employee discount (10%)" from the dropdown
5. Add items by typing or scanning the **SKU number** and clicking **Add Item**
   - The item description and price appear in the cart
   - Items must be **In-Stock** to be added
6. Review the totals (subtotal, discount if any, tax, surcharge if any, total)
7. Click **Complete Sale**
8. On the invoice view page, click **Print Receipt** to open the receipt and print it

---

## Handling Errors

| Problem | What to do |
|---------|-----------|
| SKU not found | Verify the tag; the item may not be checked in yet |
| Item already sold | The item has been purchased; check with a supervisor |
| Item is Pending | It is in another open cart; check with a supervisor |
| Wrong item added | Use the **Remove** button next to the item in the cart |

---

## CSV Import Format (Check-In)

If vendors submit a pre-filled spreadsheet, it must be a `.csv` file with these columns:

| Column | Required | Notes |
|--------|----------|-------|
| `sku` | Yes | Integer, 1–9999999 |
| `description` | No | Free text |
| `equipment_type` | No | See list below |
| `price` | Yes | Numeric; dollar sign optional (e.g. `25` or `$25.00`) |
| `donate_if_unsold` | No | `true` / `false` |

**Equipment types:** Ski, Boot, Binding, Pole, Helmet, Outerwear, Goggle, Other

Rows with missing prices, duplicate SKUs, or invalid SKUs are skipped with an error message.

---

## Printing Receipts

- **Customer receipt:** Invoice view page → **Print Receipt**
  - Formatted for the 80mm thermal receipt printer
- **Vendor check-in receipt:** Vendor page → Check In → **Print Receipt**
- **Vendor payout receipt:** Vendor page → Check Out → **Print Receipt**

> Use the browser's Print dialog and select the correct printer.
