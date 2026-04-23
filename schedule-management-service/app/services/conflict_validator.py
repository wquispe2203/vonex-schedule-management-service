from datetime import datetime

class ConflictValidatorService:
    
    def check_conflicts(self, sessions: list) -> list:
        """
        Valida la existencia de cruces de horarios de forma eficiente (O(N log N))
        :param sessions: Lista de diccionarios que representan ScheduleSession
        """
        conflicts = []
        if not sessions: 
            return []

        # 1. Agrupar por fecha para reducir el espacio de búsqueda
        by_date = {}
        for s in sessions:
            d = s["session_date"]
            if d not in by_date: by_date[d] = []
            by_date[d].append(s)

        for d, day_sessions in by_date.items():
            # 2. Dentro de cada día, validar por docente y por aula independientemente
            teachers = {}
            classrooms = {}

            for s in day_sessions:
                if s.get("is_break"): continue
                
                t_id = s.get("teacher_id")
                c_id = s.get("class_id")

                if t_id:
                    if t_id not in teachers: teachers[t_id] = []
                    teachers[t_id].append(s)
                
                if c_id:
                    if c_id not in classrooms: classrooms[c_id] = []
                    classrooms[c_id].append(s)

            # 3. Validar solapamientos por Docente
            for t_id, t_sessions in teachers.items():
                t_sessions.sort(key=lambda x: x["start_time"])
                for i in range(len(t_sessions) - 1):
                    s1, s2 = t_sessions[i], t_sessions[i+1]
                    if self._overlaps(s1["start_time"], s1["end_time"], s2["start_time"], s2["end_time"]):
                        conflicts.append({
                            "type": "TEACHER_DOUBLE_BOOKED",
                            "description": f"Docente ID {t_id} asignado doble: {d} {s1['start_time']}-{s1['end_time']} y {s2['start_time']}-{s2['end_time']}",
                            "session1": s1, "session2": s2
                        })

            # 4. Validar solapamientos por Aula
            for c_id, c_sessions in classrooms.items():
                c_sessions.sort(key=lambda x: x["start_time"])
                for i in range(len(c_sessions) - 1):
                    s1, s2 = c_sessions[i], c_sessions[i+1]
                    # Solo es conflicto si son cursos distintos (mismo curso en aula es normal en bloques)
                    if s1.get("subject_id") != s2.get("subject_id"):
                        if self._overlaps(s1["start_time"], s1["end_time"], s2["start_time"], s2["end_time"]):
                            conflicts.append({
                                "type": "CLASSROOM_DOUBLE_BOOKED",
                                "description": f"Aula ID {c_id} ocupada doble: {d} {s1['start_time']}-{s1['end_time']} y {s2['start_time']}-{s2['end_time']}",
                                "session1": s1, "session2": s2
                            })

        return conflicts

    def _overlaps(self, start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
        return start_a < end_b and end_a > start_b
