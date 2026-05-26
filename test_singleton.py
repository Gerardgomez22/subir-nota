from src.database import get_connection


def run_singleton_test():
    for _ in range(200):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO stress_test (test_type) VALUES ('singleton')")
        conn.commit()
        cursor.close()
        conn.close()
