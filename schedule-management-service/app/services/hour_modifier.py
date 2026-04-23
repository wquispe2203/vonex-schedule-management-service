import re
from datetime import datetime, timedelta

class HourModifierService:
    def __init__(self):
        self._cache = {}
    
    def apply_modifiers(self, subject_name: str, base_start_time: str, base_end_time: str) -> dict:
        """
        Aplica modificadores dinámicos de hora como (F+20) o (I-10) a una sesión.
        :param subject_name: Nombre original de la materia (e.g., 'Física(F+20)')
        :param base_start_time: Hora de inicio base formato 'HH:MM:SS'
        :param base_end_time: Hora de fin base formato 'HH:MM:SS'
        """
        if not subject_name:
            return {"start_time": base_start_time, "end_time": base_end_time}
            
        cache_key = (subject_name, base_start_time, base_end_time)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Formato de fecha para operaciones con datetime
        dt_format = "%Y-%m-%dT%H:%M:%S"
        date_str = "1970-01-01T"
        
        start_time = datetime.strptime(f"{date_str}{base_start_time}", dt_format)
        end_time = datetime.strptime(f"{date_str}{base_end_time}", dt_format)
        
        # Detectar el bloque de modificadores entre paréntesis
        mod_match = re.search(r'\((.*?)\)', subject_name)
        if mod_match:
            parts = mod_match.group(1).split('/')
            for part in parts:
                part = part.strip().upper()
                # Extraer el valor numérico asegurando que empiece con la letra esperada
                if part.startswith('I+'):
                    start_time += timedelta(minutes=int(part[2:]))
                elif part.startswith('I-'):
                    start_time -= timedelta(minutes=int(part[2:]))
                elif part.startswith('F+'):
                    end_time += timedelta(minutes=int(part[2:]))
                elif part.startswith('F-'):
                    end_time -= timedelta(minutes=int(part[2:]))
                    
        result = {
            "start_time": start_time.strftime("%H:%M:%S"),
            "end_time": end_time.strftime("%H:%M:%S")
        }
        self._cache[cache_key] = result
        return result
        
    def clean_subject_name(self, subject_name: str) -> str:
        """
        Limpia el nombre del curso quitando los operadores.
        """
        return re.sub(r'\(.*?\)', '', subject_name).strip()
