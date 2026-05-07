from app.core.database import engine
from sqlalchemy import text

def create_table_safely():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS teacher_name_overrides (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                xml_name_raw VARCHAR(255) NOT NULL,
                xml_name_normalized VARCHAR(400) NOT NULL,
                teacher_id UUID NOT NULL,
                xml_upload_id UUID,
                confidence NUMERIC(5, 2) DEFAULT 1.0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_override_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                CONSTRAINT fk_override_upload FOREIGN KEY (xml_upload_id) REFERENCES xml_uploads(id) ON DELETE CASCADE
            );
        """))
        
        # Scoped overrides unique index
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_override_scoped
            ON teacher_name_overrides (xml_name_normalized, xml_upload_id)
            WHERE xml_upload_id IS NOT NULL;
        """))

        # Global overrides unique index
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_override_global
            ON teacher_name_overrides (xml_name_normalized)
            WHERE xml_upload_id IS NULL;
        """))
        
    print("Table and indexes created successfully.")

if __name__ == "__main__":
    create_table_safely()
