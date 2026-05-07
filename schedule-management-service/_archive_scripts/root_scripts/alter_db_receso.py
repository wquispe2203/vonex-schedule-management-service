from sqlalchemy import text
from app.database import engine

def alter_tables():
    with engine.connect() as conn:
        print("Migrating receso columns to numeric...")
        conn.execute(text("ALTER TABLE rpt_planilla DROP COLUMN IF EXISTS receso;"))
        conn.execute(text("ALTER TABLE rpt_planilla ADD COLUMN receso NUMERIC(10, 2) DEFAULT 0.00;"))
        
        conn.execute(text("ALTER TABLE rpt_planilla_logs DROP COLUMN IF EXISTS receso;"))
        conn.execute(text("ALTER TABLE rpt_planilla_logs ADD COLUMN receso NUMERIC(10, 2) DEFAULT 0.00;"))
        conn.commit()
    print("Columns updated successfully.")

if __name__ == "__main__":
    alter_tables()
