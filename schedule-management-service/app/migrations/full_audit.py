import psycopg
from app.database import SQLALCHEMY_DATABASE_URL

def audit_schema():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                # 1. Obtener todas las tablas
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [r[0] for r in cur.fetchall()]
                
                print(f"--- DATABASE AUDIT ---")
                for table in tables:
                    print(f"\nTABLE: {table}")
                    
                    # 2. Obtener columnas
                    cur.execute(f"""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}'
                    """)
                    for col in cur.fetchall():
                        print(f"  - {col[0]} ({col[1]})")
                        
                    # 3. Obtener Foreign Keys
                    cur.execute(f"""
                        SELECT
                            tc.constraint_name, 
                            kcu.column_name, 
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name 
                        FROM 
                            information_schema.table_constraints AS tc 
                            JOIN information_schema.key_column_usage AS kcu
                              ON tc.constraint_name = kcu.constraint_name
                              AND tc.table_schema = kcu.table_schema
                            JOIN information_schema.constraint_column_usage AS ccu
                              ON ccu.constraint_name = tc.constraint_name
                              AND ccu.table_schema = tc.table_schema
                        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='{table}';
                    """)
                    for fk in cur.fetchall():
                        print(f"  FK: {fk[0]} ({fk[1]} -> {fk[2]}.{fk[3]})")

    except Exception as e:
        print(f"Error auditing schema: {e}")

if __name__ == "__main__":
    audit_schema()
