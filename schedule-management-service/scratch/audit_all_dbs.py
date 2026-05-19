import psycopg2

databases = ['postgres', 'horarios_db', 'schedule_db', 'schedule_temp_db', 'schedule_restore_tmp', 'schedule_test_db']
for dbname in databases:
    try:
        conn = psycopg2.connect(f'postgresql://postgres:C%40rden4s2k24@localhost:5432/{dbname}')
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = [t[0] for t in cur.fetchall()]
        print(f"=== DB: {dbname} ===")
        print("Tables:", tables)
        if 'xml_uploads' in tables:
            cur.execute('SELECT COUNT(*), COUNT(DISTINCT filename) FROM xml_uploads')
            print('  xml_uploads:', cur.fetchone())
            cur.execute('SELECT filename, status, created_at FROM xml_uploads')
            print('  Files:', cur.fetchall())
        if 'teachers' in tables:
            cur.execute('SELECT COUNT(*) FROM teachers')
            print('  teachers:', cur.fetchone()[0])
        if 'schedule_sessions' in tables:
            cur.execute('SELECT COUNT(*) FROM schedule_sessions')
            print('  sessions:', cur.fetchone()[0])
        conn.close()
    except Exception as e:
        print(f"Error reading {dbname}: {e}")
