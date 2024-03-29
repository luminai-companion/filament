import sqlite3

from app.config import config

# look i know this is the worst thing in the world but i don't feel like using migrations


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(f"{config.ai_data_dir}/luminai.db")

    return conn


def initialize_db() -> bool:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
create table if not exists memory_books (
    memory_book_id text,
    source text,
    kind text,
    name text,
    description text,
    primary key(memory_book_id)
)
    """
    )

    cur.execute(
        """
create table if not exists memories (
    memory_book_id text,
    memory_id integer,
    source text,
    entry text,
    priority real,
    weight real,
    enabled integer,
    primary key (memory_book_id, memory_id)
)
    """
    )

    conn.commit()

    return True


initialize_db()
