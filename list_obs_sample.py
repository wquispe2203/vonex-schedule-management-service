from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def list_sample_observations():
    db = SessionLocal()
    try:
        print("--- Listing 20 observations (replacement info): ---")
        query = text("""
            SELECT id, replacement_teacher_name, replacement_teacher_id 
            FROM observations 
            WHERE replacement_teacher_name IS NOT NULL AND replacement_teacher_name != ''
            LIMIT 20
        """)
        res = db.execute(query).fetchall()
        
        for r in res:
            print(f"ID: {r[0]}, Name: '{r[1]}', Rel ID: {r[2]}")

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    list_sample_observations()
