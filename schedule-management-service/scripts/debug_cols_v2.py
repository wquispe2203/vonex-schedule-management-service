import sys
import os
from sqlalchemy import create_engine, text

# Add project path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

def debug_columns(url, label):
    print(f"\n--- DEBUGGING: {label} ---")
    engine = create_engine(url)
    with engine.connect() as conn:
        for table in ['lessons', 'observations']:
            res = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")).all()
            cols = [r[0] for r in res]
            print(f"Table '{table}' columns: {cols}")

if __name__ == "__main__":
    debug_columns(settings.DATABASE_URL, "PROD/DEV")
    if settings.TEST_DATABASE_URL:
        debug_columns(settings.TEST_DATABASE_URL, "TEST")
