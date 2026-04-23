-- SCRIPT DE UNIVERSALIZACIÓN UUID (FASE 1)
-- Objetivo: Asegurar que todas las tablas tengan identidad UUID y referencias sincronizadas.

DO $$
BEGIN
    -- 1. Añadir UID a tablas que no lo tienen
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='xml_uploads' AND column_name='uid') THEN
        ALTER TABLE xml_uploads ADD COLUMN uid UUID DEFAULT gen_random_uuid();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subjects' AND column_name='uid') THEN
        ALTER TABLE subjects ADD COLUMN uid UUID DEFAULT gen_random_uuid();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='classes' AND column_name='uid') THEN
        ALTER TABLE classes ADD COLUMN uid UUID DEFAULT gen_random_uuid();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='schedule_sessions' AND column_name='uid') THEN
        ALTER TABLE schedule_sessions ADD COLUMN uid UUID DEFAULT gen_random_uuid();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='buildings' AND column_name='uid') THEN
        ALTER TABLE buildings ADD COLUMN uid UUID DEFAULT gen_random_uuid();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cards' AND column_name='uid') THEN
        ALTER TABLE cards ADD COLUMN uid UUID DEFAULT gen_random_uuid();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='rpt_planilla' AND column_name='uid') THEN
        ALTER TABLE rpt_planilla ADD COLUMN uid UUID DEFAULT gen_random_uuid();
    END IF;

    -- 2. Asegurar Columnas de Referencia (*_uid)
    -- lessons -> teacher_uid (Ya existe en models.py, asegurar en DB)
    -- lessons -> subject_uid, class_uid
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lessons' AND column_name='subject_uid') THEN
        ALTER TABLE lessons ADD COLUMN subject_uid UUID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='lessons' AND column_name='class_uid') THEN
        ALTER TABLE lessons ADD COLUMN class_uid UUID;
    END IF;

    -- schedule_sessions -> lesson_uid
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='schedule_sessions' AND column_name='lesson_uid') THEN
        ALTER TABLE schedule_sessions ADD COLUMN lesson_uid UUID;
    END IF;

    -- observations -> session_uid (Ya existe), teacher_uid (Ya existe), user_uid (Ya existe)
    -- Pero aseguramos que existan en la DB física
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='observations' AND column_name='session_uid') THEN
        ALTER TABLE observations ADD COLUMN session_uid UUID;
    END IF;

    -- 3. Sincronizar Mapeos (Legacy ID -> UUID)
    UPDATE lessons l SET subject_uid = s.uid FROM subjects s WHERE l.subject_id = s.id;
    UPDATE lessons l SET teacher_uid = t.uid FROM teachers t WHERE l.teacher_id = t.id;
    UPDATE lessons l SET class_uid = c.uid FROM classes c WHERE l.class_id = c.id;

    UPDATE schedule_sessions s SET lesson_uid = l.uid FROM lessons l WHERE s.lesson_id = l.id;

    UPDATE observations o SET session_uid = s.uid FROM schedule_sessions s WHERE o.session_id = s.id;
    UPDATE observations o SET teacher_uid = t.uid FROM teachers t WHERE o.teacher_id = t.id;
    UPDATE observations o SET user_uid = u.uid FROM users u WHERE o.user_id = u.id;
    UPDATE observations o SET replacement_teacher_uid = t.uid FROM teachers t WHERE o.replacement_teacher_id = t.id;

    -- 4. Marcar Columnas como NOT NULL (donde aplique)
    ALTER TABLE teachers ALTER COLUMN uid SET NOT NULL;
    ALTER TABLE users ALTER COLUMN uid SET NOT NULL;
    ALTER TABLE lessons ALTER COLUMN uid SET NOT NULL;
    ALTER TABLE observations ALTER COLUMN uid SET NOT NULL;
    ALTER TABLE schedule_sessions ALTER COLUMN uid SET NOT NULL;

END $$;
