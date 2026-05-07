import sys
from sqlalchemy import text
from app.core.database import engine

def migrate():
    print("Connecting to DB to add updated_at column...")
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE teachers ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();"))
            print("Successfully added updated_at column!")
        except Exception as e:
            print(f"Adding column note/error: {e}")
        
        try:
            conn.execute(text("UPDATE teachers SET updated_at = NOW() WHERE updated_at IS NULL;"))
            print("Successfully updated NULL updated_at values!")
        except Exception as e:
            print(f"Updating rows note/error: {e}")

if __name__ == "__main__":
    migrate()
