from sqlalchemy import text

from app.db.session import get_engine


def check_database() -> None:
    engine = get_engine()
    with engine.connect() as connection:
        connection.execute(text("select 1"))

