from app.database import engine
from sqlalchemy import text

def inspect_db():
    with engine.connect() as conn:
        # Check constraints
        res = conn.execute(text("SELECT conname FROM pg_constraint WHERE conname IN ('uq_role_permission', 'uq_user_role')"))
        constraints = [r[0] for r in res]
        print(f"Constraints found: {constraints}")
        
        # Check column names for users table as sample
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
        columns = [r[0] for r in res]
        print(f"Columns in 'users': {columns}")

if __name__ == "__main__":
    inspect_db()
