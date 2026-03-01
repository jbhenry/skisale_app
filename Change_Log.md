# Change Log

Technical overview of code changes made to SkiSale Manager application.

---

## Version 1.0 - Initial Release

### Database Schema

#### Vendors Table
```python
- id (Integer, Primary Key, Auto-increment)
- first_name (String)
- last_name (String)
- phone, email (String)
- address1, address2, city, state, zip_code (String)
- commission_rate (Float, default 0.20)
- payment_method (String)
- notes (Text)
- active (Boolean, default True)
- created_at, updated_at (DateTime)
```

#### Inventory Table
```python
- id (Integer, Primary Key)
- sku (String(7), Unique, 7-digit barcode)
- vendor_id (Foreign Key → vendors.id)
- equipment_type (String) - Dropdown options
- description (String)
- price (Float)
- status (String, default 'In-Stock')
- notes (Text)
- created_at, updated_at (DateTime)
```

#### Invoice Table
```python
- id (Integer, Primary Key)
- invoice_date (DateTime)
- customer_name (String)
- subtotal, tax_rate, tax_amount, total (Float)
- payment_method (String)
- notes (Text)
- created_at, updated_at (DateTime)
```

#### InvoiceLine Table
```python
- id (Integer, Primary Key)
- invoice_id (Foreign Key → invoices.id)
- inventory_id (Foreign Key → inventory.id)
- price (Float) - Price at time of sale
```

---

## Code Changes by Feature

### 1. Consignor Management (`app.py` routes 48-162)

**Routes Added:**
- `GET /vendors` - List all vendors with search/filter
- `GET/POST /vendors/new` - Create new vendor
- `GET/POST /vendors/<id>/edit` - Edit vendor
- `POST /vendors/<id>/delete` - Soft delete (set active=False)
- `GET /vendors/<id>` - View vendor details

**Key Features:**
- Active/inactive filter with JavaScript toggle
- Search by name or email
- Ordered by last_name, first_name
- Vendor statistics calculated on detail page

**Files Modified:**
- `templates/vendors_list.html` - Table view with search
- `templates/vendor_form.html` - Add/edit form
- `templates/vendor_view.html` - Detail view with inventory stats

---

### 2. Inventory Management (`app.py` routes 164-319)

**Routes Added:**
- `GET /inventory` - List with filters (status, equipment, vendor)
- `GET/POST /inventory/new` - Add item (with vendor pre-fill)
- `GET/POST /inventory/<id>/edit` - Edit item
- `POST /inventory/<id>/delete` - Hard delete item
- `GET /inventory/<id>` - View item details

**Key Features:**
- SKU validation (7 digits)
- Status tracking (In-Stock → Sold workflow)
- Equipment type dropdown
- Vendor relationship with commission calculation
- Auto-focus on SKU field for barcode scanning

**Workflow Optimization:**
- After adding vendor → redirect to vendor detail
- After adding inventory → stay on form for same vendor
- "View Consignor" button during inventory entry

**Files Modified:**
- `templates/inventory_list.html` - Filterable table
- `templates/inventory_form.html` - Add/edit with barcode focus
- `templates/inventory_view.html` - Shows vendor commission breakdown

---

### 3. Invoice/Sales System (`app.py` routes 321-447)

**Routes Added:**
- `GET /invoices` - List all invoices
- `GET/POST /invoices/new` - Create invoice shell
- `GET/POST /invoices/<id>/edit` - Add/remove items, update details
- `GET /invoices/<id>` - View completed invoice
- `GET /invoices/<id>/receipt` - Printable receipt
- `POST /invoices/<id>/delete` - Delete and return items to stock

**Key Features:**
- Multi-action form handling (add_item, remove_item, update_invoice, complete)
- Auto-calculation of totals via `Invoice.calculate_totals()` method
- Items marked "Sold" when added to invoice
- Items returned to "In-Stock" when removed
- Tax rate configurable per invoice

**Invoice Edit Workflow:**
1. Create invoice → gets ID via `flush()` and `commit()`
2. Scan SKU → looks up In-Stock item
3. Add to invoice → creates InvoiceLine, marks item Sold
4. Remove item → deletes InvoiceLine, marks item In-Stock
5. Complete → redirects to view page

**Files Created:**
- `templates/invoices_list.html` - Invoice table
- `templates/invoice_form.html` - Initial creation form
- `templates/invoice_edit.html` - Scanning interface with cart
- `templates/invoice_view.html` - Completed invoice details
- `templates/invoice_receipt.html` - Thermal-style printable receipt

---

### 4. Dashboard (`app.py` route 43-78)

**Route Modified:**
- `GET /` - Dashboard instead of redirect

**Metrics Calculated:**
- Active vendors count
- Total inventory count
- Inventory by status (query for each status)
- Total sales, tax, subtotal from all invoices
- Commission and payout calculated from sold items

**Display Sections:**
1. **Key Financial Metrics** (4 cards)
   - Total Sales, Commission, Vendor Payouts, Sales Tax
2. **Overview Metrics** (3 cards)
   - Active Consignors, Total Inventory, Sales Breakdown %
3. **Inventory Status Breakdown**
   - Count boxes per status
   - Visual progress bar
4. **Quick Actions** - Button links to common tasks

**File Created:**
- `templates/dashboard.html` - Full dashboard layout

**Navigation Updated:**
- Added "Dashboard" link to navbar (`templates/base.html`)

---

## Bug Fixes

### Fix 1: Active Consignors Toggle
**Issue:** Checkbox didn't properly toggle between true/false  
**Solution:**
- Added hidden field to track state
- JavaScript function `toggleActiveOnly()` updates hidden field
- Backend checks for None (default true) vs 'true'/'false'

**Files Modified:**
- `app.py` - Updated `vendors_list()` route logic
- `templates/vendors_list.html` - Added hidden field + JS function

---

### Fix 2: Invoice Routes Missing
**Issue:** BuildError for 'invoices_list' endpoint  
**Solution:**
- Added all invoice routes to `app.py`
- Added Invoice, InvoiceLine to imports
- Added PAYMENT_METHODS and DEFAULT_TAX_RATE constants

---

### Fix 3: Invoice Creation 404
**Issue:** Invoice created but not saved, causing 404 on edit page  
**Solution:**
- Added `db.session.commit()` after `flush()`
- Fixed tax_rate to convert percentage to decimal (/ 100)

---

### Fix 4: Missing Consignor Statistics
**Issue:** Inventory statistics disappeared from vendor detail page  
**Solution:**
- Re-added statistics calculation section
- Removed old placeholder "Sales Summary"
- Statistics now show: Total Items, Items Sold, Total Sales, Payout

---

## Constants & Configuration

### Equipment Types (`app.py` lines 17-28)
```python
['Skis', 'Snowboards', 'Boots', 'Poles', 'Bindings', 
 'Helmets', 'Goggles', 'Apparel', 'Accessories', 'Other']
```

### Inventory Statuses (`app.py` lines 30-37)
```python
['In-Stock', 'Not In Stock', 'Donated', 'Sold', 
 'Rejected', 'Returned to Vendor']
```

### Payment Methods (`app.py` lines 39-45)
```python
['Cash', 'Credit Card', 'Debit Card', 'Check', 'Other']
```

### Default Tax Rate (`app.py` line 48)
```python
DEFAULT_TAX_RATE = 0.06  # 6%
```

---

## File Structure

```
skisale_complete/
├── app.py                          # Main Flask application
├── models.py                       # Database models
├── init_db.py                      # Database initialization + sample data
├── requirements.txt                # Python dependencies
├── README.md                       # Setup instructions
├── Prompt_Log.md                   # User request history
├── Change_Log.md                   # This file
└── templates/
    ├── base.html                   # Base layout with navbar
    ├── dashboard.html              # Dashboard/home page
    ├── vendors_list.html           # Vendor table
    ├── vendor_form.html            # Vendor add/edit
    ├── vendor_view.html            # Vendor detail + stats
    ├── inventory_list.html         # Inventory table
    ├── inventory_form.html         # Inventory add/edit
    ├── inventory_view.html         # Inventory detail
    ├── invoices_list.html          # Invoice table
    ├── invoice_form.html           # Invoice creation
    ├── invoice_edit.html           # Scanning/cart interface
    ├── invoice_view.html           # Completed invoice
    └── invoice_receipt.html        # Printable receipt
```

---

## API Endpoints

### Vendor API
- `GET /api/vendors` - List all active vendors (JSON)
- `GET /api/vendors/<id>` - Get single vendor (JSON)

### Inventory API
- `GET /api/inventory` - List all inventory items (JSON)
- `GET /api/inventory/<id>` - Get single item (JSON)

---

## Database Relationships

```
Vendor (1) ──→ (Many) Inventory
Inventory (1) ──→ (0-1) InvoiceLine
Invoice (1) ──→ (Many) InvoiceLine
```

**Cascade Deletes:**
- Deleting Vendor → deletes all Inventory items
- Deleting Invoice → deletes all InvoiceLines
- Deleting Inventory → orphans InvoiceLine (should be prevented)

---

## Sample Data

### Vendors (6 total, 5 active)
- Sarah Johnson (20% commission, Check)
- Mike Smith (25% commission, PayPal)
- Lisa Chen (20% commission, Venmo)
- David Garcia (15% commission, Cash) - VIP rate
- Emily Martinez (20% commission, Check)
- Robert Wilson (Inactive)

### Inventory (10 items)
- 7 In-Stock
- 1 Sold
- Various equipment types across vendors

---

## Technology Stack

- **Backend:** Python 3.x + Flask 3.0.0
- **Database:** SQLite (via Flask-SQLAlchemy 3.1.1)
- **Frontend:** Bootstrap 5 + Bootstrap Icons
- **Templates:** Jinja2

---

## Future Considerations

**Potential Enhancements:**
- Customer table and tracking
- Barcode label printing
- Bulk inventory import (CSV)
- Email receipts
- Vendor payout reports
- Multi-location support
- Role-based access control

**Database Migration:**
- SQLite → PostgreSQL for production
- Add database migrations (Flask-Migrate)

---

## Version History

**v1.0** - Initial Release (2026-02-27)
- Core vendor, inventory, invoice functionality
- Dashboard with sales metrics
- Printable receipts
- Full CRUD operations
- Sample data included

**v1.1** - Pending Status for Invoice Safety (2026-03-01)
- Added "Pending" inventory status
- Items marked Pending when added to invoice (not Sold immediately)
- Items marked Sold only when invoice completed
- Validation: Only In-Stock items can be added to invoices
- Clear error messages for unavailable items
- Prevents double-selling items

---

## Recent Changes (v1.1)

### Inventory Status Updates

**New Status Added:**
- "Pending" - Item added to invoice but sale not completed

**Updated Status Flow:**
```
In-Stock → (add to invoice) → Pending → (complete sale) → Sold
                                ↓
                         (remove from invoice)
                                ↓
                            In-Stock
```

**Validation Added:**
- Only items with status "In-Stock" can be added to invoices
- Attempting to add item with other status shows error:
  - "Item {sku} cannot be added - status is '{status}'. Only In-Stock items can be sold."
- Prevents re-selling already sold items
- Prevents selling donated/rejected/returned items

### Code Changes

**app.py - Line 30-37:**
- Added 'Pending' to INVENTORY_STATUSES list (after In-Stock)

**app.py - invoice_edit route (lines 408-431):**
- Changed item lookup to check all items, not just In-Stock
- Added explicit status validation with error message
- Changed `item.status = 'Sold'` to `item.status = 'Pending'`
- Items now marked Pending when added to cart

**app.py - complete action (lines 461-475):**
- Added loop to mark all invoice items as Sold
- `for line in invoice.lines: line.inventory_item.status = 'Sold'`
- Only marks Sold when invoice finalized

**Templates Updated:**
- `inventory_list.html` - Added Pending badge styling (bg-warning)
- `dashboard.html` - Added Pending to status counts and progress bar
- Pending displayed in orange/warning color

### Benefits

1. **Prevents Double-Selling:** Item becomes unavailable as soon as added to cart
2. **Allows Changes:** Items can be removed from invoice before completion
3. **Clear Status:** Easy to see which items are in-progress vs actually sold
4. **Safety:** Cannot add already-sold items to new invoices
5. **Audit Trail:** Status history shows when item moved through states

---

## Version History
