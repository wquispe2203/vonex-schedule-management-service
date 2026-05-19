import os
from pathlib import Path

brain_dir = Path("C:/Users/SISTEMAS2/.gemini/antigravity/brain/632fbacc-9451-451a-805c-a4110b33cc72")
out_path = Path("d:/Desktop/MOD HOR/schedule-management-service/scratch/overview_extracted.txt")

extracted = []
for p in brain_dir.glob("*.md"):
    content = p.read_text(encoding="utf-8")
    if "sin asignar" in content.lower() or "conflicto" in content.lower() or "docente" in content.lower():
        extracted.append(f"=== File: {p.name} ===")
        extracted.append(content)
        extracted.append("\n" + "="*40 + "\n")

out_path.write_text("\n".join(extracted), encoding="utf-8")
print(f"Extracted to {out_path}")
