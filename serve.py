from waitress import serve
from app import app
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/skisale_app.log'),
        logging.StreamHandler()  # keeps console output too
    ]
)

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000, threads=4)
