import sys
import os
from datetime import datetime, timedelta

from app.services.xml_parser import XMLParserService
from app.services.hour_modifier import HourModifierService
from app.services.break_analyzer import BreakAnalyzerService
from app.services.schedule_builder import ScheduleBuilderService

try:
    p = XMLParserService()
    path = os.path.join("storage", "xml_uploads", "asctt2012.xml")
    data = p.parse_file(path)
    
    hm = HourModifierService()
    ba = BreakAnalyzerService()
    sb = ScheduleBuilderService(hm, ba)
    
    subjects_map = {str(s.get("source_id")): s.get("name") for s in data.get("subjects", [])}
    
    sessions = sb.build_sessions(
        data.get("cards", []),
        data.get("lessons", []),
        subjects_map,
        "2026-03-02",
        "2026-03-08"
    )
    
    dates_found = set(s["session_date"] for s in sessions)
    print(f"Total sessions generated: {len(sessions)}")
    print(f"Dates found in generated sessions: {dates_found}")
    
    monday_count = sum(1 for s in sessions if str(s["session_date"]) == "2026-03-02")
    tuesday_count = sum(1 for s in sessions if str(s["session_date"]) == "2026-03-03")
    
    print(f"Monday sessions: {monday_count}")
    print(f"Tuesday sessions: {tuesday_count}")

except Exception as e:
    import traceback
    traceback.print_exc()
