from app.database import engine
from sqlalchemy import text

def patch_db():
    print("Patching database...")
    with engine.connect() as conn:
        try:
            # Teachers table
            conn.execute(text("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS short_name VARCHAR(50)"))
            conn.execute(text("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS razon_social VARCHAR(255)"))
            conn.execute(text("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
            
            conn.commit()
            print("SUCCESS: columns 'short_name', 'razon_social', 'is_active' verified in 'teachers'.")
        except Exception as e:
            print(f"Error patching DB: {e}")

if __name__ == "__main__":
    patch_db()
