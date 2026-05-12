import sqlite3
import os

db_path = 'app.db'
if not os.path.exists(db_path):
    db_path = 'database.db'

print(f"Inspecting DB file: {db_path}")
if not os.path.exists(db_path):
    print("DB File not found!")
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    tables = ['xml_uploads', 'schedule_sessions', 'rpt_planilla', 'teachers', 'users', 'roles']
    for table in tables:
        try:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            count = c.fetchone()[0]
            print(f"Table {table}: {count} records")
        except Exception as e:
            print(f"Table {table} access error: {e}")
            
    try:
        c.execute("SELECT id, filename, start_date, end_date FROM xml_uploads ORDER BY created_at DESC LIMIT 3")
        rows = c.fetchall()
        print("\nLatest XML Uploads:")
        for r in rows:
            print(r)
    except Exception as e:
        print(f"Could not get XML Uploads details: {e}")
        
    try:
        c.execute("SELECT id, name, short_name FROM teachers LIMIT 5")
        rows = c.fetchall()
        print("\nSample Teachers:")
        for r in rows:
            print(r)
    except Exception as e:
        print(f"Could not get teachers details: {e}")

    conn.close()
