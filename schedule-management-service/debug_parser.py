import sys
import os
from app.services.xml_parser import XMLParserService

try:
    p = XMLParserService()
    path = os.path.join("storage", "xml_uploads", "asctt2012.xml")
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)
    cards = p.parse_file(path).get("cards", [])
    days_set = set(str(c.get('days')) for c in cards)
    print("Unique days in cards:", days_set)
    for c in cards[:5]:
        print("Card sample:", c)
except Exception as e:
    import traceback
    traceback.print_exc()
