"""
pool_sqlalchemy.py - Estrategia con Pool de conexiones usando SQLAlchemy.

SQLAlchemy incluye un sistema de pooling integrado y mas sofisticado que
el de psycopg2. Al crear un 'engine', SQLAlchemy gestiona automaticamente
un pool de conexiones bajo el capo.

Parametros clave del pool en SQLAlchemy:
  - pool_size:     número de conexiones permanentes en el pool (por defecto 5).
  - max_overflow:  conexiones adicionales temporales permitidas si el pool
                   esta lleno (por defecto 10).
  - pool_timeout:  segundos maximos de espera para obtener una conexion
                   antes de lanzar un error (por defecto 30).
  - pool_recycle:  segundos tras los cuales una conexion se recicla
                   (se cierra y reabre) para evitar conexiones obsoletas
                   por timeouts del servidor (por defecto -1 = desactivado).
  - pool_pre_ping: si es True, SQLAlchemy hace un "ping" antes de usar una
                   conexion para verificar que sigue viva (evita errores
                   de conexion cerrada por el servidor).

Ventajas sobre psycopg2.pool:
  [OK] Gestion automatica del ciclo de vida de las conexiones.
  [OK] Reciclado automatico de conexiones obsoletas.
  [OK] Pool pre-ping para deteccion de conexiones muertas.
  [OK] Integracion nativa con el ORM de SQLAlchemy.

Uso:
  python pool_sqlalchemy.py
"""

import time
from sqlalchemy import create_engine, text

from config import (
    get_sqlalchemy_url,
    POOL_MIN_CONN, POOL_MAX_CONN, NUM_INSERCIONES
)


def crear_engine():
    """Crea y devuelve un engine de SQLAlchemy con pool configurado."""
    engine = create_engine(
        get_sqlalchemy_url(),
        pool_size=POOL_MIN_CONN,          # Conexiones permanentes en el pool
        max_overflow=POOL_MAX_CONN - POOL_MIN_CONN,  # Conexiones extra temporales
        pool_timeout=30,                  # Tiempo maximo de espera (seg)
        pool_recycle=1800,                # Reciclar conexiones cada 30 min
        pool_pre_ping=True,               # Verificar conexion antes de usar
        echo=False                        # No mostrar SQL generado
    )
    print(f"  [Pool SQLAlchemy] Engine creado con pool_size={POOL_MIN_CONN}, "
          f"max_overflow={POOL_MAX_CONN - POOL_MIN_CONN}")
    return engine


def insertar_pool_sqlalchemy(num_inserciones: int) -> float:
    """
    Realiza N inserciones usando el pool de SQLAlchemy.
    Devuelve el tiempo total en segundos.
    """
    engine = crear_engine()

    inicio = time.perf_counter()

    for i in range(num_inserciones):
        #  SQLAlchemy gestiona el pool automaticamente con 'with' 
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO operaciones (dato, valor, estrategia)
                    VALUES (:dato, :valor, :estrategia)
                """),
                {
                    "dato": f"dato_{i+1}",
                    "valor": round(i * 1.5, 2),
                    "estrategia": "pool_sqlalchemy"
                }
            )
            conn.commit()
        # Al salir del 'with', la conexion se DEVUELVE al pool (no se cierra)

    fin = time.perf_counter()

    # Cerrar el engine y todas las conexiones del pool
    engine.dispose()
    print("  [Pool SQLAlchemy] Engine cerrado.")

    return fin - inicio


if __name__ == "__main__":
    print("=" * 60)
    print("  POOL SQLAlchemy - Pool integrado en el engine")
    print("=" * 60)
    print(f"\n  Realizando {NUM_INSERCIONES} inserciones...\n")

    tiempo = insertar_pool_sqlalchemy(NUM_INSERCIONES)

    print(f"\n  [OK] {NUM_INSERCIONES} inserciones completadas")
    print(f"  [T] Tiempo total:   {tiempo:.4f} segundos")
    print(f"  [T] Tiempo/insercion: {tiempo/NUM_INSERCIONES*1000:.2f} ms")
    print()
    print("  [i] SQLAlchemy gestiona el pool automaticamente con pool_pre_ping,")
    print("    pool_recycle y control de overflow.")
