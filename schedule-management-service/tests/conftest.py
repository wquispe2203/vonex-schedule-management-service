import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# 1. Forzar entorno de pruebas antes de importar la app
os.environ["TESTING"] = "True"

from app.main import create_app
from app.core.database import get_db, Base
from app.core.config import settings

# Usar la lógica de settings que ya maneja TESTING=True
TEST_DATABASE_URL = settings.database_url

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """
    Crea las tablas una sola vez por sesión de pruebas.
    """
    Base.metadata.create_all(bind=engine)
    yield
    # No borramos las tablas al final para permitir inspección si falla, 
    # pero cada test limpiará sus datos vía rollback.
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    """
    Provee una sesión de base de datos con rollback automático.
    Cada test corre en su propia transacción.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    """
    Provee un TestClient con la base de datos de pruebas inyectada.
    """
    app = create_app()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_auth(client):
    """
    Permite inyectar un usuario simulado para saltar la seguridad en los tests.
    """
    from app.dependencies.auth import get_current_active_user, require_permission
    
    class MockUser:
        def __init__(self, id=None, username="admin@vonex.edu.pe", roles=[]):
            import uuid
            self.id = id or uuid.uuid4()
            self.username = username
            self.roles = roles
            self.is_active = True

    def _setup_auth(user=None, permissions=[]):
        from app.models.user import User, Role
        if user is None:
             # Create a real SUPERADMIN user to bypass granular permission checks easily
             user = User(
                 username="admin@vonex.edu.pe",
                 password_hash="...",
                 is_active=True
             )
             db_gen = client.app.dependency_overrides[get_db]()
             test_db_session = next(db_gen)
             
             super_role = test_db_session.query(Role).filter_by(name="SUPERADMIN").first()
             if not super_role:
                 super_role = Role(name="SUPERADMIN", is_protected=True)
                 test_db_session.add(super_role)
             
             user.roles.append(super_role)
             test_db_session.add(user)
             test_db_session.commit()
             test_db_session.refresh(user)
        
        client.app.dependency_overrides[get_current_active_user] = lambda: user
             
    return _setup_auth
