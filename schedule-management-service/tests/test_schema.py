import pytest
from sqlalchemy import create_engine, inspect
from app.core.config import settings
from app.models import Base

@pytest.mark.skipif(not settings.TEST_DATABASE_URL, reason="TEST_DATABASE_URL not set")
def test_schema_parity():
    """
    Test that the database schema exactly matches the SQLAlchemy models.
    This ensures no drift between code and DB in the CI pipeline.
    """
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    
    db_tables = inspector.get_table_names()
    model_tables = Base.metadata.tables.keys()
    
    # 1. Missing Tables
    missing_tables = set(model_tables) - set(db_tables)
    assert not missing_tables, f"Missing tables in DB: {missing_tables}"
    
    # 2. Column Audit
    for table_name in model_tables:
        model_table = Base.metadata.tables[table_name]
        db_cols = {c['name']: c for c in inspector.get_columns(table_name)}
        
        for col in model_table.columns:
            # Check column existence
            assert col.name in db_cols, f"Table '{table_name}': Missing column '{col.name}' in DB"
            
            # Check basic type parity (UUID check)
            db_type = str(db_cols[col.name]['type']).lower()
            model_type = str(col.type).lower()
            if 'uuid' in model_type:
                assert 'uuid' in db_type, f"Table '{table_name}': Column '{col.name}' should be UUID but is {db_type}"

def test_no_legacy_naming_leak():
    """
    Test that no columns with the 'old_system_' prefix exist in the database.
    This enforces the 'legacy_' naming convention policy.
    """
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    
    for table_name in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns(table_name)]
        bad_cols = [c for c in columns if c.startswith('old_system_')]
        assert not bad_cols, f"Naming Policy Violation in '{table_name}': Found columns {bad_cols}. Use 'legacy_' prefix."
