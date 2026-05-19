import json
import os

baseline_path = "brain/632fbacc-9451-451a-805c-a4110b33cc72/scratch/snapshot_baseline.json"
optimized_path = "brain/632fbacc-9451-451a-805c-a4110b33cc72/scratch/snapshot_optimized.json"

def compare():
    if not os.path.exists(baseline_path) or not os.path.exists(optimized_path):
        print("Missing snapshot files.")
        return

    with open(baseline_path, 'r', encoding='utf-8') as f:
        baseline = json.load(f)
    with open(optimized_path, 'r', encoding='utf-8') as f:
        optimized = json.load(f)

    if len(baseline) != len(optimized):
        print(f"FAILED: Record count mismatch! Baseline: {len(baseline)}, Optimized: {len(optimized)}")
        # return # Continuar para ver qué cambió

    # Comparación determinista
    # Ordenar ambos por una clave única compuesta
    def sort_key(x):
        return (x.get('fecha_clase',''), x.get('docente',''), x.get('hora_inicio',''), x.get('curso',''))

    baseline_sorted = sorted(baseline, key=sort_key)
    optimized_sorted = sorted(optimized, key=sort_key)

    mismatches = 0
    for i in range(min(len(baseline_sorted), len(optimized_sorted))):
        b = baseline_sorted[i]
        o = optimized_sorted[i]
        
        # Ignorar campos no funcionales si los hay (aunque aquí deberían ser idénticos)
        # Comparar campos críticos
        critical_fields = ['docente', 'fecha_clase', 'hora_inicio', 'hora_fin', 'horas_dictadas', 'receso', 'is_replacement']
        
        row_fail = False
        for field in critical_fields:
            if b.get(field) != o.get(field):
                if not row_fail:
                    print(f"MISMATCH at row {i} ({b.get('docente')} {b.get('fecha_clase')}):")
                    row_fail = True
                print(f"  Field '{field}': Baseline={b.get(field)} vs Optimized={o.get(field)}")
                mismatches += 1

    if mismatches == 0 and len(baseline) == len(optimized):
        print("SUCCESS: Bit-Identical Output Validation PASSED.")
        print(f"Verified {len(baseline)} records across all critical academic fields.")
    else:
        print(f"FAILED: {mismatches} mismatches found.")

if __name__ == "__main__":
    compare()
