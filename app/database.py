import sqlite3
import os


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'patient'
);
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'Family',
    photo_url TEXT,
    date_label TEXT
);
CREATE TABLE IF NOT EXISTS mindmap_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'Family',
    photo_url TEXT
);
CREATE TABLE IF NOT EXISTS mindmap_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    time_label TEXT NOT NULL,
    complete INTEGER NOT NULL DEFAULT 0,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    game TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    difficulty INTEGER NOT NULL DEFAULT 1,
    created_at TEXT
);
"""

PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'patient'
);
CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'Family',
    photo_url TEXT,
    date_label TEXT
);
CREATE TABLE IF NOT EXISTS mindmap_nodes (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'Family',
    photo_url TEXT
);
CREATE TABLE IF NOT EXISTS mindmap_edges (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    time_label TEXT NOT NULL,
    complete INTEGER NOT NULL DEFAULT 0,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    game TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    difficulty INTEGER NOT NULL DEFAULT 1,
    created_at TEXT
);
"""


class PGCursor:
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is not None and "id" in row:
            self.lastrowid = row["id"]
        return row

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self):
        return self._cursor.rowcount


class PGConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql, params=()):
        translated = sql.replace("?", "%s")
        stripped = translated.strip().upper()
        if stripped.startswith("INSERT ") and "RETURNING" not in stripped:
            translated = translated.rstrip().rstrip(";") + " RETURNING id"
        cursor = PGCursor(self._connection.execute(translated, params))
        if stripped.startswith("INSERT "):
            cursor.fetchone()
        return cursor

    def executemany(self, sql, params):
        translated = sql.replace("?", "%s")
        return self._connection.executemany(translated, params)

    def commit(self):
        self._connection.commit()

    def close(self):
        self._connection.close()


def init_db(app):
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if uri.startswith(("postgresql://", "postgres://")):
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("PostgreSQL support requires the psycopg package.") from error
        connection = psycopg.connect(uri, row_factory=psycopg.rows.dict_row)
        for statement in PG_SCHEMA.split(";"):
            statement = statement.strip()
            if statement:
                connection.execute(statement)
        connection.commit()
        connection.close()
        app.config["DATABASE_PATH"] = uri
        return
    path = uri.replace("sqlite:///", "", 1)
    if not path.startswith("/") and ":" not in path:
        path = path
    app.config["DATABASE_PATH"] = path

    connection = sqlite3.connect(path)
    connection.executescript(SCHEMA)
    connection.commit()
    connection.close()


def get_db(app):
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if uri.startswith(("postgresql://", "postgres://")):
        import psycopg
        return PGConnection(psycopg.connect(uri, row_factory=psycopg.rows.dict_row))
    connection = sqlite3.connect(app.config["DATABASE_PATH"])
    connection.row_factory = sqlite3.Row
    return connection