"""
Migración manual v2 — Módulo DOCENTES
Ejecutar UNA SOLA VEZ: python migrate_teachers_v2.py

Añade columnas de trazabilidad a 'teachers_sinasignar'.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

STMTS = [
    "ALTER TABLE teachers_sinasignar ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'xml';",
    "ALTER TABLE teachers_sinasignar ADD COLUMN IF NOT EXISTS times_detected INTEGER DEFAULT 1;",
    "ALTER TABLE teachers_sinasignar ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ DEFAULT NOW();",
    # Índice para ordenamiento por frecuencia
    "CREATE INDEX IF NOT EXISTS idx_sinasignar_times ON teachers_sinasignar (times_detected DESC);",
]

if __name__ == "__main__":
    with engine.connect() as conn:
        print(">>> Migrando tabla 'teachers_sinasignar'...")
        for stmt in STMTS:
            conn.execute(text(stmt.strip()))
            print(f"  OK: {stmt.strip()[:80]}...")
        conn.commit()
        print("\n✅ Migración v2 completada.")
