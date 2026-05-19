# XML Association Matrix

Generated on: 2026-05-18T12:43:18.332988

To maintain active DB reports availability and respect post-migration schema integrity checks, this matrix outlines the association of historical data with the Virtual historical XML.

## 1. Virtual XML Upload Definition

* **Virtual Filename**: `historical_xml_import_202603.xml`
* **Static UUID**: `8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84`
* **Status**: `COMPLETED`
* **Start Date**: `2026-03-02`
* **End Date**: `2026-03-20`
* **Created At**: `2026-04-08T00:00:00Z`
* **Total Records**: 8402

## 2. Table Association Strategy

| Table Name | Count of Records | XML Association Field | Associated ID Value | Description |
| :--- | :---: | :---: | :--- | :--- |
| **rpt_planilla** | 4819 | `xml_upload_id` | `8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84` | Restores historical payroll data inside range of 2026-03. |
| **schedule_sessions** | 8402 | `xml_upload_id` | `8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84` | Restores historical sessions within range of 2026-03. |
| **lessons** | 4092 | *N/A* | *N/A* | Independent from individual XML load metadata. |

## 3. Date Distribution Analysis for Virtual XML

Below is the distribution of session dates that will be safely mapped under this historical virtual upload:

- **2026-03-02**: Monday Schedule
- **2026-03-03 to 2026-03-06**: Week 1 Schedule
- **2026-03-09 to 2026-03-13**: Week 2 Schedule
- **2026-03-16 to 2026-03-20**: Week 3 Schedule

This ensures that the reports frontend queries covering the month of **March 2026** will successfully match the `xml_upload_id` range and render the consolidated hours of all teachers.
