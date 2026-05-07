from sqlalchemy import text
from app.database import engine

def alter_tables():
    with engine.connect() as conn:
        print("Altering rpt_planilla...")
        conn.execute(text("ALTER TABLE rpt_planilla ALTER COLUMN ciclo TYPE VARCHAR(500);"))
        print("Altering rpt_planilla_logs...")
        conn.execute(text("ALTER TABLE rpt_planilla_logs ALTER COLUMN ciclo TYPE VARCHAR(500);"))
        print("Adding receso to rpt_planilla...")
        conn.execute(text("ALTER TABLE rpt_planilla ADD COLUMN IF NOT EXISTS receso VARCHAR(50);"))
        print("Adding receso to rpt_planilla_logs...")
        conn.execute(text("ALTER TABLE rpt_planilla_logs ADD COLUMN IF NOT EXISTS receso VARCHAR(50);"))
        conn.commit()
    print("Columns updated successfully.")

if __name__ == "__main__":
    alter_tables()
