-- Migración para la tabla de observaciones
ALTER TABLE observations 
ADD COLUMN teacher_id INTEGER REFERENCES teachers(id) ON DELETE CASCADE,
ADD COLUMN type VARCHAR(50) NOT NULL DEFAULT 'FALTA',
ADD COLUMN discount_type VARCHAR(50) DEFAULT 'SIMPLE',
ADD COLUMN replacement_teacher_name VARCHAR(255);

-- Comentario para el tipo de datos
COMMENT ON COLUMN observations.type IS 'Valores: FALTA, REEMPLAZO, VACACIONES, DESCANSO_MEDICO';
COMMENT ON COLUMN observations.discount_type IS 'Valores: SIMPLE, DOBLE, TRIPLE';
