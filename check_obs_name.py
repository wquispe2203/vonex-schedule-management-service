from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_observations_for_name(name_part):
    db = SessionLocal()
    try:
        print(f"--- Searching observations for replacement name containing: '{name_part}' ---")
        query = text("""
            SELECT id, teacher_id, replacement_teacher_name, replacement_teacher_id, date, observation_type 
            FROM observations 
            WHERE UPPER(replacement_teacher_name) LIKE :term
        """)
        res = db.execute(query, {"term": f"%{name_part.upper()}%"}).fetchall()
        
        if not res:
            print("No observations found as replacement for this name.")
            return

        for r in res:
            print(f"Obs ID: {r[0]}, Orig Teacher ID: {r[1]}, Repl Name: '{r[2]}', Repl ID: {r[3]}, Date: {r[4]}, Type: {r[5]}")

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_observations_for_name("MOSTACERO")
