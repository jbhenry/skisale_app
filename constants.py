"""
Shared application constants.
"""
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo('America/New_York')

EQUIPMENT_TYPES = [
    'Skis',
    'Snowboards',
    'Boots-Ski',
    'Boots-Snowboard',
    'Poles',
    'Bindings',
    'Helmets',
    'Goggles',
    'Apparel',
    'Accessories',
    'Other',
    'XC-Skis',
    'XC-Boots'
]

INVENTORY_STATUSES = [
    'In-Stock',
    'Pending',
    'Not In Stock',
    'Donated',
    'Sold',
    'Rejected',
    'Returned to Vendor'
]

PAYMENT_METHODS = [
    'Credit Card',
    'Cash',
    'Check',
    'Venmo',
]

# For now, we only pay via check...
VENDOR_PAYMENT_METHODS = [
    'Check',
]
# ... but we may add these later.
    # 'Cash',
    # 'PayPal',
    # 'Venmo',

# Default sales tax rate (can be changed per invoice)
DEFAULT_TAX_RATE = 0.06  # 6%

# Surcharge applied for certain payment methods
SURCHARGE_RATE = 0.03  # 3%
SURCHARGE_METHODS = {'Credit Card', 'Venmo'}

# Employee discount rate applied when an employee discount is selected
EMPLOYEE_DISCOUNT_RATE = 0.10  # 10%

# Default commission rate for new vendors (must match the form default in COMMISSION_RATES)
DEFAULT_VENDOR_COMMISSION_RATE = 0.23  # 23% — General Public

# Available vendor commission rates: (integer_pct, display_label)
# The first entry is the default for new vendors.
COMMISSION_RATES = [
    (15,  '15% — Employees/Patrollers'),
    (23,  '23% — General Public'),
]
# Removed this one from COMMISSION_RATES due to it causing confusion. Only one vendor will have this rate,
# and can be set manually.
#    (100, '100% — MBSP Only'),



# Valid SKU range for inventory items
SKU_MIN = 1
SKU_MAX = 9_999_999

# Disclaimer text printed at the bottom of the customer sales receipt
SALES_RECEIPT_DISCLAIMER = """ALL SALES ARE FINAL - NO RETURNS

NOTICE-DISCLAIMER
Neither the Mt. Brighton Ski Patrol, its subsidiaries, related organizations, members or agents make any representation concerning the equipment listed above on this sale receipt and in particular, no such representation, warranties, or guarantees are made towards the use or fitness for use or safety of any of this equipment and its attachments.
The purchaser of these items is advised and urged to have any bindings checked and adjusted at the ski shop of his/her choice."""

# Disclaimer text printed on the vendor check-in receipt
VENDOR_CHECKIN_DISCLAIMER = """This WINTER SPORTS EQUIPMENT SALE is run by the Mt. Brighton Ski Patrol (hereafter referred to as the MBSP) as an independent fund raising function at Mt. Brighton Ski Area. The MBSP does not assume any responsibility for the WINTER SPORTS EQUIPMENT SALE. All ski and snowboard equipment is subject to our approval prior to acceptance to the sale. We reserve the right to reject any or all equipment for any reason.

CHARGES: Estimated payout is based on items currently In-Stock. Final payout calculated after items sell. If the item sells, we will deduct a 23% commission charge calculated on the selling price and the remainder will be paid by check. Check for sold items on www.mtbrightonskipatrol.com starting Saturday afternoon.

PICK-UP OF UNSOLD MERCHANDISE: Unsold merchandise must be picked up at Mt. Brighton on the Sunday of the sale weekend, No later than 5:00pm. We do not have ANY provisions for storage of leftover merchandise and will be considered donated if not picked up by 5:00pm on Sunday of the sale weekend. Unclaimed items will be considered donated and will be disposed of at our discretion.
Beginning Saturday afternoon, we will be posting the status of sold items on our website at www.mtbrightonskipatrol.com. You can check there to see if your items have sold. Status will be updated periodically Saturday afternoon and Sunday.
Prices may not be changed on tags. Any change on tags will result in the merchandise being withdrawn from the sale. This is for your protection as well as ours.

The MBSP cannot assume responsibility for losses because of theft, fire, riot, natural disaster, or other circumstances. MBSP is a volunteer, nonprofit public service organization and does not purchase or acquire loss insurance."""

# Organization info printed on checks — update before printing
ORG_NAME  = 'Mt. Brighton Ski Patrol Ski Swap'
ORG_ADDR1 = '4141 Bauer Road'
ORG_ADDR2 = 'Brighton, MI 48116'
CHECK_NUMBER_START = 1001  # First check number in the run
