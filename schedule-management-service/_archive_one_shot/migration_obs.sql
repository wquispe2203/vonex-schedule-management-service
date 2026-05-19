-- Migration: Add missing columns to observations table
-- Run as superuser (postgres) with: psql -U postgres -d schedule_db -f migration_obs.sql

DO $$
BEGIN
    -- Add replacement_teacher_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='observations' AND column_name='replacement_teacher_id'
    ) THEN
        ALTER TABLE observations ADD COLUMN replacement_teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL;
        RAISE NOTICE 'Added column: replacement_teacher_id';
    ELSE
        RAISE NOTICE 'Column replacement_teacher_id already exists';
    END IF;

    -- Add start_time if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='observations' AND column_name='start_time'
    ) THEN
        ALTER TABLE observations ADD COLUMN start_time TIME;
        RAISE NOTICE 'Added column: start_time';
    ELSE
        RAISE NOTICE 'Column start_time already exists';
    END IF;

    -- Add end_time if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='observations' AND column_name='end_time'
    ) THEN
        ALTER TABLE observations ADD COLUMN end_time TIME;
        RAISE NOTICE 'Added column: end_time';
    ELSE
        RAISE NOTICE 'Column end_time already exists';
    END IF;
END
$$;
