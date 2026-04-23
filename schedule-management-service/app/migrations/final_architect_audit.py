import psycopg
from app.database import SQLALCHEMY_DATABASE_URL

def final_audit():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [r[0] for r in cur.fetchall()]
                
                print("--- FINAL ARCHITECTURAL AUDIT ---")
                for table in sorted(tables):
                    print(f"\n{table}:")
                    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
                    for col in cur.fetchall():
                        print(f"  - {col[0]} ({col[1]})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    final_audit()
