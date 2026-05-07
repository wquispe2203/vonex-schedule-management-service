import sys
import psycopg

try:
    conn = psycopg.connect("postgresql://postgres:C%40rden4s2k24@localhost/schedule_db")
    print("SUCCESS: Conexion establecida con schedule_db usando psycopg.")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
