import psycopg
from app.database import SQLALCHEMY_DATABASE_URL

def verify_final_state():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    tables = ["teachers", "subjects", "rpt_planilla", "observations", "schedule_sessions"]
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                print("--- FINAL ARCHITECTURAL STATE VERIFICATION ---")
                for table in tables:
                    print(f"\nTABLE: {table}")
                    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
                    cols = cur.fetchall()
                    for col in cols:
                        print(f"  - {col[0]} ({col[1]})")
                    
                    # Check for legacy_id
                    has_legacy = any(c[0] == 'legacy_id' for c in cols)
                    print(f"  Has legacy_id: {has_legacy}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_final_state()
