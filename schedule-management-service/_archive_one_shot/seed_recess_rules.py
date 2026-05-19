from app.core.database import engine, SessionLocal
from sqlalchemy import text
from app.models.infrastructure import RecessRule

def seed():
    print("--- Starting Recess Engine Seeding ---")
    with engine.connect() as conn:
        conn.execute(text('ALTER TABLE recess_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();'))
        conn.commit()
    
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(RecessRule).count() > 0:
            print("[RECESS ENGINE SEED] Table already has data. Skipping.")
            return
            
        rules = [
            RecessRule(name="RECESO 1", start_time="09:40:00", end_time="10:00:00", deduction_value=33),
            RecessRule(name="RECESO 2", start_time="10:30:00", end_time="10:50:00", deduction_value=33),
            RecessRule(name="RECESO 3", start_time="11:20:00", end_time="11:40:00", deduction_value=33),
        ]
        db.add_all(rules)
        db.commit()
        print("[RECESS RULES LOADED] Initial parity seed successful.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
