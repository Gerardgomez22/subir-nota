"""
singleton.py - Estrategia Singleton: una única conexion compartida.

El patron Singleton garantiza que solo existe UNA instancia de la conexion
a la base de datos en toda la aplicacion. Se reutiliza para todas las operaciones.

Ventajas:
  [OK] Elimina el overhead de abrir/cerrar conexiones repetidamente.
  [OK] Simple de implementar.

Limitaciones (por que NO es suficiente en entornos multiusuario):
  [X] Cuello de botella: si 10 usuarios necesitan la BBDD al mismo tiempo,
    todos deben esperar a que el anterior termine (acceso secuencial).
  [X] Si la conexion se rompe (timeout, reinicio del servidor), toda la
    aplicacion pierde acceso hasta que se detecte y reconecte manualmente.
  [X] No es thread-safe por defecto: compartir una conexion entre hilos
    puede producir errores de concurrencia.

Uso:
  python singleton.py
"""

import time
import psycopg2

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, NUM_INSERCIONES


class SingletonConnection:
    """
    Implementacion del patron Singleton para la conexion a PostgreSQL.

    Solo se crea UNA conexion, sin importar cuantas veces se llame a get_connection().
    """

    _instancia = None   # Referencia a la única instancia de la clase
    _conexion = None    # La conexion a PostgreSQL

    def __new__(cls):
        """Controla la creacion de instancias: solo permite una."""
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._conexion = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                dbname=DB_NAME
            )
            print("  [Singleton] Conexion creada (única vez).")
        return cls._instancia

    @classmethod
    def get_connection(cls):
        """Devuelve la conexion única."""
        if cls._instancia is None:
            cls()
        return cls._conexion

    @classmethod
    def close(cls):
        """Cierra la conexion y resetea el Singleton."""
        if cls._conexion is not None:
            cls._conexion.close()
            cls._conexion = None
            cls._instancia = None
            print("  [Singleton] Conexion cerrada.")


def insertar_singleton(num_inserciones: int) -> float:
    """
    Realiza N inserciones usando una única conexion Singleton.
    Devuelve el tiempo total en segundos.
    """
    inicio = time.perf_counter()

    conn = SingletonConnection.get_connection()

    for i in range(num_inserciones):
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO operaciones (dato, valor, estrategia)
            VALUES (%s, %s, %s)
            """,
            (f"dato_{i+1}", round(i * 1.5, 2), "singleton")
        )
        conn.commit()
        cursor.close()

    fin = time.perf_counter()
    return fin - inicio


if __name__ == "__main__":
    print("=" * 60)
    print("  SINGLETON - Una única conexion reutilizada")
    print("=" * 60)
    print(f"\n  Realizando {NUM_INSERCIONES} inserciones...\n")

    tiempo = insertar_singleton(NUM_INSERCIONES)

    print(f"\n  [OK] {NUM_INSERCIONES} inserciones completadas")
    print(f"  [T] Tiempo total:   {tiempo:.4f} segundos")
    print(f"  [T] Tiempo/insercion: {tiempo/NUM_INSERCIONES*1000:.2f} ms")
    print()
    print("  [i] Una sola conexion = rapido, pero no escala con múltiples usuarios.")

    SingletonConnection.close()
