"""
Initialize database with sample consignors and inventory
Run this once to set up the database with example data
"""
from app import app, db
from models import Vendor, Inventory

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Check if consignors already exist
        if Vendor.query.first():
            print("⚠ Database already has data. Skipping sample data.")
            return
        
        # Add sample consignors (ID will be auto-generated)
        sample_consignors = [
            Vendor(
                first_name="Sarah",
                last_name="Johnson",
                phone="(303) 555-0123",
                email="sarah.johnson@email.com",
                address1="1234 Mountain View Dr",
                city="Denver",
                state="CO",
                zip_code="80202",
                commission_rate=0.20,
                payment_method="Check",
                notes="Brings in high-quality ski equipment annually. Prefers checks for payment.",
                active=True
            ),
            Vendor(
                first_name="Mike",
                last_name="Smith",
                phone="(720) 555-0456",
                email="mike.smith@email.com",
                address1="567 Powder Ln",
                city="Boulder",
                state="CO",
                zip_code="80301",
                commission_rate=0.25,
                payment_method="PayPal",
                notes="Regular consignor. Mostly snowboards and winter gear.",
                active=True
            ),
            Vendor(
                first_name="Lisa",
                last_name="Chen",
                phone="(303) 555-0789",
                email="lisa.chen@email.com",
                address1="890 Alpine Way",
                city="Aspen",
                state="CO",
                zip_code="81611",
                commission_rate=0.20,
                payment_method="Venmo",
                notes="Youth ski equipment specialist. Fast response time.",
                active=True
            ),
            Vendor(
                first_name="David",
                last_name="Garcia",
                phone="(970) 555-0321",
                email="david.garcia@email.com",
                address1="2100 Peak Dr",
                city="Vail",
                state="CO",
                zip_code="81657",
                commission_rate=0.15,
                payment_method="Cash",
                notes="Large consignor with premium equipment. VIP commission rate.",
                active=True
            ),
            Vendor(
                first_name="Emily",
                last_name="Martinez",
                phone="(303) 555-0654",
                email="emily.martinez@email.com",
                address1="3711 Ski Slope Rd",
                city="Breckenridge",
                state="CO",
                zip_code="80424",
                commission_rate=0.20,
                payment_method="Check",
                notes="Seasonal consignor. Focus on women's ski gear and accessories.",
                active=True
            ),
            Vendor(
                first_name="Robert",
                last_name="Wilson",
                phone="(303) 555-0987",
                email="",
                address1="",
                city="",
                state="",
                zip_code="",
                commission_rate=0.20,
                payment_method="Cash",
                notes="One-time consignor from last season. No longer active.",
                active=False
            ),
        ]
        
        for vendor in sample_consignors:
            db.session.add(vendor)
        
        db.session.commit()
        print(f"✓ Added {len(sample_consignors)} sample consignors")
        
        # Add sample inventory items
        sample_inventory = [
            Inventory(sku="1000001", vendor_id=1, equipment_type="Skis", 
                     description="Rossignol Experience 170cm", price=150.00, status="In-Stock"),
            Inventory(sku="1000002", vendor_id=1, equipment_type="Poles", 
                     description="Aluminum ski poles", price=25.00, status="In-Stock"),
            Inventory(sku="1000003", vendor_id=2, equipment_type="Snowboards", 
                     description="Burton Custom 158cm", price=200.00, status="In-Stock"),
            Inventory(sku="1000004", vendor_id=2, equipment_type="Boots", 
                     description="Burton Ion snowboard boots, size 10", price=120.00, status="Sold"),
            Inventory(sku="1000005", vendor_id=3, equipment_type="Skis", 
                     description="Youth skis 130cm with bindings", price=75.00, status="In-Stock"),
            Inventory(sku="1000006", vendor_id=3, equipment_type="Helmets", 
                     description="Smith youth helmet, size small", price=30.00, status="In-Stock"),
            Inventory(sku="1000007", vendor_id=4, equipment_type="Skis", 
                     description="Atomic Vantage 177cm", price=250.00, status="In-Stock"),
            Inventory(sku="1000008", vendor_id=4, equipment_type="Boots", 
                     description="Salomon X Pro 120, size 27.5", price=180.00, status="In-Stock"),
            Inventory(sku="1000009", vendor_id=5, equipment_type="Apparel", 
                     description="Women's ski jacket, size M", price=60.00, status="In-Stock"),
            Inventory(sku="1000010", vendor_id=5, equipment_type="Goggles", 
                     description="Oakley Flight Deck XM", price=100.00, status="In-Stock"),
        ]
        
        for item in sample_inventory:
            db.session.add(item)
        
        db.session.commit()
        print(f"✓ Added {len(sample_inventory)} sample inventory items")
        
        print("\nSample consignors:")
        for v in Vendor.query.order_by(Vendor.id).all():
            status = "Active" if v.active else "Inactive"
            item_count = len(v.inventory_items)
            print(f"  - ID #{v.id}: {v.full_name} ({status}, {int(v.commission_rate * 100)}% commission, {item_count} items)")

if __name__ == '__main__':
    print("Initializing SkiSale database...")
    init_db()
    print("\n✓ Database initialization complete!")
    print("\nYou can now run: python app.py")
