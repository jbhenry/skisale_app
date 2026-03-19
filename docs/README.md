# MBSP Ski Swap — Documentation

This directory contains documentation for the `skisale_app` application, covering both the
software itself and how it is used to run the **Mt. Brighton Ski Patrol Ski Swap**.
Notes specific to our environment are called out where applicable.

## Contents

| File | Audience | Description |
|------|----------|-------------|
| [setup.md](setup.md) | Developers / IT | Installation, configuration, first run |
| [hardwaresetup.md](hardwaresetup.md) | Developers / IT | Installation of PC's, etc. **Mt. B-specific** |
| [operations.md](operations.md) | Event administrators | Day-of-sale workflow |
| [user-guide.md](user-guide.md) | Volunteers / cashiers | Using the app at the sale |
| [admin-guide.md](admin-guide.md) | Administrators | Admin panel, reports, backups, reset |
| [data-model.md](data-model.md) | Developers | Business rules, data model, calculations |

## Quick Links

- **Start the app:** `source bin/activate && python app.py` → http://localhost:5000
- **Production server:** `source bin/activate && python serve.py`
- **Run tests:** `source bin/activate && python -m pytest tests/ -v`
- **Re-initialize DB:** `python init_db.py` *(destructive — wipes all data)*
