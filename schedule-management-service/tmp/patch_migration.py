import re

migration_path = "migrations/versions/18d9f168a2eb_rename_legacy_id_to_old_system_id_.py"
with open(migration_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace op.add_column + op.drop_column with op.alter_column
tables = ['cards', 'classes', 'lessons', 'observations', 'permissions', 'roles', 'rpt_planilla', 'schedule_sessions', 'teachers', 'users', 'xml_change_logs', 'xml_upload_logs', 'xml_uploads']
for table in tables:
    # Rename legacy_id
    content = content.replace(
        f"op.add_column('{table}', sa.Column('old_system_id', sa.Integer(), nullable=True))\n",
        f"op.alter_column('{table}', 'legacy_id', new_column_name='old_system_id')\n"
    )
    content = re.sub(f"\\s*op\\.drop_column\\('{table}', 'legacy_id'\\)\n", "\n", content)

# Special cases for lessons
content = content.replace(
"    op.add_column('lessons', sa.Column('old_system_subject_id', sa.Integer(), nullable=True))\n",
"    op.alter_column('lessons', 'legacy_subject_id', new_column_name='old_system_subject_id')\n"
)
content = re.sub("    op\\.drop_column\\('lessons', 'legacy_subject_id'\\)\n", "", content)

content = content.replace(
"    op.add_column('lessons', sa.Column('old_system_teacher_id', sa.Integer(), nullable=True))\n",
"    op.alter_column('lessons', 'legacy_teacher_id', new_column_name='old_system_teacher_id')\n"
)
content = re.sub("    op\\.drop_column\\('lessons', 'legacy_teacher_id'\\)\n", "", content)

content = content.replace(
"    op.add_column('lessons', sa.Column('old_system_class_id', sa.Integer(), nullable=True))\n",
"    op.alter_column('lessons', 'legacy_class_id', new_column_name='old_system_class_id')\n"
)
content = re.sub("    op\\.drop_column\\('lessons', 'legacy_class_id'\\)\n", "", content)


# Special cases for observations
content = content.replace(
"    op.add_column('observations', sa.Column('old_system_session_id', sa.Integer(), nullable=True))\n",
"    op.alter_column('observations', 'legacy_session_id', new_column_name='old_system_session_id')\n"
)
content = re.sub("    op\\.drop_column\\('observations', 'legacy_session_id'\\)\n", "", content)

content = content.replace(
"    op.add_column('observations', sa.Column('old_system_teacher_id', sa.Integer(), nullable=True))\n",
"    op.alter_column('observations', 'legacy_teacher_id', new_column_name='old_system_teacher_id')\n"
)
content = re.sub("    op\\.drop_column\\('observations', 'legacy_teacher_id'\\)\n", "", content)


# For downgrade:
for table in tables:
    content = content.replace(
        f"op.add_column('{table}', sa.Column('legacy_id', sa.INTEGER(), autoincrement=False, nullable=True))\n",
        f"op.alter_column('{table}', 'old_system_id', new_column_name='legacy_id')\n"
    )
    content = re.sub(f"\\s*op\\.drop_column\\('{table}', 'old_system_id'\\)\n", "\n", content)

content = content.replace(
"    op.add_column('lessons', sa.Column('legacy_subject_id', sa.INTEGER(), autoincrement=False, nullable=True))\n",
"    op.alter_column('lessons', 'old_system_subject_id', new_column_name='legacy_subject_id')\n"
)
content = re.sub("    op\\.drop_column\\('lessons', 'old_system_subject_id'\\)\n", "", content)

content = content.replace(
"    op.add_column('lessons', sa.Column('legacy_class_id', sa.INTEGER(), autoincrement=False, nullable=True))\n",
"    op.alter_column('lessons', 'old_system_class_id', new_column_name='legacy_class_id')\n"
)
content = re.sub("    op\\.drop_column\\('lessons', 'old_system_class_id'\\)\n", "", content)

content = content.replace(
"    op.add_column('lessons', sa.Column('legacy_teacher_id', sa.INTEGER(), autoincrement=False, nullable=True))\n",
"    op.alter_column('lessons', 'old_system_teacher_id', new_column_name='legacy_teacher_id')\n"
)
content = re.sub("    op\\.drop_column\\('lessons', 'old_system_teacher_id'\\)\n", "", content)

content = content.replace(
"    op.add_column('observations', sa.Column('legacy_session_id', sa.INTEGER(), autoincrement=False, nullable=True))\n",
"    op.alter_column('observations', 'old_system_session_id', new_column_name='legacy_session_id')\n"
)
content = re.sub("    op\\.drop_column\\('observations', 'old_system_session_id'\\)\n", "", content)

content = content.replace(
"    op.add_column('observations', sa.Column('legacy_teacher_id', sa.INTEGER(), autoincrement=False, nullable=True))\n",
"    op.alter_column('observations', 'old_system_teacher_id', new_column_name='legacy_teacher_id')\n"
)
content = re.sub("    op\\.drop_column\\('observations', 'old_system_teacher_id'\\)\n", "", content)


with open(migration_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Migration script patched to RENAME instead of DROP/ADD.")
