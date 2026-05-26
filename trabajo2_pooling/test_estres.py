"""
test_estres.py - Test de estres comparativo: 200 inserciones con 4 estrategias.

Este script compara el rendimiento de 4 estrategias de conexion a PostgreSQL:
  1. Sin Pool:       conexion nueva para cada operacion (anti-patron).
  2. Singleton:      una única conexion reutilizada.
  3. Pool psycopg2:  ThreadedConnectionPool de psycopg2.
  4. Pool SQLAlchemy: pool integrado en el engine de SQLAlchemy.

Para cada estrategia se mide el tiempo total de 200 inserciones.
Al finalizar se genera:
  - Una tabla comparativa en la consola.
  - Una grafica de barras guardada en resultados/comparativa.png.

Uso:
  python test_estres.py
"""

import os
import time

import psycopg2
from psycopg2 import pool as pg_pool
from sqlalchemy import create_engine, text
import matplotlib
matplotlib.use("Agg")  # Backend sin GUI para generar imagenes
import matplotlib.pyplot as plt
from tabulate import tabulate

from config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
    POOL_MIN_CONN, POOL_MAX_CONN, NUM_INSERCIONES,
    get_sqlalchemy_url
)


# ===========================================================================
#  ESTRATEGIA 1: Sin Pool - Conexion nueva cada vez
# ===========================================================================

def test_sin_pool(n: int) -> float:
    """Abre y cierra una conexion para cada insercion."""
    inicio = time.perf_counter()

    for i in range(n):
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASSWORD,
            dbname=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO operaciones (dato, valor, estrategia) VALUES (%s, %s, %s)",
            (f"stress_{i+1}", round(i * 1.5, 2), "sin_pool")
        )
        conn.commit()
        cursor.close()
        conn.close()

    return time.perf_counter() - inicio


# ===========================================================================
#  ESTRATEGIA 2: Singleton - Una única conexion
# ===========================================================================

def test_singleton(n: int) -> float:
    """Reutiliza una sola conexion para todas las inserciones."""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        dbname=DB_NAME
    )

    inicio = time.perf_counter()

    for i in range(n):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO operaciones (dato, valor, estrategia) VALUES (%s, %s, %s)",
            (f"stress_{i+1}", round(i * 1.5, 2), "singleton")
        )
        conn.commit()
        cursor.close()

    tiempo = time.perf_counter() - inicio
    conn.close()
    return tiempo


# ===========================================================================
#  ESTRATEGIA 3: Pool psycopg2 - ThreadedConnectionPool
# ===========================================================================

def test_pool_psycopg2(n: int) -> float:
    """Usa un ThreadedConnectionPool de psycopg2."""
    connection_pool = pg_pool.ThreadedConnectionPool(
        minconn=POOL_MIN_CONN,
        maxconn=POOL_MAX_CONN,
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        dbname=DB_NAME
    )

    inicio = time.perf_counter()

    for i in range(n):
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO operaciones (dato, valor, estrategia) VALUES (%s, %s, %s)",
            (f"stress_{i+1}", round(i * 1.5, 2), "pool_psycopg2")
        )
        conn.commit()
        cursor.close()
        connection_pool.putconn(conn)

    tiempo = time.perf_counter() - inicio
    connection_pool.closeall()
    return tiempo


# ===========================================================================
#  ESTRATEGIA 4: Pool SQLAlchemy - Engine con pool integrado
# ===========================================================================

def test_pool_sqlalchemy(n: int) -> float:
    """Usa el pool integrado de SQLAlchemy."""
    engine = create_engine(
        get_sqlalchemy_url(),
        pool_size=POOL_MIN_CONN,
        max_overflow=POOL_MAX_CONN - POOL_MIN_CONN,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False
    )

    inicio = time.perf_counter()

    for i in range(n):
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO operaciones (dato, valor, estrategia) "
                     "VALUES (:dato, :valor, :estrategia)"),
                {"dato": f"stress_{i+1}", "valor": round(i * 1.5, 2),
                 "estrategia": "pool_sqlalchemy"}
            )
            conn.commit()

    tiempo = time.perf_counter() - inicio
    engine.dispose()
    return tiempo


# ===========================================================================
#  GENERACIÓN DE RESULTADOS
# ===========================================================================

def limpiar_tabla():
    """Limpia la tabla antes de cada test."""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        dbname=DB_NAME
    )
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE operaciones RESTART IDENTITY")
    conn.commit()
    cursor.close()
    conn.close()


def generar_grafica(resultados: dict, carpeta: str):
    """Genera una grafica de barras comparativa y la guarda como imagen."""
    estrategias = list(resultados.keys())
    tiempos = list(resultados.values())

    # Colores profesionales para cada barra
    colores = ["#e74c3c", "#f39c12", "#2ecc71", "#3498db"]

    fig, ax = plt.subplots(figsize=(10, 6))

    barras = ax.bar(estrategias, tiempos, color=colores, width=0.6,
                    edgecolor="white", linewidth=1.5)

    # Añadir el valor encima de cada barra
    for barra, tiempo in zip(barras, tiempos):
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height() + max(tiempos) * 0.02,
            f"{tiempo:.3f}s",
            ha="center", va="bottom",
            fontsize=13, fontweight="bold", color="#2c3e50"
        )

    ax.set_title(
        f"Test de Estres - {NUM_INSERCIONES} Inserciones en PostgreSQL",
        fontsize=16, fontweight="bold", pad=20, color="#2c3e50"
    )
    ax.set_ylabel("Tiempo (segundos)", fontsize=13, color="#2c3e50")
    ax.set_xlabel("Estrategia de conexion", fontsize=13, color="#2c3e50")

    # Estilo limpio
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#bdc3c7")
    ax.spines["bottom"].set_color("#bdc3c7")
    ax.tick_params(colors="#7f8c8d", labelsize=11)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()

    ruta = os.path.join(carpeta, "comparativa.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n   Grafica guardada en: {ruta}")


def mostrar_tabla(resultados: dict):
    """Muestra una tabla comparativa formateada en la consola."""
    filas = []
    mejor_tiempo = min(resultados.values())

    for estrategia, tiempo in resultados.items():
        ms_por_op = (tiempo / NUM_INSERCIONES) * 1000
        speedup = resultados["Sin Pool"] / tiempo if tiempo > 0 else 0
        es_mejor = "*" if tiempo == mejor_tiempo else ""

        filas.append([
            estrategia,
            f"{tiempo:.4f} s",
            f"{ms_por_op:.2f} ms",
            f"{speedup:.1f}x",
            es_mejor
        ])

    print("\n" + tabulate(
        filas,
        headers=["Estrategia", "Tiempo Total", "Tiempo/Insercion",
                 "Speedup vs Sin Pool", ""],
        tablefmt="grid",
        colalign=("left", "right", "right", "right", "center")
    ))


# ===========================================================================
#  EJECUCIÓN PRINCIPAL
# ===========================================================================

if __name__ == "__main__":
    print()
    print("+==============================================================+")
    print("|    TEST DE ESTRÉS - Comparativa de Estrategias de Conexion |")
    print("+==============================================================+")
    print(f"\n  Inserciones por estrategia: {NUM_INSERCIONES}")
    print(f"  Base de datos: {DB_NAME} @ {DB_HOST}:{DB_PORT}")
    print()

    resultados = {}

    # -- Test 1: Sin Pool --
    print("  [1/4] Ejecutando: Sin Pool (conexion nueva cada vez)...")
    limpiar_tabla()
    resultados["Sin Pool"] = test_sin_pool(NUM_INSERCIONES)
    print(f"          {resultados['Sin Pool']:.4f} s")

    # -- Test 2: Singleton --
    print("  [2/4] Ejecutando: Singleton (una conexion reutilizada)...")
    limpiar_tabla()
    resultados["Singleton"] = test_singleton(NUM_INSERCIONES)
    print(f"          {resultados['Singleton']:.4f} s")

    # -- Test 3: Pool psycopg2 --
    print("  [3/4] Ejecutando: Pool psycopg2 (ThreadedConnectionPool)...")
    limpiar_tabla()
    resultados["Pool psycopg2"] = test_pool_psycopg2(NUM_INSERCIONES)
    print(f"          {resultados['Pool psycopg2']:.4f} s")

    # -- Test 4: Pool SQLAlchemy --
    print("  [4/4] Ejecutando: Pool SQLAlchemy (engine pool)...")
    limpiar_tabla()
    resultados["Pool SQLAlchemy"] = test_pool_sqlalchemy(NUM_INSERCIONES)
    print(f"          {resultados['Pool SQLAlchemy']:.4f} s")

    # -- Resultados --
    print("\n" + "=" * 62)
    print("  RESULTADOS")
    print("=" * 62)

    mostrar_tabla(resultados)

    # -- Grafica --
    carpeta_resultados = os.path.join(os.path.dirname(__file__), "resultados")
    os.makedirs(carpeta_resultados, exist_ok=True)
    generar_grafica(resultados, carpeta_resultados)

    # -- Conclusion --
    mejor = min(resultados, key=resultados.get)
    peor = max(resultados, key=resultados.get)
    speedup = resultados[peor] / resultados[mejor]

    print(f"\n   Mejor estrategia:  {mejor} ({resultados[mejor]:.4f} s)")
    print(f"   Peor estrategia:   {peor} ({resultados[peor]:.4f} s)")
    print(f"  [FAST] Speedup:           {speedup:.1f}x mas rapido")
    print()
    print("  CONCLUSIÓN:")
    print("  Abrir una conexion nueva para cada operacion es extremadamente")
    print("  costoso. El Pool de conexiones elimina ese overhead manteniendo")
    print("  conexiones pre-creadas y reutilizandolas, lo que resulta en un")
    print("  rendimiento muy superior, especialmente en entornos de produccion")
    print("  con múltiples usuarios concurrentes.")
    print()
