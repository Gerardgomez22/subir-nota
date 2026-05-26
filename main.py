import time
from src.database import setup_database
from src.test_singleton import run_singleton_test
from src.test_pool import run_pool_test


def main():
    setup_database()

    start_singleton = time.time()
    run_singleton_test()
    end_singleton = time.time()
    singleton_ms = (end_singleton - start_singleton) * 1000

    start_pool = time.time()
    run_pool_test()
    end_pool = time.time()
    pool_ms = (end_pool - start_pool) * 1000

    diferencia = singleton_ms - pool_ms

    print("=" * 50)
    print("RESULTADOS DEL TEST DE ESTRES")
    print("=" * 50)
    print(f"Singleton (200 inserts): {singleton_ms:.2f} ms")
    print(f"Pool      (200 inserts): {pool_ms:.2f} ms")
    print("-" * 50)
    print(f"Diferencia:              {diferencia:.2f} ms")
    print(f"El Pool es {singleton_ms / pool_ms:.2f}x mas rapido")
    print("=" * 50)


if __name__ == "__main__":
    main()
