from sqlalchemy import text
from app.core.database import engine

def create_trigger():
    print("Connecting to DB to create auto-update trigger on teachers table...")
    with engine.begin() as conn:
        try:
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """))
            print("Successfully created/updated function update_updated_at_column()!")
        except Exception as e:
            print(f"Error creating function: {e}")
            
        try:
            # Drop trigger if exists to avoid duplication errors, then create it
            conn.execute(text("DROP TRIGGER IF EXISTS update_teachers_updated_at ON teachers;"))
            conn.execute(text("""
                CREATE TRIGGER update_teachers_updated_at
                BEFORE UPDATE ON teachers
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """))
            print("Successfully created auto-update trigger on teachers table!")
        except Exception as e:
            print(f"Error creating trigger: {e}")

if __name__ == "__main__":
    create_trigger()
