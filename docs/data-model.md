# Data Model & Business Rules

Reference for developers and anyone needing to understand how data flows through the app.

## Models (`models.py`)

### Vendor

Represents a person consigning items for sale.

| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer PK | Stable across events; reuse by reactivating |
| `first_name`, `last_name` | String | Combined as `full_name` property |
| `email`, `phone` | String | Optional contact info |
| `commission_rate` | Float | Default `0.23` (org keeps 23%, vendor gets 77%) |
| `active` | Boolean | Soft delete; inactive vendors hidden by default |

### Inventory

Represents a single item consigned by a vendor.

| Field | Type | Notes |
|-------|------|-------|
| `sku` | Integer | 1–9999999; must be unique |
| `vendor_id` | FK → Vendor | |
| `equipment_type` | String | Ski, Boot, Binding, Pole, Helmet, Outerwear, Goggle, Other |
| `description` | String | Optional free-text |
| `price` | Float | Asking price set by vendor |
| `status` | String | `In-Stock`, `Pending`, `Sold`, `Returned`, `Donated` |
| `donate_if_unsold` | Boolean | Vendor preference if item doesn't sell |

### Invoice

Represents a completed or in-progress sale.

| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer PK | |
| `customer_name` | String | Optional |
| `payment_method` | String | Cash, Check, Credit Card, Venmo |
| `tax_rate` | Float | Captured at invoice creation (default 6%) |
| `discount_rate` | Float | `0.0` or `0.10` (employee discount) |
| `surcharge_rate` | Float | `0.0` or `0.03`; set automatically by payment method |
| `subtotal` | Float | Sum of line prices |
| `discount_amount` | Float | `subtotal × discount_rate` |
| `tax_amount` | Float | `(subtotal − discount) × tax_rate` |
| `surcharge_amount` | Float | `(subtotal − discount) × surcharge_rate` |
| `total` | Float | `subtotal − discount + tax + surcharge` |

### InvoiceLine

One item on an invoice (join between Invoice and Inventory).

| Field | Type | Notes |
|-------|------|-------|
| `invoice_id` | FK → Invoice | |
| `inventory_id` | FK → Inventory | |
| `price` | Float | Price at time of sale (snapshot) |

---

## Invoice Calculation

```
subtotal        = Σ line.price
discount_amount = subtotal × discount_rate
discounted      = subtotal − discount_amount
tax_amount      = discounted × tax_rate
surcharge_amount= discounted × surcharge_rate   (0 if Cash or Check)
total           = discounted + tax_amount + surcharge_amount
```

`calculate_totals()` on the Invoice model recomputes all derived fields and must be
called (followed by `db.session.commit()`) any time lines are added or removed, or when
the discount/payment method changes.

---

## Item Status Lifecycle

```
         check-in
(tagged) ─────────► In-Stock
                        │
                   added to cart
                        ▼
                     Pending
                        │
               sale completed / cart abandoned
               ┌────────┴────────┐
               ▼                 ▼
             Sold            In-Stock  (item removed from cart)
                                 │
                          check-out day
                      ┌──────────┴──────────┐
                      ▼                     ▼
                  Returned              Donated
```

---

## Payout Calculation

Vendor payouts are calculated from **InvoiceLine** records, not from inventory status.
Only lines on **completed invoices** count toward payout.

```
vendor_payout = Σ line.price × (1 − vendor.commission_rate)
```

The dashboard and payout report both use this formula.

---

## SKU Rules

- Must be an integer between 1 and 9,999,999
- Unique across all vendors (not scoped per vendor)
- Bulk Vendors typically receive a pre-assigned range for self-tagging
- SKUs sort ascending in all list views and reports

---

## Surcharge Triggers

A 3% surcharge (`SURCHARGE_RATE` in `models.py`) is automatically applied when
`payment_method` is `"Credit Card"` or `"Venmo"`. All other methods have no surcharge.

---

## Database Migrations

No migration tool (Alembic, Flask-Migrate) is used. New columns are added via
`ALTER TABLE` statements in `app.py` at startup, inside a try/except block:

```python
try:
    db.session.execute(text('ALTER TABLE invoice ADD COLUMN discount_rate FLOAT DEFAULT 0.0'))
    db.session.commit()
except Exception:
    db.session.rollback()  # column already exists — safe to ignore
```

Column type changes require a table rename + recreate + copy pattern.
