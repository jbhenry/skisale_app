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

VENDOR_PAYMENT_METHODS = [
    'Cash',
    'Check',
    'PayPal',
    'Venmo',
]

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
    (15,  '15% — Employees'),
    (23,  '23% — General Public'),
    (100, '100% — MBSP Only'),
]

# Valid SKU range for inventory items
SKU_MIN = 1
SKU_MAX = 9_999_999

# Organization info printed on checks — update before printing
ORG_NAME  = 'Mt. Brighton Ski Patrol Ski Swap'
ORG_ADDR1 = '4141 Bauer Road'
ORG_ADDR2 = 'Brighton, MI 48116'
CHECK_NUMBER_START = 1001  # First check number in the run
