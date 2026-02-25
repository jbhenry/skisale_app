# 🎿 SkiSale - Quick Start Guide

## What You Got

A complete **Consignor Management** web app to replace your Access database!

### Features
- ✅ Add, edit, view, and deactivate consignors (individual people bringing in gear)
- ✅ Track commission rates (% you keep from sales)
- ✅ Track payment preferences (Cash, Check, PayPal, Venmo, etc.)
- ✅ Search and filter
- ✅ Modern, clean interface
- ✅ Works on any device (desktop, tablet, phone)
- ✅ Multi-user ready (10 users can use it simultaneously)

---

## 🚀 Get Started in 3 Steps

### Step 1: Install Flask
Open terminal/command prompt in the `skisale_app` folder and run:

```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database with Sample Data
```bash
python init_db.py
```

This creates the database and adds 6 sample consignors so you can see how it works.

### Step 3: Start the App
```bash
python app.py
```

### Step 4: Open in Browser
Go to: **http://localhost:5000**

---

## 📖 How to Use

### Main Features

1. **View Consignors**: Click "Consignors" in the nav bar
2. **Add New Consignor**: Click "New Consignor" button (Vendor ID assigned automatically)
3. **Search**: Type in the search box (searches name or email)
4. **View Details**: Click any consignor's last name
5. **Edit**: Click the pencil icon or "Edit" button (Vendor ID cannot be changed)
6. **Deactivate**: Click the trash icon

### Tips
- Vendor IDs are auto-generated (e.g., #1, #2, #3)
- Default commission rate is 20% (you keep 20%, they get 80%)
- Toggle "Active consignors only" to filter
- The app auto-saves when you click Create/Update

---

## 🌐 Network Access (For Your 10 Users)

To let others access the app on your network:

1. **Find your computer's IP address**:
   - Windows: Open cmd, type `ipconfig`, look for "IPv4 Address"
   - Mac: System Preferences → Network
   - Linux: Run `ip addr` or `ifconfig`

2. **Share this URL with your team**:
   `http://YOUR_IP_ADDRESS:5000`
   
   Example: `http://192.168.1.100:5000`

3. **Make sure**:
   - Your firewall allows port 5000
   - Everyone is on the same network
   - The app is running (don't close the terminal)

---

## 📁 File Structure

```
skisale_app/
├── app.py              # Main application (Flask routes)
├── models.py           # Database models (Vendor table)
├── init_db.py          # Database initialization script
├── requirements.txt    # Python dependencies
├── README.md          # Full documentation
├── skisale.db         # SQLite database (created when you run init_db.py)
└── templates/         # HTML templates
    ├── base.html           # Base layout
    ├── vendors_list.html   # Vendor list page
    ├── vendor_form.html    # Add/Edit form
    └── vendor_view.html    # Vendor detail page
```

---

## ❓ Common Questions

**Q: Can I customize the consignor fields?**
A: Yes! Edit `models.py` to add fields, then recreate the database.

**Q: How do I backup my data?**
A: Just copy the `skisale.db` file. That's your entire database!

**Q: Can I change the commission rates?**
A: Yes! Each consignor can have their own commission rate (e.g., 15%, 20%, 25%).

**Q: Can I switch to PostgreSQL later?**
A: Absolutely! Just change one line in `app.py`. Everything else stays the same.

**Q: What's next after Consignors?**
A: We'll build Inventory (track items by consignor), then Customers, then Invoices. One module at a time!

**Q: How do I stop the server?**
A: Press `Ctrl+C` in the terminal

---

## 🆘 Troubleshooting

**"Port 5000 already in use"**
- Another app is using that port
- Edit `app.py`, change `port=5000` to `port=5001`

**"Can't connect from other computers"**
- Check firewall settings
- Make sure `host='0.0.0.0'` is in app.py (it is by default)
- Verify everyone is on the same WiFi/network

**"Database errors"**
- Delete `skisale.db` and run `python init_db.py` again
- This resets everything to fresh

---

## 🎯 Next Steps

Once you're comfortable with Consignors, let me know and I'll build:
1. **Inventory module** (track ski equipment by consignor)
2. **Customer module** (with customer types and discounts)
3. **Invoice module** (sales transactions with line items)
4. **Reports** (sales reports, consignor payouts, inventory reports)

Test it out with the sample data and let me know what you think! 🎿
