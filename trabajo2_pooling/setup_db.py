"""
setup_db.py - Preparacion de la base de datos para los tests de pooling.

Este script:
  1. Se conecta al servidor PostgreSQL.
  2. Crea la base de datos 'pooling_test' si no existe.
  3. Crea la tabla 'operaciones' para las pruebas de insercion.
  4. Limpia datos anteriores si existen.

Uso:
  python setup_db.py
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def crear_base_datos():
    """Crea la base de datos si no existe."""
    print(f"[1/3] Comprobando si la base de datos '{DB_NAME}' existe...")

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname="postgres"  # Nos conectamos a la BBDD por defecto
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Comprobar si la BBDD ya existe
    cursor.execute(
        "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
        (DB_NAME,)
    )
    existe = cursor.fetchone()

    if not existe:
        cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"  [OK] Base de datos '{DB_NAME}' creada correctamente.")
    else:
        print(f"  [OK] La base de datos '{DB_NAME}' ya existe.")

    cursor.close()
    conn.close()


def crear_tabla():
    """Crea la tabla 'operaciones' para las pruebas."""
    print("[2/3] Creando tabla 'operaciones'...")

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operaciones (
            id          SERIAL PRIMARY KEY,
            dato        VARCHAR(100) NOT NULL,
            valor       NUMERIC(10, 2) NOT NULL,
            estrategia  VARCHAR(30) NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    print("  [OK] Tabla 'operaciones' lista.")

    cursor.close()
    conn.close()


def limpiar_datos():
    """Elimina los datos de pruebas anteriores."""
    print("[3/3] Limpiando datos de pruebas anteriores...")

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
    cursor = conn.cursor()

    cursor.execute("TRUNCATE TABLE operaciones RESTART IDENTITY")
    conn.commit()

    print("  [OK] Datos anteriores eliminados.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  SETUP - Preparacion de la Base de Datos")
    print("=" * 60)
    print()

    try:
        crear_base_datos()
        crear_tabla()
        limpiar_datos()

        print()
        print("=" * 60)
        print("  [OK] Todo listo! Ya puedes ejecutar los tests.")
        print("=" * 60)

    except psycopg2.OperationalError as e:
        print()
        print("=" * 60)
        print("  [X] ERROR DE CONEXION")
        print("=" * 60)
        print(f"\n  No se pudo conectar a PostgreSQL: {e}")
        print("\n  Comprueba que:")
        print("    1. PostgreSQL esta corriendo (o ejecuta: docker-compose up -d)")
        print("    2. Los datos de config.py son correctos")
        print(f"    3. El servidor esta accesible en {DB_HOST}:{DB_PORT}")
