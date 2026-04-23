import sqlite3
import os

db_path = r"d:\Desktop\MOD HOR\schedule-management-service\app.db"
if not os.path.exists(db_path):
    print("Database not found")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT last_name, first_name, COUNT(*) as c FROM teachers GROUP BY last_name, first_name HAVING c > 1;")
    rows = cur.fetchall()
    if rows:
        print("Duplicates found:")
        for r in rows:
            print(f"{r[0]}, {r[1]} - Count: {r[2]}")
    else:
        print("No exact duplicates found")
    conn.close()
