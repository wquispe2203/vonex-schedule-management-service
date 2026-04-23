import psycopg
from app.database import SQLALCHEMY_DATABASE_URL

def check_schema():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    tables = ['teachers', 'lessons', 'observations', 'users', 'classes', 'subjects', 'schedule_sessions']
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                print("--- PHYSICAL SCHEMA AUDIT ---")
                for table in tables:
                    print(f"\nTABLE: {table}")
                    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
                    for col in cur.fetchall():
                        print(f"  - {col[0]} ({col[1]})")
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    check_schema()
