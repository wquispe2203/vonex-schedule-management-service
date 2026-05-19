from app.core.database import SessionLocal
from app.services.xml_parser import XMLParserService
import os

def run():
    xml_path = "d:\\Desktop\\MOD HOR\\horario-academia-lima.xml"
    if not os.path.exists(xml_path):
        print(f"File not found: {xml_path}")
        return
        
    print(f"Parsing file: {xml_path}")
    parser = XMLParserService()
    parsed_data = parser.parse_file(xml_path)
    
    xml_teachers = parsed_data.get("teachers", [])
    print(f"Total teachers parsed from XML: {len(xml_teachers)}")
    if xml_teachers:
        print("First 5 XML teachers preview:")
        for t in xml_teachers[:5]:
            print(t)
            
if __name__ == "__main__":
    run()
