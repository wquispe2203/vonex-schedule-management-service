import os
from app.services.xml_parser import XMLParserService
from app.services.schedule_builder import ASC_PERIODS

xml_path = os.path.join("storage", "xml_uploads", "asctt2012.xml")
parser = XMLParserService()
data = parser.parse_file(xml_path)

# Buscar Pedro
teacher_id = next((t["source_id"] for t in data["teachers"] if "PEDROZO GARGATE" in t["last_name"]), None)

print(f"Teacher ID: {teacher_id}")

pedro_lessons = [l for l in data["lessons"] if str(l["teacher_id"]) == str(teacher_id)]

for l in pedro_lessons:
    subject = next((s for s in data["subjects"] if str(s["source_id"]) == str(l["subject_id"])), None)
    print(f"Lesson: {l['source_id']} - Subject: {subject['name'] if subject else 'Unknown'} - RAW: {l.get('raw_class_ids')}")

    for c in data["cards"]:
        if str(c["lesson_id"]) == str(l["source_id"]):
            per = ASC_PERIODS.get(int(c['period']))
            print(f"  Card Day: {c['days']}, Period: {c['period']}, Time: {per['start']} to {per['end']}")
