import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuración - Ajustar según app/database.py
DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"

def migrate():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("🚀 Iniciando migración de datos a UUID...")

    try:
        # 1. Crear tabla temporal para mapear IDs Enteros a UUIDs
        session.execute(text("CREATE TEMP TABLE teacher_id_map (old_id INT, new_id UUID)"))

        # 2. Mapear docentes existentes (Maestra)
        teachers = session.execute(text("SELECT id FROM teachers")).fetchall()
        for t in teachers:
            new_id = uuid.uuid4()
            session.execute(
                text("INSERT INTO teacher_id_map (old_id, new_id) VALUES (:old, :new)"),
                {"old": t.id, "new": new_id}
            )

        # 3. Mapear docentes SinAsignar (pasarán a la tabla teachers)
        # Nota: Asumimos que la tabla teachers_sinasignar todavía existe
        sa_teachers = session.execute(text("SELECT id, apellidos, nombres, dni, razon_social, normalized_name, source, times_detected, last_seen_at FROM teachers_sinasignar")).fetchall()
        for sa in sa_teachers:
            new_id = uuid.uuid4()
            # Insertar en teachers directamente como is_assigned=False
            session.execute(
                text("""
                    INSERT INTO teachers (id, first_name, last_name, dni, razon_social, normalized_name, is_assigned, source, times_detected, last_seen_at, source_id)
                    VALUES (:id, :fn, :ln, :dni, :rs, :norm, false, :src, :td, :ls, :sid)
                """),
                {
                    "id": new_id,
                    "fn": sa.nombres,
                    "ln": sa.apellidos,
                    "dni": sa.dni,
                    "rs": sa.razon_social,
                    "norm": sa.normalized_name,
                    "src": sa.source,
                    "td": sa.times_detected,
                    "ls": sa.last_seen_at,
                    "sid": f"MIGRATED_SA_{sa.id}"
                }
            )
            # Guardamos el mapeo por si había referencias
            session.execute(
                text("INSERT INTO teacher_id_map (old_id, new_id) VALUES (:old, :new)"),
                {"old": sa.id, "new": new_id}
            )

        # 4. Actualizar Foreign Keys en otras tablas
        print("🔗 Actualizando Foreign Keys...")
        
        # Tabla Lessons
        session.execute(text("""
            UPDATE lessons l
            SET teacher_id = m.new_id
            FROM teacher_id_map m
            WHERE CAST(l.teacher_id AS TEXT) = CAST(m.old_id AS TEXT)
        """))

        # Tabla Observations
        session.execute(text("""
            UPDATE observations o
            SET teacher_id = m.new_id
            FROM teacher_id_map m
            WHERE CAST(o.teacher_id AS TEXT) = CAST(m.old_id AS TEXT)
        """))
        
        session.execute(text("""
            UPDATE observations o
            SET replacement_teacher_id = m.new_id
            FROM teacher_id_map m
            WHERE CAST(o.replacement_teacher_id AS TEXT) = CAST(m.old_id AS TEXT)
        """))

        print("✅ Migración completada exitosamente.")
        session.commit()

    except Exception as e:
        session.rollback()
        print(f"❌ ERROR durante la migración: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
