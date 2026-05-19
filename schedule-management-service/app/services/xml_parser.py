import xml.etree.ElementTree as ET

class XMLParserService:
    def __init__(self):
        pass

    def parse_file(self, file_path: str) -> dict:
        """
        Parses the XML file using iterparse for memory efficiency.
        """
        data = {
            "periods": {},
            "subjects": [],
            "teachers": [],
            "classes": [],
            "buildings": [],
            "lessons": [],
            "cards": []
        }
        
        context = ET.iterparse(file_path, events=('end',))
        for event, elem in context:
            tag = elem.tag
            
            if tag == 'period':
                p_data = self._parse_period_elem(elem)
                if p_data: data["periods"][p_data["id"]] = p_data["data"]
            elif tag == 'subject':
                data["subjects"].append({
                    "source_id": elem.get('id'),
                    "name": elem.get('name'),
                    "short_name": elem.get('short')
                })
            elif tag == 'teacher':
                data["teachers"].append({
                    "source_id": elem.get('id'),
                    "first_name": elem.get('firstname', ''),
                    "last_name": elem.get('lastname', ''),
                    "short_name": elem.get('short')
                })
            elif tag == 'class':
                data["classes"].append({
                    "source_id": elem.get('id'),
                    "name": elem.get('name')
                })
            elif tag == 'building':
                data["buildings"].append({
                    "source_id": elem.get('id'),
                    "name": elem.get('name')
                })
            elif tag == 'lesson':
                data["lessons"].append({
                    "source_id": elem.get('id'),
                    "subject_id": elem.get('subjectid'),
                    "teacher_id": elem.get('teacherids', '').split(',')[0] if elem.get('teacherids') else None,
                    "class_ids": [cid.strip() for cid in elem.get('classids', '').split(',')] if elem.get('classids') else [],
                    "raw_class_ids": elem.get('classids', '')
                })
            elif tag == 'card':
                data["cards"].append({
                    "source_id": elem.get('id'),
                    "lesson_id": elem.get('lessonid'),
                    "days": elem.get('days'),
                    "period": int(elem.get('period', 0))
                })
            
            # Limpiar el elemento para liberar memoria
            elem.clear()
            
        return data

    def _parse_period_elem(self, item):
        p_id = item.get('period')
        if not p_id: return None
        
        start = item.get('starttime', '')
        end = item.get('endtime', '')
        
        # Pad to HH:MM:SS if needed
        if len(start) == 4 and start[1] == ':': start = '0' + start
        if len(end) == 4 and end[1] == ':': end = '0' + end
        if start and len(start) == 5: start += ':00'
        if end and len(end) == 5: end += ':00'
        
        return {
            "id": int(p_id),
            "data": {
                "start": start,
                "end": end
            }
        }
