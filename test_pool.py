from src.database import get_pool


def run_pool_test():
    connection_pool = get_pool(minconn=1, maxconn=10)
    for _ in range(200):
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO stress_test (test_type) VALUES ('pool')")
        conn.commit()
        cursor.close()
        connection_pool.putconn(conn)
    connection_pool.closeall()
