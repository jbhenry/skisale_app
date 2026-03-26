# Event Operations Guide

This guide covers the full lifecycle of running a ski swap event using this application,
from pre-event setup through vendor payouts.

## Event Lifecycle Overview

1. [Pre-Event: Vendor Registration](#1-pre-event-vendor-registration)
2. [Check-In Day: Receiving Items](#2-check-in-day-receiving-items)
3. [Sale Day: Processing Sales](#3-sale-day-processing-sales)
4. [Post-Sale: Checkout & Payouts](#4-post-sale-checkout--payouts)
5. [Reset for Next Event](#5-reset-for-next-event)

---

## 1. Pre-Event: Vendor Registration

- Add vendors via **Vendors → New Vendor**
- Assign each vendor a unique ID (auto-incremented)
- Set the commission rate (default: 23% — General Public)
- Print or distribute SKU ranges to vendors so they can tag their items

---

## 2. Check-In Day: Receiving Items

- Navigate to a vendor's detail page → **Check In Items**
- Scan or type each SKU as the vendor brings items in
- Items are set to **In-Stock** status upon check-in
- A **Check-In Receipt** can be printed for the vendor to sign — it lists all items
  accepted and the estimated payout

### CSV Import (bulk check-in)

If vendors pre-fill a spreadsheet, use **Import CSV** on the vendor page.
See [user-guide.md](user-guide.md) for CSV format requirements.

---

## 3. Sale Day: Processing Sales

- Set your **Register ID** from the navbar (required once per browser session before making any changes)
- Create a new sale via **Invoices → New Sale** or the **Dashboard** button
- Add items by SKU; items move to **Pending** status when added to a cart
- Select payment method (Cash, Check, Credit Card, Venmo)
  - Credit Card and Venmo automatically add a 3% surcharge
- Apply an employee/volunteer discount if applicable (10%)
- Complete the sale → items move to **Sold** status
- Print the receipt for the customer

---

## 4. Post-Sale: Checkout & Payouts

- Navigate to each vendor's page → **Check Out Items**
- Scan or select items to mark as **Returned to Vendor** (items not sold that the vendor is
  picking up) or **Donated** (left for the organization to keep/discard)
- Print the **Payout Receipt** — it shows items sold, commission withheld, and net payout
- Use **Admin → Payout Report** to download an XLSX spreadsheet of all vendor payouts
  for writing checks

---

## 5. Reset for Next Event

> ⚠️ **This is destructive.** Back up the database before proceeding.

- **Admin → Backup Database (Server)** — save a timestamped copy to the server's `backups/` folder
- **Admin → Download Database** — download a copy directly to your browser for off-site storage
- **Admin → Initialize for New Event** — clears all invoices, sales, and inventory;
  sets all vendors to inactive

Vendors are set inactive (not deleted) so their names and IDs are preserved for
future events. Reactivate returning vendors rather than creating duplicates.
