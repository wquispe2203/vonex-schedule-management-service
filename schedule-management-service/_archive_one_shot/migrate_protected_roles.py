from app.core.database import engine, SessionLocal
from sqlalchemy import text
from app.models.user import Role

def migrate():
    print("--- Starting Superadmin Migration ---")
    with engine.connect() as conn:
        conn.execute(text('ALTER TABLE roles ADD COLUMN IF NOT EXISTS is_protected BOOLEAN DEFAULT FALSE;'))
        conn.commit()
    
    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == 'SUPERADMIN').first()
        if role:
            role.is_protected = True
            db.commit()
            print('[SUPERADMIN FLAG ENABLED] Role "SUPERADMIN" migrated to structural protection.')
        else:
            print('[MIGRATION WARNING] Role "SUPERADMIN" not found in DB.')
        
        # Check SISTEMAS role too if it exists
        sistemas = db.query(Role).filter(Role.name == 'SISTEMAS').first()
        if sistemas:
            sistemas.is_protected = True
            db.commit()
            print('[SUPERADMIN FLAG ENABLED] Role "SISTEMAS" migrated to structural protection.')
            
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
