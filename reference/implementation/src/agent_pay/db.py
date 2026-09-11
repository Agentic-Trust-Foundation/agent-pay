"""Small PostgreSQL connection helper for the reference implementation."""
from contextlib import contextmanager
import os
from typing import Iterator

import psycopg


def database_url() -> str:
    return os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/agent_pay")


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(database_url())
    try:
        yield conn
    finally:
        conn.close()
