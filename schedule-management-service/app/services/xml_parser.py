import xml.etree.ElementTree as ET

class XMLParserService:
    def __init__(self):
        pass

    def parse_file(self, file_path: str) -> dict:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        return {
            "periods": self._extract_periods(root.find("periods") if root.find("periods") is not None else root),
            "subjects": self._extract_subjects(root.find("subjects") if root.find("subjects") is not None else root),
            "teachers": self._extract_teachers(root.find("teachers") if root.find("teachers") is not None else root),
            "classes": self._extract_classes(root.find("classes") if root.find("classes") is not None else root),
            "buildings": self._extract_buildings(root.find("buildings") if root.find("buildings") is not None else root),
            "lessons": self._extract_lessons(root.find("lessons") if root.find("lessons") is not None else root),
            "cards": self._extract_cards(root.find("cards") if root.find("cards") is not None else root)
        }

    def _extract_periods(self, element) -> dict:
        periods = {}
        if element is None: return periods
        for item in element.findall('period'):
            p_id = item.get('period')
            start = item.get('starttime', '')
            end = item.get('endtime', '')
            
            # Pad to HH:MM:SS if needed
            if len(start) == 4 and start[1] == ':': start = '0' + start
            if len(end) == 4 and end[1] == ':': end = '0' + end
            if start and len(start) == 5: start += ':00'
            if end and len(end) == 5: end += ':00'
            
            if p_id:
                periods[int(p_id)] = {
                    "start": start,
                    "end": end
                }
        return periods

    def _extract_subjects(self, element) -> list:
        subjects = []
        if element is None: return subjects
        for item in element.findall('subject'):
            subjects.append({
                "source_id": item.get('id'),
                "name": item.get('name'),
                "short_name": item.get('short')
            })
        return subjects

    def _extract_teachers(self, element) -> list:
        teachers = []
        if element is None: return teachers
        for item in element.findall('teacher'):
            teachers.append({
                "source_id": item.get('id'),
                "first_name": item.get('firstname', ''),
                "last_name": item.get('lastname', ''),
                "short_name": item.get('short')
            })
        return teachers

    def _extract_classes(self, element) -> list:
        classes = []
        if element is None: return classes
        for item in element.findall('class'):
            classes.append({
                "source_id": item.get('id'),
                "name": item.get('name')
            })
        return classes

    def _extract_buildings(self, element) -> list:
        buildings = []
        if element is None: return buildings
        for item in element.findall('building'):
            buildings.append({
                "source_id": item.get('id'),
                "name": item.get('name')
            })
        return buildings

    def _extract_lessons(self, element) -> list:
        lessons = []
        if element is None: return lessons
        for item in element.findall('lesson'):
            lessons.append({
                "source_id": item.get('id'),
                "subject_id": item.get('subjectid'),
                "teacher_id": item.get('teacherids', '').split(',')[0] if item.get('teacherids') else None,
                "class_ids": [cid.strip() for cid in item.get('classids', '').split(',')] if item.get('classids') else [],
                "raw_class_ids": item.get('classids', '')
            })
        return lessons

    def _extract_cards(self, element) -> list:
        cards = []
        if element is None: return cards
        for item in element.findall('card'):
            cards.append({
                "source_id": item.get('id'),
                "lesson_id": item.get('lessonid'),
                "days": item.get('days'),
                "period": int(item.get('period', 0))
            })
        return cards
