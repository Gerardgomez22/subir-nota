"""
sin_pool.py - Estrategia SIN pool: abrir y cerrar una conexion nueva para cada operacion.

Este es el anti-patron clasico: cada vez que necesitamos hacer una insercion,
abrimos una conexion TCP/IP completa con PostgreSQL, la usamos y la cerramos.

Coste por conexion:
  1. Handshake TCP de 3 vias (SYN  SYN-ACK  ACK)
  2. Negociacion SSL (si aplica)
  3. Autenticacion del usuario en PostgreSQL
  4. Creacion de un proceso backend en el servidor (fork)
  5. Asignacion de memoria para el proceso
  6. Al cerrar: liberacion de recursos + cierre TCP (FIN  ACK)

Multiplicar esto por 200 operaciones resulta en un overhead enorme.

Uso:
  python sin_pool.py
"""

import time
import psycopg2

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, NUM_INSERCIONES


def insertar_sin_pool(num_inserciones: int) -> float:
    """
    Realiza N inserciones abriendo y cerrando una conexion nueva cada vez.
    Devuelve el tiempo total en segundos.
    """
    inicio = time.perf_counter()

    for i in range(num_inserciones):
        #  Abrir conexion (costoso) 
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        cursor = conn.cursor()

        #  Insertar un registro 
        cursor.execute(
            """
            INSERT INTO operaciones (dato, valor, estrategia)
            VALUES (%s, %s, %s)
            """,
            (f"dato_{i+1}", round(i * 1.5, 2), "sin_pool")
        )
        conn.commit()

        #  Cerrar conexion (costoso) 
        cursor.close()
        conn.close()

    fin = time.perf_counter()
    return fin - inicio


if __name__ == "__main__":
    print("=" * 60)
    print("  SIN POOL - Conexion nueva para cada operacion")
    print("=" * 60)
    print(f"\n  Realizando {NUM_INSERCIONES} inserciones...\n")

    tiempo = insertar_sin_pool(NUM_INSERCIONES)

    print(f"  [OK] {NUM_INSERCIONES} inserciones completadas")
    print(f"  [T] Tiempo total:   {tiempo:.4f} segundos")
    print(f"  [T] Tiempo/insercion: {tiempo/NUM_INSERCIONES*1000:.2f} ms")
    print()
    print("  [!] Cada insercion ha requerido abrir y cerrar una conexion TCP/IP")
    print("    completa con PostgreSQL (handshake + autenticacion + fork).")
