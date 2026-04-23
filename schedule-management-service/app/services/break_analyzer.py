from sqlalchemy.orm import Session
from app.models import BreakConfig

class BreakAnalyzerService:
    def __init__(self):
        self.breaks = []
        
    def load_breaks(self, db: Session):
        """Carga la configuración de recesos desde la BD al inicializar el servicio"""
        self.breaks = [] # Reset to avoid duplicates on reload
        try:
            records = db.query(BreakConfig).all()
            for r in records:
                self.breaks.append({
                    "start_time": r.start_time.strftime('%H:%M:%S') if r.start_time else "00:00:00",
                    "end_time": r.end_time.strftime('%H:%M:%S') if r.end_time else "00:00:00",
                    "description": r.description 
                })
        except Exception as e:
            print(f"Error loading breaks in BreakAnalyzerService: {e}")
            self.breaks = []
            
    def analyze_breaks_for_day(self, sessions_of_day: list) -> list:
        """Comprueba e inserta recesos en un día particular."""
        return self.breaks
