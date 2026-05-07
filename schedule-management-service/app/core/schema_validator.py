from sqlalchemy import inspect
from app.core.config import settings
from app.models import Base
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)

def validate_db_schema():
    """
    Validates that the database schema matches the SQLAlchemy models.
    Runs on application startup.
    """
    logger.info("Starting schema validation...")
    try:
        engine = create_engine(settings.database_url)
        inspector = inspect(engine)
        
        db_tables = inspector.get_table_names()
        model_tables = Base.metadata.tables.keys()
        
        missing_tables = set(model_tables) - set(db_tables)
        if missing_tables:
            logger.error(f"CRITICAL: Missing tables in database: {missing_tables}")
            return False
            
        for table_name in model_tables:
            model_table = Base.metadata.tables[table_name]
            db_cols = {c['name']: c for c in inspector.get_columns(table_name)}
            
            for col in model_table.columns:
                if col.name not in db_cols:
                    logger.error(f"CRITICAL: Table '{table_name}' is missing column '{col.name}'")
                    return False
        
        logger.info("Schema validation successful: 100% parity.")
        return True
    except Exception as e:
        logger.error(f"Failed to perform schema validation: {e}")
        return False
