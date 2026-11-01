from sqlalchemy import create_engine, text

from app.core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def check_database_connection() -> bool:
    """Return whether PostgreSQL can execute a simple query."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
