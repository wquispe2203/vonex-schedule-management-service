import pytest
from fastapi.testclient import TestClient

@pytest.mark.security
def test_unauthorized_access_denied(client):
    """
    SECURITY GATE: Verifica que sin autenticación el acceso sea denegado (403/401).
    """
    # Intentar subir XML sin token ni mock
    response = client.post("/api/schedule/upload", files={"file": ("test.xml", "content", "text/xml")})
    assert response.status_code in (401, 403)

    # Intentar ver RPT
    response = client.get("/api/rpt-planilla/", params={"fecha_inicio": "2026-03-02", "fecha_fin": "2026-03-02"})
    assert response.status_code in (401, 403)

@pytest.mark.security
def test_restricted_role_access_denied(client, db):
    """
    SECURITY GATE: Verifica que un rol sin permisos específicos sea denegado.
    """
    from tests.fixtures.factories import TestFactory
    # Crear un usuario con un rol sin permisos
    user, token = TestFactory.create_user_with_token(db, role_name="GUEST_ROLE")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Intentar subir XML
    response = client.post("/api/schedule/upload", 
                          files={"file": ("test.xml", "content", "text/xml")},
                          headers=headers)
    assert response.status_code == 403
    
    # Intentar ver RPT
    response = client.get("/api/rpt-planilla/", 
                         params={"fecha_inicio": "2026-03-02", "fecha_fin": "2026-03-02"},
                         headers=headers)
    assert response.status_code == 403

@pytest.mark.security
def test_bulk_delete_excel_permissions(client, db):
    """
    SECURITY GATE: Verifica que la eliminación masiva por Excel esté restringida
    estrictamente a usuarios con el rol de SUPERADMIN.
    """
    from app.models.user import User, Role, Permission
    from app.core.security import create_access_token
    
    # 1. Crear un rol COORDINADOR con permiso gestionar_docentes pero NO SUPERADMIN
    role_coord = db.query(Role).filter_by(name="COORDINADOR").first()
    if not role_coord:
        role_coord = Role(name="COORDINADOR")
        db.add(role_coord)
        db.flush()
        
    perm = db.query(Permission).filter_by(code="gestionar_docentes").first()
    if not perm:
        perm = Permission(code="gestionar_docentes", description="Gestionar Docentes")
        db.add(perm)
        db.flush()
        
    if perm not in role_coord.permissions:
        role_coord.permissions.append(perm)
        db.flush()
    
    user_coord = User(username="coordinador@vonex.edu.pe", password_hash="...", is_active=True)
    user_coord.roles.append(role_coord)
    db.add(user_coord)
    db.flush()
    
    token_coord = create_access_token(subject=str(user_coord.id))
    headers_coord = {"Authorization": f"Bearer {token_coord}"}
    
    # Debe ser denegado por la validación interna del endpoint (403 con mensaje de SUPERADMIN)
    response = client.post("/api/docentes/bulk-delete-excel", headers=headers_coord)
    assert response.status_code == 403
    assert response.json()["detail"] == "Operación restringida exclusivamente para SUPERADMIN."
    
    # 2. Intentar con un usuario SUPERADMIN
    role_super = db.query(Role).filter_by(name="SUPERADMIN").first()
    if not role_super:
        role_super = Role(name="SUPERADMIN")
        db.add(role_super)
        db.flush()
    
    user_super = User(username="superadmin@vonex.edu.pe", password_hash="...", is_active=True)
    user_super.roles.append(role_super)
    db.add(user_super)
    db.flush()
    
    token_super = create_access_token(subject=str(user_super.id))
    headers_super = {"Authorization": f"Bearer {token_super}"}
    
    response = client.post("/api/docentes/bulk-delete-excel", headers=headers_super)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "deleted_counts" in res_data["data"]
