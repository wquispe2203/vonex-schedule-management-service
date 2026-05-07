
import os
import sys
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.xml_upload import XMLUploadService
from app.services.xml_parser import XMLParserService
from app.services.schedule_builder import ScheduleBuilderService
from app.services.hour_modifier import HourModifierService
from app.services.break_analyzer import BreakAnalyzerService
from datetime import datetime

def analyze_xml_sessions(file_path, start_date_str, end_date_str):
    parser = XMLParserService()
    hour_mod = HourModifierService()
    break_an = BreakAnalyzerService()
    builder = ScheduleBuilderService(hour_mod, break_an)
    
    print(f"--- ANALYZING XML: {file_path} ---")
    parsed_data = parser.parse_file(file_path)
    
    print(f"[STEP 1] Subjects: {len(parsed_data.get('subjects', []))}")
    print(f"[STEP 2] Teachers: {len(parsed_data.get('teachers', []))}")
    print(f"[STEP 3] Cards: {len(parsed_data.get('cards', []))}")
    
    subjects_map = {str(s["source_id"]): s["name"] for s in parsed_data["subjects"] if s.get("source_id")}
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    sessions = builder.build_sessions(
        parsed_data.get("periods", {}), 
        parsed_data.get("cards", []), 
        parsed_data.get("lessons", []), 
        subjects_map, 
        start_date, 
        end_date
    )
    
    print(f"[STEP 4] Sessions: {len(sessions)}")
    print(f"[DATES] {start_date} to {end_date}")

    if len(sessions) == 0:
        # Debug deeper
        print("\n--- DEEP DEBUG ---")
        lesson_map = {str(l.get("source_id")): l for l in parsed_data["lessons"] if l.get("source_id")}
        periods_map = parsed_data.get("periods", {})
        
        print(f"Periods in XML: {list(periods_map.keys())}")
        
        sample_cards = parsed_data.get("cards", [])[:5]
        for i, card in enumerate(sample_cards):
            l_id = str(card.get("lesson_id"))
            lesson = lesson_map.get(l_id)
            period = card.get("period", 0)
            period_time = periods_map.get(period)
            days = card.get("days", "")
            
            print(f"Card {i}: lesson={l_id} (found={lesson is not None}), period={period} (found={period_time is not None}), days={days}")
            if lesson:
                s_id = str(lesson.get("subject_id"))
                s_name = subjects_map.get(s_id, "N/A")
                print(f"  -> Subject: {s_id} ({s_name})")

if __name__ == "__main__":
    xml_file = "storage/xml_uploads/20260428_163516_ACADLIMA_0203-0803.xml"
    analyze_xml_sessions(xml_file, "2026-03-02", "2026-03-08")
