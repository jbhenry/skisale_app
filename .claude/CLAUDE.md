# SkiSale App - Claude Instructions

## Environment
- Python virtualenv in `bin/` — always activate before running anything:
  ```
  source bin/activate
  ```
- Start the app: `python app.py` → http://localhost:5000
- Initialize DB with sample data: `python init_db.py`
- Production database: `var/app-instance/skisale.db`
- Backup: copy `var/app-instance/skisale.db`

## Run Tests
```
source bin/activate && python -m pytest tests/ -v      # full suite, verbose
source bin/activate && python -m pytest tests/ -q      # full suite, quiet
source bin/activate && python -m pytest tests/test_admin.py -v   # one file
```

## Architecture
- Flask + SQLAlchemy + SQLite, no Alembic — schema changes done as startup migrations
- Soft-delete vendors (`active=False`), hard-delete inventory
- Invoice workflow: In-Stock → Pending (in cart) → Sold (invoice completed)
- 3% surcharge applied automatically for Credit Card and Venmo payments
- Dashboard payouts calculated from invoice lines, not inventory status

## Database Migrations
New columns are added at startup in `app.py` using try/except ALTER TABLE:
```python
try:
    db.session.execute(text('ALTER TABLE ... ADD COLUMN ...'))
    db.session.commit()
except Exception:
    db.session.rollback()  # column already exists
```
Column type changes (like sku VARCHAR→INTEGER) require table rename + recreate + copy.

## Testing — Critical Pattern
Flask-SQLAlchemy caches the production engine at startup. Changing
`SQLALCHEMY_DATABASE_URI` has no effect. Tests swap the engine directly:
```python
engine_cache = _db._app_engines[flask_app]
engine_cache[None] = test_engine   # swap in
# ... test ...
engine_cache[None] = prod_engine   # restore
```
`StaticPool` is required so all connections share one in-memory SQLite DB.
**Never use `db.drop_all()` without this isolation — it will wipe production data.**

## Code Conventions
- `db.get_or_404()` — not the deprecated `.query.get_or_404()`
- `utcnow()` helper (models.py) — not `datetime.utcnow`
- SKU is `db.Integer`, up to 7 digits (1–9999999)
- Inventory list and XLSX reports sort by SKU ascending
- Vendor list: combined full_name column, sortable by ID or Name
- XLSX reports: row 1 = merged title (bold, size 16), row 2 = headers, row 3+ = data
