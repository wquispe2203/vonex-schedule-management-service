import psycopg2
import sys

def migrate():
    try:
        # DB connection details from app/database.py
        # URL: postgresql://postgres:C%40rden4s2k24@localhost/schedule_db
        conn = psycopg2.connect(
            dbname="schedule_db",
            user="postgres",
            password="C@rden4s2k24",
            host="localhost"
        )
        conn.autocommit = True
        cur = conn.cursor()

        print("Checking existing columns in 'observations' table...")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'observations';")
        existing_columns = [row[0] for row in cur.fetchall()]
        print(f"Existing columns: {existing_columns}")

        # Columns to add
        cols_to_add = [
            ("start_time", "TIME"),
            ("end_time", "TIME"),
            ("replacement_teacher_id", "INTEGER REFERENCES teachers(id) ON DELETE SET NULL")
        ]

        for col_name, col_type in cols_to_add:
            if col_name not in existing_columns:
                print(f"Adding column '{col_name}'...")
                cur.execute(f"ALTER TABLE observations ADD COLUMN {col_name} {col_type};")
                print(f"Column '{col_name}' added successfully.")
            else:
                print(f"Column '{col_name}' already exists.")

        cur.close()
        conn.close()
        print("Migration completed successfully.")

    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
