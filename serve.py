from waitress import serve
from app import app
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        RotatingFileHandler('logs/skisale_app.log', maxBytes=1_000_000, backupCount=5),
        logging.StreamHandler()  # keeps console output too
    ]
)

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000, threads=4)
