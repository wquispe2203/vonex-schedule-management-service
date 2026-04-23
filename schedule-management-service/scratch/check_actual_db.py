from app.database import engine
from sqlalchemy import inspect

def check_db():
    inspector = inspect(engine)
    tables = ["users", "xml_uploads", "rpt_planilla", "break_config", "lunch_config"]
    
    for table in tables:
        print(f"\n--- Columns in '{table}' ---")
        try:
            columns = inspector.get_columns(table)
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
        except Exception as e:
            print(f"  Error checking table {table}: {e}")

if __name__ == "__main__":
    check_db()
