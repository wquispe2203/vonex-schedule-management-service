-- Migration: Add replacement_teacher_id to observations
ALTER TABLE observations ADD COLUMN replacement_teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL;

-- Initial sync: If we have names that match exactly, we could try to populate it, 
-- but it's safer to let the user select them via the new autocomplete.
