import logging
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.models import Teacher, RptPlanilla, ScheduleSession

logger = logging.getLogger("app.pipeline.preflight")

class SchemaValidator:
    REQUIRED_COLUMNS = {
        "teachers": ["status", "updated_at"],
        "rpt_planilla": ["hora_inicio", "sede", "ciclo", "curso", "xml_upload_id"],
        "schedule_sessions": ["xml_upload_id"]
    }

    REQUIRED_INDEXES = {
        "rpt_planilla": ["uq_rpt_planilla_unique"],
        "schedule_sessions": ["uq_session_lesson_time"]
    }

    @classmethod
    def validate_production_schema(cls, db: Session) -> bool:
        """
        Validates that the current database schema matches the expected structure 
        for the academic consolidation pipeline.
        """
        logger.info("[PRODUCTION SCHEMA VERIFIED] Starting pre-flight check...")
        engine = db.get_bind()
        inspector = inspect(engine)
        
        errors = []

        # 1. Check Columns
        for table, cols in cls.REQUIRED_COLUMNS.items():
            existing_cols = [c['name'] for c in inspector.get_columns(table)]
            for col in cols:
                if col not in existing_cols:
                    errors.append(f"Missing column '{col}' in table '{table}'")

        # 2. Check Indexes/Constraints
        for table, indexes in cls.REQUIRED_INDEXES.items():
            existing_indexes = [idx['name'] for idx in inspector.get_indexes(table)]
            for idx in indexes:
                if idx not in existing_indexes:
                    # In some cases it might be a constraint, check that too
                    constraints = [c['name'] for c in inspector.get_unique_constraints(table)]
                    if idx not in constraints:
                        errors.append(f"Missing unique index/constraint '{idx}' in table '{table}'")

        if errors:
            for err in errors:
                logger.error(f"[SCHEMA DRIFT DETECTED] {err}")
            logger.critical("[ACADEMIC PIPELINE BLOCKED] Schema mismatch detected. Refusing to process.")
            return False

        logger.info("[SCHEMA PREFLIGHT OK] All critical structures verified.")
        return True
