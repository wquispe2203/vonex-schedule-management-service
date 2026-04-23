import psycopg
from app.database import SQLALCHEMY_DATABASE_URL

def check_teachers():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'teachers'")
                cols = [r[0] for r in cur.fetchall()]
                print(f"Columns in teachers: {cols}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_teachers()
