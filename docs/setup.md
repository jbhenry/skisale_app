# Setup & Installation

## Requirements

- Python 3.12+
- A Unix-like OS (Linux, macOS) or Windows with WSL

## Installation

```bash
# Clone the repository
git clone https://github.com/jbhenry/skisale_app.git
cd skisale_app

# Create and activate a virtual environment
python3 -m venv .
source bin/activate

# Install dependencies
pip install -r requirements.txt
```

## First Run

```bash
# Initialize the database with sample data (optional)
python init_db.py

# Start the development server
python app.py
```

The app will be available at http://localhost:5000.

> **Note:** `python app.py` uses Flask's built-in development server. Do not use this in
> production. See [Production Deployment](#production-deployment) below.

## Configuration

Key constants are defined at the top of `app.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `DEFAULT_TAX_RATE` | `0.06` (6%) | Sales tax rate applied to all invoices |
| `SURCHARGE_RATE` | `0.03` (3%) | Applied to Credit Card and Venmo payments |

These are code-level constants, not environment variables. Edit `app.py` to change them.

## Database

- **Location:** `var/app-instance/skisale.db` (SQLite)
- **Schema changes** are applied automatically at startup via `ALTER TABLE` migrations
  in `app.py` — no migration tool (e.g. Alembic) is used
- **Backups** are stored in `backups/` and can be triggered from the Admin panel

## Production Deployment

Use Waitress instead of the Flask dev server:

```bash
source bin/activate
python serve.py
```

Waitress listens on `0.0.0.0:5000` with 4 threads by default. To run on a different port,
edit `serve.py`.

For external access, place a reverse proxy (nginx, Caddy) in front of Waitress.

## Receipt Printer (MBSP-specific)

The invoice receipt page (`/invoices/<id>/receipt`) is formatted for the **Rongta RS332**
80mm thermal receipt printer. Print from any browser; select the Rongta as the printer
and the CSS will size the output correctly.
