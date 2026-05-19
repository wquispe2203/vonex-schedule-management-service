from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime, time
import pandas as pd
import io
import logging
import re

logger = logging.getLogger(__name__)
from . import repository
from app.models import RptPlanilla, Teacher, Observation, RecessRule
from app.modules.docentes.service import resolve_teacher


def normalize_name(name: str) -> str:
    """
    Normaliza un nombre para comparación agnóstica al orden:
    - Minúsculas, sin comas, palabras ordenadas alfabéticamente.
    """
    if not name:
        return ""
    clean = name.lower().replace(',', ' ').strip()
    words = [w for w in clean.split() if w]
    words.sort()
    return " ".join(words)


def get_time_diff_minutes(t1, t2) -> int:
    if not t1 or not t2:
        return 0
    return (t2.hour * 60 + t2.minute) - (t1.hour * 60 + t1.minute)


def calculate_overlap_minutes(start1, end1, start2, end2) -> int:
    if not all([start1, end1, start2, end2]):
        return 0
    s1 = start1.hour * 60 + start1.minute
    e1 = end1.hour * 60 + end1.minute
    s2 = start2.hour * 60 + start2.minute
    e2 = end2.hour * 60 + end2.minute
    overlap_start = max(s1, s2)
    overlap_end   = min(e1, e2)
    return max(0, overlap_end - overlap_start)


from app.core.observability import rpt_logger, log_event
import time as time_lib

def process_rpt_logic(
    db: Session,
    records: List[RptPlanilla],
    fecha_init: date,
    fecha_end: date,
    target_docente: Optional[str] = None,
    target_teacher_id: Optional[int] = None,
    xml_upload_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lógica central de procesamiento de planillas - LÓGICA BINARIA.

    REGLAS DE NEGOCIO DEFINITIVAS:
      1. Titular con REEMPLAZO en el bloque -> horas_dictadas = 0, receso = 0.
      2. Reemplazante -> hereda horas_dictadas y receso COMPLETOS del bloque RPT.
      3. Los tiempos (hora_inicio / hora_fin) mostrados son SIEMPRE los del RPT original.
         Nunca los de la Observation.
      4. Un bloque RPT genera UNA SOLA fila de reemplazo.
         Clave de deduplicación: (rpt_record.id, session_id).
         Esto elimina duplicados incluso cuando hay múltiples Observations
         apuntando a la misma sesión o al mismo bloque.
    """
    start_perf = time_lib.perf_counter()
    print("[PERFORMANCE OPTIMIZATION ACTIVE] Surgical Consolidation Mode Engaged")
    log_event(rpt_logger, "INFO", "[RPT CONSOLIDATION START]", f"Processing {len(records)} records", {
        "range": f"{fecha_init} to {fecha_end}",
        "docente": target_docente,
        "xml_upload_id": xml_upload_id,
        "optimization": "active"
    })

    # ------------------------------------------------------------------
    # 0. Tablas de lookup de docentes
    # ------------------------------------------------------------------
    teachers_raw = repository.fetch_teachers_lookup(db)
    name_to_id: Dict[str, int] = {}
    clean_name_to_id: Dict[str, int] = {}
    id_to_names: Dict[int, list] = {}
    
    for t_id, t_uid, t_fn, t_ln in teachers_raw:
        fn = (t_fn or "").strip().upper()
        ln = (t_ln or "").strip().upper()
        variants = [f"{fn} {ln}", f"{ln} {fn}"]
        for v in variants:
            name_to_id[v] = t_id
            clean_name_to_id[v.replace(',', '').strip()] = t_id
        id_to_names[t_id] = variants
    
    print("[RPT HASHMAP ENABLED] Teacher Lookup Cache Build")

    # Parsear filtro de docente activo
    target_docente_clean = target_docente.strip().upper() if target_docente and target_docente != "Todos" else None
    t_no_comma = target_docente_clean.replace(',', '').strip() if target_docente_clean else None
    t_parts = target_docente_clean.split(',') if target_docente_clean else []
    t_last  = t_parts[0].strip() if len(t_parts) >= 1 else t_no_comma
    t_first = t_parts[1].strip() if len(t_parts) >= 2 else ""

    # ------------------------------------------------------------------
    # 1. Cargar datos de contexto: sesiones + observaciones del rango
    # [QUERY CACHE HIT] Passing pre-calculated u_ids if available from outer scope
    all_obs, sessions = repository.fetch_context_data(
        db, fecha_init, fecha_end, xml_upload_id, pre_fetched_u_ids=getattr(db, "_rpt_active_u_ids", None)
    )

    # Índice rápido: session_id → (date, start_time, end_time, teacher_id, subject_name, class_group_name)
    session_info_by_id: Dict[int, tuple] = {
        row[0]: row
        for row in sessions
    }

    # Índice: session_id → [Observation, ...]
    obs_by_session: Dict[int, list] = {}
    for obs in all_obs:
        obs_by_session.setdefault(obs.session_id, []).append(obs)

    # Índice espacial: (teacher_id, date) → lista de bloques {id, start, end}
    blocks_by_teacher_date: Dict[tuple, list] = {}
    for s_id, s_date, s_start, s_end, s_t_id, s_subj, s_class in sessions:
        blocks_by_teacher_date.setdefault((s_t_id, s_date), []).append(
            {"id": s_id, "start": s_start, "end": s_end}
        )

    # Nuevo Índice Espacial Absoluto para Observaciones por (Docente/Nombre, Fecha)
    # Esto previene el escape geométrico si una observación multi-bloque se ató solo al primer session_id.
    obs_by_teacher_date: Dict[tuple, list] = {}
    for obs in all_obs:
        s_info = session_info_by_id.get(obs.session_id)
        if not s_info:
            continue
        o_date = s_info[1]
        
        # 1. Indexar por Titular ID
        if obs.teacher_id:
            obs_by_teacher_date.setdefault((obs.teacher_id, o_date), []).append(obs)
            
        # 2. Indexar por Nombre Normalizado del Titular (Resiliencia)
        tit_names = id_to_names.get(obs.teacher_id, [])
        for n in tit_names:
            obs_by_teacher_date.setdefault((n.upper(), o_date), []).append(obs)
            
        # 3. Indexar por Reemplazante ID si existe (para que figure en su reporte)
        if obs.replacement_teacher_id:
            obs_by_teacher_date.setdefault((obs.replacement_teacher_id, o_date), []).append(obs)
            
        # 4. Indexar por Nombre del Reemplazante textual
        if obs.replacement_teacher_name:
            rn_clean = obs.replacement_teacher_name.strip().upper()
            obs_by_teacher_date.setdefault((rn_clean, o_date), []).append(obs)

    # ------------------------------------------------------------------
    # 2. Helpers internos
    # ------------------------------------------------------------------
    def normalize_hours(val) -> float:
        return round(float(val or 0), 2)

    def find_session_ids_for_row(t_id, r_date, r_start, r_end) -> List[Any]:
        """Mapea un bloque RPT a TODAS las ScheduleSession.id del titular que se solapan."""
        if t_id is None or r_start is None or r_end is None:
            return []
        candidates = blocks_by_teacher_date.get((t_id, r_date), [])
        # Encontrar todas las sesiones que intersectan el rango temporal del RPT
        return [
            b["id"] for b in candidates
            if b["start"] < r_end and b["end"] > r_start
        ]

    def resolve_rpt_teacher_id(name: str) -> Optional[int]:
        name_upper = (name or "").strip().upper()
        name_clean = name_upper.replace(',', '').strip()
        
        # 1. Intentar exacto o sin comas (O(1) lookup)
        tid = name_to_id.get(name_upper) or clean_name_to_id.get(name_clean)
        if tid:
            return tid
            
        # 2. Fallback iterativo resiliente (Solo si el hash falló)
        for k_clean, v in clean_name_to_id.items():
            if name_clean in k_clean or k_clean in name_clean:
                return v
        return None

    def obs_touches_block(o: Observation, r_start, r_end, r_session_id: Optional[Any]) -> bool:
        """
        ¿La observation aplica a este bloque RPT?
        - Con tiempos propios → verificar overlap temporal positivo.
        - Sin tiempos       → match por session_id exacto.
        """
        if o.start_time and o.end_time:
            return calculate_overlap_minutes(r_start, r_end, o.start_time, o.end_time) > 0
        return o.session_id == r_session_id

    def matches_target(name_up: str, no_comma: str, tid: Optional[int]) -> bool:
        """¿Este nombre / id coincide con el filtro de búsqueda activo?"""
        if not target_docente_clean:
            return True
        if target_teacher_id and tid == target_teacher_id:
            return True
        if t_first and t_last:
            if (f"{t_last} {t_first}" in no_comma) or (f"{t_first} {t_last}" in no_comma):
                return True
        if t_no_comma and (
            t_no_comma in no_comma
            or target_docente_clean in name_up
            or name_up in target_docente_clean
        ):
            return True
        return False

    # ------------------------------------------------------------------
    # Pre-calcular session_ids y teacher_id de cada fila RPT (evita N+1)
    # ------------------------------------------------------------------
    rpt_to_sessions: Dict[int, List[Any]] = {}
    rpt_to_teacher: Dict[int, Optional[int]] = {}
    
    for r in records:
        t_id = resolve_rpt_teacher_id(r.docente)
        
        r_s = getattr(r, 'hora_inicio', None)
        r_e = getattr(r, 'hora_fin', None)
        if r_e is None and r_s is not None:
            h_dictadas = float(getattr(r, 'horas_dictadas', 0))
            total_mins = r_s.hour * 60 + r_s.minute + int(h_dictadas * 50)
            r_e = time(int(total_mins // 60) % 24, int(total_mins % 60))
            
        # CORRECCIÓN CRÍTICA: Recuperar TODAS las sesiones vinculadas
        session_ids = find_session_ids_for_row(t_id, getattr(r, 'fecha_clase', None), r_s, r_e)
        rpt_to_sessions[r.id] = session_ids
        rpt_to_teacher[r.id] = t_id

    processed_data: List[Dict[str, Any]] = []
    used_obs_ids = set()  # Rastrear IDs de observaciones consumidas por bloques RPT existentes

    # ==================================================================
    # FASE 1 — SPLIT GEOMÉTRICO Y VIRTUAL OVERLAYS (HARDENED)
    # ==================================================================
    for r in records:
        r_start = getattr(r, 'hora_inicio', None)
        r_end   = getattr(r, 'hora_fin', None)
        
        if r_end is None and r_start is not None:
            h_dictadas = float(getattr(r, 'horas_dictadas', 0))
            total_mins = r_start.hour * 60 + r_start.minute + int(h_dictadas * 50)
            r_end = time(int(total_mins // 60) % 24, int(total_mins % 60))
            
        r_date       = getattr(r, 'fecha_clase', None)
        r_teacher_id = rpt_to_teacher.get(r.id)
        r_sess_ids   = rpt_to_sessions.get(r.id, [])
        
        # Identificar TODAS las observaciones que tocan este bloque recolectando de múltiples sesiones
        relevant = []
        seen_obs_in_block = set()
        # AHORA: Cosecha espacial absoluta. Buscar en todas las observaciones registradas
        # para este docente o nombre ese día, y filtrar por intersección geométrica.
        candidates = []
        if r_teacher_id:
            candidates = obs_by_teacher_date.get((r_teacher_id, r_date), [])
            
        # Fallback Resiliente por Nombre Textual (por si el mapeo de IDs no cuadró)
        r_doc_clean = (r.docente or "").strip().upper().replace(',', '').strip()
        if r_doc_clean:
            for c_obs in obs_by_teacher_date.get((r_doc_clean, r_date), []):
                if c_obs not in candidates:
                    candidates.append(c_obs)
                    
        # --- ALINEACIÓN / SNAPPING DE TIEMPOS DE OBSERVACIONES ---
        import copy
        snapped_candidates = []
        
        # Recolectar intervalos RPT de este docente el día de hoy
        def get_rpt_teacher_id(docente_str):
            if not docente_str:
                return None
            norm = (docente_str or "").strip().upper()
            norm_clean = norm.replace(',', '').strip()
            return name_to_id.get(norm) or name_to_id.get(norm_clean) or clean_name_to_id.get(norm_clean)

        day_records = [
            x for x in records 
            if getattr(x, 'fecha_clase', None) == r_date 
            and get_rpt_teacher_id(x.docente) == r_teacher_id
        ]
        
        rpt_intervals = []
        for dr in day_records:
            dr_s = getattr(dr, 'hora_inicio', None)
            dr_e = getattr(dr, 'hora_fin', None)
            if dr_e is None and dr_s is not None:
                h_dict = float(getattr(dr, 'horas_dictadas', 0))
                t_mins = dr_s.hour * 60 + dr_s.minute + int(h_dict * 50)
                dr_e = time(int(t_mins // 60) % 24, int(t_mins % 60))
            if dr_s and dr_e:
                rpt_intervals.append((dr_s, dr_e))
                
        for o in candidates:
            if not o.start_time or not o.end_time:
                snapped_candidates.append(o)
                continue
                
            o_copy = copy.copy(o)
            o_start_mins = o.start_time.hour * 60 + o.start_time.minute
            o_end_mins = o.end_time.hour * 60 + o.end_time.minute
            
            best_match = None
            min_diff = 9999
            
            for r_start_t, r_end_t in rpt_intervals:
                r_start_mins = r_start_t.hour * 60 + r_start_t.minute
                r_end_mins = r_end_t.hour * 60 + r_end_t.minute
                
                diff_start = abs(o_start_mins - r_start_mins)
                diff_end = abs(o_end_mins - r_end_mins)
                
                # Tolerancia de hasta 35 minutos de diferencia en ambos extremos
                if diff_start <= 35 and diff_end <= 35:
                    total_diff = diff_start + diff_end
                    if total_diff < min_diff:
                        min_diff = total_diff
                        best_match = (r_start_t, r_end_t)
                        
            if best_match:
                o_copy.start_time = best_match[0]
                o_copy.end_time = best_match[1]
                
            snapped_candidates.append(o_copy)
                    
        for o in snapped_candidates:
            if o.id not in seen_obs_in_block and obs_touches_block(o, r_start, r_end, None):
                relevant.append(o)
                seen_obs_in_block.add(o.id)

        orig_h = normalize_hours(getattr(r, 'horas_dictadas', 0))
        block_tit_h = 0.0
        block_repl_h = 0.0
        block_absent_h = 0.0

        # -- CASO SIMPLE: Sin observaciones
        if not relevant:
            titular_name_up = (r.docente or "").strip().upper()
            titular_no_comma = titular_name_up.replace(',', '').strip()
            
            if matches_target(titular_name_up, titular_no_comma, r_teacher_id):
                processed_data.append({
                    "id":             r.id,
                    "fecha_clase":    r_date,
                    "sede":           r.sede or "---",
                    "ciclo":          r.ciclo or "---",
                    "docente":        r.docente or "",
                    "curso":          r.curso or "---",
                    "hora_inicio":    r_start,
                    "hora_fin":       r_end,
                    "horas_dictadas": normalize_hours(r.horas_dictadas),
                    "receso":         0.0,
                    "is_replacement": False,
                    "titular_original": None,
                    "observation":    None,
                    "obs_type":       "NORMAL"
                })
            print(f"[RPT CONSERVATION CHECK] Teacher={r.docente} | Original={orig_h} Derived={orig_h} | Status=OK (No Obs)")
            continue

        # -- CASO COMPLEJO: Fragmentación Geométrica del bloque
        # Sanitizar timestamps para evitar errores en el sorteador de boundaries
        if not r_start or not r_end:
            # Si no hay tiempos, no podemos fragmentar ni evaluar recesos.
            # Solo agregamos el registro tal cual si coincide con el filtro.
            tit_name_up = (r.docente or "").strip().upper()
            tit_no_comma = tit_name_up.replace(',', '').strip()
            if matches_target(tit_name_up, tit_no_comma, r_teacher_id):
                processed_data.append({
                    "id":             r.id,
                    "fecha_clase":    r_date,
                    "sede":           r.sede or "---",
                    "ciclo":          r.ciclo or "---",
                    "docente":        r.docente or "",
                    "curso":          r.curso or "---",
                    "hora_inicio":    r_start,
                    "hora_fin":       r_end,
                    "horas_dictadas": normalize_hours(r.horas_dictadas),
                    "receso":         0.0,
                    "is_replacement": False,
                    "titular_original": None,
                    "observation":    None,
                    "obs_type":       "DEGRADED_NO_TIME"
                })
            continue

        boundaries = set()
        if r_start: boundaries.add(r_start)
        if r_end: boundaries.add(r_end)
        
        for o in relevant:
            o_s = o.start_time or r_start
            o_e = o.end_time or r_end
            if r_start and o_s and r_start < o_s < r_end:
                boundaries.add(o_s)
            if r_end and o_e and r_start < o_e < r_end:
                boundaries.add(o_e)
        
        sorted_bounds = sorted(list(boundaries))
        # print(f"[RPT GEOMETRIC SPLIT] {r.docente} | Block {r_start}-{r_end} sliced into {len(sorted_bounds)-1} segments.")

        for i in range(len(sorted_bounds) - 1):
            seg_s = sorted_bounds[i]
            seg_e = sorted_bounds[i+1]
            
            mins = get_time_diff_minutes(seg_s, seg_e)
            if mins <= 0:
                continue
            # Normalización explícita de payroll
            seg_hours = normalize_hours(mins / 50.0)
            
            active_repl = None
            active_abs  = None
            
            for o in relevant:
                o_s = o.start_time or r_start
                o_e = o.end_time or r_end
                # Overlap inclusion check
                if o_s <= seg_s and o_e >= seg_e:
                    if o.type == 'REEMPLAZO':
                        active_repl = o
                    elif o.type in ('FALTA', 'VACACIONES', 'DESCANSO_MEDICO'):
                        active_abs = o
            
            winner = active_repl or active_abs
            if winner:
                used_obs_ids.add(winner.id)
                if winner.type == 'REEMPLAZO':
                    block_repl_h += seg_hours
                else:
                    block_absent_h += seg_hours
            else:
                block_tit_h += seg_hours
            
            # A) Registrar para el TITULAR
            tit_name_up = (r.docente or "").strip().upper()
            tit_no_comma = tit_name_up.replace(',', '').strip()
            
            if matches_target(tit_name_up, tit_no_comma, r_teacher_id):
                tit_hours = 0.0 if winner else seg_hours
                
                obs_meta = None
                if winner:
                    obs_meta = {
                        "type": winner.type,
                        "discount_type": getattr(winner, 'discount_type', 'SIMPLE') or 'SIMPLE',
                        "has_discount_impact": winner.type != 'REEMPLAZO',
                        "replacement_teacher_name": winner.replacement_teacher_name if winner.type == 'REEMPLAZO' else None,
                        "description": winner.description or "",
                        "ids": [winner.id]
                    }
                
                processed_data.append({
                    "id":             r.id,
                    "fecha_clase":    r_date,
                    "sede":           r.sede or "---",
                    "ciclo":          r.ciclo or "---",
                    "docente":        r.docente or "",
                    "curso":          r.curso or "---",
                    "hora_inicio":    seg_s,
                    "hora_fin":       seg_e,
                    "horas_dictadas": tit_hours,
                    "receso":         0.0,
                    "is_replacement": False,
                    "titular_original": None,
                    "observation":    obs_meta,
                    "obs_type":       winner.type if winner else "NORMAL"
                })
            
            # B) Registrar para el REEMPLAZANTE (si aplica)
            if active_repl:
                rn_raw = active_repl.replacement_teacher_name or "DOCENTE EXTERNO"
                rn_up  = rn_raw.strip().upper()
                rn_no  = rn_up.replace(',', '').strip()
                rn_tid = active_repl.replacement_teacher_id or name_to_id.get(rn_up)
                
                if matches_target(rn_up, rn_no, rn_tid):
                    true_tit = id_to_names.get(r_teacher_id, [r.docente or "S/D"])[0]
                    processed_data.append({
                        "id":             f"repl_{r.id}_{active_repl.id}",
                        "fecha_clase":    r_date,
                        "sede":           r.sede or "---",
                        "ciclo":          r.ciclo or "---",
                        "docente":        rn_raw,
                        "curso":          r.curso or "---",
                        "hora_inicio":    seg_s,
                        "hora_fin":       seg_e,
                        "horas_dictadas": seg_hours,
                        "receso":         0.0,
                        "is_replacement": True,
                        "titular_original": true_tit,
                        "observation": {
                            "id": active_repl.id,
                            "type": "REEMPLAZO",
                            "discount_type": getattr(active_repl, 'discount_type', 'SIMPLE') or 'SIMPLE',
                            "has_discount_impact": False,
                            "replacement_teacher_name": rn_raw,
                            "description": f"Reemplazo a {r.docente}: {active_repl.description or ''}",
                            "ids": [active_repl.id]
                        },
                        "obs_type": "REEMPLAZO"
                    })

        # C) CÁLCULO DE CONSERVACIÓN MATEMÁTICA POR BLOQUE
        # derived_h = normalize_hours(block_tit_h + block_repl_h + block_absent_h)
        # drift = abs(orig_h - derived_h)
        # c_status = "OK" if drift <= 0.01 else "FAIL"
        # print(f"[RPT CONSERVATION CHECK] Teacher={r.docente} | Original={orig_h} Derived={derived_h} (Tit={block_tit_h}, Repl={block_repl_h}, Abs={block_absent_h}) | Status={c_status}")

    # ==================================================================
    # FASE 2 — FALLBACK OBSERVACIONES FLOTANTES
    # ==================================================================
    for o in all_obs:
        if o.type != 'REEMPLAZO' or o.id in used_obs_ids:
            continue
            
        rn_raw = o.replacement_teacher_name or "DOCENTE EXTERNO"
        rn_up  = rn_raw.strip().upper()
        rn_no  = rn_up.replace(',', '').strip()
        rn_tid = o.replacement_teacher_id or name_to_id.get(rn_up)
        
        if not matches_target(rn_up, rn_no, rn_tid):
            continue
            
        if not o.start_time or not o.end_time:
            continue
            
        fallback_date = fecha_init
        f_sede = "S/D"
        f_ciclo = "S/D"
        f_curso = "S/D"
        
        s_info = session_info_by_id.get(o.session_id)
        if s_info:
            fallback_date = s_info[1]
            s_subj = s_info[5]
            s_class = s_info[6]
            
            if s_subj:
                f_curso = re.sub(r'\(.*?\)', '', str(s_subj)).strip()
            
            if s_class:
                class_str = str(s_class)
                c_match = re.search(r'\((.*?)\)', class_str)
                ext_code = c_match.group(1).strip() if c_match else class_str.strip()
                f_ciclo = ext_code
                
                c_code = ext_code.split('/')[0].strip()
                if len(c_code) >= 2:
                    pen_char = c_code[-2].upper()
                    sed_map = {
                        '1': 'LIMA CERCADO', '2': 'SJL BASADRE', '3': 'INDEPENDENCIA',
                        '4': '2 DE MAYO', '5': 'CONSTITUCION', '6': 'CRESPO Y CASTILLO',
                        '8': 'SANTA ANITA', '9': 'COMAS', 'Z': 'PUENTE PIEDRA',
                        'Y': 'SJL LOS JARDINES', 'X': 'VMT'
                    }
                    f_sede = sed_map.get(pen_char, "DESCONOCIDA")

        f_mins = get_time_diff_minutes(o.start_time, o.end_time)
        if f_mins <= 0:
            continue
        f_hours = normalize_hours(f_mins / 50.0)
        
        true_tit = id_to_names.get(o.teacher_id, ["S/D"])[0]
        
        processed_data.append({
            "id":             f"repl_fb_{o.id}",
            "fecha_clase":    fallback_date,
            "sede":           f_sede,
            "ciclo":          f_ciclo,
            "docente":        rn_raw,
            "curso":          f_curso,
            "hora_inicio":    o.start_time,
            "hora_fin":       o.end_time,
            "horas_dictadas": f_hours,
            "receso":         0.0,
            "is_replacement": True,
            "titular_original": true_tit,
            "observation": {
                "id": o.id,
                "type": "REEMPLAZO",
                "discount_type": getattr(o, 'discount_type', 'SIMPLE') or 'SIMPLE',
                "has_discount_impact": False,
                "replacement_teacher_name": rn_raw,
                "description": f"Reemplazo Flotante de {true_tit}: {o.description or ''}",
                "ids": [o.id]
            },
            "obs_type": "REEMPLAZO"
        })

    # ------------------------------------------------------------------
    # FASE 3 — CONSOLIDACIÓN DE BLOQUES CONTIGUOS Y RECESOS
    # ------------------------------------------------------------------
    consolidated: List[Dict[str, Any]] = []
    
    # Sort processed_data by date, teacher, sede, course, classroom, is_replacement, start_time
    from app.services.session_consolidator import consolidate_sessions
    consolidated = consolidate_sessions(
        processed_data,
        date_key="fecha_clase",
        start_time_key="hora_inicio",
        end_time_key="hora_fin",
        hours_key="horas_dictadas",
        group_fields=["docente", "sede", "curso", "ciclo", "is_replacement", "obs_type"],
        module_tag="RPT"
    )
    
    # Initialize receso default before window validation
    for c in consolidated:
        if "receso" not in c:
            c["receso"] = 0.0

    # for block in consolidated:
    #     print(f"[RPT FINAL CONSOLIDATED] Block consolidated: {block['docente']} | {block['hora_inicio']}-{block['hora_fin']} | hrs={block['horas_dictadas']}")

    # [RPT BREAK SHIFT] Garantizar orden temporal estricto por docente antes de evaluar recesos
    consolidated.sort(key=lambda x: (x["fecha_clase"], (x["docente"] or "").strip().upper(), x["hora_inicio"]))
    
    # Construir índice temporal por día para detección de continuidad pedagógica
    timeline_by_day: Dict[tuple, list] = {}
    for b in consolidated:
        k = ((b["docente"] or "").strip().upper(), b["fecha_clase"])
        timeline_by_day.setdefault(k, []).append(b)

    # Set to keep track of applied breaks per teacher per day: (docente, fecha)
    applied_breaks = set()
    
    # [RPT HASHMAP ENABLED] Pre-calculating replacement lookup map for O(1) transfer
    # Key: (fecha, start_time, end_time), Value: list of replacement blocks
    replacement_lookup: Dict[tuple, list] = {}
    for b in consolidated:
        if b.get("is_replacement"):
            k = (b["fecha_clase"], b["hora_inicio"], b["hora_fin"])
            replacement_lookup.setdefault(k, []).append(b)
    
    print("[RPT HASHMAP ENABLED] Recess Transfer Map Build")

    # ------------------------------------------------------------------
    # 3. CARGA HÍBRIDA DE REGLAS DE RECESO
    # ------------------------------------------------------------------
    try:
        db_rules = db.query(RecessRule).filter(RecessRule.is_active == True).all()
        if not db_rules:
            print("[RECESS DB EMPTY] No active rules found in DB. Engaging hardcoded fallback.")
            recess_rules = None
        else:
            recess_rules = []
            for r in db_rules:
                try:
                    h_s, m_s = map(int, r.start_time.split(":")[:2])
                    h_e, m_e = map(int, r.end_time.split(":")[:2])
                    recess_rules.append({
                        "name": r.name,
                        "start": time(h_s, m_s),
                        "end": time(h_e, m_e),
                        "value": round(r.deduction_value / 100.0, 2)
                    })
                except Exception as pe:
                    print(f"[RECESS RULE PARSE ERROR] Error parsing rule {r.name}: {pe}")
            
            if recess_rules:
                print(f"[RECESS RULES LOADED] {len(recess_rules)} rules active from DB.")
            else:
                recess_rules = None
    except Exception as dbe:
        print(f"[RECESS FALLBACK ACTIVATED] DB error fetching recess rules: {dbe}. Using hardcoded parity.")
        recess_rules = None

    # FALLBACK HARCODED (REGLA DE ORO: NO ROMPER RPT)
    if not recess_rules:
        recess_rules = [
            {"name": "RECESO 1", "start": time(9, 40), "end": time(10, 0), "value": 0.33},
            {"name": "RECESO 2", "start": time(10, 30), "end": time(10, 50), "value": 0.33},
            {"name": "RECESO 3", "start": time(11, 20), "end": time(11, 40), "value": 0.33},
        ]

    for block in consolidated:
        # [RPT BREAK SHIELD] Si el bloque ya posee crédito por transferencia previa, blindarlo de sobre-escritura
        if float(block.get("receso", 0.0)) > 0.0:
            print(f"[RPT BREAK SHIELD] Block already possesses transferred recess credit. Safeguarding value.")
            continue

        docente = (block["docente"] or "").strip().upper()
        fecha = block["fecha_clase"]
        start_time = block["hora_inicio"]
        end_time = block["hora_fin"]
        
        # DEFENSIVE: Skip if times are missing (legacy records)
        if not start_time or not end_time:
            block["receso"] = 0.0
            continue

        print(f"[RPT BREAK WINDOW] Evaluating block {start_time}-{end_time} on {fecha} for teacher '{docente}'")
        
        # Excluir fines de semana (Regla Académica)
        if fecha.weekday() in (5, 6):
            continue
        
        # Identificar el siguiente bloque cronológico para evaluar continuidad (O(1) index access)
        teacher_key = (docente, fecha)
        day_blocks = timeline_by_day.get(teacher_key, [])
        next_start = None
        
        # En vez de .index(block), iteramos sobre day_blocks una vez o mantenemos un puntero si fuera necesario.
        # Dado que day_blocks suele ser pequeño (2-4 bloques/día), el impacto de index es menor que en consolidated
        # pero optimizamos igual usando el hecho de que consolidated está ordenado.
        try:
            curr_idx = -1
            for idx, b in enumerate(day_blocks):
                if b is block: # Identity check is fast
                    curr_idx = idx
                    break
            
            if curr_idx != -1 and curr_idx < len(day_blocks) - 1:
                next_b = day_blocks[curr_idx + 1]
                next_start = next_b["hora_inicio"]
        except (ValueError, IndexError):
            next_start = None

        # Validar ventana razonable de continuidad (Máximo 13:00 hrs para tramo mañana/mediodía)
        LIMIT_CONTINUITY = time(13, 0)
        is_within_window = False
        if next_start and next_start <= LIMIT_CONTINUITY:
            is_within_window = True

        # Evaluar reglas de receso (Híbrido)
        matched_rule = None
        for rule in recess_rules:
            # Caso A: El bloque cruza el receso (Ej: 8:00 - 11:00)
            crosses = (start_time < rule["start"] and end_time >= rule["end"])
            # Caso B: El bloque termina justo donde empieza el receso y hay continuidad (Ej: 8:00 - 9:40)
            is_prev = (end_time == rule["start"] and is_within_window)
            
            if crosses or is_prev:
                matched_rule = rule
                break

        # Mantener "Final Cut" legacy (Regla de 11:40) por compatibilidad
        reaches_final_cut = (start_time < time(11, 40) and end_time >= time(11, 40))
        
        if matched_rule or reaches_final_cut:
            teacher_day_key = (docente, fecha)
            if teacher_day_key in applied_breaks:
                continue
            
            # applied_breaks.add(teacher_day_key) # Mover abajo para permitir transferencias
            
            # Valor del receso (Priorizar regla sobre final cut legacy si ambas coinciden)
            break_val = matched_rule["value"] if matched_rule else 0.33
            
            # -- NUEVA LOGICA DE TRANSFERENCIA POR OBSERVACIONES (O(1) lookup) --
            if float(block.get("horas_dictadas", 0.0)) <= 0.0:
                block["receso"] = 0.0
                o_type = block.get("obs_type")
                
                if o_type == "REEMPLAZO":
                    # Usar el lookup map en lugar de escanear 'consolidated' (O(1) vs O(N))
                    target_key = (fecha, start_time, end_time)
                    targets = replacement_lookup.get(target_key, [])
                    
                    for target in targets:
                        tgt_name = (target["docente"] or "").strip().upper()
                        tgt_key = (tgt_name, fecha)
                        if tgt_key in applied_breaks:
                            continue
                        
                        target["receso"] = break_val
                        applied_breaks.add(tgt_key)
                        applied_breaks.add(teacher_day_key) # Marcar original como "break applied"
                        # logger.debug(f"[RPT BREAK TRANSFER] Transferred {break_val} from {docente} to {tgt_name}")
                        break
            else:
                # Caso normal: el docente trabajó físicamente sus horas.
                block["receso"] = break_val
                applied_breaks.add(teacher_day_key)
                # print(f"[RPT BREAK APPLIED] Recess of {break_val} applied to block {start_time}-{end_time} for {docente} on {fecha}.")
        else:
            block["receso"] = 0.00
            print(f"[RPT BREAK REJECTED] Block {start_time}-{end_time} does not match break criteria.")

    print(f"[RPT FINAL BLOCKS]\ntotal_final_blocks: {len(consolidated)}")
    logger.info(f"[RPT FINAL BLOCKS] total_final_blocks={len(consolidated)}")

    result = sorted(consolidated, key=lambda x: (x["fecha_clase"], x["hora_inicio"]))
    
    total_dictadas = sum(float(b.get("horas_dictadas", 0.0)) for b in result)
    total_receso = sum(float(b.get("receso", 0.0)) for b in result)
    
    duration_ms = int((time_lib.perf_counter() - start_perf) * 1000)
    log_event(rpt_logger, "INFO", "[RPT CONSOLIDATION SUCCESS]", f"Processed {len(result)} consolidated blocks", {
        "duration_ms": duration_ms,
        "total_dictadas": round(total_dictadas, 2),
        "total_receso": round(total_receso, 2)
    })
    
    return result


def get_planilla_data(
    db: Session,
    fecha_inicio: date,
    fecha_fin: date,
    docente: Optional[str] = None,
    sede: Optional[str] = None,
    aula: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    xml_upload_id: Optional[str] = None
):
    """Obtiene la data completa del reporte (JSON)."""

    # 1. Resolver docente target
    target_id = None
    replacement_session_ids = []
    if docente and docente != "Todos":
        # Validar si docente es un UUID
        from uuid import UUID
        try:
            target_uuid = UUID(docente)
            t_obj = resolve_teacher(db, target_uuid)
            target_id = t_obj.id if t_obj else None
            if t_obj:
                docente = f"{t_obj.last_name}, {t_obj.first_name}"
        except ValueError:
            # Fallback a búsqueda flexible por nombre
            t = repository.fetch_teacher_by_name_flexible(db, docente)
            target_id = t.id if t else None
        
        replacement_session_ids = repository.fetch_replacement_sessions_ids(db, target_id or docente, docente)

    # [QUERY CACHE HIT] Fetch active uploads ONCE for the entire request scope
    from app.models import XmlUpload
    active_uploads = (
        db.query(XmlUpload)
        .filter(
            XmlUpload.status == "COMPLETED",
            XmlUpload.start_date <= fecha_fin,
            XmlUpload.end_date >= fecha_inicio
        )
        .order_by(XmlUpload.created_at.desc())
        .all()
    )
    db._rpt_active_u_ids = [u.id for u in active_uploads]
    
    # 2. Obtener registros base de RPT
    all_filtered_rpt = repository.fetch_rpt_records(db, fecha_inicio, fecha_fin, sede, aula, xml_upload_id)

    if docente and docente != "Todos":
        doc_norm = normalize_name(docente)

        # Titulares: comparar nombre normalizado
        titular_recs = [
            r for r in all_filtered_rpt
            if (lambda rn: doc_norm == rn or doc_norm in rn or rn in doc_norm)(normalize_name(r.docente))
        ]
        titular_ids = {r.id for r in titular_recs}

        # Reemplazos: filas RPT del titular cuya sesión fue reemplazada por el docente buscado
        repl_titular_recs = []
        if replacement_session_ids:
            sessions_info = repository.fetch_sessions_info(db, replacement_session_ids, fecha_inicio, fecha_fin)
            teachers_map = {
                t[0]: [f"{t[1]} {t[2]}".upper(), f"{t[2]} {t[1]}".upper()]
                for t in repository.fetch_teachers_lookup(db)
            }
            for si_date, si_start, si_end, si_tid in sessions_info:
                names = teachers_map.get(si_tid, [])
                for r in all_filtered_rpt:
                    if r.id in titular_ids:
                        continue
                        
                    r_s = getattr(r, 'hora_inicio', None)
                    r_e = getattr(r, 'hora_fin', None)
                    if r_e is None and r_s is not None:
                        h_dictadas = float(getattr(r, 'horas_dictadas', 0))
                        total_mins = r_s.hour * 60 + r_s.minute + int(h_dictadas * 50)
                        r_e = time(int(total_mins // 60) % 24, int(total_mins % 60))

                    if (getattr(r, 'fecha_clase', None) == si_date
                            and r_s and r_e
                            and r_s < si_end
                            and r_e > si_start
                            and any(n in (r.docente or "").upper() for n in names)):
                        repl_titular_recs.append(r)
                        titular_ids.add(r.id)

        records_to_process = sorted(
            titular_recs + repl_titular_recs,
            key=lambda x: (x.fecha_clase, x.hora_inicio)
        )
    else:
        records_to_process = all_filtered_rpt

    # 3. Procesar lógica completa ANTES de paginar
    full_processed_list = process_rpt_logic(
        db, records_to_process, fecha_inicio, fecha_fin, docente, target_id, xml_upload_id
    )

    # 4. Totales
    total_hours_sum  = sum(d["horas_dictadas"] for d in full_processed_list)
    total_receso_sum = sum(d["receso"] for d in full_processed_list)
    total_records    = len(full_processed_list)

    # 5. Paginación
    total_pages = max(1, (total_records + limit - 1) // limit)
    start_idx   = (page - 1) * limit
    end_idx     = start_idx + limit
    paginated   = full_processed_list[start_idx:end_idx]

    result = []
    for d in paginated:
        row = d.copy()
        row["fecha_clase"] = (
            d["fecha_clase"].strftime("%Y-%m-%d")
            if isinstance(d["fecha_clase"], (date, datetime))
            else str(d["fecha_clase"])
        )
        row["hora_inicio"] = (
            d["hora_inicio"].strftime("%H:%M:%S")
            if isinstance(d["hora_inicio"], (time, datetime))
            else str(d["hora_inicio"])
        )
        row["hora_fin"] = (
            d["hora_fin"].strftime("%H:%M:%S")
            if isinstance(d["hora_fin"], (time, datetime))
            else str(d["hora_fin"])
        )
        result.append(row)

    return {
        "success": True,
        "data": {
            "data": result,
            "total": total_records,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_hours_sum": round(total_hours_sum, 2),
            "total_receso_count": round(total_receso_sum / 0.33, 1) if total_receso_sum > 0 else 0
        },
        "error": None
    }


def generate_excel_file(data: List[Dict[str, Any]]) -> io.BytesIO:
    """Genera archivo Excel a partir de la data procesada."""
    df_data = []
    for r in data:
        obs = r.get("observation")
        info_extra = ""
        if r.get("is_replacement"):
            info_extra = f"[REEMPLAZO DE {r.get('titular_original')}]"
        elif obs:
            info_extra = f"[{obs.get('type')}]"

        df_data.append({
            "Fecha":        r["fecha_clase"],
            "Sede":         r["sede"],
            "Ciclo/Aula":   r["ciclo"],
            "Docente":      r["docente"],
            "Curso":        r["curso"],
            "Inicio":       r["hora_inicio"],
            "Fin":          r["hora_fin"],
            "Horas Acad.":  r["horas_dictadas"],
            "Receso":       r["receso"],
            "Observación":  f"{info_extra} {obs['description'] if obs else ''}".strip()
        })

    df = pd.DataFrame(df_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Planilla')
    output.seek(0)
    return output
