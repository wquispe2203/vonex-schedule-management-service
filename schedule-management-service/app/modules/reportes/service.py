from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime, time
import pandas as pd
import io
from . import repository
from app.models import RptPlanilla, Teacher, Observation
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
    Lógica central de procesamiento de planillas — LÓGICA BINARIA.

    REGLAS DE NEGOCIO DEFINITIVAS:
      1. Titular con REEMPLAZO en el bloque → horas_dictadas = 0, receso = 0.
      2. Reemplazante → hereda horas_dictadas y receso COMPLETOS del bloque RPT.
      3. Los tiempos (hora_inicio / hora_fin) mostrados son SIEMPRE los del RPT original.
         Nunca los de la Observation.
      4. Un bloque RPT genera UNA SOLA fila de reemplazo.
         Clave de deduplicación: (rpt_record.id, session_id).
         Esto elimina duplicados incluso cuando hay múltiples Observations
         apuntando a la misma sesión o al mismo bloque.
    """

    # ------------------------------------------------------------------
    # 0. Tablas de lookup de docentes
    # ------------------------------------------------------------------
    teachers_raw = repository.fetch_teachers_lookup(db)
    name_to_id: Dict[str, int] = {}
    id_to_names: Dict[int, list] = {}
    
    for t_id, t_uid, t_fn, t_ln in teachers_raw:
        fn = (t_fn or "").strip().upper()
        ln = (t_ln or "").strip().upper()
        variants = [f"{fn} {ln}", f"{ln} {fn}"]
        for v in variants:
            name_to_id[v] = t_id
        id_to_names[t_id] = variants

    # Parsear filtro de docente activo
    target_docente_clean = target_docente.strip().upper() if target_docente and target_docente != "Todos" else None
    t_no_comma = target_docente_clean.replace(',', '').strip() if target_docente_clean else None
    t_parts = target_docente_clean.split(',') if target_docente_clean else []
    t_last  = t_parts[0].strip() if len(t_parts) >= 1 else t_no_comma
    t_first = t_parts[1].strip() if len(t_parts) >= 2 else ""

    # ------------------------------------------------------------------
    # 1. Cargar datos de contexto: sesiones + observaciones del rango
    # ------------------------------------------------------------------
    all_obs, sessions = repository.fetch_context_data(db, fecha_init, fecha_end, xml_upload_id)

    # Índice rápido: session_id → (date, start_time, end_time, teacher_id)
    session_info_by_id: Dict[int, tuple] = {
        s_id: (s_d, s_s, s_e, s_ltid)
        for s_id, s_d, s_s, s_e, s_ltid in sessions
    }

    # Índice: session_id → [Observation, ...]
    obs_by_session: Dict[int, list] = {}
    for obs in all_obs:
        obs_by_session.setdefault(obs.session_id, []).append(obs)

    # Índice espacial: (teacher_id, date) → lista de bloques {id, start, end}
    blocks_by_teacher_date: Dict[tuple, list] = {}
    for s_id, s_date, s_start, s_end, s_t_id in sessions:
        blocks_by_teacher_date.setdefault((s_t_id, s_date), []).append(
            {"id": s_id, "start": s_start, "end": s_end}
        )

    # ------------------------------------------------------------------
    # 2. Helpers internos
    # ------------------------------------------------------------------
    def find_session_id_for_row(t_id, r_date, r_start, r_end) -> Optional[int]:
        """Mapea un bloque RPT → ScheduleSession.id del titular."""
        if t_id is None or r_start is None or r_end is None:
            return None
        candidates = blocks_by_teacher_date.get((t_id, r_date), [])
        # Prioridad 1: tiempos exactos
        for blk in candidates:
            if blk["start"] == r_start and blk["end"] == r_end:
                return blk["id"]
        # Prioridad 2: inicio del RPT cae dentro del bloque
        for blk in candidates:
            if blk["start"] <= r_start < blk["end"]:
                return blk["id"]
        # Prioridad 3: bloque más cercano anterior
        eligible = [b for b in candidates if b["start"] <= r_start]
        if eligible:
            return max(eligible, key=lambda b: b["start"])["id"]
        return None

    def resolve_rpt_teacher_id(name: str) -> Optional[int]:
        name_upper = (name or "").strip().upper()
        tid = name_to_id.get(name_upper)
        if tid:
            return tid
        for k, v in name_to_id.items():
            if name_upper in k or k in name_upper:
                return v
        return None

    def obs_touches_block(o: Observation, r_start, r_end, r_session_id: Optional[int]) -> bool:
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

    # Pre-calcular session_id y teacher_id de cada fila RPT (evita N+1 en loops)
    rpt_to_session: Dict[int, Optional[int]] = {}
    rpt_to_teacher: Dict[int, Optional[int]] = {}
    for r in records:
        t_id = resolve_rpt_teacher_id(r.docente)
        
        r_s = getattr(r, 'hora_inicio', None)
        r_e = getattr(r, 'hora_fin', None)
        if r_e is None and r_s is not None:
            h_dictadas = float(getattr(r, 'horas_dictadas', 0))
            total_mins = r_s.hour * 60 + r_s.minute + int(h_dictadas * 50)
            r_e = time(int(total_mins // 60) % 24, int(total_mins % 60))
            
        s_id = find_session_id_for_row(t_id, getattr(r, 'fecha_clase', None), r_s, r_e)
        rpt_to_session[r.id] = s_id
        rpt_to_teacher[r.id] = t_id

    processed_data: List[Dict[str, Any]] = []

    # ==================================================================
    # FASE 1 — TITULARES
    # Regla binaria: cualquier REEMPLAZO que toque el bloque → 0 horas.
    # Tiempos mostrados = siempre los del RPT.
    # ==================================================================
    for r in records:
        r_start      = getattr(r, 'hora_inicio', None)
        r_end        = getattr(r, 'hora_fin', None)
        
        if r_end is None and r_start is not None:
            # Calcular hora_fin en base a horas_dictadas (1 hora dictada = 50 min)
            h_dictadas = float(getattr(r, 'horas_dictadas', 0))
            total_mins = r_start.hour * 60 + r_start.minute + int(h_dictadas * 50)
            r_end = time(int(total_mins // 60) % 24, int(total_mins % 60))

        r_date       = getattr(r, 'fecha_clase', None)
        r_teacher_id = rpt_to_teacher[r.id]
        r_session_id = rpt_to_session[r.id]

        orig_hours  = float(getattr(r, 'horas_dictadas', 0) or 0)
        orig_receso = float(getattr(r, 'receso', 0) or 0)

        # Observations que aplican a este bloque (solo por session_id exacto)
        relevant = [
            o for o in obs_by_session.get(r_session_id, [])
            if obs_touches_block(o, r_start, r_end, r_session_id)
        ] if r_session_id else []

        print(
            f"[F1] {r.docente} | {r_date} [{r_start}-{r_end}] | "
            f"session_id={r_session_id} | "
            f"obs=[{', '.join(str(o.id)+':'+o.type for o in relevant)}]"
        )

        # LÓGICA BINARIA
        has_replacement = any(o.type == 'REEMPLAZO' for o in relevant)
        has_absence     = any(o.type in ('FALTA', 'VACACIONES', 'DESCANSO_MEDICO') for o in relevant)

        if has_replacement or has_absence:
            net_hours  = 0.0
            net_receso = 0.0
        else:
            net_hours  = orig_hours
            net_receso = orig_receso

        print(f"  > replacement={has_replacement} absence={has_absence} > net_hours={net_hours}")

        # ¿Incluir esta fila según el filtro de docente?
        r_docente_up   = (r.docente or "").strip().upper()
        r_doc_no_comma = r_docente_up.replace(',', '').strip()
        if not matches_target(r_docente_up, r_doc_no_comma, r_teacher_id):
            continue

        block_obs_list = [{"id": o.id, "type": o.type, "description": o.description or ""} for o in relevant]
        block_repls    = [o.replacement_teacher_name or "" for o in relevant if o.type == 'REEMPLAZO']

        processed_data.append({
            "id":             r.id,
            "fecha_clase":    r_date,
            "sede":           r.sede or "---",
            "ciclo":          r.ciclo or "---",
            "docente":        r.docente or "",
            "curso":          r.curso or "---",
            "hora_inicio":    r_start,          # ← tiempos originales RPT
            "hora_fin":       r_end,             # ← tiempos originales RPT
            "horas_dictadas": max(0.0, round(net_hours, 2)),
            "receso":         max(0.0, round(net_receso, 2)),
            "is_replacement": False,
            "titular_original": None,
            "observation": {
                "type": ", ".join(sorted(set(x["type"] for x in block_obs_list))),
                "discount_type": "",
                "has_discount_impact": has_absence,
                "replacement_teacher_name": ", ".join(sorted(set(block_repls))),
                "description": " | ".join(sorted(set(
                    x["description"] for x in block_obs_list if x["description"]
                ))),
                "ids": [x["id"] for x in block_obs_list]
            } if block_obs_list else None
        })

    # ==================================================================
    # FASE 2 — REEMPLAZANTES
    # Regla binaria: una fila por (rpt_id, session_id).
    # Horas y recesos = 100% del bloque RPT del titular.
    # Tiempos = los del RPT titular (no los de la Observation).
    # ==================================================================
    injected_keys: set = set()       # (rpt_id, session_id) ya inyectado
    injected_records: List[Dict[str, Any]] = []

    for o in all_obs:
        if o.type != 'REEMPLAZO':
            continue

        repl_name_raw = o.replacement_teacher_name or ""
        repl_name_up  = repl_name_raw.strip().upper()
        repl_tid      = o.replacement_teacher_id or name_to_id.get(repl_name_up)
        repl_no_comma = repl_name_up.replace(',', '').strip()

        if not matches_target(repl_name_up, repl_no_comma, repl_tid):
            continue

        # Resolver fecha y titular a partir del session_id de la observation
        o_teacher_id = o.teacher_id
        o_date       = fecha_init  # fallback
        s_info = session_info_by_id.get(o.session_id)
        if s_info:
            o_date = s_info[0]
            if not o_teacher_id:
                o_teacher_id = s_info[3]

        true_titular_name = id_to_names.get(o_teacher_id, ["S/D"])[0]

        # Buscar el/los bloques RPT del TITULAR que corresponden a esta sesión
        # Prioridad 1: match exacto por session_id
        matching_rpt = [r for r in records
                        if r.fecha_clase == o_date and rpt_to_session[r.id] == o.session_id]

        # Prioridad 2 (fallback): overlap temporal si la obs tiene tiempos
        if not matching_rpt and o.start_time and o.end_time:
            matching_rpt = []
            for r in records:
                if getattr(r, 'fecha_clase', None) == o_date:
                    r_s = getattr(r, 'hora_inicio', None)
                    r_e = getattr(r, 'hora_fin', None)
                    if r_e is None and r_s is not None:
                        h_dictadas = float(getattr(r, 'horas_dictadas', 0))
                        total_mins = r_s.hour * 60 + r_s.minute + int(h_dictadas * 50)
                        r_e = time(int(total_mins // 60) % 24, int(total_mins % 60))
                    
                    if r_s and r_e and calculate_overlap_minutes(r_s, r_e, o.start_time, o.end_time) > 0:
                        matching_rpt.append(r)

        print(
            f"[F2] obs.id={o.id} | session={o.session_id} | {o_date} | "
            f"reemplazante={repl_name_raw} | matching_rpt={[r.id for r in matching_rpt]}"
        )

        if not matching_rpt:
            # Fallback absoluto: sin fila RPT de referencia
            if o.start_time and o.end_time:
                fb_key = (f"fb_{o.id}", o.session_id)
                if fb_key not in injected_keys:
                    injected_keys.add(fb_key)
                    mins = get_time_diff_minutes(o.start_time, o.end_time)
                    fb_hours = round(mins / 50.0, 2)
                    print(f"  > FALLBACK sin RPT: horas={fb_hours}")
                    injected_records.append({
                        "id":             f"repl_fb_{o.id}",
                        "fecha_clase":    o_date,
                        "sede":           "S/D",
                        "ciclo":          "S/D",
                        "docente":        repl_name_raw or "---",
                        "curso":          "S/D",
                        "hora_inicio":    o.start_time,
                        "hora_fin":       o.end_time,
                        "horas_dictadas": fb_hours,
                        "receso":         0.0,
                        "is_replacement": True,
                        "titular_original": true_titular_name,
                        "observation": {
                            "id": o.id, "type": "REEMPLAZO",
                            "discount_type": o.discount_type,
                            "has_discount_impact": False,
                            "replacement_teacher_name": "",
                            "description": f"Reemplazando a {true_titular_name}: {o.description or ''}"
                        }
                    })
            continue

        for best_r in matching_rpt:
            # ✅ DEDUPLICACIÓN SEMÁNTICA/VISUAL:
            # Usamos los valores exactos que se renderizarán en la fila.
            # Así, dos sub-sesiones de BD que forman el mismo bloque visual
            # no generarán dos filas idénticas para el reemplazante.
            best_r_s = getattr(best_r, 'hora_inicio', None)
            best_r_e = getattr(best_r, 'hora_fin', None)
            if best_r_e is None and best_r_s is not None:
                h_dictadas = float(getattr(best_r, 'horas_dictadas', 0))
                total_mins = best_r_s.hour * 60 + best_r_s.minute + int(h_dictadas * 50)
                best_r_e = time(int(total_mins // 60) % 24, int(total_mins % 60))

            dedup_key = (
                repl_name_raw.strip().upper(),
                getattr(best_r, 'fecha_clase', None),
                best_r_s,
                best_r_e,
                (getattr(best_r, 'ciclo', "") or "").strip()
            )
            if dedup_key in injected_keys:
                print(f"  > SKIP VISUAL-DUPLICADO: {dedup_key}")
                continue
            injected_keys.add(dedup_key)

            # ✅ HORAS BINARIAS: 100% del bloque RPT
            repl_hours  = float(getattr(best_r, 'horas_dictadas', 0) or 0)
            repl_receso = float(getattr(best_r, 'receso', 0) or 0)

            print(
                f"  > INJECT: rpt_id={best_r.id} "
                f"[{best_r_s}-{best_r_e}] "
                f"horas={repl_hours} receso={repl_receso} > {repl_name_raw}"
            )
            injected_records.append({
                "id":             f"repl_{best_r.id}_{o.id}",
                "fecha_clase":    getattr(best_r, 'fecha_clase', None),
                "sede":           best_r.sede or "---",
                "ciclo":          best_r.ciclo or "---",
                "docente":        repl_name_raw or "---",
                "curso":          best_r.curso or "---",
                "hora_inicio":    best_r_s,   # ← tiempos del RPT titular
                "hora_fin":       best_r_e,       # ← tiempos del RPT titular
                "horas_dictadas": round(repl_hours, 2),
                "receso":         round(repl_receso, 2),
                "is_replacement": True,
                "titular_original": true_titular_name,
                "observation": {
                    "id": o.id, "type": "REEMPLAZO",
                    "discount_type": o.discount_type,
                    "has_discount_impact": False,
                    "replacement_teacher_name": "",
                    "description": f"Reemplazando a {true_titular_name}: {o.description or ''}"
                }
            })

    processed_data.extend(injected_records)
    
    # ------------------------------------------------------------------
    # FASE 3 — CONSOLIDACIÓN DE BLOQUES CONTIGUOS Y RECESOS
    # ------------------------------------------------------------------
    consolidated: List[Dict[str, Any]] = []
    
    # Sort processed_data by date, teacher, sede, course, classroom, is_replacement, start_time
    sorted_for_merge = sorted(processed_data, key=lambda x: (
        x["fecha_clase"],
        (x["docente"] or "").strip().upper(),
        (x["sede"] or "").strip().upper(),
        (x["curso"] or "").strip().upper(),
        (x["ciclo"] or "").strip().upper(),
        x["is_replacement"],
        x["hora_inicio"]
    ))

    print("[RPT SESSION MERGE]")
    import logging
    logger = logging.getLogger(__name__)
    logger.info("[RPT SESSION MERGE] Starting contiguous block consolidation.")

    current_group: Optional[Dict[str, Any]] = None
    merged_count = 0

    for item in sorted_for_merge:
        # Print [RPT XML BLOCK] for every raw block
        print(f"[RPT XML BLOCK] Processing raw block: docente='{item['docente']}' | {item['hora_inicio']}-{item['hora_fin']} | curso='{item['curso']}' | ciclo='{item['ciclo']}' | hrs={item['horas_dictadas']}")
        
        if current_group is None:
            current_group = dict(item)
            current_group["receso"] = 0.0
            continue
            
        # Check continuity conditions
        same_date = current_group["fecha_clase"] == item["fecha_clase"]
        same_docente = (current_group["docente"] or "").strip().upper() == (item["docente"] or "").strip().upper()
        same_curso = (current_group["curso"] or "").strip().upper() == (item["curso"] or "").strip().upper()
        same_ciclo = (current_group["ciclo"] or "").strip().upper() == (item["ciclo"] or "").strip().upper()
        same_sede = (current_group["sede"] or "").strip().upper() == (item["sede"] or "").strip().upper()
        same_repl = current_group["is_replacement"] == item["is_replacement"]
        
        # Calculate time difference in minutes between previous end and current start
        gap_minutes = get_time_diff_minutes(current_group["hora_fin"], item["hora_inicio"])
        
        # We consolidate if they are consecutive or overlapping (gap <= 20 mins)
        is_consecutive = gap_minutes <= 20
        
        if same_date and same_docente and same_curso and same_ciclo and same_sede and same_repl and is_consecutive:
            prev_end = current_group["hora_fin"]
            if gap_minutes < 0:
                print(f"[RPT OVERLAP DETECTED] Overlap found for {item['docente']} between current {current_group['hora_inicio']}-{current_group['hora_fin']} and item {item['hora_inicio']}-{item['hora_fin']}")
            
            # Extend end time based on combined horas_dictadas to respect F+30 academic blocks
            current_group["horas_dictadas"] += item["horas_dictadas"]
            total_mins = current_group["hora_inicio"].hour * 60 + current_group["hora_inicio"].minute + int(current_group["horas_dictadas"] * 50)
            current_group["hora_fin"] = time(int(total_mins // 60) % 24, int(total_mins % 60))
            
            print(f"[RPT XML MERGED] Merged blocks for {item['docente']}: {current_group['hora_inicio']}-{prev_end} with {item['hora_inicio']}-{item['hora_fin']} => new end {current_group['hora_fin']} | total hrs: {current_group['horas_dictadas']}")
            logger.info(f"[RPT XML MERGED] Merging block for {current_group['docente']}: {current_group['hora_inicio']}->{prev_end} with {item['hora_inicio']}->{item['hora_fin']} => {current_group['hora_fin']}")
            
            # Merge observations if present
            if item.get("observation"):
                if not current_group.get("observation"):
                    current_group["observation"] = item["observation"]
                else:
                    current_group["observation"]["type"] = ", ".join(sorted(set(filter(None, [current_group["observation"]["type"], item["observation"]["type"]]))))
                    current_group["observation"]["description"] = " | ".join(sorted(set(filter(None, [current_group["observation"]["description"], item["observation"]["description"]]))))
                    current_group["observation"]["ids"].extend(item["observation"]["ids"])
            
            merged_count += 1
        else:
            consolidated.append(current_group)
            current_group = dict(item)
            current_group["receso"] = 0.0
            
    if current_group is not None:
        consolidated.append(current_group)

    # Print [RPT FINAL CONSOLIDATED] for every consolidated block
    for block in consolidated:
        print(f"[RPT FINAL CONSOLIDATED] Block consolidated: {block['docente']} | {block['hora_inicio']}-{block['hora_fin']} | hrs={block['horas_dictadas']}")

    # Set to keep track of applied breaks per teacher per day: (docente, fecha)
    applied_breaks = set()

    # Now calculate recess (receso) for each consolidated block based on official break windows
    for block in consolidated:
        docente = (block["docente"] or "").strip().upper()
        fecha = block["fecha_clase"]
        start_time = block["hora_inicio"]
        end_time = block["hora_fin"]
        
        print(f"[RPT BREAK WINDOW] Evaluating block {start_time}-{end_time} on {fecha} for teacher '{docente}'")
        
        # Check matching criteria
        crosses_break_1 = (
            start_time < time(9, 40)
            and end_time >= time(10, 0)
        )

        crosses_break_2 = (
            start_time < time(10, 30)
            and end_time >= time(10, 50)
        )

        reaches_final_cut = (
            start_time < time(11, 40)
            and end_time >= time(11, 40)
        )
        
        matched_break = crosses_break_1 or crosses_break_2
        matched_cut = reaches_final_cut
        
        if matched_break or matched_cut:
            if matched_break:
                print(f"[RPT BREAK MATCHED] Block {start_time}-{end_time} matches official break window.")
            if matched_cut:
                print(f"[RPT FINAL CUT] Block {start_time}-{end_time} reaches final cut 11:40.")
                
            teacher_day_key = (docente, fecha)
            if teacher_day_key in applied_breaks:
                print(f"[RPT SINGLE BREAK ENFORCED] Already applied break for {docente} on {fecha}. Skipping consecutive breaks.")
                block["receso"] = 0.00
            else:
                block["receso"] = 0.33
                applied_breaks.add(teacher_day_key)
                print(f"[RPT BREAK APPLIED] Recess of 0.33 applied to block {start_time}-{end_time} for {docente} on {fecha}.")
        else:
            block["receso"] = 0.00
            print(f"[RPT BREAK REJECTED] Block {start_time}-{end_time} does not match break criteria.")

    print(f"[RPT FINAL BLOCKS]\ntotal_final_blocks: {len(consolidated)}")
    logger.info(f"[RPT FINAL BLOCKS] total_final_blocks={len(consolidated)}")

    total_dictadas = sum(b["horas_dictadas"] for b in consolidated)
    total_receso = sum(b["receso"] for b in consolidated)
    print(f"[RPT TOTAL HOURS]\ntotal_dictadas: {total_dictadas}\ntotal_receso: {total_receso}")
    logger.info(f"[RPT TOTAL HOURS] total_dictadas={total_dictadas} total_receso={total_receso}")

    result = sorted(consolidated, key=lambda x: (x["fecha_clase"], x["hora_inicio"]))
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
