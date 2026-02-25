# SkiSale Manager - Consignor Module

Python/Flask web application to replace Microsoft Access SkiSale database for consignment ski sales.

## What's Included

This is the **Consignor Management** module with:
- ✅ Create, view, edit, and deactivate consignors
- ✅ Track commission rates and payment preferences
- ✅ Search and filter consignors
- ✅ Clean, modern web interface
- ✅ SQLite database (easy to migrate to PostgreSQL later)
- ✅ Responsive design (works on desktop, tablet, mobile)

## Setup Instructions

### 1. Install Python Requirements

```bash
cd skisale_app
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The app will start on **http://localhost:5000** (or your computer's IP address on port 5000)

### 3. Access from Other Computers

If you want your 10 users to access this on the network:

1. Find your computer's IP address:
   - Windows: Run `ipconfig` in command prompt
   - Mac/Linux: Run `ifconfig` or `ip addr`

2. Other users can access via: `http://YOUR_IP:5000`
   - Example: `http://192.168.1.100:5000`

## Usage

### Adding a Consignor

1. Click "New Consignor" button
2. Fill in required fields (First Name, Last Name)
3. Set commission rate (default 20%)
4. Optionally add contact info, address, payment method, and notes
5. Click "Create Consignor"
6. A Vendor ID will be automatically assigned

### Viewing Consignors

- **List View**: See all consignors in a table with their Vendor ID
- **Detail View**: Click any consignor last name to see full details
- **Search**: Use search box to filter by name or email
- **Filter**: Toggle "Active consignors only" to hide inactive consignors

### Editing a Consignor

1. Click the pencil icon or open consignor detail view
2. Click "Edit" button
3. Make changes (note: Vendor ID cannot be changed)
4. Click "Update Consignor"

### Deactivating a Consignor

Click the trash icon next to a consignor (soft delete - consignor remains in database but marked inactive)

## Database

- **Location**: `skisale_app/skisale.db` (SQLite file)
- **Backup**: Just copy this file to backup your data
- **Migration to PostgreSQL**: Easy to switch when you're ready for production

## Database Schema

### Vendors Table (Consignors)

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key (auto-increment) - this is the Vendor ID |
| first_name | String(50) | Consignor's first name |
| last_name | String(50) | Consignor's last name |
| phone | String(20) | Phone number |
| email | String(100) | Email address |
| address1 | String(200) | Address line 1 |
| address2 | String(200) | Address line 2 |
| city | String(100) | City |
| state | String(2) | State (2-letter code) |
| zip_code | String(10) | ZIP/postal code |
| commission_rate | Float | Commission rate (e.g., 0.20 for 20%) |
| payment_method | String(20) | Preferred payment method (Cash, Check, PayPal, etc.) |
| notes | Text | Additional notes |
| active | Boolean | Is consignor active? |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

## Next Steps

Once you're happy with the Consignor module, we'll add:

1. **Inventory** - Track ski equipment by consignor
2. **Customers** - Customer management with discounts
3. **Invoices** - Sales transactions with line items
4. **Reports** - Sales reports, consignor payouts, inventory reports, etc.

## API Endpoints

The app includes REST API endpoints:

- `GET /api/vendors` - List all active consignors (JSON)
- `GET /api/vendors/<id>` - Get single consignor (JSON)

These can be used for integrations or custom reports.

## Customization

### Change Port

Edit `app.py`, line: `app.run(debug=True, host='0.0.0.0', port=5000)`

Change `port=5000` to your preferred port.

### Database Location

Edit `app.py`, line: `app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skisale.db'`

## Troubleshooting

**Port already in use**:
```bash
# Use a different port
python app.py
# Then edit app.py to use port 5001 or another port
```

**Can't access from other computers**:
- Check your firewall allows port 5000
- Make sure you're using `host='0.0.0.0'` in app.py
- Verify all computers are on the same network

**Database errors**:
- Delete `skisale.db` file and restart (this will reset the database)
- Check file permissions

## Support

Need help? Questions about next steps? Just ask!
