-- MASTER SCHEMA CORRECTION SCRIPT
-- Objective: Standardize legacy fields to legacy_* naming convention
-- Scope: lessons and observations tables

BEGIN;

-- 1. Table: lessons
DO $$ 
BEGIN
    -- Rename old_system_subject_id -> legacy_subject_id
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lessons' AND column_name='old_system_subject_id') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lessons' AND column_name='legacy_subject_id') THEN
            ALTER TABLE lessons RENAME COLUMN old_system_subject_id TO legacy_subject_id;
        ELSE
            UPDATE lessons SET legacy_subject_id = old_system_subject_id WHERE legacy_subject_id IS NULL;
            ALTER TABLE lessons DROP COLUMN old_system_subject_id;
        END IF;
    END IF;

    -- Rename old_system_teacher_id -> legacy_teacher_id
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lessons' AND column_name='old_system_teacher_id') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lessons' AND column_name='legacy_teacher_id') THEN
            ALTER TABLE lessons RENAME COLUMN old_system_teacher_id TO legacy_teacher_id;
        ELSE
            UPDATE lessons SET legacy_teacher_id = old_system_teacher_id WHERE legacy_teacher_id IS NULL;
            ALTER TABLE lessons DROP COLUMN old_system_teacher_id;
        END IF;
    END IF;

    -- Rename old_system_class_id -> legacy_class_id
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lessons' AND column_name='old_system_class_id') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lessons' AND column_name='legacy_class_id') THEN
            ALTER TABLE lessons RENAME COLUMN old_system_class_id TO legacy_class_id;
        ELSE
            UPDATE lessons SET legacy_class_id = old_system_class_id WHERE legacy_class_id IS NULL;
            ALTER TABLE lessons DROP COLUMN old_system_class_id;
        END IF;
    END IF;
END $$;

-- 2. Table: observations
DO $$ 
BEGIN
    -- Rename old_system_session_id -> legacy_session_id
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='observations' AND column_name='old_system_session_id') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='observations' AND column_name='legacy_session_id') THEN
            ALTER TABLE observations RENAME COLUMN old_system_session_id TO legacy_session_id;
        ELSE
            UPDATE observations SET legacy_session_id = old_system_session_id WHERE legacy_session_id IS NULL;
            ALTER TABLE observations DROP COLUMN old_system_session_id;
        END IF;
    END IF;

    -- Rename old_system_teacher_id -> legacy_teacher_id
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='observations' AND column_name='old_system_teacher_id') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='observations' AND column_name='legacy_teacher_id') THEN
            ALTER TABLE observations RENAME COLUMN old_system_teacher_id TO legacy_teacher_id;
        ELSE
            UPDATE observations SET legacy_teacher_id = old_system_teacher_id WHERE legacy_teacher_id IS NULL;
            ALTER TABLE observations DROP COLUMN old_system_teacher_id;
        END IF;
    END IF;
END $$;

-- 3. Rename Indexes (Generic Pattern)
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT indexname FROM pg_indexes WHERE indexname LIKE '%old_system%') LOOP
        EXECUTE 'ALTER INDEX ' || quote_ident(r.indexname) || ' RENAME TO ' || quote_ident(replace(r.indexname, 'old_system', 'legacy'));
    END LOOP;
END $$;

COMMIT;
