"""
Migración manual — Módulo DOCENTES
Ejecutar UNA SOLA VEZ: python migrate_teachers.py

Añade columnas a 'teachers' y crea tabla 'teachers_sinasignar'.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

ALTER_TEACHERS = [
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS dni VARCHAR(15) NULL;",
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS razon_social VARCHAR(255) NULL;",
    "ALTER TABLE teachers ADD COLUMN IF NOT EXISTS normalized_name VARCHAR(400) NULL;",
    # Índice único parcial: solo para DNIs no nulos
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_teachers_dni
        ON teachers (dni)
        WHERE dni IS NOT NULL AND dni != '';
    """,
    "CREATE INDEX IF NOT EXISTS idx_teachers_normalized ON teachers (normalized_name);",
]

CREATE_SINASIGNAR = """
CREATE TABLE IF NOT EXISTS teachers_sinasignar (
    id            SERIAL PRIMARY KEY,
    dni           VARCHAR(15)  NULL,
    apellidos     VARCHAR(255) NOT NULL,
    nombres       VARCHAR(255) NOT NULL,
    razon_social  VARCHAR(255) NULL,
    normalized_name VARCHAR(400) NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_sinasignar_normalized UNIQUE (normalized_name)
);
CREATE INDEX IF NOT EXISTS idx_sinasignar_normalized ON teachers_sinasignar (normalized_name);
"""

if __name__ == "__main__":
    with engine.connect() as conn:
        print(">>> Modificando tabla 'teachers'...")
        for stmt in ALTER_TEACHERS:
            conn.execute(text(stmt.strip()))
            print(f"  OK: {stmt.strip()[:70]}...")

        print(">>> Creando tabla 'teachers_sinasignar'...")
        conn.execute(text(CREATE_SINASIGNAR))
        print("  OK: teachers_sinasignar creada (o ya existía)")

        conn.commit()
        print("\n✅ Migración completada exitosamente.")
