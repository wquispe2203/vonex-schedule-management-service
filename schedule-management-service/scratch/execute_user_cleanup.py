import sys
from app.core.database import SessionLocal
from app.models.user import User
from sqlalchemy import text

print("Starting transactional cleanup of user 'sistemas@vonex.edu.pe'...")

db = SessionLocal()
try:
    # 1. Find user by username
    user = db.query(User).filter(User.username == "sistemas@vonex.edu.pe").first()
    if not user:
        print("ERROR: User 'sistemas@vonex.edu.pe' not found in database.")
        sys.exit(1)
        
    user_id = str(user.id)
    print(f"Found user: {user.username} (ID: {user_id})")

    # 2. Delete associations in user_roles
    print("Deleting user-role associations...")
    deleted_associations = db.execute(
        text("DELETE FROM user_roles WHERE user_id = :uid"),
        {"uid": user_id}
    ).rowcount
    print(f"Deleted {deleted_associations} user-role associations.")

    # 3. Nullify resolved_by in match_reviews
    print("Nullifying resolved_by references in match_reviews...")
    nullified_reviews = db.execute(
        text("UPDATE match_reviews SET resolved_by = NULL WHERE resolved_by = :uid"),
        {"uid": user_id}
    ).rowcount
    print(f"Nullified {nullified_reviews} match_reviews references.")

    # 4. Delete user
    print("Deleting user from 'users' table...")
    db.delete(user)
    db.commit()
    print("Transaction successfully committed.")

    # 5. Verification
    checked_user = db.query(User).filter(User.username == "sistemas@vonex.edu.pe").first()
    if not checked_user:
        print("SUCCESS: User 'sistemas@vonex.edu.pe' has been completely removed.")
    else:
        print("ERROR: User still exists in the database.")

    # Check total users remaining
    total_users = db.query(User).all()
    print(f"Remaining users in DB: {len(total_users)}")
    for u in total_users:
        print(f"- {u.username} (Roles: {[r.name for r in u.roles]})")

except Exception as e:
    db.rollback()
    print(f"ERROR: Deletion aborted and transaction rolled back. Details: {e}")
    sys.exit(1)
finally:
    db.close()
