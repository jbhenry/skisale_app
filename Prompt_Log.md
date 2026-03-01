# Prompt Log

This file tracks all user requests and feature additions to the SkiSale Manager application.

---

## Session 1: Initial Setup & Core Features

### 1. Project Initialization
**Date:** 2026-02-27  
**Prompt:** Migrate Microsoft Access SkiSale database to Python Flask web application for consignment ski equipment sales

**Requirements:**
- ~10 users managing consignment ski sales
- Vendors are individual people (consignors) bringing merchandise to sell
- Multi-user support via browser-based interface
- SQLite database (with PostgreSQL migration path)

---

### 2. Consignor Module
**Prompt:** Build Consignor/Vendor management system

**Requirements:**
- Fields: first_name, last_name, phone, email, address, commission_rate, payment_method
- CRUD operations (Create, Read, Update, Delete)
- Soft delete (mark inactive instead of removing)
- Search and filter functionality

---

### 3. Remove Unused Fields
**Prompt:** Remove "Consignor Code" field and TaxID field

**Changes:**
- Use auto-generated Vendor_ID instead of custom codes
- Removed tax_id field (not needed)
- Updated all templates and forms

---

### 4. Inventory Module
**Prompt:** Add Inventory with 7-digit SKU, equipment type dropdown, description, price, and status dropdown

**Requirements:**
- SKU: 7-digit barcode number
- Equipment Types: Skis, Snowboards, Boots, Poles, Bindings, Helmets, Goggles, Apparel, Accessories, Other
- Status: In-Stock, Not In Stock, Donated, Sold, Rejected, Returned to Vendor
- Link inventory to vendors (consignors)

---

### 5. Workflow Improvements
**Prompt:** After adding a new Vendor, go to vendor view. After adding Inventory item, stay on form to add another for same vendor

**Changes:**
- New vendor redirects to vendor detail page
- Add inventory loops back to form with vendor pre-filled
- Added "View Consignor" button during inventory entry
- Auto-focus on SKU field for quick scanning

---

### 6. Fix Active Consignors Toggle
**Prompt:** "Active Consignors Only" toggle does not work, it always stays on

**Fix:**
- Implemented hidden field approach with JavaScript
- Backend logic updated to properly handle true/false state
- Toggle now correctly shows/hides inactive consignors

---

### 7. Add Consignor Statistics
**Prompt:** Add inventory statistics to Consignor view screen: total items consigned, number sold, total to be paid after commissions

**Added Metrics:**
- Total Items Consigned
- Items Sold
- Total Sales
- Consignor Payout (after commission)

---

### 8. Invoice/Sales System
**Prompt:** Add Invoice and Invoice_Line tables, form to enter sale, add items, total out sale. Mark items sold. Bonus: printable receipt

**Features Implemented:**
- Invoice table with customer info, tax, payment method
- InvoiceLine table linking inventory to invoices
- Barcode scanning interface for adding items
- Auto-calculation of subtotal, tax, total
- Items automatically marked "Sold" when added
- Items returned to "In-Stock" if removed
- Printable thermal-style receipt
- Tax rate configurable per invoice (default 6%)

**Workflow:**
1. Create new sale → enter customer/tax details
2. Scan/add items by SKU
3. Items appear in cart with running total
4. Complete sale
5. Print receipt for customer

---

### 9. Enable Invoices Link
**Prompt:** Invoices link in header is not active

**Fix:**
- Removed "disabled" class from navbar
- Added proper route and active state highlighting

---

### 10. Fix Invoice Creation Error
**Prompt:** BuildError - Could not build url for endpoint 'invoices_list'

**Fix:**
- Added missing invoice routes to app.py
- Added Invoice and InvoiceLine imports
- Added PAYMENT_METHODS and DEFAULT_TAX_RATE constants
- Added Invoice and InvoiceLine models to models.py

---

### 11. Fix Invoice Redirect Error
**Prompt:** After creating invoice, get 404 error on /invoices/1/edit

**Fix:**
- Added `db.session.commit()` after `flush()` to save invoice
- Fixed tax_rate conversion from percentage to decimal

---

### 12. Restore Consignor Statistics
**Prompt:** Summary information missing from Consignee detail screen (regression)

**Fix:**
- Re-added inventory statistics section that was lost
- Removed old placeholder "Sales Summary" section
- Statistics now show live data from sold items

---

### 13. Dashboard Creation
**Prompt:** Create dashboard to keep eye on sale progress. Show active vendors, inventory by status, sales totals, tax collected, vendor payouts, commission

**Dashboard Features:**
- **Financial Metrics:**
  - Total Sales (with invoice count)
  - Our Commission
  - Vendor Payouts
  - Sales Tax Collected
  
- **Overview Metrics:**
  - Active Consignors count
  - Total Inventory count
  - Sales breakdown (commission vs payout %)
  
- **Inventory Status:**
  - Count by each status
  - Visual progress bar breakdown
  
- **Quick Actions:**
  - Buttons for common tasks (New Sale, Add Inventory, etc.)

- **Navigation:**
  - New "Dashboard" link in navbar
  - Home page shows dashboard

---

### 14. Change Tracking
**Prompt:** Log prompts in Prompt_Log.md and keep overview of changes in Change_Log.md

**Action:** Created this file and Change_Log.md to track development history

---

### 15. Pending Status for Invoice Processing
**Prompt:** Add 'Pending' inventory status. When item added to invoice, mark as Pending. When sale completed, mark as Sold. Only allow In-Stock items to be added to invoices with error message for other statuses.

**Requirements:**
- New status: "Pending"
- Add item to invoice → status becomes "Pending" (not Sold yet)
- Complete sale → all Pending items become "Sold"
- Prevent adding non-In-Stock items (especially already Sold items)
- Clear error messages when trying to add unavailable items

**Workflow:**
1. Item starts as "In-Stock"
2. Scan item → added to invoice → status = "Pending"
3. Can still remove item from invoice (returns to "In-Stock")
4. Click "Complete Sale" → all items in invoice become "Sold"

**Prevents:**
- Double-selling same item
- Adding sold/donated/rejected items to new sales
- Confusion about which items are actually sold vs just in cart

---

### 16. Dashboard Financial Math Fix (Attempt 1 - Incomplete)
**Prompt:** Dashboard showing vendor payouts ($300) higher than total sales ($265) - we'd go broke!

**Initial Fix:**
- Added financial breakdown section
- Clarified labels

**Result:** Still broken - now showing 120% payouts!

---

### 17. Dashboard Financial Math Fix (Real Fix)
**Prompt:** Still broken! Vendor payouts exceed total sales. Financial breakdown showing 120% payouts!

**Root Cause Found:**
- Dashboard calculated payouts from ALL items with status='Sold'
- But calculated sales from invoice totals only
- **Problem:** If items marked "Sold" manually (testing, old data, etc.) they counted in payouts but NOT in sales!
- This created phantom payouts with no corresponding revenue

**Example of the bug:**
```
Invoice #1: Sold item A for $100 → counted in sales
Manual: Marked item B as "Sold" (not in invoice) → counted in payouts but NOT sales
Result: $100 sales, $160 payouts (item A + item B) = 160% payout rate!
```

**Correct Fix:**
- Calculate payouts from **invoice lines** not inventory status
- Loop through invoices → loop through lines → calculate commission
- Use `line.price` (price at time of sale) not `item.price`
- Now payouts ONLY count items actually sold through invoices
- Payouts + Commission should ALWAYS equal invoice subtotal

**Math Check:**
```
Invoice subtotal:      $300.00
├─ Vendor payout:     $240.00 (80%)
└─ Our commission:     $60.00 (20%)
Total should be:      $300.00 ✓
```

---

### 18. UI Cleanup and Defaults
**Prompt:** A couple of small things to clean up:
- When adding new Vendor, make commission % dropdown with 23% default, other options 15% and 100%. Default payment method Check.
- On inventory list, provide total under Price column
- On invoice list, provide totals under Subtotal, Tax, and Total columns

**Changes Made:**
1. **Vendor Form:**
   - Commission rate changed from text input to dropdown
   - Options: 15%, 23% (default), 100%
   - Payment method defaults to "Check" for new vendors

2. **Inventory List:**
   - Added footer row with total of all prices
   - Shows sum of all inventory item prices

3. **Invoice List:**
   - Added footer row with totals
   - Shows: Total Subtotal, Total Tax, Total Amount
   - Quick view of all sales without opening dashboard

---

### 19. Test Framework Setup
**Date:** 2026-03-01
**Prompt:** What would be the best testing framework to use with this app? / Yes set up test scaffolding using Pytest

**Requirements:**
- Automated test coverage for all major functionality
- Tests should use an isolated in-memory database (not affect production data)
- Cover models, vendor routes, inventory routes, invoice business logic

**Changes:**
- Installed pytest and pytest-flask into the virtualenv
- Created `tests/` directory with full test scaffolding
- 58 tests covering models, vendors, inventory, and invoices — all passing

---

## Notes

- All changes maintain backward compatibility with existing data
- Database uses soft deletes (active flag) to preserve data integrity
- Sample data includes 6 consignors and 10 inventory items
- Application ready for production use with proper backup procedures
