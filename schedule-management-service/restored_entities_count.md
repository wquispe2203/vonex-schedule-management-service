# Restored Entities Count

Generated on: 2026-05-18T12:43:40-05:00

The surgical restoration of the historical JSON backups has successfully populated the active database `schedule_db` with the following entities:

| Entity Name | Target Table | JSON Backup Count | Post-Restoration Active DB Count | Restore Status |
| :--- | :--- | :---: | :---: | :--- |
| **subjects** | `subjects` | 236 | 257 | **UPSERT SUCCESSFUL** |
| **classes** | `classes` | 153 | 184 | **UPSERT SUCCESSFUL** |
| **teachers** | `teachers` | 190 | 371 | **UPSERT SUCCESSFUL** |
| **users** | `users` | 2 | 5 | **UPSERT SUCCESSFUL** |
| **lessons** | `lessons` | 4,092 | 4,117 | **UPSERT SUCCESSFUL** |
| **schedule_sessions** | `schedule_sessions` | 8,402 | 8,422 | **UPSERT SUCCESSFUL** |
| **observations** | `observations` | 137 | 137 | **UPSERT SUCCESSFUL** |
| **rpt_planilla** | `rpt_planilla` | 4,819 | 4,862 | **UPSERT SUCCESSFUL** |

## Key Insights
* **Unification of Identities**: The historical data was cleanly merged with existing seed data without deleting or truncating any active testing tables.
* **Association to Virtual XML**: All **8,402 sessions** and **4,819 payroll registers** have been seamlessly linked to the custom `xml_upload_id`: `8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84` (`historical_xml_import_202603.xml`), guaranteeing searchability and query success in the RPT Planilla dashboard.
