import os
import sys
from app.core.database import SessionLocal
from app.models import Teacher, MatchReview, TeacherNameOverride
from sqlalchemy import text

print("Starting transactional surgical teacher cleanup...")

db = SessionLocal()
try:
    # 1. Clear self-referential foreign keys on teachers to avoid circular dependency constraint violations during delete
    print("Clearing self-referential foreign keys on teachers...")
    db.execute(text("UPDATE teachers SET possible_match_id = NULL, merged_into_id = NULL, match_review_id = NULL"))
    db.flush()

    # 2. Clear match reviews
    print("Deleting all match reviews...")
    deleted_reviews = db.execute(text("DELETE FROM match_reviews")).rowcount
    print(f"Deleted {deleted_reviews} match reviews.")

    # 3. Clear teacher name overrides
    print("Deleting all teacher name overrides...")
    deleted_overrides = db.execute(text("DELETE FROM teacher_name_overrides")).rowcount
    print(f"Deleted {deleted_overrides} teacher name overrides.")

    # 4. Clear all teachers
    print("Deleting all teachers...")
    deleted_teachers = db.execute(text("DELETE FROM teachers")).rowcount
    print(f"Deleted {deleted_teachers} teachers from table 'teachers'.")

    # 5. Commit transaction
    db.commit()
    print("Transaction successfully committed.")

    # 6. Verify count
    remaining_teachers = db.query(Teacher).count()
    print(f"Verification - Remaining teachers count in DB: {remaining_teachers}")
    
    if remaining_teachers == 0:
        print("SUCCESS: The teachers table is completely empty.")
    else:
        print("WARNING: Some teachers still exist in the database.")

except Exception as e:
    db.rollback()
    print(f"ERROR: Transaction rolled back. Details: {e}")
    sys.exit(1)
finally:
    db.close()
