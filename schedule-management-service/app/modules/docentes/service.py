"""
Service del módulo DOCENTES — v2 completo.
Lógica de negocio: normalización, UPSERT Excel, cruce XML, reprocesamiento histórico + fuzzy.
"""
import logging
import unicodedata
import re
import time as time_lib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session

import os
import json
from . import repository
from app.models import Teacher
from app.modules.observaciones import repository as obs_repo
from sqlalchemy import or_
from uuid import UUID

logger = logging.getLogger(__name__)

EVIDENCE_FILE = r"D:\Desktop\MOD HOR\schedule-management-service\mdm_evidence.json"

# --- CONSTANTES DE NORMALIZACIÓN v4 ---
ABBREVIATIONS = {
    "M.": "MARIA",
    "MZA.": "MARIA",
    "Mª": "MARIA",
    "FCO.": "FRANCISCO",
    "J.": "JOSE",
    "L.": "LUIS",
    "P.": "PEDRO",
    "R.": "RICARDO",
    "C.": "CARLOS",
    "A.": "ALBERTO",
    "FNDZ.": "FERNANDEZ",
    "GZ.": "GONZALEZ",
    "MTZ.": "MARTINEZ",
    "RZ.": "RODRIGUEZ",
}

PARTICLES = {"DE", "DEL", "LA", "LAS", "LO", "LOS", "Y"}
TITLES = {"PROF.", "LIC.", "DR.", "DRA.", "ING.", "MAG."}

def log_mdm_evidence(data: Dict[str, Any]):
    try:
        current_evidence = []
        if os.path.exists(EVIDENCE_FILE):
            with open(EVIDENCE_FILE, "r", encoding="utf-8") as f:
                current_evidence = json.load(f)
        
        from app.core.context import request_id_ctx
        current_evidence.append({
            **data,
            "request_id": request_id_ctx.get(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        with open(EVIDENCE_FILE, "w", encoding="utf-8") as f:
            json.dump(current_evidence, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error guardando evidencia MDM: {e}")


from app.core.config import settings
def resolve_teacher(db: Session, identifier: UUID) -> Teacher:
    """
    Resuelve un docente por ID (UUID) de manera estricta.
    Retorna el modelo Teacher o levanta un error si no lo encuentra.
    """
    if not identifier:
        raise ValueError("Identificador de docente no proporcionado")
    
    t = repository.fetch_teacher_by_id_full(db, identifier)
    if t:
        return t
        
    raise ValueError(f"No se encontró docente con el integrador UUID: {identifier}")


# ════════════════════════════════════════════════════════
#  NORMALIZACIÓN
# ════════════════════════════════════════════════════════

def normalize_teacher_name(apellidos: str, nombres: str) -> Dict[str, str]:
    """
    Normalización Dual (v4.0):
    1. canonical: [Paterno] [Materno] [Nombres] - Limpio pero legible.
    2. match: Versión sin partículas y tokens ordenados.
    """
    raw_ap = (apellidos or "").upper().strip()
    raw_nom = (nombres or "").upper().strip()
    
    all_text = f"{raw_ap} {raw_nom}"
    
    # Quitar tildes
    nfkd = unicodedata.normalize("NFKD", all_text)
    txt = "".join(c for c in nfkd if not unicodedata.combining(c))
    
    # Limpieza básica
    txt = re.sub(r"[,;.]", " ", txt) # Puntos se quitan para tokens pero ojo con M.
    # Re-evaluación: Si queremos expandir abrev, mejor no quitar puntos aún.
    
    # Mejor flujo:
    def preprocess(s: str) -> List[str]:
        # Expandir abreviaturas
        tokens = s.replace(",", " ").split()
        expanded = []
        for t in tokens:
            upper_t = t.upper()
            if upper_t in ABBREVIATIONS:
                expanded.append(ABBREVIATIONS[upper_t])
            elif upper_t.endswith(".") and upper_t in ABBREVIATIONS: # Doble chequeo
                 expanded.append(ABBREVIATIONS[upper_t])
            elif upper_t in TITLES:
                continue
            else:
                if len(upper_t) <= 2 and upper_t.endswith("."):
                    logger.warning(f"MDM_NORM: Abreviatura desconocida detectada: {upper_t}")
                expanded.append(upper_t)
        return expanded

    # 1. Canonical: Mantener estructura original limpia
    canonical_tokens = preprocess(f"{raw_ap} {raw_nom}")
    canonical = " ".join(canonical_tokens)
    
    # 2. Match Key: Quitar partículas y ordenar
    match_tokens = [t for t in canonical_tokens if t not in PARTICLES]
    match_tokens.sort()
    match_key = " ".join(match_tokens)
    
    return {
        "canonical": canonical.lower(),
        "match": match_key.lower()
    }


def normalize_single(name: str) -> str:
    """Fallback para compatibilidad legacy."""
    res = normalize_teacher_name(name, "")
    return res["canonical"]


def _fuzzy_ratio(a: str, b: str) -> float:
    """Ratio de similitud 0-100. Usa rapidfuzz si está instalado; fallback a difflib."""
    try:
        from rapidfuzz import fuzz
        return fuzz.ratio(a, b)
    except ImportError:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a, b).ratio() * 100


# ════════════════════════════════════════════════════════
#  FUNCIÓN EXISTENTE — INTOCABLE
# ════════════════════════════════════════════════════════

def get_active_teachers_list(db: Session) -> List[str]:
    """Aplica la lógica de negocio para agrupar y formatear los nombres."""
    try:
        active_teachers_query = repository.fetch_active_teachers(db)
        return _format_teacher_list(active_teachers_query)
    except Exception as e:
        raise RuntimeError(f"Error procesando docentes activos: {str(e)}")


def get_active_teachers_for_rpt(db: Session) -> List[str]:
    """REGLA v3.10: Docentes visibles en el reporte (Solo Activos + Con carga)."""
    try:
        active_teachers_query = repository.fetch_active_teachers_for_rpt(db)
        return _format_teacher_list(active_teachers_query)
    except Exception as e:
        raise RuntimeError(f"Error procesando docentes para RPT: {str(e)}")


def _format_teacher_list(teachers_query) -> List[str]:
    unique_names = set()
    grouped_by_last_name = {}

    for t in teachers_query:
        fn = (t.first_name or "").strip().upper()
        ln = (t.last_name or "").strip().upper()
        formatted = f"{ln}, {fn}"
        unique_names.add(formatted)

    for name in unique_names:
        parts = name.split(",")
        if len(parts) >= 2:
            last_names = parts[0].strip()
            first_names = parts[1].strip()
            if last_names not in grouped_by_last_name:
                grouped_by_last_name[last_names] = name
            else:
                if len(first_names) > len(grouped_by_last_name[last_names].split(",")[1].strip()):
                    grouped_by_last_name[last_names] = name
        else:
            grouped_by_last_name[name] = name

    final_list = list(grouped_by_last_name.values())
    final_list.sort()
    return final_list


# ════════════════════════════════════════════════════════
#  MAESTRA — CRUD DE TEACHERS
# ════════════════════════════════════════════════════════

def _teacher_to_dict(t: Teacher, active_ids: set = None) -> Dict[str, Any]:
    # Detectamos si 'id' es UUID o legacy
    t_id_str = str(t.id)
    legacy_id = getattr(t, 'legacy_id', None)

    return {
        "id": t_id_str, # Siempre UUID en la nueva arquitectura
        "legacy_id": legacy_id,
        "source_id": t.source_id,
        "first_name": t.first_name or "",
        "last_name": t.last_name or "",
        "short_name": t.short_name or "",
        "dni": t.dni or "",
        "razon_social": t.razon_social or "",
        "normalized_name": t.normalized_name or "",
        "is_active": t.is_active,
        "is_assigned": getattr(t, 'is_assigned', True),
        "possible_duplicate": getattr(t, 'possible_duplicate', False),
        "times_detected": getattr(t, 'times_detected', 0),
        "last_seen_at": t.last_seen_at.strftime("%Y-%m-%d") if getattr(t, 'last_seen_at', None) else "",
        "is_active_by_workload": (t.id in active_ids) if active_ids is not None else False,
    }


def get_all_teachers(
    db: Session,
    filter_mode: str = "all",
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    status_filter: Optional[str] = None, # acts, inacts
) -> Dict[str, Any]:
    result = repository.fetch_all_teachers_paginated(db, filter_mode, search, page, limit, status_filter)
    active_ids = {t.id for t in repository.fetch_active_teachers(db)}
    return {
        "success": True,
        "data": [_teacher_to_dict(t, active_ids) for t in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "total_pages": result["total_pages"],
    }


def create_teacher_manual(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
    apellidos = (payload.get("last_name") or "").strip()
    nombres   = (payload.get("first_name") or "").strip()
    dni       = (payload.get("dni") or "").strip() or None
    norm      = normalize_teacher_name(apellidos, nombres)

    if dni:
        existing = repository.fetch_teacher_by_dni(db, dni)
        if existing:
            raise ValueError(f"Ya existe un docente con DNI {dni} (id={existing.id})")

    existing = repository.fetch_teacher_by_normalized(db, norm)
    if existing:
        raise ValueError(f"Ya existe un docente similar: {existing.last_name} {existing.first_name}")

    data = {
        "source_id":       f"MANUAL_{int(time_lib.time())}",
        "first_name":      nombres,
        "last_name":       apellidos,
        "short_name":      payload.get("short_name", ""),
        "dni":             dni,
        "razon_social":    (payload.get("razon_social") or "").strip() or None,
        "normalized_name": norm,
    }
    t = repository.create_teacher(db, data)
    db.commit()
    return _teacher_to_dict(t)


def update_teacher_data(db: Session, teacher_id: UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
    t = resolve_teacher(db, teacher_id)
    if not t:
        raise ValueError("Docente no encontrado")

    apellidos = (payload.get("last_name") or t.last_name or "").strip()
    nombres   = (payload.get("first_name") or t.first_name or "").strip()
    norm      = normalize_teacher_name(apellidos, nombres)

    updated = repository.update_teacher(db, t, {
        "first_name":      nombres,
        "last_name":       apellidos,
        "short_name":      payload.get("short_name", t.short_name or ""),
        "dni":             (payload.get("dni") or "").strip() or None,
        "razon_social":    (payload.get("razon_social") or "").strip() or None,
        "normalized_name": norm,
    })
    db.commit()
    return _teacher_to_dict(updated)


def update_teacher_status(db: Session, teacher_id: UUID, is_active: bool) -> Dict[str, Any]:
    """Actualiza solo el campo is_active."""
    t = resolve_teacher(db, teacher_id)
    if not t:
        raise ValueError("Docente no encontrado")
    
    updated = repository.update_teacher(db, t, {"is_active": is_active})
    db.commit()
    return _teacher_to_dict(updated)


def get_teacher_activity_info(db: Session, teacher_id: UUID) -> Dict[str, bool]:
    """Retorna si el docente tiene actividad para el modal de advertencia v3.10."""
    t = resolve_teacher(db, teacher_id)
    return repository.check_teacher_activity(db, t.id)


# ════════════════════════════════════════════════════════
#  EXCEL IMPORT (openpyxl, sin pandas)
# ════════════════════════════════════════════════════════

def import_excel(db: Session, file_bytes: bytes) -> Dict[str, Any]:
    import openpyxl, io
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active

    headers_raw = [str(ws.cell(1, c).value or "").strip().upper() for c in range(1, ws.max_column + 1)]
    col_map: Dict[str, int] = {}
    ALIASES = {
        "DNI":          ["DNI", "RUC", "DOCUMENTO"],
        "APELLIDOS":    ["APELLIDOS", "APELLIDO", "LAST_NAME"],
        "NOMBRES":      ["NOMBRES", "NOMBRE", "FIRST_NAME"],
        "RAZON_SOCIAL": ["RAZON SOCIAL", "RAZÓN SOCIAL", "RAZON_SOCIAL", "EMPRESA"],
    }
    for canonical, aliases in ALIASES.items():
        for idx, h in enumerate(headers_raw, start=1):
            if h in aliases:
                col_map[canonical] = idx
                break

    if "APELLIDOS" not in col_map or "NOMBRES" not in col_map:
        raise ValueError("El archivo debe tener columnas APELLIDOS y NOMBRES como mínimo.")

    rows_preview, inserted, updated, skipped = [], 0, 0, 0

    try:
        for row_idx in range(2, ws.max_row + 1):
            def cell(key):
                idx = col_map.get(key)
                if idx is None:
                    return ""
                val = ws.cell(row_idx, idx).value
                return str(val).strip() if val is not None else ""

            apellidos    = cell("APELLIDOS")
            nombres      = cell("NOMBRES")
            dni          = cell("DNI") or None
            razon_social = cell("RAZON_SOCIAL") or None

            if not apellidos and not nombres:
                continue

            norm_dict = normalize_teacher_name(apellidos, nombres)
            norm = norm_dict["canonical"]
            match_key = norm_dict["match"]

            existing: Optional[Teacher] = None
            if dni:
                existing = repository.fetch_teacher_by_dni(db, dni)
            if not existing:
                existing = repository.fetch_teacher_by_normalized(db, norm)

            if existing:
                repository.update_teacher(db, existing, {
                    "first_name":      nombres,
                    "last_name":       apellidos,
                    "dni":             dni,
                    "razon_social":    razon_social,
                    "normalized_name": norm,
                    "normalized_for_match": match_key
                })
                updated += 1
                action = "updated"
            else:
                repository.create_teacher(db, {
                    "source_id":       f"EXCEL_{int(time_lib.time())}_{row_idx}",
                    "first_name":      nombres,
                    "last_name":       apellidos,
                    "short_name":      "",
                    "dni":             dni,
                    "razon_social":    razon_social,
                    "normalized_name": norm,
                    "normalized_for_match": match_key
                })
                inserted += 1
                action = "inserted"

            rows_preview.append({
                "row":          row_idx,
                "apellidos":    apellidos,
                "nombres":      nombres,
                "dni":          dni or "",
                "razon_social": razon_social or "",
                "normalized_name": norm,
                "action":       action,
            })

        db.commit()
        return {"success": True, "inserted": inserted, "updated": updated, "skipped": skipped, "rows": rows_preview}

    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Error importando Excel: {str(e)}")


def _get_fuzzy_match(db: Session, norm: str, original_name: str = "N/A", search_match_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Motor de búsqueda endurecido (v4.0):
    1. Filtro por prefijo y longitud sobre 'normalized_for_match'.
    2. Regla de Protección: Comparación separada Apellido vs Nombre en forma canónica.
    3. Retorno estructurado con auditoría JSON en stdout.
    """
    default_res = {"decision": "NO_MATCH", "match_id": None, "score": 0, "candidate_name": None}
    if not norm or len(norm) < 2: return default_res
    
    from app.core.context import request_id_ctx
    req_id = request_id_ctx.get()

    # Si no nos pasan la match_key, la calculamos (para compatibilidad)
    if not search_match_key:
        search_match_key = normalize_teacher_name(norm, "")["match"]
    
    match_key = search_match_key
    min_l = int(len(match_key) * 0.8)
    max_l = int(len(match_key) * 1.2)
    
    # fetch_fuzzy_candidates retorna List[Tuple[UUID, str, str]] -> (id, canonical, match_key)
    candidates = repository.fetch_fuzzy_candidates(db, match_key, min_l, max_l)
    
    if not candidates:
        ev = {
            "event": "teacher_matching",
            "xml_name": original_name,
            "normalized_name": norm,
            "candidate": None,
            "score": 0,
            "decision": "NO_MATCH",
            "request_id": req_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        print(json.dumps(ev))
        log_mdm_evidence(ev)
        return default_res

    best_candidate_id = None
    best_candidate_name = None
    max_score = 0
    final_decision = "NO_MATCH"

    # Preparar componentes del nombre de búsqueda (Canonical)
    search_parts = norm.split(' ', 1)
    s_ln = search_parts[0]
    s_fn = search_parts[1] if len(search_parts) > 1 else ""

    FUZZY_THRESHOLD = settings.FUZZY_THRESHOLD # 90-95 generalmente

    for c_id, cand_norm, cand_match_key in candidates:
        # Comparación global sobre Match Key (sin partículas, tokens ordenados)
        global_score = _fuzzy_ratio(match_key, cand_match_key)
        
        # Regla de Protección Estricta sobre Canonical
        is_hardened_dudoso = False
        cand_parts = cand_norm.split(' ', 1)
        c_ln = cand_parts[0]
        c_fn = cand_parts[1] if len(cand_parts) > 1 else ""
        
        # Protección: Si apellidos coinciden pero nombres no
        if len(s_fn) > 3 and s_ln and c_ln:
            ln_sim = _fuzzy_ratio(s_ln, c_ln) / 100.0
            fn_sim = _fuzzy_ratio(s_fn, c_fn) / 100.0
            if ln_sim > 0.95 and fn_sim < 0.70:
                is_hardened_dudoso = True

        # Clasificación de decisión
        current_decision = "NO_MATCH"
        if global_score >= FUZZY_THRESHOLD and not is_hardened_dudoso:
            current_decision = "MATCH_AUTOMATICO"
        elif global_score >= 75 or is_hardened_dudoso:
            current_decision = "MATCH_DUDOSO"
        
        # Lógica de Selección del Mejor Candidato
        if current_decision == "MATCH_AUTOMATICO":
            if final_decision != "MATCH_AUTOMATICO" or global_score > max_score:
                final_decision = "MATCH_AUTOMATICO"
                max_score = global_score
                best_candidate_id = c_id
                best_candidate_name = cand_norm
        elif current_decision == "MATCH_DUDOSO" and final_decision != "MATCH_AUTOMATICO":
            if global_score > max_score or final_decision == "NO_MATCH":
                final_decision = "MATCH_DUDOSO"
                max_score = global_score
                best_candidate_id = c_id
                best_candidate_name = cand_norm

    res = {
        "decision": final_decision,
        "match_id": best_candidate_id,
        "score": max_score,
        "candidate_name": best_candidate_name
    }
    
    # Auditoría Final JSON
    ev = {
        "event": "teacher_matching",
        "xml_name": original_name,
        "normalized_name": norm,
        "candidate": best_candidate_name,
        "score": max_score,
        "decision": final_decision,
        "request_id": req_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    print(json.dumps(ev))
    log_mdm_evidence(ev)
    
    return res

    # NO_MATCH
    ev = {
        "event": "teacher_matching",
        "xml_name": original_name,
        "normalized_name": norm,
        "candidate": None,
        "score": 0,
        "decision": "NO_MATCH"
    }
    logger.info(f"MDM: No se encontró match para {original_name}", extra=ev)
    log_mdm_evidence(ev)
    return default_res


def cross_check_xml_teachers(db: Session, teachers_xml: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Compara docentes del XML contra la maestra.
    No encontrados → teachers_sinasignar (sin duplicar por normalized_name).
    """
    now_utc = datetime.now(timezone.utc)
    nuevos = ya_maestra = ya_sinasignar = 0

    for t in teachers_xml:
        fn = (t.get("first_name") or "").strip()
        ln = (t.get("last_name") or "").strip()
        if not fn and not ln:
            continue

        norm = normalize_teacher_name(ln, fn)

        # 1. Match Exacto en Maestra
        if repository.fetch_teacher_by_normalized(db, norm):
            ya_maestra += 1
            continue

        # 2. Match Exacto en SinAsignar
        existing_sa = repository.fetch_sinasignar_by_normalized(db, norm)
        if existing_sa:
            repository.increment_sinasignar_detection(db, existing_sa)
            ya_sinasignar += 1
            continue

        # 3. Match FUZZY optimizado (v3.2)
        possible_match_id = _get_fuzzy_match(db, norm, f"{ln}, {fn}")
        is_possible_duplicate = possible_match_id is not None

        repository.create_sinasignar(db, {
            "last_name":       ln,
            "first_name":      fn,
            "normalized_name": norm,
            "source":          "xml",
            "times_detected":  1,
            "last_seen_at":    now_utc,
            "possible_duplicate": is_possible_duplicate,
            "possible_match_id":  possible_match_id,
        })
        nuevos += 1

    db.commit()
    return {
        "success":          True,
        "nuevos_sinasignar": nuevos,
        "ya_en_maestra":    ya_maestra,
        "ya_en_sinasignar": ya_sinasignar,
        "detalle_nuevos":   [],
    }


# ════════════════════════════════════════════════════════
#  REPROCESAMIENTO HISTÓRICO — NUEVO ENDPOINT
# ════════════════════════════════════════════════════════

FUZZY_THRESHOLD = 90.0


def reprocesar_historico(db: Session) -> Dict[str, Any]:
    """
    1. Lee todos los Teacher de la BD (provienen de XMLs históricos).
    2. Puebla normalized_name donde falta.
    3. Obtiene el set de normalized_name de la maestra (con DNI o enriched).
    4. Para cada teacher no en maestra: fuzzy match. Si ≥ 90 → conflicto.
    5. Si no hay match: inserta en sinasignar (o incrementa times_detected).
    Retorna estadísticas y lista de conflictos fuzzy para resolución humana.
    """
    logger.info("[reprocesar_historico] Iniciando...")
    now_utc = datetime.now(timezone.utc)

    # ── Paso 1: Cargar todos los teachers del sistema ──────────
    all_teachers: List[Teacher] = repository.fetch_all_teachers_from_table(db)
    logger.info(f"  Teachers en BD: {len(all_teachers)}")

    # ── Paso 2: Poblar normalized_name donde esté vacío ───────
    updates_needed: List[Tuple[Any, str]] = []
    for t in all_teachers:
        if not t.normalized_name:
            norm = normalize_teacher_name(t.last_name or "", t.first_name or "")
            if norm:
                updates_needed.append((t.id, norm))
                t.normalized_name = norm  # local cache

    if updates_needed:
        repository.bulk_update_normalized(db, updates_needed)
        db.flush()
        logger.info(f"  Normalized_name poblado para {len(updates_needed)} registros")

    # ── Paso 3: Construir set de maestra (teachers con normalized) ─
    maestra_set = {
        t.normalized_name
        for t in all_teachers
        if t.normalized_name
    }
    maestra_list = sorted(maestra_set)  # para fuzzy

    # ── Paso 4: Construir set de docentes no asignados existentes ──
    sinasignar_norms = {
        s.normalized_name
        for s in db.query(Teacher).filter(Teacher.is_assigned == False).all()
    }

    # ── Paso 5: Analizar cada teacher ─────────────────────────
    analizados = 0
    nuevos = 0
    duplicados = 0
    conflictos: List[Dict[str, Any]] = []

    for t in all_teachers:
        norm = t.normalized_name
        if not norm:
            continue

        analizados += 1

        # Ya está en maestra (debería siempre ser cierto ya que viene de allí)
        # Buscamos si el teacher tiene match por parte del Excel (dni / razon_social)
        # La lógica real: teachers que NO tienen dni ni razon_social son "solo XML"
        is_xml_only = (not t.dni and not t.razon_social)
        if not is_xml_only:
            continue  # Ya enriquecido por Excel — no procesar

        # ── Nivel 1: Exact match en maestra enriched ───────────
        # Buscar si existe otro teacher (con dni/razon_social) con mismo normalized_name
        maestra_enriched = {
            t2.normalized_name
            for t2 in all_teachers
            if (t2.dni or t2.razon_social) and t2.normalized_name
        }
        if norm in maestra_enriched:
            logger.debug(f"  SKIP (exact maestra enriched): {norm}")
            continue

        # ── Nivel 2: Fuzzy match ───────────────────────────────
        best_match_norm: Optional[str] = None
        best_score: float = 0.0

        for m_norm in maestra_enriched:
            score = _fuzzy_ratio(norm, m_norm)
            if score > best_score:
                best_score = score
        # B) Match Fuzzy optimizado
        possible_match_id = _get_fuzzy_match(db, norm)
        if possible_match_id:
            match_t = repository.fetch_teacher_by_id_full(db, possible_match_id)
            conflictos.append({
                "teacher_id": t.id,
                "detected": f"{t.last_name}, {t.first_name}",
                "detected_norm": norm,
                "suggested_norm": match_t.normalized_name if match_t else "ID:" + str(possible_match_id),
                "score": _fuzzy_ratio(norm, match_t.normalized_name) if match_t else 0
            })
            continue

        # C) Sin match -> Crear en SinAsignar o actualizar
        if norm in sinasignar_norms:
            # Ya existe → incrementar contador
            existing_sa = repository.fetch_sinasignar_by_normalized(db, norm)
            if existing_sa:
                repository.increment_sinasignar_detection(db, existing_sa)
            duplicados += 1
            logger.debug(f"  DUPLICATE sinasignar (incrementado): {norm}")
        else:
            repository.create_sinasignar(db, {
                "apellidos":       t.last_name or "",
                "nombres":         t.first_name or "",
                "normalized_name": norm,
                "source":          "xml",
                "times_detected":  1,
                "last_seen_at":    now_utc,
            })
            sinasignar_norms.add(norm)
            nuevos += 1
            logger.info(f"  NUEVO sinasignar: {norm}")

    db.commit()

    logger.info(
        f"[reprocesar_historico] Fin — "
        f"analizados={analizados}, nuevos={nuevos}, "
        f"duplicados={duplicados}, fuzzy={len(conflictos)}"
    )
    return {
        "success":                    True,
        "total_docentes_analizados":  analizados,
        "nuevos_insertados":          nuevos,
        "duplicados_detectados":      duplicados,
        "posibles_coincidencias_fuzzy": conflictos,
    }


# ════════════════════════════════════════════════════════
#  RESOLUCIÓN DE CONFLICTOS FUZZY
# ════════════════════════════════════════════════════════

def vincular_teacher_alias(db: Session, teacher_id: UUID, target_norm: str) -> Dict[str, Any]:
    """
    'Vincular': actualiza el normalized_name del teacher para que coincida
    con el target (teacher enriquecido por maestra). Esto resuelve la ambigüedad.
    """
    t = repository.fetch_teacher_by_id_full(db, teacher_id)
    if not t:
        raise ValueError("Docente no encontrado")

    old_norm = t.normalized_name
    repository.update_teacher(db, t, {"normalized_name": target_norm})

    # Si estaba en sinasignar con el normalized_name viejo, eliminarlo
    sa = repository.fetch_sinasignar_by_normalized(db, old_norm)
    if sa:
        repository.delete_sinasignar(db, sa)

    # 3. Sincronizar incidencias que usaban el alias/nombre viejo
    synced = obs_repo.sync_teacher_id_by_name(db, teacher_id, old_norm)
    
    db.commit()
    msg = f"Alias vinculado: '{old_norm}' → '{target_norm}'."
    if synced > 0:
        msg += f" {synced} incidencias actualizadas."
    return {"success": True, "message": msg}


# ════════════════════════════════════════════════════════
#  CRUD — TEACHERS_SINASIGNAR
# ════════════════════════════════════════════════════════

def _sinasignar_to_dict(obj: Teacher) -> Dict[str, Any]:
    """Usa el modelo Teacher unificado para representar registros Sin Asignar."""
    return {
        "id":             str(obj.id),
        "dni":            obj.dni or "",
        "apellidos":      obj.last_name,
        "nombres":        obj.first_name,
        "razon_social":   getattr(obj, 'razon_social', ""),
        "normalized_name": obj.normalized_name,
        "source":         obj.source or "xml",
        "times_detected": obj.times_detected or 1,
        "is_possible_duplicate": obj.possible_duplicate,
        "last_seen_at":   obj.last_seen_at.strftime("%Y-%m-%d") if obj.last_seen_at else "",
    }


def get_sinasignar(db: Session, page: int = 1, limit: int = 20) -> Dict[str, Any]:
    # REGLA FASE 2: Filtrar de la tabla única teachers
    from sqlalchemy import and_
    q = db.query(Teacher).filter(Teacher.is_assigned == False).order_by(
        Teacher.times_detected.desc(),
        Teacher.last_name
    )
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()

    return {
        "success":     True,
        "data":        [_sinasignar_to_dict(o) for o in items],
        "total":       total,
        "page":        page,
        "total_pages": max(1, (total + limit - 1) // limit),
    }


def update_sinasignar_item(db: Session, sid: UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
    obj = repository.fetch_sinasignar_by_id(db, sid)
    if not obj:
        raise ValueError("Registro no encontrado")

    apellidos = (payload.get("apellidos") or obj.apellidos).strip()
    nombres   = (payload.get("nombres") or obj.nombres).strip()
    norm      = normalize_teacher_name(apellidos, nombres)

    repository.update_sinasignar(db, obj, {
        "dni":             (payload.get("dni") or "").strip() or None,
        "last_name":       apellidos,
        "first_name":      nombres,
        "razon_social":    (payload.get("razon_social") or "").strip() or None,
        "normalized_name": norm,
    })
    db.commit()
    return _sinasignar_to_dict(obj)


def promote_sinasignar(db: Session, identifier: UUID) -> Dict[str, Any]:
    # REGLA FASE 2: Buscar en tabla única
    obj = resolve_teacher(db, identifier)
    if not obj:
        raise ValueError("Registro no encontrado")

    if obj.is_assigned:
        return {"action": "already_promoted", "message": "Este docente ya está asignado.", "teacher": _teacher_to_dict(obj)}

    # Verificar si ya existe un docente titular con el mismo nombre (Fusión implícita)
    existing = db.query(Teacher).filter(
        Teacher.normalized_name == obj.normalized_name,
        Teacher.is_assigned == True,
        Teacher.uid != obj.uid
    ).first()

    if existing:
        # Transferimos relaciones de este 'sin asignar' al titular y borramos el duplicado
        repository.merge_teachers_db(db, existing.id, obj.id)
        db.commit()
        return {"action": "merged", "message": f"Se fusionó con el docente titular existente (id={existing.id}).", "teacher": _teacher_to_dict(existing)}

    # Promoción simple
    obj.is_assigned = True
    obj.source = f"PROMOTED_{int(time_lib.time())}"
    
    # Sincronizar incidencias
    obs_repo.sync_teacher_id_by_name(db, obj.id, obj.normalized_name)
    
    db.commit()
    return {"action": "promoted", "message": "Docente promovido exitosamente", "teacher": _teacher_to_dict(obj)}


def delete_sinasignar_item(db: Session, identifier: UUID) -> bool:
    obj = resolve_teacher(db, identifier)
    if not obj:
        raise ValueError("Registro no encontrado")
    repository.delete_sinasignar(db, obj)
    db.commit()
    return True


# ════════════════════════════════════════════════════════
#  FUSIÓN — MERGE
# ════════════════════════════════════════════════════════

def merge_teachers(db: Session, main_id: UUID, merge_id: UUID) -> Dict[str, Any]:
    """
    Orquestación de la fusión de dos docentes.
    REGLA: Debe ser atómica y recalcular normalized_name.
    """
    if main_id == merge_id:
        raise ValueError("No se puede fusionar un docente con el mismo registro.")

    t_main = resolve_teacher(db, main_id)
    t_merge = resolve_teacher(db, merge_id)

    if not t_main or not t_merge:
        raise ValueError("Uno o ambos docentes no existen.")

    try:
        # 1. Ejecutar transferencia de relaciones y eliminación del secundario
        secondary_norm_copy = t_merge.normalized_name # Guardamos para limpieza
        secondary_id_copy   = t_merge.id
        
        repository.merge_teachers_db(db, main_id, merge_id)

        # 2. Recalcular normalized_name del resultante para asegurar consistencia
        new_norm = normalize_teacher_name(t_main.last_name or "", t_main.first_name or "")
        repository.update_teacher(db, t_main, {"normalized_name": new_norm})

        # 3. Limpieza DIRIGIDA (v3.2) de SinAsignar
        repository.cleanup_sinasignar_post_merge(db, secondary_id_copy, secondary_norm_copy)
        # También limpiar el nombre nuevo del principal si existía en pendientes
        repository.cleanup_sinasignar_post_merge(db, main_id, new_norm)

        # 4. Sincronizar incidencias del eliminado (por nombre) al nuevo ID principal
        # Especialmente útil si había incidencias con el nombre del secundario pero sin ID
        synced_sec = obs_repo.sync_teacher_id_by_name(db, main_id, secondary_norm_copy)
        
        db.commit()
        logger.info(f"FUSIÓN EXITOSA: main_id={main_id}, merge_id={merge_id}. {synced_sec} incidencias huérfanas vinculadas.")
        return {
            "success": True,
            "message": f"Fusión completada. {synced_sec} incidencias reconectadas.",
            "teacher": _teacher_to_dict(t_main)
        }
    except Exception as e:
        db.rollback()
        logger.error(f"ERROR EN FUSIÓN: {str(e)}")
        raise RuntimeError(f"Error crítico en la fusión. Operación cancelada (Rollback ejecutado): {str(e)}")


def get_potential_duplicates(db: Session) -> List[Dict[str, Any]]:
    """Obtiene docentes marcados como posibles duplicados para auditoría (v3.2)."""
    duplicates = db.query(Teacher).filter(Teacher.possible_duplicate == True).all()
    # Usar active_ids vacío como fallback para el mapeo simple de auditoría
    return [_teacher_to_dict(t, set()) for t in duplicates]
