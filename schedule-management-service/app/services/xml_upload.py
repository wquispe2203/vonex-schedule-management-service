import os
from uuid import UUID
from sqlalchemy.orm import Session
from .xml_parser import XMLParserService
from .hour_modifier import HourModifierService
from .break_analyzer import BreakAnalyzerService
from .schedule_builder import ScheduleBuilderService
from .conflict_validator import ConflictValidatorService
from app.models import XmlUpload, Subject, Teacher, ClassGroup, Lesson, ScheduleSession, Card, RptPlanilla, AuditLog, MatchReview
from app.modules.docentes.service import normalize_teacher_name, _get_fuzzy_match
from app.modules.docentes import repository
from app.core.context import request_id_ctx
from sqlalchemy.exc import IntegrityError
import traceback
import re
import json
from app.core.transactions import with_retry_on_deadlock
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
class XMLUploadService:
    def __init__(self):
        self.parser = XMLParserService()
        self.hour_modifier = HourModifierService()
        self.break_analyzer = BreakAnalyzerService()
        self.builder = ScheduleBuilderService(self.hour_modifier, self.break_analyzer)
        self.validator = ConflictValidatorService()

    def _get_sede(self, aula_code: str) -> str:
        if not aula_code:
            return "DESCONOCIDA"
        
        # Extraer lo que está entre paréntesis o usar todo si no hay
        match = re.search(r'\((.*?)\)', aula_code)
        if match:
            code = match.group(1).strip()
        else:
            # Por si envían el ciclo ya limpio como "SMINT1025P1A / SMINT1025P2A"
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
            return sedes_map.get(penultimate, "DESCONOCIDA")
        return "DESCONOCIDA"

    def _extract_ciclo_code(self, full_name: str) -> str:
        if not full_name: return "N/A"
        match = re.search(r'\((.*?)\)', full_name)
        if match:
            return match.group(1).strip()
        return full_name.strip()


    def _clean_curso(self, curso_name: str) -> str:
        if not curso_name:
            return ""
        # Eliminar cualquier cosa entre paréntesis, ej: ALGEBRA(E0) -> ALGEBRA
        return re.sub(r'\(.*?\)', '', curso_name).strip()

    def _calculate_hours(self, start_time, end_time) -> float:
        def parse_time(t):
            if isinstance(t, time):
                return t
            if isinstance(t, str):
                for fmt in ("%H:%M:%S", "%H:%M"):
                    try:
                        return datetime.strptime(t, fmt).time()
                    except ValueError:
                        continue
            return t # Si no es string ni time, dejar que combine falle con el error original o manejarlo

        t_start_obj = parse_time(start_time)
        t_end_obj = parse_time(end_time)
        
        dummy_date = datetime(2000, 1, 1)
        t_start = datetime.combine(dummy_date, t_start_obj)
        t_end = datetime.combine(dummy_date, t_end_obj)
        delta = t_end - t_start
        # Calcular en base a hora académica de 50 minutos (50 * 60 = 3000 segundos)
        return round(delta.total_seconds() / 3000.0, 2)

    @with_retry_on_deadlock(max_retries=3)
    def process_upload(self, db: Session, file_path: str, start_date: str, end_date: str, overwrite: bool, user_id: UUID, original_filename: str = None, usuario: str = "SISTEMA"):
        try:
            # Asegurar que las fechas sean objetos date
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            # 1. Registrar subida (flush para tener ID pero commit al final)
            new_upload = XmlUpload(
                filename=original_filename or os.path.basename(file_path)
            )
            db.add(new_upload)
            db.flush()

            # 2. Parsear XML
            print("[XML_UPLOAD] Comenzando parsing de XML...")
            parsed_data = self.parser.parse_file(file_path)
            print(f"[XML_UPLOAD] XML parseado. Registros: {len(parsed_data.get('lessons', []))} lecciones")

            # 3. Guardado transaccional y mapeo
            def get_or_create(model, data_list, id_field="source_id"):
                if not data_list: return {}
                source_ids = [item.get(id_field) for item in data_list if item.get(id_field)]
                existing_objs = db.query(model).filter(getattr(model, id_field).in_(source_ids)).all()
                existing_map = {getattr(obj, id_field): obj for obj in existing_objs}
                new_objs = []
                for item in data_list:
                    s_id = item.get(id_field)
                    if s_id and s_id not in existing_map:
                        new_obj = model(**item)
                        db.add(new_obj)
                        existing_map[s_id] = new_obj
                        new_objs.append(new_obj)
                if new_objs:
                    db.flush()
                return {s_id: obj.id for s_id, obj in existing_map.items()}

            subjects_db_map = get_or_create(Subject, parsed_data.get("subjects", []))
            
            # --- MANEJO INTELIGENTE DE DOCENTES (UPSERT v4) ---
            print("[XML_UPLOAD] Verificando docentes (UPSERT)...")
            teacher_list = parsed_data.get("teachers", [])
            teachers_db_map = {}
            for t_data in teacher_list:
                s_id = t_data.get("source_id")
                if not s_id: continue
                
                # 1. Buscar por source_id (Autoridad Final)
                existing = db.query(Teacher).filter(Teacher.source_id == s_id).first()
                if existing:
                    # Garantizar que apuntamos al Root Teacher si fue fusionado
                    root_id = repository.get_root_teacher_id(db, existing.id)
                    teachers_db_map[s_id] = root_id
                    continue
                
                # 2. Normalización v4.0 (Dual)
                norm_dict = normalize_teacher_name(t_data.get("last_name", ""), t_data.get("first_name", ""))
                norm = norm_dict["canonical"]
                match_key = norm_dict["match"]
                
                # 3. Match Exacto en Maestra (Solo no fusionados)
                existing_norm = repository.fetch_teacher_by_normalized(db, norm)
                if existing_norm:
                    print(f"[XML_UPLOAD] Teacher existente (Maestra Match Exacto): {norm}")
                    teachers_db_map[s_id] = existing_norm.id
                    continue

                # 4. Match FUZZY contra Maestra (v4.0 Hardened)
                print(f"[XML_UPLOAD] Intentando match FUZZY para: {norm}")
                raw_name = f"{t_data.get('last_name')}, {t_data.get('first_name')}"
                mdm_res = _get_fuzzy_match(db, norm, raw_name, search_match_key=match_key)
                
                decision = mdm_res.get("decision")
                match_id = mdm_res.get("match_id")

                if decision == "MATCH_AUTOMATICO" and match_id:
                    print(f"[XML_UPLOAD] Match AUTOMATICO encontrado -> Reutilizando ID {match_id}")
                    teachers_db_map[s_id] = match_id
                    continue

                # 5. DUDOSO o NO_MATCH -> Crear como SinAsignar (Registro temporal pero auditable)
                print(f"[XML_UPLOAD] Decisión MDM: {decision}. Creando en SinAsignar: {norm}")
                new_t = Teacher(**t_data)
                new_t.normalized_name = norm
                new_t.normalized_for_match = match_key
                new_t.is_assigned = False
                new_t.is_active = True
                new_t.times_detected = 1
                new_t.last_seen_at = datetime.now(timezone.utc)
                db.add(new_t)
                db.flush() # Importante: obtener new_t.id
                
                if decision == "MATCH_DUDOSO" and match_id:
                    # Crear registro obligatorio en cola de revisión (v4.2 con upload_id)
                    review_data = {
                        "xml_raw_name": raw_name,
                        "normalized_name": norm,
                        "candidate_id": match_id,
                        "xml_teacher_id": new_t.id,
                        "score": mdm_res.get("score"),
                        "decision": "MATCH_DUDOSO",
                        "request_id": request_id_ctx.get(),
                        "upload_id": new_upload.id, # Vínculo para métricas granulares
                        "xml_source_id": s_id,
                        "status": "PENDING"
                    }
                    review = repository.create_match_review(db, review_data)
                    new_t.match_review_id = review.id
                    print(json.dumps({
                        "event": "mdm_review_created",
                        "mdm_version": "v4.2",
                        "review_id": str(review.id),
                        "upload_id": str(new_upload.id),
                        "request_id": str(request_id_ctx.get()),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))

                teachers_db_map[s_id] = new_t.id
                db.flush()
            
            classes_db_map = get_or_create(ClassGroup, parsed_data.get("classes", []))
            
            mapped_lessons = []
            for lesson in parsed_data.get("lessons", []):
                for cid in lesson.get("class_ids", []):
                    mapped_lessons.append({
                        "source_id": f"{lesson.get('source_id')}_{cid}",
                        "subject_id": subjects_db_map.get(lesson.get("subject_id")),
                        "teacher_id": teachers_db_map.get(lesson.get("teacher_id")),
                        "class_id": classes_db_map.get(cid)
                    })
            lessons_db_map = get_or_create(Lesson, mapped_lessons)
            print("[XML_UPLOAD] Catálogos base (docentes, cursos, aulas) verificados/creados")

            subjects_map = {str(s["source_id"]): s["name"] for s in parsed_data["subjects"] if s.get("source_id")}

            periods_map = parsed_data.get("periods", {})
            print("[XML_UPLOAD] Generando sesiones (build_sessions)...")
            sessions = self.builder.build_sessions(
                periods_map,
                parsed_data.get("cards", []),
                parsed_data.get("lessons", []),
                subjects_map,
                start_date,
                end_date
            )
            print(f"[XML_UPLOAD] Sesiones generadas: {len(sessions)}")

            if not sessions:
                return {"success": False, "message": "No se generaron sesiones para el rango de fechas proporcionado."}

            # 5. Validar Existencia de Datos (Control de Duplicados por Rango)
            if not overwrite:
                existing_session = db.query(ScheduleSession).filter(
                    ScheduleSession.session_date >= start_date,
                    ScheduleSession.session_date <= end_date
                ).first()
                existing_payroll = db.query(RptPlanilla).filter(
                    RptPlanilla.fecha_clase >= start_date,
                    RptPlanilla.fecha_clase <= end_date
                ).first()

                if existing_session or existing_payroll:
                    return {
                        "success": False, 
                        "error_type": "DUPLICATE_RANGE",
                        "message": "Ya existen datos para estas fechas. Usa force_overwrite=true para reemplazarlos"
                    }

            # 6. Validar Conflictos
            conflicts = self.validator.check_conflicts(sessions)
            
            if conflicts and not overwrite:
                return {"success": False, "conflicts": conflicts, "message": "Conflictos detectados en el horario"}

            # 7. Limpieza en Overwrite: Eliminar registros existentes en el rango de fechas
            if overwrite:
                db.query(RptPlanilla).filter(
                    RptPlanilla.fecha_clase >= start_date,
                    RptPlanilla.fecha_clase <= end_date
                ).delete(synchronize_session=False)

                db.query(ScheduleSession).filter(
                    ScheduleSession.session_date >= start_date,
                    ScheduleSession.session_date <= end_date
                ).delete(synchronize_session=False)
                
                db.flush()

            # 8. Guardar sesiones en DB
            session_objects = []
            for s in sessions:
                real_lesson_id = lessons_db_map.get(s["lesson_id"])
                if not real_lesson_id: continue
                session_objects.append(ScheduleSession(
                    lesson_id=real_lesson_id,
                    session_date=s["session_date"],
                    start_time=s["start_time"],
                    end_time=s["end_time"],
                    status=s["status"]
                ))

            if session_objects:
                print(f"[XML_UPLOAD] Insertando {len(session_objects)} sesiones en DB...")
                db.bulk_save_objects(session_objects)
                db.flush()
                print("[XML_UPLOAD] Sesiones insertadas")

            # 7. Procesar Histórico de Planilla (RptPlanilla)
            payroll_records = []
            duplicate_errors = []
            
            # Obtener nombres directos estructurados desde el XML para evitar colisiones de source_id en BB.DD.
            xml_teachers = {str(t.get("source_id")): f"{t.get('first_name', '')} {t.get('last_name', '')}".strip() for t in parsed_data.get("teachers", []) if t.get("source_id")}
            xml_lessons = {str(l.get("source_id")): l for l in parsed_data.get("lessons", []) if l.get("source_id")}
            class_source_map = {str(c["source_id"]): c["name"] for c in parsed_data.get("classes", []) if c.get("source_id")}
            
            from datetime import time
            
            # Agrupar por docente, fecha y hora de inicio para lecciones unidas
            print("[XML_UPLOAD] Iniciando procesamiento de grouped_payroll...")
            grouped_payroll = {}

            for session in sessions:
                # 1. & 2. Card -> Lesson (Soporte para IDs compuestos)
                composite_id = str(session["lesson_id"])
                original_lesson_id = composite_id.split('_')[0]
                raw_lesson = xml_lessons.get(original_lesson_id)
                if not raw_lesson: continue

                # 3. & 4. Lesson -> Teacher -> Name
                teacher_id = raw_lesson.get("teacher_id")
                docente_name = xml_teachers.get(str(teacher_id), "N/A")
                
                if raw_lesson.get("raw_class_ids"):
                    cids = [c.strip() for c in raw_lesson["raw_class_ids"].split(",") if c.strip()]
                    ciclo_names = [self._extract_ciclo_code(class_source_map.get(cid, "N/A")) for cid in cids]
                    ciclo_name = " / ".join(ciclo_names) if ciclo_names else "N/A"
                else:
                    ciclo_name = "N/A"

                curso_clean = self._clean_curso(subjects_map.get(str(raw_lesson.get("subject_id")), "N/A"))

                # FILTRO: Omitir sesiones de RECESO, ALMUERZO, EXSE o EXSI
                if curso_clean.upper() in ["RECESO", "ALMUERZO", "EXSE", "EXSI"]:
                    continue

                sede_name = self._get_sede(ciclo_name)
                # Asegurar que la fecha sea un objeto date
                s_date = session["session_date"]
                if isinstance(s_date, str):
                    s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
                elif isinstance(s_date, datetime):
                    s_date = s_date.date()

                subject_name_raw = session.get("subject_name_raw", "")

                key = (docente_name, s_date, session["start_time"])
                if key not in grouped_payroll:
                    grouped_payroll[key] = {
                        "date": s_date,
                        "start_time": session["start_time"],
                        "end_time": session["end_time"],
                        "period": session.get("period", 0),
                        "docente_name": docente_name,
                        "ciclos": [ciclo_name],
                        "curso_clean": curso_clean,
                        "subject_name_raw": subject_name_raw
                    }
                else:
                    if ciclo_name not in grouped_payroll[key]["ciclos"]:
                        grouped_payroll[key]["ciclos"].append(ciclo_name)
                        
            # Paso 2: Agrupar por docente y fecha para cálculo global de recesos (estilo GAS)
            payroll_by_teacher_day = {}
            for data in grouped_payroll.values():
                t_key = (data["docente_name"], data["date"])
                if t_key not in payroll_by_teacher_day:
                    payroll_by_teacher_day[t_key] = []
                payroll_by_teacher_day[t_key].append(data)

            # Paso 3: Agrupar por docente, fecha, curso y ciclo para bloques finales
            blocks_by_class = {}
            for data in grouped_payroll.values():
                final_ciclo = " / ".join(data["ciclos"])
                b_key = (data["docente_name"], data["date"], data["curso_clean"], final_ciclo, data["subject_name_raw"])
                if b_key not in blocks_by_class:
                    blocks_by_class[b_key] = []
                blocks_by_class[b_key].append(data)
                
            print(f"[XML_UPLOAD] grouped_payroll listo. Grupos: {len(grouped_payroll)}")
            final_consolidated_blocks = []
            
            for b_key, period_list in blocks_by_class.items():
                docente_name, s_date, curso_clean, final_ciclo, subject_name_raw = b_key
                # Ordenar por numero de periodo cronologicamente
                period_list.sort(key=lambda x: int(x.get("period", 0)))
                
                merged_blocks = []
                current_block = None
                
                for p in period_list:
                    p_num = int(p.get("period", 0))
                    course = p["curso_clean"]
                    if current_block is None:
                        current_block = {
                            "min_period": p_num,
                            "max_period": p_num,
                            "periods": [p],
                            "real_class_count": 1,
                            "curso": course, 
                            "date": s_date 
                        }
                    else:
                        # Permitir puente de 1 periodo (el receso usual) si es el mismo curso y fecha
                        if current_block and course == current_block["curso"] and s_date == current_block["date"]:
                            if p_num <= current_block["max_period"] + 2: # Allow 1 period gap (e.g., P1, P2, P4 -> P1-P4)
                                current_block["max_period"] = p_num
                                current_block["periods"].append(p)
                                current_block["real_class_count"] += 1
                                continue
                        
                        # Si no es continuo o es un curso/fecha diferente, cerrar el bloque actual y empezar uno nuevo
                        merged_blocks.append(current_block)
                        current_block = {
                            "min_period": p_num,
                            "max_period": p_num,
                            "periods": [p],
                            "real_class_count": 1,
                            "curso": course,
                            "date": s_date
                        }
                if current_block:
                    merged_blocks.append(current_block)
                
                # Guardamos los bloques mergeados para este b_key para el paso de consolidación
                blocks_by_class[b_key] = merged_blocks

            print(f"[XML_UPLOAD] Consolidación terminada. Registros RPT a procesar...")
            
            # Pre-calcular el bloque más temprano para cada docente/día para evitar O(N^2)
            first_block_map = {}
            for b_key, merged_blocks in blocks_by_class.items():
                d_name, s_date = b_key[0], b_key[1]
                t_key = (d_name, s_date)
                for mb in merged_blocks:
                    # Usar el periodo mínimo como referencia de tiempo
                    b_start_time = periods_map.get(mb["min_period"])["start"]
                    if t_key not in first_block_map or b_start_time < first_block_map[t_key]["start"]:
                        first_block_map[t_key] = {"start": b_start_time, "b_key": b_key, "min_period": mb["min_period"]}

            for b_key, merged_blocks in blocks_by_class.items():
                docente_name, s_date, curso_clean, final_ciclo, subject_name_raw = b_key
                for mb in merged_blocks:
                    # Obtener base real de inicio y fin desde dictionaries
                    min_p = periods_map.get(mb["min_period"])
                    max_p = periods_map.get(mb["max_period"])
                    
                    if not min_p or not max_p: continue
                    
                    # Aplicar modificador robustamente
                    try:
                        modified_times = self.hour_modifier.apply_modifiers(
                            subject_name_raw, 
                            min_p["start"], 
                            max_p["end"]
                        )
                    except Exception as mod_err:
                        print(f"Error applying modifiers for {subject_name_raw}: {mod_err}")
                        modified_times = {"start_time": min_p["start"], "end_time": max_p["end"]}
                    
                    effective_horas = float(mb["real_class_count"])
                    
                    # --- NUEVA LÓGICA ESTILO GAS (break.gs) ---
                    b_start_1 = time(9, 40)
                    b_end_1 = time(10, 0)
                    b_start_2 = time(10, 30)
                    b_end_2 = time(10, 50)
                    b_end_3 = time(11, 40)
                    
                    t_key = (docente_name, s_date)
                    day_data = payroll_by_teacher_day.get(t_key, [])
                    # Restricción: Sin receso los sábados (5) y domingos (6)
                    if not day_data or s_date.weekday() >= 5:
                        receso_final = 0.0
                    else:
                        # 1. Encontrar el rango de trabajo total del docente en el día
                        d_start = min(datetime.strptime(str(d["start_time"]), "%H:%M:%S").time() for d in day_data)
                        d_finish = max(datetime.strptime(str(d["end_time"]), "%H:%M:%S").time() for d in day_data)
                        
                        # 2. Verificar cruce de marcadores de receso (Cualquier cruce = 0.33)
                        receso_detectado = False
                        
                        # Cruce Receso 1 (9:40 - 10:00)
                        if d_start <= b_start_1 and d_finish >= b_end_1:
                            receso_detectado = True
                            
                        # Cruce Receso 2 (10:30 - 10:50)
                        if d_start <= b_start_2 and d_finish >= b_end_2:
                            receso_detectado = True
                            
                        # Solo 0.33 o 0 según requerimiento (Columna H)
                        receso_final_day = 0.33 if receso_detectado else 0.0
                        
                        # 3. ASIGNACIÓN CRÍTICA: Solo al bloque más temprano del día
                        if t_key in first_block_map and b_key == first_block_map[t_key]["b_key"] and mb["min_period"] == first_block_map[t_key]["min_period"]:
                            receso_final = receso_final_day
                        else:
                            receso_final = 0.0
                    
                    final_sede = self._get_sede(final_ciclo)
                    
                    final_consolidated_blocks.append({
                        "date": s_date,
                        "docente_name": docente_name,
                        "curso_clean": curso_clean,
                        "ciclo": final_ciclo,
                        "sede": final_sede,
                        "start_time": modified_times["start_time"],
                        "end_time": modified_times["end_time"],
                        "horas": effective_horas,
                        "receso": Decimal(str(receso_final)),
                        "block_start_t": datetime.strptime(modified_times["start_time"], "%H:%M:%S").time(),
                        "block_end_t": datetime.strptime(modified_times["end_time"], "%H:%M:%S").time()
                    })


            # Insertar los consolidados en la Base de Datos
            for data in final_consolidated_blocks:
                
                # Validar duplicados SIEMPRE Y CUANDO NO se haya hecho overwrite (porque el overwrite ya limpió todo)
                if not overwrite:
                    existing_rpc = db.query(RptPlanilla).filter(
                        RptPlanilla.fecha_clase == data["date"],
                        RptPlanilla.docente == data["docente_name"],
                        RptPlanilla.hora_inicio == data["start_time"] # Unicidad garantizada por docente-fecha-hora
                    ).first()

                    if existing_rpc:
                        duplicate_errors.append(f"{data['ciclo']} - {data['docente_name']} ({data['date']} {data['start_time']})")
                        continue
                
                # Insertar nuevo registro (si es overwrite, la tabla ya está limpia para estas fechas)
                new_rpc = RptPlanilla(
                    fecha_clase=data["date"],
                    docente=data["docente_name"][:255],
                    horas_dictadas=data["horas"]
                )
                db.add(new_rpc)
                print(f"[XML_UPLOAD] RPT: Preparado registro para {data['docente_name']} en {data['date']}")

            if duplicate_errors and not overwrite:
                db.rollback()
                return {
                    "success": False, 
                    "conflicts": duplicate_errors, 
                    "message": "Registros duplicados detectados en el histórico de planilla"
                }

            # 8. Commit principal del upload
            print("[XML_UPLOAD] Realizando commit final...")
            db.commit()
            
            # Auditoría en DB
            db.add(AuditLog(
                usuario_id=user_id,
                accion="UPLOAD_XML"
            ))
            db.commit()
            
            print("[XML_UPLOAD] Proceso COMPLETADO exitosamente")

            # 9. Cruce automático XML → teachers_sinasignar (no crítico)
            cross_result = {}
            try:
                from app.modules.docentes.service import cross_check_xml_teachers
                xml_teacher_list = [
                    {"first_name": t.get("first_name", ""), "last_name": t.get("last_name", "")}
                    for t in parsed_data.get("teachers", [])
                ]
                cross_result = cross_check_xml_teachers(db, xml_teacher_list)
                print(f"[XML_UPLOAD] Cruce docentes: {cross_result.get('nuevos_sinasignar', 0)} nuevos en sinasignar")
            except Exception as cross_err:
                print(f"[XML_UPLOAD] WARN: cruce docentes falló (no crítico): {cross_err}")

            return {
                "success": True,
                "message": "Horarios y planilla histórica procesados exitosamente",
                "records": len(session_objects),
                "cross_check": cross_result,
            }

        except IntegrityError as ie:
            db.rollback()
            print(f"[XML_UPLOAD] FATAL: Error de integridad (posible duplicado): {ie}")
            return {
                "success": False, 
                "error_type": "INTEGRITY_ERROR",
                "message": "Error de integridad: El XML contiene datos (docentes/cursos) que ya existen con ID conflictivo.",
                "detail": str(ie.orig)
            }
        except Exception as e:
            db.rollback()
            err_msg = traceback.format_exc()
            print("ERROR IN PROCESS_UPLOAD:", err_msg)
            return {"success": False, "message": str(e) + " | Details: " + err_msg}
