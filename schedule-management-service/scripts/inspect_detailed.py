import sys
import os
from sqlalchemy import create_engine, text

# Add project path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

def inspect_structure(url, label):
    print(f"\n=== INSPECTING: {label} ===")
    engine = create_engine(url)
    with engine.connect() as conn:
        tables = ['lessons', 'observations']
        for t in tables:
            print(f"\n--- Table: {t} ---")
            # Columns
            cols = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t}'")).all()
            print("Columns:", [f"{c[0]} ({c[1]})" for c in cols])
            
            # Indexes
            idxs = conn.execute(text(f"SELECT indexname, indexdef FROM pg_indexes WHERE tablename = '{t}'")).all()
            print("Indexes:")
            for i in idxs:
                print(f"  - {i[0]}: {i[1]}")
                
            # Constraints
            cons = conn.execute(text(f"SELECT constraint_name, constraint_type FROM information_schema.table_constraints WHERE table_name = '{t}'")).all()
            print("Constraints:", [f"{c[0]} [{c[1]}]" for c in cons])

if __name__ == "__main__":
    inspect_structure(settings.DATABASE_URL, "PROD/DEV")
    if settings.TEST_DATABASE_URL:
        inspect_structure(settings.TEST_DATABASE_URL, "TEST")
