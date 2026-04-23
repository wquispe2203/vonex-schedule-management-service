import os
from app.services.xml_parser import XMLParserService

parser = XMLParserService()
file_path = "storage/xml_uploads/asctt2012.xml"

try:
    print(f"Leyendo: {file_path}")
    data = parser.parse_file(file_path)

    for key, value in data.items():
        print(f"{key}: {len(value)} records")
        if len(value) > 0:
            print(f"  Sample: {value[0]}")
except Exception as e:
    import traceback
    print("Error parseando:", traceback.format_exc())
