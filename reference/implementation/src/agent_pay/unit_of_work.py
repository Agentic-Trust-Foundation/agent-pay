"""Transaction boundary for financial mutations."""
from contextlib import AbstractContextManager

from psycopg import Connection


class UnitOfWork(AbstractContextManager):
    def __init__(self, conn: Connection):
        self.conn = conn

    def __enter__(self):
        self.conn.execute("BEGIN")
        return self

    def commit(self) -> None:
        self.conn.commit()

    def rollback(self) -> None:
        self.conn.rollback()

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        return False
