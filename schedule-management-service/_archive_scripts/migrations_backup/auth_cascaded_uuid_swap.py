import psycopg
from app.database import SQLALCHEMY_DATABASE_URL

def migrate_auth_to_uuid():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                print("--- INICIANDO MIGRACIÓN CASCADA DE AUTENTICACIÓN ---")
                
                # 1. Preparar ROLES
                print("1. Migrando tabla 'roles'...")
                cur.execute("ALTER TABLE roles ADD COLUMN IF NOT EXISTS id_uuid UUID DEFAULT gen_random_uuid();")
                cur.execute("ALTER TABLE roles ADD COLUMN IF NOT EXISTS legacy_id INTEGER;")
                cur.execute("UPDATE roles SET legacy_id = id;")
                # No podemos hacer el swap de PK todavía hasta que todo esté poblado
                
                # 2. Preparar PERMISSIONS
                print("2. Migrando tabla 'permissions'...")
                cur.execute("ALTER TABLE permissions ADD COLUMN IF NOT EXISTS id_uuid UUID DEFAULT gen_random_uuid();")
                cur.execute("ALTER TABLE permissions ADD COLUMN IF NOT EXISTS legacy_id INTEGER;")
                cur.execute("UPDATE permissions SET legacy_id = id;")
                
                # 3. Poblar USER_ROLES
                print("3. Poblando 'user_roles' con UUIDs...")
                # Poblar user_uid (usando users.legacy_id)
                cur.execute("""
                    UPDATE user_roles ur
                    SET user_uid = u.id
                    FROM users u
                    WHERE ur.user_id = u.legacy_id;
                """)
                # Poblar role_uid (usando roles.legacy_id)
                cur.execute("""
                    UPDATE user_roles ur
                    SET role_uid = r.id_uuid
                    FROM roles r
                    WHERE ur.role_id = r.legacy_id;
                """)
                
                # 4. Poblar ROLE_PERMISSIONS
                print("4. Poblando 'role_permissions' con UUIDs...")
                cur.execute("""
                    UPDATE role_permissions rp
                    SET role_uid = r.id_uuid
                    FROM roles r
                    WHERE rp.role_id = r.legacy_id;
                """)
                cur.execute("""
                    UPDATE role_permissions rp
                    SET permission_uid = p.id_uuid
                    FROM permissions p
                    WHERE rp.permission_id = p.legacy_id;
                """)
                
                # 5. EL GRAN SWAP (Físico)
                print("5. Ejecutando Swap Físico y Constraints...")
                
                # --- ROLES ---
                cur.execute("ALTER TABLE user_roles DROP CONSTRAINT IF EXISTS user_roles_role_id_fkey;")
                cur.execute("ALTER TABLE role_permissions DROP CONSTRAINT IF EXISTS role_permissions_role_id_fkey;")
                cur.execute("ALTER TABLE roles DROP CONSTRAINT IF EXISTS roles_pkey CASCADE;")
                cur.execute("ALTER TABLE roles RENAME COLUMN id TO old_id_to_purge;")
                cur.execute("ALTER TABLE roles RENAME COLUMN id_uuid TO id;")
                cur.execute("ALTER TABLE roles ADD PRIMARY KEY (id);")
                
                # --- PERMISSIONS ---
                cur.execute("ALTER TABLE role_permissions DROP CONSTRAINT IF EXISTS role_permissions_permission_id_fkey;")
                cur.execute("ALTER TABLE permissions DROP CONSTRAINT IF EXISTS permissions_pkey CASCADE;")
                cur.execute("ALTER TABLE permissions RENAME COLUMN id TO old_id_to_purge;")
                cur.execute("ALTER TABLE permissions RENAME COLUMN id_uuid TO id;")
                cur.execute("ALTER TABLE permissions ADD PRIMARY KEY (id);")
                
                # --- USER_ROLES ---
                cur.execute("ALTER TABLE user_roles RENAME COLUMN user_id TO legacy_user_id;")
                cur.execute("ALTER TABLE user_roles RENAME COLUMN role_id TO legacy_role_id;")
                cur.execute("ALTER TABLE user_roles RENAME COLUMN user_uid TO user_id;")
                cur.execute("ALTER TABLE user_roles RENAME COLUMN role_uid TO role_id;")
                cur.execute("ALTER TABLE user_roles ADD CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id);")
                cur.execute("ALTER TABLE user_roles ADD CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id);")
                
                # --- ROLE_PERMISSIONS ---
                cur.execute("ALTER TABLE role_permissions RENAME COLUMN role_id TO legacy_role_id;")
                cur.execute("ALTER TABLE role_permissions RENAME COLUMN permission_id TO legacy_permission_id;")
                cur.execute("ALTER TABLE role_permissions RENAME COLUMN role_uid TO role_id;")
                cur.execute("ALTER TABLE role_permissions RENAME COLUMN permission_uid TO permission_id;")
                cur.execute("ALTER TABLE role_permissions ADD CONSTRAINT fk_role_perms_role FOREIGN KEY (role_id) REFERENCES roles(id);")
                cur.execute("ALTER TABLE role_permissions ADD CONSTRAINT fk_role_perms_perm FOREIGN KEY (permission_id) REFERENCES permissions(id);")
                
                # 6. Limpiar tablas secundarias (Purificación)
                cur.execute("ALTER TABLE roles DROP COLUMN old_id_to_purge;")
                cur.execute("ALTER TABLE permissions DROP COLUMN old_id_to_purge;")
                
                print("  [SUCCESS] Migración Cascada completada exitosamente.")
                conn.commit()
    except Exception as e:
        print(f"  [ERROR] Fallo en la migración cascada: {e}")
        raise

if __name__ == "__main__":
    migrate_auth_to_uuid()
