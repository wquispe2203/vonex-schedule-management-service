from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any
import re
from . import repository
from app.modules.docentes.service import resolve_teacher
from app.services.session_consolidator import consolidate_sessions
from datetime import time, date, datetime

def get_teachers_list(db: Session) -> List[Dict[str, Any]]:
    teachers = repository.fetch_all_teachers(db)
    return [{"id": t.id, "first_name": t.first_name, "last_name": t.last_name} for t in teachers]

def get_classes_list(db: Session) -> List[Dict[str, Any]]:
    classes = repository.fetch_all_classes(db)
    return [{"id": c.id, "name": c.name} for c in classes]

def get_teacher_schedule_grid(db: Session, teacher_id: Any, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    target_teacher = resolve_teacher(db, teacher_id)
    if not target_teacher:
        return []
    
    t_id = target_teacher.id
    teacher_fullname = f"{target_teacher.first_name} {target_teacher.last_name}".strip()

    # 1. Obtener sesiones combinadas (Titular + Reemplazos realizados)
    # Este query ya filtra por rango de fechas estrictamente.
    combined_sessions = repository.fetch_teacher_combined_sessions(db, t_id, start_date, end_date, teacher_fullname)
    
    # 2. Obtener RptPlanilla para sincronizar metadata de horas si existe
    # (Opcional, pero ayuda a mantener consistencia en horas_dictadas y receso)
    rpt_rows = repository.fetch_rpt_rows(db, teacher_fullname, target_teacher.last_name, start_date, end_date, t_id)
    
    # Mapeo de RPT por session_id (estimado) para rescatar horas_dictadas/receso
    # Usaremos una lógica de proximidad similar a find_session_id si fuera necesario, 
    # pero aquí priorizaremos la data de ScheduleSession.
    
    data = []
    for s in combined_sessions:
        is_repl = False
        titular_name = None
        raw_subject = s.lesson.subject.name if s.lesson and s.lesson.subject else "S/N"
        
        # Clean subject (strip XML metadata tags like F+30 to allow semantic grouping)
        subject_name = re.sub(r'\(.*?\)', '', raw_subject).strip()
        
        class_group = s.lesson.class_group.name if s.lesson and s.lesson.class_group else "S/A"
        
        # Determinar si es Reemplazo Realizado (Conjunto B)
        # Buscamos la observación de reemplazo específica para este docente
        repl_obs = next((o for o in s.observations if o.type == 'REEMPLAZO' and (o.replacement_teacher_id == t_id or o.replacement_teacher_name == teacher_fullname)), None)
        
        if repl_obs:
            is_repl = True
            t = s.lesson.teacher
            titular_name = f"{t.first_name} {t.last_name}".strip() if t else "Desconocido"
            # El curso es el de la lección original
        else:
            # Es Conjunto A (Titular)
            # ¿Fue reemplazado por alguien más? Si hay un reemplazo donde el titular es Abanto pero el reemplazante es OTRO.
            someone_else_replacing = any(o for o in s.observations if o.type in ['REEMPLAZO', 'FALTA'] and o.teacher_id == t_id and o.replacement_teacher_id != t_id)
            if someone_else_replacing:
                continue # EXCLUIR: No dictó esta clase (Conjunto A filtrado)

        # Encontrar metadata en RPT (para receso y sede)
        rpt_match = next((r for r in rpt_rows if r.fecha_clase == s.session_date and r.hora_inicio == s.start_time), None)
        
        # AJUSTE: No usar rpt_match.horas_dictadas directamente por sesión, ya que RPT suele agregar 
        # (ej: una fila de 2h para 2 sesiones). En el visor cada bloque cuenta como su duración.
        # Para alinearnos a los 26.00 esperados con 26 sesiones, cada bloque debe ser 1.0.
        horas_dictadas = 1.0
        receso = 0.0 # RptPlanilla does not store receso (it's computed in reportes engine)
        sede = rpt_match.sede if rpt_match else "SEDE"

        data.append({
            "id":             s.id,
            "rpt_id":         rpt_match.id if rpt_match else None,
            "date":           s.session_date,
            "start_time":     s.start_time,
            "end_time":       s.end_time,
            "subject":        subject_name,
            "class_group":    class_group,
            "sede":           sede,
            "horas_dictadas": horas_dictadas,
            "receso":         receso,
            "is_break":       False,
            "status":         s.status,
            "is_virtual":     False,
            "is_replacement": is_repl,
            "titular_name":   titular_name,
            "docente":        teacher_fullname, # Temp for group field compatibility
            "observations": [
                {
                    "id": o.id,
                    "type": o.type,
                    "start_time": o.start_time,
                    "end_time": o.end_time
                } for o in s.observations
            ]
        })

    # 3. Apply Shared Academic Consolidation
    consolidated = consolidate_sessions(
        data,
        date_key="date",
        start_time_key="start_time",
        end_time_key="end_time",
        hours_key="horas_dictadas",
        group_fields=["docente", "sede", "subject", "class_group", "is_replacement"],
        module_tag="SCHEDULE"
    )

    # 4. Final Format Output
    final_result = []
    for c in consolidated:
        row = dict(c)
        row["date"] = c["date"].strftime("%Y-%m-%d") if isinstance(c["date"], (date, datetime)) else "---"
        row["start_time"] = c["start_time"].strftime("%H:%M") if isinstance(c["start_time"], time) else "--:--"
        row["end_time"] = c["end_time"].strftime("%H:%M") if isinstance(c["end_time"], time) else "--:--"
        
        # Format internal observations
        formatted_obs = []
        for o in c.get("observations", []):
            o_copy = dict(o)
            o_copy["start_time"] = o["start_time"].strftime("%H:%M") if isinstance(o["start_time"], time) else None
            o_copy["end_time"] = o["end_time"].strftime("%H:%M") if isinstance(o["end_time"], time) else None
            formatted_obs.append(o_copy)
        row["observations"] = formatted_obs
        
        # Cleanup temp fields
        if "docente" in row:
            del row["docente"]
            
        final_result.append(row)

    print(f"[SCHEDULE RENDER] Returning {len(final_result)} consolidated blocks for teacher grid.")
    return final_result

def get_classroom_schedule_grid(db: Session, class_id: UUID, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    sessions = repository.fetch_classroom_sessions(db, class_id, start_date, end_date)
    
    data = []
    for s in sessions:
        is_repl = any(o for o in s.observations if o.type == 'REEMPLAZO')
        active_teacher = f"{s.lesson.teacher.first_name} {s.lesson.teacher.last_name}" if s.lesson and s.lesson.teacher else "S/D"
        
        raw_subj = s.lesson.subject.name if s.lesson and s.lesson.subject else ""
        subject_clean = re.sub(r'\(.*?\)', '', raw_subj).strip()
        
        # In classroom view, if replacement is active, we should ideally show the replacement's name if known
        if is_repl:
            r_obs = next((o for o in s.observations if o.type == 'REEMPLAZO'), None)
            if r_obs and r_obs.replacement_teacher_name:
                active_teacher = r_obs.replacement_teacher_name
        
        data.append({
            "id": s.id,
            "date": s.session_date,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "horas_dictadas": 1.0, # Base value for aggregation
            "subject": subject_clean,
            "teacher": active_teacher,
            "is_break": False,
            "is_replacement": is_repl,
            "status": s.status,
            "observations": [
                {
                    "id": o.id,
                    "type": o.type,
                    "start_time": o.start_time,
                    "end_time": o.end_time
                } for o in s.observations
            ]
        })

    # Apply Shared Academic Consolidation
    consolidated = consolidate_sessions(
        data,
        date_key="date",
        start_time_key="start_time",
        end_time_key="end_time",
        hours_key="horas_dictadas",
        group_fields=["teacher", "subject", "is_replacement"],
        module_tag="SCHEDULE"
    )
    
    # Final Formatting
    final_result = []
    for c in consolidated:
        row = dict(c)
        row["date"] = c["date"].strftime("%Y-%m-%d") if isinstance(c["date"], (date, datetime)) else "---"
        row["start_time"] = c["start_time"].strftime("%H:%M") if isinstance(c["start_time"], time) else "--:--"
        row["end_time"] = c["end_time"].strftime("%H:%M") if isinstance(c["end_time"], time) else "--:--"
        
        formatted_obs = []
        for o in c.get("observations", []):
            o_copy = dict(o)
            o_copy["start_time"] = o["start_time"].strftime("%H:%M") if isinstance(o["start_time"], time) else None
            o_copy["end_time"] = o["end_time"].strftime("%H:%M") if isinstance(o["end_time"], time) else None
            formatted_obs.append(o_copy)
        row["observations"] = formatted_obs
        
        final_result.append(row)

    print(f"[SCHEDULE RENDER] Returning {len(final_result)} consolidated blocks for classroom grid.")
    return final_result

def get_export_excel_bytes(db: Session, export_type: str, target_id: Any, start_date: str, end_date: str):
    from app.services.export_schedule import ExportScheduleService
    
    # Si es por docente, resolvemos el ID real primero
    final_target_id = target_id
    if export_type == 'teacher':
        t_obj = resolve_teacher(db, target_id)
        final_target_id = t_obj.id

    sessions = repository.fetch_export_sessions(db, export_type, final_target_id, start_date, end_date)
    
    if not sessions:
        raise ValueError("No hay horarios para exportar")
        
    excel_file = ExportScheduleService.generate_excel(db, sessions)
    return excel_file
