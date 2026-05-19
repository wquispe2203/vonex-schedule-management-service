from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/vonex_schedule"))
inspector = inspect(engine)
columns = inspector.get_columns('observations')
print("COLUMNS IN 'observations' TABLE:")
for col in columns:
    print(f"  - {col['name']} ({col['type']})")
