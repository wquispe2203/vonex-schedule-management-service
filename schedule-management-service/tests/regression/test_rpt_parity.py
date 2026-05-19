import pytest
from io import BytesIO
from tests.fixtures.factories import TestFactory
from app.models.teacher import Teacher

@pytest.mark.rpt
@pytest.mark.regression
def test_xml_to_rpt_parity_simple(client, db, mock_auth):
    """
    VALDACIÓN QUIRÚRGICA: Ingesta XML -> Consolidación RPT (Simple).
    Verifica paridad de nombres y horas dictadas.
    """
    mock_auth()
    # Preparar Docente en Maestra
    TestFactory.create_teacher(db, name="GOLDEN 1, DOCENTE", source_id="T_GOLDEN_1")
    
    xml_path = "tests/golden_datasets/xml_simple.xml"
    with open(xml_path, "rb") as f:
        content = f.read()
    
    files = {"file": ("xml_simple.xml", BytesIO(content), "text/xml")}
    data = {
        "start_date": "2026-03-02",
        "end_date": "2026-03-08",
        "force_overwrite": "true"
    }
    client.post("/api/schedule/upload", files=files, data=data)
    
    params = {"fecha_inicio": "2026-03-02", "fecha_fin": "2026-03-02"}
    response = client.get("/api/rpt-planilla/", params=params)
    assert response.status_code == 200
    
    data = response.json()["data"]["data"]
    assert len(data) == 1
    record = data[0]
    
    assert record["docente"] == "GOLDEN 1, DOCENTE"
    assert record["hora_inicio"] == "08:00:00"
    assert record["hora_fin"] == "09:40:00"
    
    # 2 periodos de 50 min = 100 min = 2.0 academic hours
    assert float(record["horas_dictadas"]) == 2.0
    assert float(record["receso"]) == 0.0

@pytest.mark.rpt
@pytest.mark.regression
def test_xml_to_rpt_parity_recesos(client, db, mock_auth):
    """
    VALDACIÓN QUIRÚRGICA: Transferencia de Recesos.
    Verifica que el receso de 0.33 se asigne correctamente.
    """
    mock_auth()
    TestFactory.create_teacher(db, name="RECESO, DOCENTE", source_id="T_GOLDEN_2")
    
    xml_path = "tests/golden_datasets/xml_recesos.xml"
    with open(xml_path, "rb") as f:
        content = f.read()
    
    files = {"file": ("xml_recesos.xml", BytesIO(content), "text/xml")}
    data = {"start_date": "2026-03-02", "end_date": "2026-03-08", "force_overwrite": "true"}
    client.post("/api/schedule/upload", files=files, data=data)
    
    params = {"fecha_inicio": "2026-03-02", "fecha_fin": "2026-03-02"}
    response = client.get("/api/rpt-planilla/", params=params)
    assert response.status_code == 200
    
    data = response.json()["data"]["data"]
    for i, r in enumerate(data):
        print(f"DEBUG RECESO {i}: {r['hora_inicio']}-{r['hora_fin']} | hours={r['horas_dictadas']} | receso={r['receso']}")
    
    # El sistema consolida si el gap es <= 20 min. 
    # 09:40 a 10:00 es exactamente 20 min, por lo que se consolidan en un solo bloque.
    assert len(data) == 1
    record = data[0]
    
    # 08:00-11:40 = 4.0 academic hours (2.0 + 2.0)
    assert float(record["horas_dictadas"]) == 4.0
    assert float(record["receso"]) == 0.33
