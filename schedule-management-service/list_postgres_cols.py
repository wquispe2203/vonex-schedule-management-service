from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:C%40rden4s2k24@localhost:5432/schedule_db"
engine = create_engine(db_url)

tables = ['teachers', 'xml_uploads', 'schedule_sessions', 'rpt_planilla', 'users']

with engine.connect() as conn:
    for t in tables:
        print(f"\n=== Structure of Table: {t} ===")
        try:
            # Query information_schema to get columns and types
            query = text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{t}'
                ORDER BY ordinal_position
            """)
            res = conn.execute(query)
            for row in res.fetchall():
                print(f"  Column: {row[0]:25} | Type: {row[1]:20} | Nullable: {row[2]}")
        except Exception as e:
            print(f"Error inspecting {t}: {e}")
