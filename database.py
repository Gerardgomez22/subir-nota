import psycopg2
from psycopg2 import pool

DB_CONFIG = {
    "dbname": "testdb",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_pool(minconn=1, maxconn=10):
    return psycopg2.pool.SimpleConnectionPool(minconn, maxconn, **DB_CONFIG)


def setup_database():
    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS stress_test ("
        "id SERIAL PRIMARY KEY, "
        "insert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "test_type VARCHAR(50))"
    )
    cursor.execute("TRUNCATE TABLE stress_test")
    cursor.close()
    conn.close()
