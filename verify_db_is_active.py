import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_db():
    db = SessionLocal()
    try:
        print("Checking column 'is_active' in table 'teachers'...")
        res = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='teachers' AND column_name='is_active'")).fetchone()
        if not res:
            print("ERROR: Column 'is_active' NOT FOUND in table 'teachers'")
            return
        
        print("Column 'is_active' exists. Checking for NULL values...")
        res = db.execute(text("SELECT count(*) FROM teachers WHERE is_active IS NULL")).fetchone()
        null_count = res[0]
        print(f"Number of teachers with 'is_active' IS NULL: {null_count}")

        print("\nChecking first 5 teachers:")
        res = db.execute(text("SELECT id, first_name, last_name, is_active FROM teachers LIMIT 5")).fetchall()
        for r in res:
            print(f"ID: {r[0]}, Name: {r[1]} {r[2]}, is_active: {r[3]}")

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
