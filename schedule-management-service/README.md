# Vonex Schedule Management Service

Sistema de gestión académica diseñado para la conciliación de horarios, docentes e incidencias.

## 🚀 Características
- **Módulo de Docentes**: Gestión maestra con Fuzzy Matching.
- **Módulo de Horarios**: Importación masiva desde XML aSc Horarios.
- **Módulo de Incidencias**: Registro de faltas y reemplazos con lógica de liquidación.
- **Módulo de Reportes**: Generación de planillas de pago configurables.
- **Seguridad**: RBAC granular con JWT.

## 🛠️ Stack Tecnológico
- **Backend**: FastAPI
- **DB**: PostgreSQL / SQLite (Dev)
- **Seguimiento**: JWT + RBAC

## 📦 Instalación
1. Instalar dependencias: `pip install -r requirements.txt`
2. Configurar base de datos en `database.py`.
3. Ejecutar: `uvicorn app.main:app --reload`

## 📄 Documentación
Consultar el archivo `ARCHITECTURE.md` para detalles de la arquitectura modular.
