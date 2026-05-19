-- Production Schema Fix: Phase 4 Academic Consolidation
-- Simplified Version: Direct Idempotent Statements
-- Safe to run multiple times.

-- 1. TEACHERS TABLE
ALTER TABLE teachers ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVO';
ALTER TABLE teachers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
CREATE INDEX IF NOT EXISTS ix_teachers_status ON teachers (status);

-- 2. RPT_PLANILLA TABLE
ALTER TABLE rpt_planilla ADD COLUMN IF NOT EXISTS hora_inicio TIME;
ALTER TABLE rpt_planilla ADD COLUMN IF NOT EXISTS sede VARCHAR(255);
ALTER TABLE rpt_planilla ADD COLUMN IF NOT EXISTS ciclo VARCHAR(255);
ALTER TABLE rpt_planilla ADD COLUMN IF NOT EXISTS curso VARCHAR(255);

-- 3. UNIQUE CONSTRAINTS
-- We create them as indexes if they don't exist to avoid naming conflicts with constraints
CREATE UNIQUE INDEX IF NOT EXISTS uq_rpt_planilla_unique ON rpt_planilla (fecha_clase, docente, hora_inicio);
CREATE UNIQUE INDEX IF NOT EXISTS uq_session_lesson_time ON schedule_sessions (lesson_id, session_date, start_time);

-- 4. ALIGN ALEMBIC VERSION
-- Ensure it stays at the latest known working version
UPDATE alembic_version SET version_num = '992c6ae1636a' WHERE version_num IS NOT NULL;
