import logging
from datetime import time, date, datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_time_diff_minutes(t1: time, t2: time) -> int:
    if not t1 or not t2:
        return 0
    return (t2.hour * 60 + t2.minute) - (t1.hour * 60 + t1.minute)

def consolidate_sessions(
    sessions: List[Dict[str, Any]],
    date_key: str = "fecha_clase",
    start_time_key: str = "hora_inicio",
    end_time_key: str = "hora_fin",
    hours_key: str = "horas_dictadas",
    group_fields: Optional[List[str]] = None,
    module_tag: str = "RPT" # "RPT" or "SCHEDULE"
) -> List[Dict[str, Any]]:
    """
    Consolidates consecutive or overlapping academic sessions into a single continuous block.
    Follows academic logic: gap <= 20 minutes is continuous.
    Recalculates final time using actual accumulated academic hours.
    """
    if not sessions:
        return []
    
    # Default RPT group fields
    if group_fields is None:
        group_fields = ["docente", "sede", "curso", "ciclo", "is_replacement"]

    def get_norm_val(item, field):
        val = item.get(field)
        if isinstance(val, str):
            return val.strip().upper()
        return val

    # Sort sessions to ensure temporal continuity per group
    # Helper sort key
    def sort_key(x):
        key_parts = [x.get(date_key)]
        for f in group_fields:
            key_parts.append(get_norm_val(x, f))
        key_parts.append(x.get(start_time_key))
        return tuple(key_parts)

    sorted_sessions = sorted(sessions, key=sort_key)
    
    consolidated: List[Dict[str, Any]] = []
    current_group: Optional[Dict[str, Any]] = None

    for item in sorted_sessions:
        # Logging requested by user
        start_val = item.get(start_time_key)
        end_val = item.get(end_time_key)
        hours_val = item.get(hours_key, 0.0)
        
        # log_context = f"docente='{item.get('docente','N/A')}' | {start_val}-{end_val} | curso='{item.get('curso','N/A')}' | ciclo='{item.get('ciclo','N/A')}' | hrs={hours_val}"
        # print(f"[{module_tag} XML BLOCK] Processing raw block: {log_context}")
        
        if current_group is None:
            current_group = dict(item)
            continue
        
        # Check group identity
        same_group = True
        if current_group.get(date_key) != item.get(date_key):
            same_group = False
        else:
            for f in group_fields:
                if get_norm_val(current_group, f) != get_norm_val(item, f):
                    same_group = False
                    break
        
        # If not same group, cannot merge
        if not same_group:
            consolidated.append(current_group)
            current_group = dict(item)
            continue

        # Time analysis
        c_end = current_group.get(end_time_key)
        i_start = item.get(start_time_key)
        
        if not isinstance(c_end, time) or not isinstance(i_start, time):
            # Fallback if someone passed strings, just don't merge for now or try parsing
            consolidated.append(current_group)
            current_group = dict(item)
            continue

        gap_minutes = get_time_diff_minutes(c_end, i_start)
        
        # Merge criteria: gap <= 20 mins (handles overlaps <0 and gaps 0..20)
        if gap_minutes <= 20:
            prev_end = c_end
            
            if gap_minutes < 0:
                logger.info(f"[{module_tag} OVERLAP DETECTED] Overlap found for {item.get('docente','N/A')} between current {current_group.get(start_time_key)}-{prev_end} and item {i_start}-{item.get(end_time_key)}")
            
            # Perform Merge
            current_group[hours_key] = float(current_group.get(hours_key, 0)) + float(hours_val)
            
            c_start = current_group.get(start_time_key)
            
            if module_tag == "RPT":
                # PROTECCIÓN CRÍTICA RPT: El bloque debe representar la unión física máxima.
                # No recalcular en base a horas ya que las FALTAS (0.0 hrs) colapsarían el bloque temporalmente.
                current_group[end_time_key] = max(prev_end, end_val)
                new_end = current_group[end_time_key]
            else:
                # Recalculate end time based on start + (total_hours * 50) for pure XML parser logic
                total_mins = c_start.hour * 60 + c_start.minute + int(current_group[hours_key] * 50)
                new_end = time(int(total_mins // 60) % 24, int(total_mins % 60))
                current_group[end_time_key] = new_end
            
            # print(f"[{module_tag} XML MERGED] Merged blocks for {item.get('docente','N/A')}: {c_start}-{prev_end} with {i_start}-{end_val} => new end {new_end} | total hrs: {current_group[hours_key]}")
            logger.info(f"[{module_tag} XML MERGED] Merging block: {c_start}->{prev_end} with {i_start}->{end_val} => {new_end}")
            
            # Merge Observations if they exist
            if item.get("observation") or item.get("observations"):
                # Handle both key formats: RPT stores "observation" dict, Schedule stores "observations" list
                if "observation" in item:
                    # RPT format logic extraction
                    if not current_group.get("observation"):
                        current_group["observation"] = item["observation"]
                    else:
                        c_obs = current_group["observation"]
                        i_obs = item["observation"]
                        c_obs["type"] = ", ".join(sorted(set(filter(None, [c_obs.get("type"), i_obs.get("type")]))))
                        c_obs["description"] = " | ".join(sorted(set(filter(None, [c_obs.get("description"), i_obs.get("description")]))))
                        if "ids" in c_obs and "ids" in i_obs:
                            c_obs["ids"].extend(i_obs["ids"])
                
                if "observations" in item:
                    # Schedule format
                    if "observations" not in current_group:
                        current_group["observations"] = []
                    current_group["observations"].extend(item.get("observations", []))
        else:
            # Gap > 20, finalize current group
            consolidated.append(current_group)
            current_group = dict(item)

    # Append last one
    if current_group is not None:
        consolidated.append(current_group)
        
    # Log final consolidation stats
    # for b in consolidated:
    #     print(f"[{module_tag} FINAL CONSOLIDATED] Block consolidated: {b.get('docente','N/A')} | {b.get(start_time_key)}-{b.get(end_time_key)} | hrs={b.get(hours_key)}")
    
    # Tag requested for Schedule module specifically
    if module_tag == "SCHEDULE":
        print(f"[SCHEDULE CONSOLIDATED] Final consolidated block count: {len(consolidated)}")

    return consolidated
