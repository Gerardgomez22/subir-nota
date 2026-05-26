"""
Configuración centralizada para la conexión a PostgreSQL.
Modifica estos valores según tu entorno.
"""

# ─── Parámetros de conexión a PostgreSQL ────────────────────────────────
DB_HOST = "localhost"
DB_PORT = 5433
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "pooling_test"

# ─── Parámetros del Pool ────────────────────────────────────────────────
POOL_MIN_CONN = 2      # Conexiones mínimas mantenidas abiertas
POOL_MAX_CONN = 10     # Conexiones máximas permitidas

# ─── Parámetros del Test de Estrés ──────────────────────────────────────
NUM_INSERCIONES = 200   # Número de inserciones para el test de estrés


def get_dsn() -> str:
    """Devuelve el DSN (Data Source Name) para psycopg2."""
    return (
        f"host={DB_HOST} port={DB_PORT} "
        f"user={DB_USER} password={DB_PASSWORD} "
        f"dbname={DB_NAME}"
    )


def get_sqlalchemy_url() -> str:
    """Devuelve la URL de conexión para SQLAlchemy."""
    return (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
