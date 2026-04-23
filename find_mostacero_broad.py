from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def find_hidden_mostacero():
    db = SessionLocal()
    try:
        print("--- Searching 'MOSTACERO' in ALL observation fields ---")
        query = text("""
            SELECT id, teacher_id, replacement_teacher_name, replacement_teacher_id, observation_type 
            FROM observations 
            WHERE replacement_teacher_name ILIKE '%MOSTACERO%'
               OR replacement_teacher_name ILIKE '%JORDY%'
        """)
        res = db.execute(query).fetchall()
        
        if not res:
            print("Zero observations found with 'MOSTACERO' or 'JORDY' in replacement name.")
        else:
            for r in res:
                print(f"ID: {r[0]}, Repl Name: '{r[2]}', Repl ID: {r[3]}, Type: {r[4]}")

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    find_hidden_mostacero()
