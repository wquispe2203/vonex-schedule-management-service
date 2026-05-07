import psycopg2
from datetime import time

def test_insert():
    try:
        conn = psycopg2.connect(
            dbname="schedule_db",
            user="postgres",
            password="C@rden4s2k24",
            host="localhost"
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Get a session_id to use
        cur.execute("SELECT id FROM schedule_sessions LIMIT 1;")
        res = cur.fetchone()
        if not res:
            print("No sessions found to link the test observation.")
            return
        session_id = res[0]

        print(f"Attempting to insert test observation for session_id {session_id}...")
        
        # Test columns: start_time, end_time, replacement_teacher_id
        # We use a dummy type 'TEST' to not interfere
        cur.execute("""
            INSERT INTO observations (session_id, type, start_time, end_time, replacement_teacher_id, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (session_id, 'TEST', '08:00:00', '09:00:00', None, 'Test insert'))
        
        new_id = cur.fetchone()[0]
        print(f"Test insert successful! New observation ID: {new_id}")

        # Clean up the test record
        cur.execute("DELETE FROM observations WHERE id = %s;", (new_id,))
        print("Test record cleaned up.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Test insert failed: {e}")

if __name__ == "__main__":
    test_insert()
