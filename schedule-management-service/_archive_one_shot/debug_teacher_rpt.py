from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_teacher_visibility(full_name):
    db = SessionLocal()
    try:
        print(f"--- Debugging visibility for: {full_name} ---")
        
        # 1. Search in teachers table
        search_term = f"%{full_name.replace(' ', '%').upper()}%"
        query = text("""
            SELECT id, first_name, last_name, is_active, normalized_name 
            FROM teachers 
            WHERE UPPER(last_name || ' ' || first_name) LIKE :term
               OR UPPER(first_name || ' ' || last_name) LIKE :term
        """)
        res = db.execute(query, {"term": search_term}).fetchall()
        
        if not res:
            print(f"ERROR: Teacher not found in 'teachers' table with name like '{full_name}'")
            return
        
        for t in res:
            t_id, fname, lname, is_active, norm_name = t
            print(f"Teacher Found: ID={t_id}, Name='{lname}, {fname}', is_active={is_active}, Normalized='{norm_name}'")
            
            # 2. Check Lessons
            lesson_count = db.execute(text("SELECT count(*) FROM lessons WHERE teacher_id = :id"), {"id": t_id}).scalar()
            print(f" - Lessons found: {lesson_count}")
            
            # 3. Check Observations (as original teacher)
            obs_orig = db.execute(text("SELECT count(*) FROM observations WHERE teacher_id = :id"), {"id": t_id}).scalar()
            print(f" - Observations (as primary): {obs_orig}")
            
            # 4. Check Observations (as replacement)
            obs_repl = db.execute(text("SELECT count(*) FROM observations WHERE replacement_teacher_id = :id"), {"id": t_id}).scalar()
            print(f" - Observations (as replacement): {obs_repl}")
            
            # 5. Check if they SHOULD be in the list
            should_be_visible = is_active and (lesson_count > 0 or obs_repl > 0)
            print(f"VERDICT: Should be visible in RPT? {'YES' if should_be_visible else 'NO'}")
            
            if not is_active:
                print(" REASON: is_active is FALSE.")
            elif lesson_count == 0 and obs_repl == 0:
                print(" REASON: No workload (lessons) AND no replacement observations found for this ID.")

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_teacher_visibility("MOSTACERO GUTIERREZ JORDY ANDRES")
