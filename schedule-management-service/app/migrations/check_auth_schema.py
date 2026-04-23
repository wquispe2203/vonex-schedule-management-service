import psycopg
from app.database import SQLALCHEMY_DATABASE_URL

def check_auth_schema():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                print("--- AUDITANDO TABLAS DE AUTENTICACIÓN ---")
                
                for table in ['users', 'roles', 'user_roles']:
                    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
                    cols = cur.fetchall()
                    print(f"\nTable '{table}':")
                    for c in cols:
                        print(f"  - {c[0]} ({c[1]})")
                        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_auth_schema()
