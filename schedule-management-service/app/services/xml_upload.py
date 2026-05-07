import os
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
import logging

logger = logging.getLogger("app.xml_upload")

class XMLUploadService:
    def __init__(self):
        self.parser = XMLParserService()
        self.hour_modifier = HourModifierService()
        self.break_analyzer = BreakAnalyzerService()
        self.builder = ScheduleBuilderService(self.hour_modifier, self.break_analyzer)
        self.validator = ConflictValidatorService()

    def _get_sede(self, aula_code: str) -> str:
        if not aula_code:
            logger.warning("[XML_PARSER] Aula code is empty. Setting sede to DESCONOCIDA")
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
                logger.warning(f"[XML_PARSER] Unknown sede code '{penultimate}' in '{code}'. Full aula_code: '{aula_code}'")
                return "DESCONOCIDA"
            return sede
        
        logger.warning(f"[XML_PARSER] Aula code too short to extract sede: '{code}'. Full aula_code: '{aula_code}'")
        return "DESCONOCIDA"

    def _extract_ciclo_code(self, full_name: str) -> str:
        if not full_name:
            logger.warning("[XML_PARSER] Ciclo full_name is empty.")
            return "N/A"
        match = re.search(r'\((.*?)\)', full_name)
        if match:
            return match.group(1).strip()
        return full_name.strip()


    def _clean_curso(self, curso_name: str) -> str:
        if not curso_name:
            return ""
        return re.sub(r'\(.*?\)', '', curso_name).strip()

    def _calculate_hours(self, start_time, end_time) -> float:
        def parse_time(t):
            if isinstance(t, time): return t
            if isinstance(t, str):
                for fmt in ("%H:%M:%S", "%H:%M"):
                    try: return datetime.strptime(t, fmt).time()
                    except ValueError: continue
            return t

        t_start_obj = parse_time(start_time)
        t_end_obj = parse_time(end_time)
        dummy_date = datetime(2000, 1, 1)
        t_start = datetime.combine(dummy_date, t_start_obj)
        t_end = datetime.combine(dummy_date, t_end_obj)
        delta = t_end - t_start
        return round(delta.total_seconds() / 3000.0, 2)

    @with_retry_on_deadlock(max_retries=3)
    def process_upload(self, db: Session, file_path: str, start_date: str, end_date: str, overwrite: bool, user_id: UUID, original_filename: str = None, usuario: str = "SISTEMA"):
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
                return {"success": True, "message": "Archivo ya procesado previamente e idéntico.", "upload_id": str(upload_id)}

            process_start = datetime.now()
            with PostgresAdvisoryLock(db, 1001):
                parsed_data = self.parser.parse_file(file_path)
                
                logger.info(f"[STEP 1] XML Parseado: subjects={len(parsed_data.get('subjects', []))} teachers={len(parsed_data.get('teachers', []))} lessons={len(parsed_data.get('lessons', []))}")
                print(f"[STEP 1] XML Parseado: subjects={len(parsed_data.get('subjects', []))} teachers={len(parsed_data.get('teachers', []))} lessons={len(parsed_data.get('lessons', []))}")

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
                
                # --- [STEP 2] MAPEADO DE DOCENTES (JERARQUÍA ESTRICTA) ---
                logger.info(f"[STEP 2] Iniciando mapeo de docentes con gobernanza de datos...")
                teacher_list = parsed_data.get("teachers", [])
                teachers_db_map = {}
                teacher_report = {
                    "matched_exact": [], 
                    "matched_fuzzy": [], 
                    "matched_conflict": [],
                    "unmatched_new": [], 
                    "duplicates": []
                }

                all_source_ids = [t.get("source_id") for t in teacher_list if t.get("source_id")]
                existing_teachers_list = db.query(Teacher).filter(Teacher.source_id.in_(all_source_ids)).all() if all_source_ids else []
                existing_teachers_by_source = {t.source_id: t for t in existing_teachers_list}

                for t_data in teacher_list:
                    s_id = t_data.get("source_id")
                    if not s_id: continue
                    
                    raw_name = f"{t_data.get('last_name')}, {t_data.get('first_name')}"
                    dni_xml = t_data.get("dni")
                    
                    # 1. Match Directo por source_id
                    existing = existing_teachers_by_source.get(s_id)
                    if existing:
                        root_id = repository.get_root_teacher_id(db, existing.id)
                        teachers_db_map[s_id] = root_id
                        teacher_report["matched_exact"].append(raw_name)
                        continue
                    
                    # 2. Match por DNI (si viene en XML)
                    if dni_xml:
                        existing_dni = repository.fetch_teacher_by_dni(db, dni_xml)
                        if existing_dni:
                            teachers_db_map[s_id] = existing_dni.id
                            teacher_report["matched_exact"].append(f"{raw_name} (DNI)")
                            continue

                    # Normalizar para búsquedas
                    norm_dict = normalize_teacher_name(t_data.get("last_name", ""), t_data.get("first_name", ""))
                    norm = norm_dict["canonical"]
                    match_key = norm_dict["match"]
                    
                    # 3. Match por normalized_name + status='ACTIVO'
                    existing_norm = repository.fetch_teacher_by_normalized(db, norm)
                    if existing_norm:
                        if existing_norm.status == "ACTIVO":
                            teachers_db_map[s_id] = existing_norm.id
                            teacher_report["matched_exact"].append(raw_name)
                            continue
                        
                        # 4. Match por normalized_name + status='INCOMPLETO' -> Marcar CONFLICTO
                        if existing_norm.status == "INCOMPLETO":
                            logger.warning(f"MDM: Docente '{raw_name}' coincide pero está INCOMPLETO. Marcando CONFLICTO.")
                            existing_norm.status = "CONFLICTO"
                            db.flush()
                            teachers_db_map[s_id] = existing_norm.id
                            teacher_report["matched_conflict"].append(raw_name)
                            continue
                        
                        # Caso ya en conflicto
                        teachers_db_map[s_id] = existing_norm.id
                        teacher_report["matched_conflict"].append(raw_name)
                        continue
                    
                    # 5. Fuzzy Match Estricto (>= 95%)
                    # Usamos settings.FUZZY_THRESHOLD pero forzamos un mínimo de 95 para auto-match en XML
                    mdm_res = _get_fuzzy_match(db, norm, raw_name, search_match_key=match_key)
                    if mdm_res.get("decision") == "MATCH_AUTOMATICO" and mdm_res.get("score", 0) >= 95:
                        teachers_db_map[s_id] = mdm_res.get("match_id")
                        teacher_report["matched_fuzzy"].append(raw_name)
                        continue
                        
                    # 6. Crear nuevo docente (Sin Asignar)
                    # Calculamos status real antes de insertar
                    new_status = determine_teacher_status(db, t_data.get("last_name", ""), t_data.get("first_name", ""), dni_xml)
                    
                    new_t = Teacher(**t_data)
                    new_t.normalized_name = norm
                    new_t.normalized_for_match = match_key
                    new_t.is_assigned = False # Marcado para revisión (Sin Asignar)
                    new_t.status = new_status
                    new_t.times_detected = 1
                    new_t.source = "xml"
                    
                    db.add(new_t)
                    db.flush()
                    teachers_db_map[s_id] = new_t.id
                    teacher_report["unmatched_new"].append(raw_name)

                # Auditoría de Mapeo
                total_mapped = len(teacher_list)
                exact = len(teacher_report["matched_exact"])
                fuzzy = len(teacher_report["matched_fuzzy"])
                conflict = len(teacher_report["matched_conflict"])
                new_count = len(teacher_report["unmatched_new"])

                log_step2 = f"[STEP 2] Mapeo completo: total={total_mapped} exact={exact} fuzzy={fuzzy} conflict={conflict} new={new_count}"
                logger.info(log_step2)
                print(log_step2)

                # Validación de Falsos Positivos
                if total_mapped > 10 and exact == total_mapped:
                    warn_msg = "[MATCH WARNING] 100% exact match improbable. Verificar normalización y calidad de datos."
                    logger.warning(warn_msg)
                    print(warn_msg)

                classes_db_map = get_or_create(ClassGroup, parsed_data.get("classes", []))

                # --- [STEP 3] CONSTRUCCIÓN DE LESSONS Y SESIONES ---
                logger.info(f"[STEP 3] Construyendo lessons y sesiones...")
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
                
                # Generar Sesiones
                sessions = self.builder.build_sessions(
                    parsed_data.get("periods", {}), 
                    parsed_data.get("cards", []), 
                    parsed_data.get("lessons", []), 
                    subjects_map, 
                    start_date, 
                    end_date
                )
                
                num_sessions = len(sessions)
                print(f"[STEP 4] Sessions: {num_sessions}")
                if num_sessions == 0:
                    raise ValueError(f"No se generaron sesiones reales en el rango {start_date} a {end_date}.")

                new_upload.total_records = num_sessions
                db.flush()

                if overwrite:
                    db.query(RptPlanilla).filter(RptPlanilla.fecha_clase >= start_date, RptPlanilla.fecha_clase <= end_date).delete(synchronize_session=False)
                    db.query(ScheduleSession).filter(ScheduleSession.session_date >= start_date, ScheduleSession.session_date <= end_date).delete(synchronize_session=False)
                    db.flush()
                elif db.query(ScheduleSession).filter(ScheduleSession.session_date >= start_date, ScheduleSession.session_date <= end_date).first():
                    raise ValueError("DUPLICATE_RANGE: Ya existen datos para estas fechas.")

                # Insertar Sesiones
                session_mappings = [
                    {
                        "lesson_id": lessons_db_map.get(f"{s['lesson_id']}_{s.get('class_id')}") or lessons_db_map.get(s["lesson_id"]),
                        "session_date": s["session_date"],
                        "start_time": s["start_time"],
                        "end_time": s["end_time"],
                        "status": s["status"],
                        "xml_upload_id": upload_id
                    }
                    for s in sessions if lessons_db_map.get(s["lesson_id"]) or lessons_db_map.get(f"{s['lesson_id']}_{s.get('class_id')}")
                ]
                if session_mappings:
                    stmt = pg_insert(ScheduleSession).values(session_mappings)
                    update_cols = {c.name: c for c in stmt.excluded if c.name not in ['lesson_id', 'session_date', 'start_time', 'id']}
                    stmt = stmt.on_conflict_do_update(index_elements=['lesson_id', 'session_date', 'start_time'], set_=update_cols)
                    db.execute(stmt)
                    db.flush()

                # Procesar RPT Planilla
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
                    
                    subject_id = str(raw_lesson.get("subject_id"))
                    subject_name_raw = subjects_map.get(subject_id, "N/A")
                    curso_clean = self._clean_curso(subject_name_raw)
                    
                    if curso_clean.upper() in ["RECESO", "ALMUERZO", "EXSE", "EXSI"]: continue
                        
                    key = (docente_name, session["session_date"], session["start_time"])
                    if key not in grouped_payroll:
                        grouped_payroll[key] = {
                            "date": session["session_date"], "start_time": session["start_time"], 
                            "end_time": session["end_time"], "docente_name": docente_name, 
                            "ciclos": [ciclo_name], "curso_clean": curso_clean
                        }
                    elif ciclo_name not in grouped_payroll[key]["ciclos"]:
                        grouped_payroll[key]["ciclos"].append(ciclo_name)

                payroll_mappings = []
                for data in grouped_payroll.values():
                    ciclo_final = " / ".join(data["ciclos"])
                    h_start = data["start_time"]
                    if isinstance(h_start, str):
                        try: h_start_obj = datetime.strptime(h_start, "%H:%M:%S").time()
                        except: h_start_obj = datetime.strptime(h_start, "%H:%M").time()
                    else: h_start_obj = h_start

                    payroll_mappings.append({
                        "fecha_clase": data["date"], "docente": data["docente_name"][:255],
                        "sede": self._get_sede(ciclo_final), "ciclo": ciclo_final,
                        "curso": data["curso_clean"], "horas_dictadas": float(1.0), "hora_inicio": h_start_obj,
                        "xml_upload_id": upload_id
                    })
                
                if payroll_mappings:
                    rpt_stmt = pg_insert(RptPlanilla).values(payroll_mappings)
                    rpt_update_cols = {c.name: c for c in rpt_stmt.excluded if c.name not in ['fecha_clase', 'docente', 'hora_inicio', 'id']}
                    rpt_stmt = rpt_stmt.on_conflict_do_update(index_elements=['fecha_clase', 'docente', 'hora_inicio'], set_=rpt_update_cols)
                    db.execute(rpt_stmt)
                    db.flush()

                duration_ms = int((datetime.now() - process_start).total_seconds() * 1000)
                new_upload.status = 'COMPLETED'
                new_upload.processed_records = len(payroll_mappings)
                new_upload.process_time_ms = duration_ms
                new_upload.error_summary = json.dumps({"teacher_report": teacher_report})

                # Archive older completed uploads that overlap with this one
                db.query(XmlUpload).filter(
                    XmlUpload.id != upload_id,
                    XmlUpload.status == 'COMPLETED',
                    XmlUpload.start_date <= end_date,
                    XmlUpload.end_date >= start_date
                ).update({"status": "ARCHIVED"}, synchronize_session=False)

                db.commit()
                
                print(f"[STEP 6] Upload completado: {len(payroll_mappings)} registros RPT")
                return {"success": True, "upload_id": str(upload_id), "processed_records": len(payroll_mappings), "records": len(payroll_mappings)}

        except Exception as e:
            db.rollback()
            err_msg = traceback.format_exc()
            logger.error(f"[XML_UPLOAD] Error: {str(e)}\n{err_msg}")
            try:
                db.query(XmlUpload).filter(XmlUpload.id == upload_id).update({
                    "status": "FAILED", "error_summary": f"{str(e)} | Trace: {err_msg[:500]}"
                })
                db.commit()
            except: pass
            return {"success": False, "message": str(e), "error_type": "PROCESS_ERROR"}
