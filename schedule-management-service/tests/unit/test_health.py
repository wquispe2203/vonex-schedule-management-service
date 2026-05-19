import pytest
from tests.fixtures.factories import TestFactory
from app.models.teacher import Teacher

@pytest.mark.unit
def test_root_endpoint(client):
    """
    Verifica que la API esté corriendo y responda al root.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Schedule Management Service API is running"}

@pytest.mark.integration
def test_db_isolation(db):
    """
    Verifica que la base de datos de pruebas esté aislada y funcione.
    """
    teacher = TestFactory.create_teacher(db, "ISOLATION TEST")
    assert teacher.id is not None
    
    # Verificar que persiste en esta sesión
    db_teacher = db.query(Teacher).filter_by(normalized_name="ISOLATION TEST").first()
    assert db_teacher is not None

@pytest.mark.rbac
def test_rbac_dependency_exists(client):
    """
    Verifica que los endpoints protegidos existan y respondan (401 si no hay auth).
    """
    response = client.get("/api/users/me")
    assert response.status_code == 401
