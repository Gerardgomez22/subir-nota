"""
pool_psycopg2.py - Estrategia con Pool de conexiones usando psycopg2.pool.

psycopg2 incluye varios tipos de pool:
  - SimpleConnectionPool:  para aplicaciones de un solo hilo.
  - ThreadedConnectionPool: thread-safe, para aplicaciones multiusuario.

En este ejemplo usamos ThreadedConnectionPool, que es el mas realista
para un entorno de produccion.

Como funciona:
  1. Al crear el pool, se abren 'minconn' conexiones de inmediato.
  2. Cuando se solicita una conexion con getconn(), el pool devuelve una
     conexion libre. Si no hay ninguna disponible y no se ha alcanzado
     'maxconn', se crea una nueva.
  3. Cuando se devuelve la conexion con putconn(), NO se cierra: se marca
     como disponible para reutilizar.
  4. Esto elimina el overhead de abrir/cerrar conexiones TCP/IP.

Parametros clave:
  - minconn: conexiones que se crean al iniciar (pre-calentamiento).
  - maxconn: limite maximo de conexiones simultaneas.

Uso:
  python pool_psycopg2.py
"""

import time
from psycopg2 import pool as pg_pool

from config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
    POOL_MIN_CONN, POOL_MAX_CONN, NUM_INSERCIONES
)


def crear_pool() -> pg_pool.ThreadedConnectionPool:
    """Crea y devuelve un ThreadedConnectionPool configurado."""
    connection_pool = pg_pool.ThreadedConnectionPool(
        minconn=POOL_MIN_CONN,
        maxconn=POOL_MAX_CONN,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
    print(f"  [Pool psycopg2] Creado con min={POOL_MIN_CONN}, max={POOL_MAX_CONN}")
    return connection_pool


def insertar_pool_psycopg2(num_inserciones: int) -> float:
    """
    Realiza N inserciones usando un ThreadedConnectionPool.
    Devuelve el tiempo total en segundos.
    """
    connection_pool = crear_pool()

    inicio = time.perf_counter()

    for i in range(num_inserciones):
        #  Obtener conexion del pool (rapido, sin handshake TCP) 
        conn = connection_pool.getconn()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO operaciones (dato, valor, estrategia)
            VALUES (%s, %s, %s)
            """,
            (f"dato_{i+1}", round(i * 1.5, 2), "pool_psycopg2")
        )
        conn.commit()
        cursor.close()

        #  Devolver conexion al pool (NO se cierra, se reutiliza) 
        connection_pool.putconn(conn)

    fin = time.perf_counter()

    # Cerrar todas las conexiones del pool al finalizar
    connection_pool.closeall()
    print("  [Pool psycopg2] Pool cerrado.")

    return fin - inicio


if __name__ == "__main__":
    print("=" * 60)
    print("  POOL psycopg2 - ThreadedConnectionPool")
    print("=" * 60)
    print(f"\n  Realizando {NUM_INSERCIONES} inserciones...\n")

    tiempo = insertar_pool_psycopg2(NUM_INSERCIONES)

    print(f"\n  [OK] {NUM_INSERCIONES} inserciones completadas")
    print(f"  [T] Tiempo total:   {tiempo:.4f} segundos")
    print(f"  [T] Tiempo/insercion: {tiempo/NUM_INSERCIONES*1000:.2f} ms")
    print()
    print("  [i] Las conexiones se reutilizan del pool sin overhead TCP.")
