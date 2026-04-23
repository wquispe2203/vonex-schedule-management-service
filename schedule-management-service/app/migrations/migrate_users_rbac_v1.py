import sys
import os
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

# Añadir ruta para importar correctamente config y modelos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.database import SessionLocal, engine
from app.models import Base

def migrate():
    # 1. Ejecutar ALTER TABLE directamente sobre users usando SQL nativo.
    with engine.begin() as conn:
        print("[1/3] Añadiendo columnas y actualizando tabla 'users'...")
        try:
            # Ampliar campo username
            conn.execute(text("ALTER TABLE users ALTER COLUMN username TYPE VARCHAR(255);"))
        except Exception as e:
            print(f"Update warning (username TYPE): {e}")

        try:
            # Hacer password_hash nullable temporalmente o para soporte
            conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;"))
        except Exception as e:
            print(f"Update warning (password_hash DROP NOT NULL): {e}")

        try:
            # Añadir nuevos campos de la fase 1 (RBAC y Profile)
            conn.execute(text("ALTER TABLE users ADD COLUMN nombres VARCHAR(100);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN apellidos VARCHAR(100);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN area VARCHAR(100);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now());"))
            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;"))
            
            # Crear índice en is_active
            conn.execute(text("CREATE INDEX ix_users_is_active ON users (is_active);"))
            
            print("Columnas y configuraciones añadidas correctamente.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicada" in str(e).lower():
                print("Columnas de users ya existen, procediendo...")
            else:
                print(f"SQL Error adaptando columns de users: {e}")

    # 2. Crear las nuevas tablas a través de Base.metadata.create_all
    # Esto creará roles, permissions, user_roles y role_permissions si no existen.
    print("[2/3] Creando tablas RBAC si no existen...")
    Base.metadata.create_all(bind=engine)
    print("Tablas RBAC generadas.")

    # 3. Datos: Sincronizar roles heredados
    print("[3/3] Migrando roles legacy...")
    db: Session = SessionLocal()
    try:
        # Obtener todos los usuarios de la base de datos
        from app.models import User, Role, user_roles
        users_in_db = db.query(User).all()

        if not users_in_db:
            print("No hay usuarios para migrar.")
        else:
            print(f"Encontrados {len(users_in_db)} usuarios.")
            role_cache = {}

            for u in users_in_db:
                # Normalizar el string role (legacy) a nuestro nuevo mapping estándar
                legacy_role = (u.role or "sistemas").strip().lower()

                # Mapa explícito sugerido para roles estandarizados del negocio si corresponde
                if legacy_role in ["admin", "administrator", "superadmin"]:
                    mapped_role_name = "SUPERADMIN"
                elif legacy_role in ["sistemas", "sys"]:
                    mapped_role_name = "SISTEMAS"
                elif legacy_role in ["dirección", "direccion_academica"]:
                    mapped_role_name = "DIRECCION_ACADEMICA"
                elif legacy_role in ["gth", "rrhh"]:
                    mapped_role_name = "GTH"
                else:
                    # En caso de otro rol desconocido, crear la version UPPER(legacy)
                    mapped_role_name = legacy_role.upper()

                # Obtener de db o cache, crearlo si no existe
                if mapped_role_name not in role_cache:
                    existing_r = db.query(Role).filter(Role.name == mapped_role_name).first()
                    if not existing_r:
                        existing_r = Role(name=mapped_role_name)
                        db.add(existing_r)
                        db.commit() # Flush para tener el id
                        db.refresh(existing_r)
                    role_cache[mapped_role_name] = existing_r

                target_role = role_cache[mapped_role_name]

                # Vincular en tabla intermedia si no lo está (evitar dupes directos)
                # Verificamos cruzando manual
                existing_link = db.execute(
                    user_roles.select().where(
                        (user_roles.c.user_id == u.id) & 
                        (user_roles.c.role_id == target_role.id)
                    )
                ).first()

                if not existing_link:
                    db.execute(user_roles.insert().values(user_id=u.id, role_id=target_role.id))
                    print(f"  -> Migrado usuario '{u.username}' al rol {mapped_role_name}")
                
            db.commit()
            print("Migración legacy completada con éxito.")

    except Exception as e:
        db.rollback()
        print(f"Error procesando migración de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Iniciando migración de Fase 1: Módulo RBAC...")
    migrate()
    print("=> FINALIZADO.")
