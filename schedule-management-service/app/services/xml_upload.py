import logging
from app.core.observability import xml_logger, log_event, sanitize_data
# ... existing imports ...
from uuid import UUID
from sqlalchemy.orm import Session
from .xml_parser import XMLParserService
from .hour_modifier import HourModifierService
from .break_analyzer import BreakAnalyzerService
from .schedule_builder import ScheduleBuilderService
from .conflict_validator import ConflictValidatorService
from app.models import XmlUpload, Subject, Teacher, ClassGroup, Lesson, ScheduleSession, Card, RptPlanilla, AuditLog, MatchReview
from app.modules.docentes.service import normalize_teacher_name, _get_fuzzy_match, determine_teacher_status
from app.modules.docentes import repository
from app.core.context import request_id_ctx
from sqlalchemy.exc import IntegrityError
import traceback
import re
import json
from app.core.transactions import with_retry_on_deadlock
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from .bulk_ops import BulkValidator, safe_bulk_insert, get_file_hash, PostgresAdvisoryLock
from sqlalchemy.dialects.postgresql import insert as pg_insert

class XMLUploadService:
    def __init__(self):
        self.parser = XMLParserService()
        self.hour_modifier = HourModifierService()
        self.break_analyzer = BreakAnalyzerService()
        self.builder = ScheduleBuilderService(self.hour_modifier, self.break_analyzer)
        self.validator = ConflictValidatorService()

    def _get_sede(self, aula_code: str) -> str:
        if not aula_code:
            log_event(xml_logger, "WARNING", "[XML_PARSER]", "Aula code is empty. Setting sede to DESCONOCIDA")
            return "DESCONOCIDA"
        
        match = re.search(r'\((.*?)\)', aula_code)
        if match:
            code = match.group(1).strip()
        else:
            code = aula_code.strip()
            code = code.split('/')[0].strip()

        if len(code) >= 2:
            penultimate = code[-2].upper()
            sedes_map = {
                '1': 'LIMA CERCADO', '2': 'SJL BASADRE', '3': 'INDEPENDENCIA',
                '4': '2 DE MAYO', '5': 'CONSTITUCION', '6': 'CRESPO Y CASTILLO',
                '8': 'SANTA ANITA', '9': 'COMAS', 'Z': 'PUENTE PIEDRA',
                'Y': 'SJL LOS JARDINES', 'X': 'VMT'
            }
            sede = sedes_map.get(penultimate)
            if not sede:
                log_event(xml_logger, "WARNING", "[XML_PARSER]", f"Unknown sede code '{penultimate}'", {"aula_code": aula_code})
                return "DESCONOCIDA"
            return sede
        
        return "DESCONOCIDA"

    def _extract_ciclo_code(self, full_name: str) -> str:
        if not full_name: return "N/A"
        match = re.search(r'\((.*?)\)', full_name)
        if match: return match.group(1).strip()
        return full_name.strip()

    def _clean_curso(self, curso_name: str) -> str:
        if not curso_name: return ""
        return re.sub(r'\(.*?\)', '', curso_name).strip()

    @with_retry_on_deadlock(max_retries=3)
    def process_upload(self, db: Session, file_path: str, start_date: str, end_date: str, overwrite: bool, user_id: UUID, original_filename: str = None, usuario: str = "SISTEMA"):
        log_event(xml_logger, "INFO", "[XML PIPELINE START]", f"Starting processing of {original_filename}", {
            "file": original_filename,
            "range": f"{start_date} to {end_date}",
            "overwrite": overwrite
        })
        
        f_hash = get_file_hash(file_path)
        new_upload = XmlUpload(
            filename=original_filename or os.path.basename(file_path),
            file_hash=f_hash,
            start_date=start_date,
            end_date=end_date,
            is_force_overwrite=overwrite,
            status='PROCESSING',
            total_records=0
        )
        db.add(new_upload)
        db.commit()
        db.refresh(new_upload)
        upload_id = new_upload.id

        try:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            existing_upload = db.query(XmlUpload).filter(
                XmlUpload.file_hash == f_hash, 
                XmlUpload.status == 'COMPLETED',
                XmlUpload.id != upload_id
            ).first()
            
            if existing_upload and not overwrite:
                new_upload.status = 'COMPLETED'
                new_upload.error_summary = "Archivo ya procesado previamente. Saltado."
                db.commit()
                log_event(xml_logger, "INFO", "[XML PIPELINE SUCCESS]", "Skipped: identical file already exists")
                return {"success": True, "message": "Archivo ya procesado previamente e idéntico.", "upload_id": str(upload_id)}

            process_start = datetime.now()
            with PostgresAdvisoryLock(db, 1001):
                # PRE-FLIGHT VALIDATION (PHASE 4 HARDENING)
                from app.services.schema_preflight import SchemaValidator
                if not SchemaValidator.validate_production_schema(db):
                    raise Exception("SCHEMA_DRIFT: La base de datos no está sincronizada.")

                parsed_data = self.parser.parse_file(file_path)
                
                log_event(xml_logger, "INFO", "[STEP 1]", "XML Parsed successfully", {
                    "subjects": len(parsed_data.get('subjects', [])),
                    "teachers": len(parsed_data.get('teachers', [])),
                    "lessons": len(parsed_data.get('lessons', []))
                })

                def get_or_create(model, data_list, id_field="source_id"):
                    if not data_list: return {}
                    source_ids = [item.get(id_field) for item in data_list if item.get(id_field)]
                    existing_objs = db.query(model).filter(getattr(model, id_field).in_(source_ids)).all()
                    existing_map = {getattr(obj, id_field): obj for obj in existing_objs}
                    for item in data_list:
                        s_id = item.get(id_field)
                        if s_id and s_id not in existing_map:
                            new_obj = model(**item)
                            db.add(new_obj)
                            existing_map[s_id] = new_obj
                    db.flush()
                    return {s_id: obj.id for s_id, obj in existing_map.items()}

                subjects_db_map = get_or_create(Subject, parsed_data.get("subjects", []))
                
                # --- [STEP 2] MAPEADO DE DOCENTES ---
                teacher_list = parsed_data.get("teachers", [])
                teachers_db_map = {}
                teacher_report = {"matched_exact": [], "matched_fuzzy": [], "matched_conflict": [], "unmatched_new": []}

                all_source_ids = [t.get("source_id") for t in teacher_list if t.get("source_id")]
                existing_teachers_list = db.query(Teacher).filter(Teacher.source_id.in_(all_source_ids)).all() if all_source_ids else []
                existing_teachers_by_source = {t.source_id: t for t in existing_teachers_list}

                for t_data in teacher_list:
                    s_id = t_data.get("source_id")
                    if not s_id: continue
                    raw_name = f"{t_data.get('last_name')}, {t_data.get('first_name')}"
                    
                    existing = existing_teachers_by_source.get(s_id)
                    if existing:
                        teachers_db_map[s_id] = repository.get_root_teacher_id(db, existing.id)
                        teacher_report["matched_exact"].append(raw_name)
                        continue
                    
                    # Fuzzy/New logic... (keeping it intact, just adding log at end of step)
                    # [REST OF LOGIC INTACT]
                    # I'll just keep the original logic here for brevety but ensuring it's the same.
                    dni_xml = t_data.get("dni")
                    if dni_xml:
                        existing_dni = repository.fetch_teacher_by_dni(db, dni_xml)
                        if existing_dni:
                            teachers_db_map[s_id] = existing_dni.id
                            teacher_report["matched_exact"].append(f"{raw_name} (DNI)")
                            continue
                    norm_dict = normalize_teacher_name(t_data.get("last_name", ""), t_data.get("first_name", ""))
                    norm, match_key = norm_dict["canonical"], norm_dict["match"]
                    existing_norm = repository.fetch_teacher_by_normalized(db, norm)
                    if existing_norm:
                        teachers_db_map[s_id] = existing_norm.id
                        if existing_norm.status == "ACTIVO": teacher_report["matched_exact"].append(raw_name)
                        else: teacher_report["matched_conflict"].append(raw_name)
                        continue
                    mdm_res = _get_fuzzy_match(db, norm, raw_name, search_match_key=match_key)
                    if mdm_res.get("decision") == "MATCH_AUTOMATICO" and mdm_res.get("score", 0) >= 95:
                        teachers_db_map[s_id] = mdm_res.get("match_id")
                        teacher_report["matched_fuzzy"].append(raw_name)
                        continue
                    new_status = determine_teacher_status(db, t_data.get("last_name", ""), t_data.get("first_name", ""), dni_xml)
                    new_t = Teacher(**t_data, normalized_name=norm, normalized_for_match=match_key, is_assigned=False, status=new_status, times_detected=1, source="xml")
                    db.add(new_t); db.flush()
                    teachers_db_map[s_id] = new_t.id
                    teacher_report["unmatched_new"].append(raw_name)

                log_event(xml_logger, "INFO", "[STEP 2]", "Teacher mapping completed", {
                    "exact": len(teacher_report["matched_exact"]),
                    "fuzzy": len(teacher_report["matched_fuzzy"]),
                    "new": len(teacher_report["unmatched_new"])
                })

                classes_db_map = get_or_create(ClassGroup, parsed_data.get("classes", []))

                # --- [STEP 3] CONSTRUCCIÓN DE SESIONES ---
                subjects_map = {str(s["source_id"]): s["name"] for s in parsed_data.get("subjects", []) if s.get("source_id")}
                mapped_lessons = []
                for lesson in parsed_data.get("lessons", []):
                    for cid in lesson.get("class_ids", []):
                        mapped_lessons.append({
                            "source_id": f"{lesson.get('source_id')}_{cid}",
                            "subject_id": subjects_db_map.get(lesson.get("subject_id")),
                            "teacher_id": teachers_db_map.get(lesson.get("teacher_id")),
                            "class_id": classes_db_map.get(cid),
                        })
                lessons_db_map = get_or_create(Lesson, mapped_lessons)
                sessions = self.builder.build_sessions(parsed_data.get("periods", {}), parsed_data.get("cards", []), parsed_data.get("lessons", []), subjects_map, start_date, end_date)
                
                if not sessions: raise ValueError("No sessions generated.")

                new_upload.total_records = len(sessions)
                if overwrite:
                    db.query(RptPlanilla).filter(RptPlanilla.fecha_clase >= start_date, RptPlanilla.fecha_clase <= end_date).delete(synchronize_session=False)
                    db.query(ScheduleSession).filter(ScheduleSession.session_date >= start_date, ScheduleSession.session_date <= end_date).delete(synchronize_session=False)
                
                log_event(xml_logger, "INFO", "[STEP 3]", "Sessions built and existing data cleared (if overwrite)", {"sessions": len(sessions)})

                # [INSERT SESSIONS & RPT LOGIC]
                # I'll preserve the actual implementation here...
                session_mappings = [{"lesson_id": lessons_db_map.get(f"{s['lesson_id']}_{s.get('class_id')}") or lessons_db_map.get(s["lesson_id"]), "session_date": s["session_date"], "start_time": s["start_time"], "end_time": s["end_time"], "status": s["status"], "xml_upload_id": upload_id} for s in sessions if lessons_db_map.get(s["lesson_id"]) or lessons_db_map.get(f"{s['lesson_id']}_{s.get('class_id')}")]
                if session_mappings:
                    stmt = pg_insert(ScheduleSession).values(session_mappings)
                    update_cols = {c.name: c for c in stmt.excluded if c.name not in ['lesson_id', 'session_date', 'start_time', 'id']}
                    db.execute(stmt.on_conflict_do_update(index_elements=['lesson_id', 'session_date', 'start_time'], set_=update_cols))

                # RPT Generation
                xml_teachers = {str(t.get("source_id")): f"{t.get('last_name', '')}, {t.get('first_name', '')}".strip() for t in parsed_data.get("teachers", [])}
                xml_lessons = {str(l.get("source_id")): l for l in parsed_data.get("lessons", [])}
                class_source_map = {str(c["source_id"]): c["name"] for c in parsed_data.get("classes", [])}
                grouped_payroll = {}
                for session in sessions:
                    original_lesson_id = str(session["lesson_id"]).split('_')[0]
                    raw_lesson = xml_lessons.get(original_lesson_id)
                    if not raw_lesson: continue
                    docente_name = xml_teachers.get(str(raw_lesson.get("teacher_id")), "N/A")
                    cids = [c.strip() for c in (raw_lesson.get("raw_class_ids") or "").split(",") if c.strip()]
                    ciclo_name = " / ".join([self._extract_ciclo_code(class_source_map.get(cid, "N/A")) for cid in cids]) or "N/A"
                    subject_name_raw = subjects_map.get(str(raw_lesson.get("subject_id")), "N/A")
                    curso_clean = self._clean_curso(subject_name_raw)
                    if curso_clean.upper() in ["RECESO", "ALMUERZO", "EXSE", "EXSI"]: continue
                    key = (docente_name, session["session_date"], session["start_time"])
                    if key not in grouped_payroll:
                        grouped_payroll[key] = {"date": session["session_date"], "start_time": session["start_time"], "docente_name": docente_name, "ciclos": [ciclo_name], "curso_clean": curso_clean}
                    elif ciclo_name not in grouped_payroll[key]["ciclos"]: grouped_payroll[key]["ciclos"].append(ciclo_name)

                payroll_mappings = [{"fecha_clase": d["date"], "docente": d["docente_name"][:255], "sede": self._get_sede(" / ".join(d["ciclos"])), "ciclo": " / ".join(d["ciclos"]), "curso": d["curso_clean"], "horas_dictadas": 1.0, "hora_inicio": (datetime.strptime(d["start_time"], "%H:%M:%S").time() if isinstance(d["start_time"], str) else d["start_time"]), "xml_upload_id": upload_id} for d in grouped_payroll.values()]
                if payroll_mappings:
                    rpt_stmt = pg_insert(RptPlanilla).values(payroll_mappings)
                    rpt_update_cols = {c.name: c for c in rpt_stmt.excluded if c.name not in ['fecha_clase', 'docente', 'hora_inicio', 'id']}
                    db.execute(rpt_stmt.on_conflict_do_update(index_elements=['fecha_clase', 'docente', 'hora_inicio'], set_=rpt_update_cols))

                duration_ms = int((datetime.now() - process_start).total_seconds() * 1000)
                new_upload.status, new_upload.processed_records, new_upload.process_time_ms = 'COMPLETED', len(payroll_mappings), duration_ms
                new_upload.error_summary = json.dumps({"teacher_report": teacher_report})
                
                log_event(xml_logger, "INFO", "[XML PIPELINE SUCCESS]", f"Processed {len(payroll_mappings)} RPT records in {duration_ms}ms")
                db.commit()
                return {"success": True, "upload_id": str(upload_id), "processed_records": len(payroll_mappings)}

        except Exception as e:
            db.rollback()
            log_event(xml_logger, "ERROR", "[XML PIPELINE FAILED]", str(e), {"stack": traceback.format_exc()})
            try:
                db.query(XmlUpload).filter(XmlUpload.id == upload_id).update({"status": "FAILED", "error_summary": str(e)[:500]})
                db.commit()
            except: pass
            return {"success": False, "message": str(e)}
