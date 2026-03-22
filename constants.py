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

# Default sales tax rate (can be changed per invoice)
DEFAULT_TAX_RATE = 0.06  # 6%

# Organization info printed on checks — update before printing
ORG_NAME  = 'Mt. Brighton Ski Patrol Ski Swap'
ORG_ADDR1 = '4141 Bauer Road'
ORG_ADDR2 = 'Brighton, MI 48116'
CHECK_NUMBER_START = 1001  # First check number in the run
