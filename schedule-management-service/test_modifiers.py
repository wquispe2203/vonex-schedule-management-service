from app.services.hour_modifier import HourModifierService

def test_modifiers():
    hm = HourModifierService()
    
    # Caso 1: Sin modificador
    print("Caso 1:", hm.apply_modifiers("MATEMATICA", "08:00:00", "09:40:00"))
    
    # Caso 2: Modificador antiguo F+30
    print("Caso 2:", hm.apply_modifiers("FISICA(F+30)", "10:00:00", "11:20:00"))
    
    # Caso 3: Modificador I-10 al inicio
    print("Caso 3:", hm.apply_modifiers("LENGUAJE(I-10)", "08:00:00", "09:40:00"))
    
    # Caso 4: Multiples modificadores con barra ignorando E0
    print("Caso 4:", hm.apply_modifiers("FILOSOFIA (E0/I-10/F-10)", "14:00:00", "15:40:00"))
    
    # Caso 5: Extraños y sumas
    print("Caso 5:", hm.apply_modifiers("QUIMICA(E0/F+30)", "08:00:00", "10:30:00"))

if __name__ == "__main__":
    test_modifiers()
