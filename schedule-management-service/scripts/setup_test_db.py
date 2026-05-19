import sqlalchemy
from sqlalchemy import create_engine, text

def setup_test_db():
    # Use the postgres database to create the test database
    base_url = "postgresql://postgres:C%40rden4s2k24@localhost:5432/postgres"
    target_db = "schedule_test_db"
    
    engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        # Terminate active connections to the test db to allow dropping
        conn.execute(text(f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{target_db}' AND pid <> pg_backend_pid();"))
        
        # Drop if exists
        print(f"Dropping database {target_db} if exists...")
        conn.execute(text(f"DROP DATABASE IF EXISTS {target_db}"))
        
        # Create
        print(f"Creating database {target_db}...")
        conn.execute(text(f"CREATE DATABASE {target_db}"))
        print("Database created successfully.")

if __name__ == "__main__":
    setup_test_db()
