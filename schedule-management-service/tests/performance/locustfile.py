import time
import random
from locust import HttpUser, task, between, events
from io import BytesIO

class VonexUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """Autenticación inicial usando dev-login"""
        response = self.client.get("/api/users/dev-login")
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            print(f"FAILED LOGIN: {response.status_code}")

    @property
    def auth_header(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def view_rpt_planilla(self):
        """Simula visualización de reportes (Lectura pesada)"""
        params = {
            "fecha_inicio": "2026-03-02",
            "fecha_fin": "2026-03-08",
            "page": 1,
            "limit": 50
        }
        with self.client.get("/api/rpt-planilla/", params=params, headers=self.auth_header, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def upload_xml_stress(self):
        """Simula ingesta de XML (Escritura pesada)"""
        # Contenido XML válido para generar sesiones
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <root>
            <periods>
                <period period="1" starttime="08:00" endtime="09:40"/>
            </periods>
            <subjects>
                <subject id="S1" name="MATEMATICA" short="MAT"/>
            </subjects>
            <teachers>
                <teacher id="T1" firstname="LOAD" lastname="TEST" short="LT"/>
            </teachers>
            <classes>
                <class id="C1" name="AULA 101 (1)"/>
            </classes>
            <lessons>
                <lesson id="L1" subjectid="S1" teacherids="T1" classids="C1"/>
            </lessons>
            <cards>
                <card id="K1" lessonid="L1" days="1000000" period="1"/>
            </cards>
        </root>"""
        
        files = {"file": ("load_test.xml", BytesIO(xml_content.encode('utf-8')), "text/xml")}
        data = {
            "start_date": "2026-04-01",
            "end_date": "2026-04-07",
            "force_overwrite": "true",
            "usuario": "LOCUST_RUNNER"
        }
        
        with self.client.post("/api/schedule/upload", files=files, data=data, headers=self.auth_header, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    def check_permissions_load(self):
        """Simula navegación y validación de permisos (Meta-data)"""
        self.client.get("/api/users/me", headers=self.auth_header)
        self.client.get("/api/rpt-planilla/sedes", headers=self.auth_header)

@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--rpt-threshold", type=int, default=1000, help="P95 threshold for RPT")
