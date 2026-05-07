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
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'lessons'")).all()
        cols = [r[0] for r in res]
        print(f"Found columns in 'lessons': {cols}")
        
        target = 'old_system_subject_id'
        if target in cols:
            print(f"MATCH: {target} is in list.")
        else:
            print(f"NO MATCH: {target} NOT in list.")

if __name__ == "__main__":
    debug_columns(settings.DATABASE_URL, "PROD/DEV")
