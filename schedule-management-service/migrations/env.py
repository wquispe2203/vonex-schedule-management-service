from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Importar la configuración y la Base del proyecto
from app.core.config import settings
from app.models import Base
import app.models

# Configuración del logger de Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de los modelos para autogenerate
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Ejecutar migraciones en modo 'offline'."""
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Ejecutar migraciones en modo 'online'."""
    # Sobrescribir la URL de sqlalchemy.url con la de settings
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.database_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    def validate_migration_directives(context, revision, directives):
        """Guardrail to prevent non-standard naming in new migrations."""
        if not getattr(context.config.cmd_opts, 'autogenerate', False):
            return

        for directive in directives:
            # Check for Table and Column renames/adds
            for op_obj in directive.upgrade_ops.ops:
                # Basic check for legacy naming convention
                if hasattr(op_obj, 'column_name'):
                    col_name = op_obj.column_name
                    if 'old_system_' in col_name:
                        raise ValueError(f"NON-STANDARD NAMING: Column '{col_name}' uses legacy 'old_system_' prefix. Use 'legacy_' instead.")
                
                # Check for table renames or additions if they exist
                if hasattr(op_obj, 'table_name'):
                    # Prevent specific legacy patterns if necessary
                    pass

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            process_revision_directives=validate_migration_directives
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
