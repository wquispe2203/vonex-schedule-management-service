from app.core.database import SessionLocal
from app.modules.docentes.service import normalize_name, check_strict_match, get_latest_completed_upload, get_docente_names_from_xml
from app.models import Teacher
import difflib

def run_validation():
    db = SessionLocal()
    latest = get_latest_completed_upload(db)
    xml_names = get_docente_names_from_xml(latest) if latest else []
    
    db_teachers = db.query(Teacher).filter(Teacher.merged_into_id.is_(None)).all()
    
    # STRESS TEST CASES
    test_cases = [
        {"xml": "MARIA LOPEZ", "db": "MARIA LOPEZ DELGADO"},
        {"xml": "JUAN CARLOS PEREZ", "db": "JUAN PEREZ"},
        {"xml": "LUIS GONZALES", "db": "LUIS GONZALEZ"},
        {"xml": "ANA TORRES", "db": "ANA MARIA TORRES"},
        {"xml": "JOSE HERRERA", "db": "JOSE HERERA"},
    ]
    
    for tc in test_cases:
        xml_names.append(tc["xml"])
        
    class FakeTeacher:
        def __init__(self, full_name):
            parts = full_name.split()
            if len(parts) >= 2:
                self.last_name = " ".join(parts[1:])
                self.first_name = parts[0]
            else:
                self.last_name = full_name
                self.first_name = ""
            self.dni = "00000000"
            self.merged_into_id = None
            
    for tc in test_cases:
        db_teachers.append(FakeTeacher(tc["db"]))

    db_names = []
    db_data_map = {} 
    db_sorted_data_map = {}
    db_map = {}
    db_sorted_map = {}
    
    for t in db_teachers:
        full_name = normalize_name(f"{t.last_name} {t.first_name}")
        db_names.append(full_name)
        if full_name not in db_data_map: db_data_map[full_name] = []
        db_data_map[full_name].append(t)
        db_map[full_name] = t
        
        sorted_tokens = " ".join(sorted(full_name.split()))
        if sorted_tokens not in db_sorted_data_map: db_sorted_data_map[sorted_tokens] = []
        db_sorted_data_map[sorted_tokens].append(t)
        db_sorted_map[sorted_tokens] = t
        
    unique_db_names = list(set(db_names))
    
    matched = []
    sin_asignar = []
    conflictos = []
    
    xml_targets = [tc["xml"] for tc in test_cases]
    
    print("\n--- STRESS TEST DEBUG LOG ---")
    for x_name in xml_names:
        x_sorted = " ".join(sorted(x_name.split()))
        
        decision = ""
        best_match_str = ""
        similarity = 0.0
        tc_xml = len(x_name.split())
        tc_db = 0
        candidates = []

        if x_name in db_data_map and len(db_data_map[x_name]) > 1:
            decision = "CONFLICTO"
            best_match_str = "MULTIPLE_EXACT_MATCHES"
            similarity = 1.0
            candidates = [f"{t.last_name} {t.first_name}" for t in db_data_map[x_name]]
            conflictos.append({"nombre_xml": x_name, "motivo": "MULTIPLES COINCIDENCIAS EXACTAS", "posibles_coincidencias": candidates})
            
        elif x_sorted in db_sorted_data_map and len(db_sorted_data_map[x_sorted]) > 1:
            decision = "CONFLICTO"
            best_match_str = "MULTIPLE_SWAPPED_MATCHES"
            similarity = 1.0
            candidates = [f"{t.last_name} {t.first_name}" for t in db_sorted_data_map[x_sorted]]
            conflictos.append({"nombre_xml": x_name, "motivo": "MULTIPLES COINCIDENCIAS INVERTIDAS", "posibles_coincidencias": candidates})
            
        elif x_name in db_map:
            db_n = normalize_name(f"{db_map[x_name].last_name} {db_map[x_name].first_name}")
            candidates.append(db_n)
            best_match_str = db_n
            similarity = 1.0
            tc_db = len(db_n.split())
            if check_strict_match(x_name, db_n):
                decision = "MATCHED"
                matched.append((x_name, db_map[x_name]))
            else:
                decision = "CONFLICTO"
                conflictos.append({"nombre_xml": x_name, "motivo": "FAILED_STRICT_EXACT", "posibles_coincidencias": [db_n]})
                
        elif x_sorted in db_sorted_map:
            db_t = db_sorted_map[x_sorted]
            db_n = normalize_name(f"{db_t.last_name} {db_t.first_name}")
            candidates.append(db_n)
            best_match_str = db_n
            similarity = 1.0
            tc_db = len(db_n.split())
            if check_strict_match(x_name, db_n):
                decision = "MATCHED"
                matched.append((x_name, db_t))
            else:
                decision = "CONFLICTO"
                conflictos.append({"nombre_xml": x_name, "motivo": "FAILED_STRICT_SWAPPED", "posibles_coincidencias": [db_n]})
                
        else:
            best_matches = []
            is_matched = False
            for db_n in unique_db_names:
                score_normal = difflib.SequenceMatcher(None, x_name, db_n).ratio()
                db_sorted = " ".join(sorted(db_n.split()))
                score_sorted = difflib.SequenceMatcher(None, x_sorted, db_sorted).ratio()
                score = max(score_normal, score_sorted)
                
                if score >= 0.9:
                    if check_strict_match(x_name, db_n):
                        decision = "MATCHED"
                        best_match_str = db_n
                        similarity = score
                        tc_db = len(db_n.split())
                        candidates.append(db_n)
                        matched.append((x_name, db_map[db_n]))
                        is_matched = True
                        break
                    else:
                        best_matches.append((db_n, score))
                elif score >= 0.7:
                    best_matches.append((db_n, score))
            
            if not is_matched:
                if best_matches:
                    best_matches.sort(key=lambda x: x[1], reverse=True)
                    decision = "CONFLICTO"
                    best_match_str = best_matches[0][0]
                    similarity = best_matches[0][1]
                    tc_db = len(best_matches[0][0].split())
                    candidates = [m[0] for m in best_matches[:3]]
                    conflictos.append({"nombre_xml": x_name, "motivo": "SIMILITUD DUDOSA", "posibles_coincidencias": candidates})
                else:
                    decision = "SIN_ASIGNAR"
                    best_match_str = "N/A"
                    similarity = 0.0
                    tc_db = 0
                    sin_asignar.append({"nombre_xml": x_name, "motivo": "NO ENCONTRADO"})

        if x_name in xml_targets:
            print(f"XML_NAME: '{x_name}'")
            print(f"MATCH_CANDIDATES: {candidates}")
            print(f"BEST_MATCH: '{best_match_str}'")
            print(f"SIMILARITY: {similarity:.2f}")
            print(f"TOKEN_COUNT_XML: {tc_xml}")
            print(f"TOKEN_COUNT_DB: {tc_db}")
            print(f"DECISION: {decision}")
            print("-" * 40)
            
    print("\n--- VALIDATION SUMMARY ---")
    print(f"TOTAL XML: {len(xml_names)}")
    print(f"TOTAL DB: {len(db_teachers)}")
    print(f"MATCHED: {len(matched)}")
    print(f"SIN ASIGNAR: {len(sin_asignar)}")
    print(f"CONFLICTOS: {len(conflictos)}")

if __name__ == "__main__":
    run_validation()
