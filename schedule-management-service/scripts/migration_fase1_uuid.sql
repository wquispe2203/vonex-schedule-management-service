-- =============================================================================
-- MIGRACIÓN UUID FASE 1: COEXISTENCIA Y VALIDACIÓN RIGUROSA (v1.1)
-- =============================================================================
-- REGLAS ACTUALIZADAS:
-- 1. Unificación sin filtrado: Se insertan duplicados marcados como possible_duplicate.
-- 2. Validación crítica: RAISE EXCEPTION detiene la migración ante errores.
-- =============================================================================

BEGIN;

-- 1. Habilitar extensión para generación de UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- PASO 1: ADICIÓN DE COLUMNAS
-- -----------------------------------------------------------------------------
DO $$ 
BEGIN 
    -- Maestras
    ALTER TABLE users ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE roles ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE permissions ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE teachers ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE teachers ADD COLUMN IF NOT EXISTS possible_duplicate BOOLEAN DEFAULT FALSE;
    ALTER TABLE teachers ADD COLUMN IF NOT EXISTS is_assigned BOOLEAN DEFAULT TRUE;
    ALTER TABLE teachers ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual';
    ALTER TABLE teachers ADD COLUMN IF NOT EXISTS times_detected INTEGER DEFAULT 1;
    ALTER TABLE teachers ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ DEFAULT now();
    -- Permitir source_id nulo para registros unificados/manuales
    ALTER TABLE teachers ALTER COLUMN source_id DROP NOT NULL;
    ALTER TABLE subjects ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE grades ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE classes ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE buildings ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE lessons ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE cards ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE schedule_sessions ADD COLUMN IF NOT EXISTS uid UUID;
    ALTER TABLE observations ADD COLUMN IF NOT EXISTS uid UUID;

    -- FKs Paralelas
    ALTER TABLE user_roles ADD COLUMN IF NOT EXISTS user_uid UUID;
    ALTER TABLE user_roles ADD COLUMN IF NOT EXISTS role_uid UUID;
    ALTER TABLE role_permissions ADD COLUMN IF NOT EXISTS role_uid UUID;
    ALTER TABLE role_permissions ADD COLUMN IF NOT EXISTS permission_uid UUID;
    ALTER TABLE classes ADD COLUMN IF NOT EXISTS grade_uid UUID;
    ALTER TABLE lessons ADD COLUMN IF NOT EXISTS subject_uid UUID;
    ALTER TABLE lessons ADD COLUMN IF NOT EXISTS teacher_uid UUID;
    ALTER TABLE lessons ADD COLUMN IF NOT EXISTS class_uid UUID;
    ALTER TABLE cards ADD COLUMN IF NOT EXISTS lesson_uid UUID;
    ALTER TABLE schedule_sessions ADD COLUMN IF NOT EXISTS lesson_uid UUID;
    ALTER TABLE observations ADD COLUMN IF NOT EXISTS session_uid UUID;
    ALTER TABLE observations ADD COLUMN IF NOT EXISTS teacher_uid UUID;
    ALTER TABLE observations ADD COLUMN IF NOT EXISTS user_uid UUID;
    ALTER TABLE observations ADD COLUMN IF NOT EXISTS replacement_teacher_uid UUID;
END $$;

-- -----------------------------------------------------------------------------
-- PASO 2: POBLACIÓN DE DATOS
-- -----------------------------------------------------------------------------

UPDATE users SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE roles SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE permissions SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE teachers SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE subjects SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE grades SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE classes SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE buildings SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE lessons SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE cards SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE schedule_sessions SET uid = gen_random_uuid() WHERE uid IS NULL;
UPDATE observations SET uid = gen_random_uuid() WHERE uid IS NULL;

-- Mapear FKs paralelas
UPDATE user_roles ur SET user_uid = u.uid FROM users u WHERE ur.user_id = u.id;
UPDATE user_roles ur SET role_uid = r.uid FROM roles r WHERE ur.role_id = r.id;
UPDATE role_permissions rp SET role_uid = r.uid FROM roles r WHERE rp.role_id = r.id;
UPDATE role_permissions rp SET permission_uid = p.uid FROM permissions p WHERE rp.permission_id = p.id;
UPDATE classes c SET grade_uid = g.uid FROM grades g WHERE c.grade_id = g.id;
UPDATE lessons l SET subject_uid = s.uid FROM subjects s WHERE l.subject_id = s.id;
UPDATE lessons l SET teacher_uid = t.uid FROM teachers t WHERE l.teacher_id = t.id;
UPDATE lessons l SET class_uid = c.uid FROM classes c WHERE l.class_id = c.id;
UPDATE cards c SET lesson_uid = l.uid FROM lessons l WHERE c.lesson_id = l.id;
UPDATE schedule_sessions ss SET lesson_uid = l.uid FROM lessons l WHERE ss.lesson_id = l.id;
UPDATE observations o SET session_uid = ss.uid FROM schedule_sessions ss WHERE o.session_id = ss.id;
UPDATE observations o SET teacher_uid = t.uid FROM teachers t WHERE o.teacher_id = t.id;
UPDATE observations o SET user_uid = u.uid FROM users u WHERE o.user_id = u.id;
UPDATE observations o SET replacement_teacher_uid = t.uid FROM teachers t WHERE o.replacement_teacher_id = t.id;

-- -----------------------------------------------------------------------------
-- PASO 3: RESTRICCIONES (NOT NULL + UNIQUE)
-- -----------------------------------------------------------------------------

ALTER TABLE users ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_users_uid UNIQUE (uid);
ALTER TABLE roles ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_roles_uid UNIQUE (uid);
ALTER TABLE permissions ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_permissions_uid UNIQUE (uid);
ALTER TABLE teachers ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_teachers_uid UNIQUE (uid);
ALTER TABLE subjects ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_subjects_uid UNIQUE (uid);
ALTER TABLE grades ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_grades_uid UNIQUE (uid);
ALTER TABLE classes ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_classes_uid UNIQUE (uid);
ALTER TABLE buildings ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_buildings_uid UNIQUE (uid);
ALTER TABLE lessons ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_lessons_uid UNIQUE (uid);
ALTER TABLE cards ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_cards_uid UNIQUE (uid);
ALTER TABLE schedule_sessions ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_sessions_uid UNIQUE (uid);
ALTER TABLE observations ALTER COLUMN uid SET NOT NULL, ADD CONSTRAINT uq_observations_uid UNIQUE (uid);

-- -----------------------------------------------------------------------------
-- PASO 4: CONSOLIDACIÓN CON MARCADO DE DUPLICADOS
-- -----------------------------------------------------------------------------

-- Migrar TODOS los registros de sinasignar
INSERT INTO teachers (
    uid, first_name, last_name, dni, razon_social, normalized_name, 
    is_assigned, source, times_detected, last_seen_at, possible_duplicate
)
SELECT 
    gen_random_uuid(), 
    sa.nombres, 
    sa.apellidos, 
    sa.dni, 
    sa.razon_social, 
    sa.normalized_name, 
    false, 
    'xml_unassigned', 
    sa.times_detected, 
    sa.last_seen_at,
    EXISTS (SELECT 1 FROM teachers t WHERE t.normalized_name = sa.normalized_name) -- Marcado si ya existe el nombre
FROM teachers_sinasignar sa;

-- -----------------------------------------------------------------------------
-- PASO 5: VALIDACIÓN CRÍTICA (RAISE EXCEPTION SI HAY NULOS)
-- -----------------------------------------------------------------------------

DO $$ 
DECLARE 
    null_count INTEGER;
BEGIN 
    -- Validación Lecciones
    SELECT count(*) INTO null_count FROM lessons WHERE teacher_uid IS NULL AND teacher_id IS NOT NULL;
    IF null_count > 0 THEN RAISE EXCEPTION '❌ MIGRACIÓN ABORTADA: % lecciones tienen teacher_uid NULL', null_count; END IF;

    -- Validación Observaciones
    SELECT count(*) INTO null_count FROM observations WHERE replacement_teacher_uid IS NULL AND replacement_teacher_id IS NOT NULL;
    IF null_count > 0 THEN RAISE EXCEPTION '❌ MIGRACIÓN ABORTADA: % observaciones tienen replacement_teacher_uid NULL', null_count; END IF;

    -- Validación Usuarios
    SELECT count(*) INTO null_count FROM observations WHERE user_uid IS NULL AND user_id IS NOT NULL;
    IF null_count > 0 THEN RAISE EXCEPTION '❌ MIGRACIÓN ABORTADA: % observaciones tienen user_uid NULL', null_count; END IF;

    RAISE NOTICE '✅ Integridad validada satisfactoriamente.';
END $$;

COMMIT;
