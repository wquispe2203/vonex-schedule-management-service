import re

with open("app/models.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace legacy_id with old_system_id, taking care of index=True
content = re.sub(
    r'legacy_(id|teacher_id|subject_id|class_id|session_id)(\s*)=\s*Column\((.*?)(,\s*index=True)?(.*?)\)',
    r'old_system_\1\2= Column(\3\5)',
    content
)

with open("app/models.py", "w", encoding="utf-8") as f:
    f.write(content)
print("models.py actualizado con éxito.")
