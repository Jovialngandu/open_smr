import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

NEW_DB_NAME = os.getenv("POSTGRES_DB", "open_smr_db")
NEW_DB_USER = os.getenv("POSTGRES_USER", "open_smr_user")
NEW_DB_PASS = os.getenv("POSTGRES_PASSWORD", "super_password_123!")
DB_ADMIN_PASS = os.getenv("DB_ADMIN_PASS", "postgres") # Remplacer 'postgres' par le pass local si défini

try:
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password=DB_ADMIN_PASS,
        host="127.0.0.1"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Vérification si l'utilisateur existe déjà
    cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname='{NEW_DB_USER}';")
    if not cursor.fetchone():
        cursor.execute(f"CREATE USER {NEW_DB_USER} WITH PASSWORD '{NEW_DB_PASS}';")
        print(f"Utilisateur '{NEW_DB_USER}' créé avec succès.")
    else:
        print(f"Utilisateur '{NEW_DB_USER}' existe déjà.")

    # Vérification si la base de données existe déjà
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname='{NEW_DB_NAME}';")
    if not cursor.fetchone():
        cursor.execute(f"CREATE DATABASE {NEW_DB_NAME} OWNER {NEW_DB_USER};")
        print(f"Base de données '{NEW_DB_NAME}' créée avec succès.")
    else:
        print(f"Base de données '{NEW_DB_NAME}' existe déjà.")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Erreur : {e}")