import os
import sys

# Forzar el modo TESTING antes de importar nada de la app
os.environ["TESTING"] = "True"

# Asegurar que el modulo app sea visible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL, engine, SessionLocal
from app.models import Base, User, Role, Permission, Teacher, BreakConfig, LunchConfig
from app.core.security import get_password_hash

def ensure_database_exists():
    """Crea la base de datos de pruebas si no existe"""
    try:
        if "schedule_test_db" in SQLALCHEMY_DATABASE_URL:
            admin_url = SQLALCHEMY_DATABASE_URL.replace("schedule_test_db", "postgres")
        else:
            admin_url = SQLALCHEMY_DATABASE_URL
            
        temp_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        
        with temp_engine.connect() as conn:
            # Revisa si la bd de test existe
            exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname='schedule_test_db'")).scalar()
            if not exists:
                print("CREATING DATABASE 'schedule_test_db'...")
                conn.execute(text("CREATE DATABASE schedule_test_db"))
            else:
                print("DATABASE 'schedule_test_db' ALREADY EXISTS.")
        temp_engine.dispose()
    except Exception as e:
        print(f"WARNING: error while checking DB: {e}")
        print("Continuing (assuming DB exists)...")

def run_seed():
    print(f"--- STARTING DETERMINISTIC SEED (TESTING) ---")
    print(f"DEBUG: SQLALCHEMY_DATABASE_URL = {SQLALCHEMY_DATABASE_URL}")
    
    if "schedule_test_db" not in SQLALCHEMY_DATABASE_URL:
        print("ERROR: Database URL is not TESTING. ABORTING.")
        return

    # 1. Reset Total
    print("CLEANING SCHEMA (DROP ALL)...")
    Base.metadata.drop_all(bind=engine)
    print("RECREATING SCHEMA (CREATE ALL)...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. Seed Permissions
        print("SEEDING: Permissions...")
        perms_data = [
            {"code": "ver_rpt", "desc": "Ver reporte de planillas"},
            {"code": "ver_horarios", "desc": "Ver visor de horarios"},
            {"code": "subir_xml", "desc": "Cargar archivos XML"},
            {"code": "gestionar_usuarios", "desc": "Administrar usuarios"},
            {"code": "gestionar_configuracion", "desc": "Admin configuracion"},
            {"code": "ver_observaciones", "desc": "Ver observaciones"},
            {"code": "crear_observaciones", "desc": "Crear observaciones"}
        ]
        permissions = {}
        for p in perms_data:
            perm = Permission(code=p["code"], description=p["desc"])
            db.add(perm)
            permissions[p["code"]] = perm
        
        # 3. Seed Roles
        print("SEEDING: Roles...")
        role_sistemas = Role(name="SISTEMAS")
        role_admin = Role(name="ADMIN")
        role_docente = Role(name="DOCENTE")
        
        db.add_all([role_sistemas, role_admin, role_docente])
        db.flush()
        
        # Asignar todos los permisos a SISTEMAS
        role_sistemas.permissions = list(permissions.values())
        
        # 4. Seed User (ADMIN TEST)
        print("SEEDING: Admin User (admin_test@vonex.edu.pe)...")
        admin_test = User(
            username="admin_test@vonex.edu.pe",
            password_hash=get_password_hash("TestAdmin123!"),
            nombres="Admin",
            apellidos="Test",
            is_active=True
        )
        admin_test.roles.append(role_sistemas)
        db.add(admin_test)
        
        # 5. Seed Business Data
        print("SEEDING: Master Data...")
        teacher = Teacher(
            first_name="Docente",
            last_name="Prueba",
            source_id="TEST-T-001"
        )
        db.add(teacher)
        
        receso = BreakConfig(description="Receso Manana", start_time="10:00:00", end_time="10:20:00")
        almuerzo = LunchConfig(description="Almuerzo General", start_time="13:00:00", end_time="14:00:00")
        db.add_all([receso, almuerzo])
        
        db.commit()
        print("--- SEED COMPLETE ---")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: Seed failed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    ensure_database_exists()
    run_seed()
