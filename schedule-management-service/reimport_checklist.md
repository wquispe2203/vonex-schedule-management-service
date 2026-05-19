# Checklist de Reimportación Real

**Objetivo:** Reiniciar pruebas académicas usando archivos XML y Excel reales desde el frontend, validando la estabilidad sin alterar reglas matemáticas ni arquitectura.

## 1. Preparativos (Backend & DB)
- [x] Eliminar XML dummies (Ej. `temp_rule_test_upload.xml`). *(Completado)*
- [x] Verificar que base de datos `schedule_db` está libre de data sintética reciente. *(Completado)*
- [x] Verificar que el XML histórico (`historical_xml_import_202603.xml`) se mantiene intacto y funcional. *(Completado)*
- [x] Validar servicio backend ejecutándose correctamente (`uvicorn`).

## 2. Acciones del Usuario (Frontend)
El usuario ejecutará las siguientes acciones desde el dashboard web:

- [ ] **Paso 1:** Navegar a la vista de "Docentes" -> Importar Excel y subir el archivo Excel real de docentes actualizados.
- [ ] **Paso 2:** Navegar a la vista de "Importar XML" y subir los archivos XML reales de la semana.
- [ ] **Paso 3:** Navegar a la vista "Maestra de Docentes" y verificar la correcta visualización de los profesores.
- [ ] **Paso 4:** Revisar "Sin Asignar" para mapear aquellos docentes del XML que aún no coincidan o falte información.
- [ ] **Paso 5:** Revisar "Conflictos" y resolver colisiones en caso de nombres ambíguos.
- [ ] **Paso 6:** Navegar a "RPT Planillas", seleccionar el nuevo XML subido y verificar el total y cálculos de horas.

## 3. Validaciones Posteriores (Headless & Logs)
Una vez el usuario complete los uploads, ejecutaremos validaciones mínimas vía TestClient/SQL:

- [ ] Verificar que la nueva carga (`XmlUpload`) tenga status `COMPLETED`.
- [ ] Verificar que no existan IDs duplicados o registros corrompidos en `rpt_planilla`.
- [ ] Verificar que el número de registros en `teachers` se incrementó correctamente o se fusionó.
- [ ] Validar que el dropdown de "RPT Planillas" contiene a los docentes del nuevo XML.
- [ ] Asegurar que el cálculo de recesos (0.33) y reglas `F+30` funcionaron en los bloques nuevos sin romper los cálculos de Marzo 2026.
