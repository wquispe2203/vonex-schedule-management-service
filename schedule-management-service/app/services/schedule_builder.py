from datetime import datetime, timedelta
from .hour_modifier import HourModifierService
from .break_analyzer import BreakAnalyzerService

class ScheduleBuilderService:
    def __init__(self, hour_modifier: HourModifierService, break_analyzer: BreakAnalyzerService):
        self.hour_modifier = hour_modifier
        self.break_analyzer = break_analyzer

    def build_sessions(self, periods_map: dict, cards: list, lessons: list, subjects_map: dict, start_date_str: str, end_date_str: str) -> list:
        sessions = []
        
        from datetime import date
        
        # Convertir a datetime si vienen como string o date
        if isinstance(start_date_str, str):
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        elif isinstance(start_date_str, date) and not isinstance(start_date_str, datetime):
            start_date = datetime.combine(start_date_str, datetime.min.time())
        else:
            start_date = start_date_str

        if isinstance(end_date_str, str):
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        elif isinstance(end_date_str, date) and not isinstance(end_date_str, datetime):
            end_date = datetime.combine(end_date_str, datetime.min.time())
        else:
            end_date = end_date_str

        # Mapeo rapido de lessons por source_id
        lesson_map = {str(l.get("source_id")): l for l in lessons if l.get("source_id")}

        # PRE-CALCULAR: Tiempos modificados para cada card (O(N_cards))
        precalculated_cards = []
        for card in cards:
            l_id = str(card.get("lesson_id"))
            lesson = lesson_map.get(l_id)
            if not lesson:
                # logger.debug(f"[BUILDER] Lesson {l_id} not found for card {card.get('source_id')}")
                continue

            period = card.get("period", 0)
            period_time = periods_map.get(period)
            if not period_time:
                # logger.debug(f"[BUILDER] Period {period} not found in periods_map for card {card.get('source_id')}")
                continue

            import re
            if lesson:
                s_id = str(lesson.get("subject_id"))
                subject_name = subjects_map.get(s_id, "")
                clean_name = re.sub(r'\(.*?\)', '', subject_name).strip().upper()
                if clean_name in ["RECESO", "ALMUERZO"]:
                    continue

                class_ids = lesson.get("class_ids", [])
                for cid in class_ids:
                    precalculated_cards.append({
                        "lesson_id": f"{lesson.get('source_id')}_{cid}",
                        "teacher_id": lesson.get("teacher_id"),
                        "class_id": cid,
                        "subject_id": s_id,
                        "subject_name_raw": subject_name,
                        "days_bits": card.get("days", ""),
                        "period": period,
                        "start_time": period_time["start"],
                        "end_time": period_time["end"]
                    })

        print(f"[STEP 3] Cards: {len(precalculated_cards)}")
        if precalculated_cards:
            print(f"[DEBUG] first card: {precalculated_cards[0]}")

        print(f"[DEBUG BUILDER] precalculated_cards: {len(precalculated_cards)}")
        print(f"[DEBUG BUILDER] range: {start_date} to {end_date}")

        # Iterar diariamente desde start_date hasta end_date
        current_date = start_date
        total_days = 0
        while current_date <= end_date:
            total_days += 1
            current_weekday = current_date.weekday()
            # print(f"[DEBUG BUILDER] Processing {current_date.date()} (weekday={current_weekday})")

            for card in precalculated_cards:
                days_val = str(card["days_bits"])
                
                # El XML indica los días con bits '1' (ej: 1111100 -> Lunes a Viernes)
                for day_index, bit in enumerate(days_val):
                    if bit == "1" and day_index == current_weekday:
                        sessions.append({
                            "lesson_id": card["lesson_id"],
                            "teacher_id": card["teacher_id"],
                            "class_id": card["class_id"],
                            "subject_id": card["subject_id"],
                            "subject_name_raw": card["subject_name_raw"],
                            "session_date": current_date.date(),
                            "period": card["period"],
                            "start_time": card["start_time"],
                            "end_time": card["end_time"],
                            "status": "ACTIVE"
                        })
                    
            # Avanzar al siguiente día
            current_date += timedelta(days=1)
            
        print(f"[DEBUG BUILDER] sessions generated: {len(sessions)} in {total_days} days")
            
        return sessions
