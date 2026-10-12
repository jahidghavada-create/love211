from datetime import datetime, timezone
from pathlib import Path
import sqlite3


SCHEMA_VERSION = 1


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exception_type, exception_value, traceback):
        try:
            return super().__exit__(exception_type, exception_value, traceback)
        finally:
            self.close()


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect_database(database_path):
    connection = sqlite3.connect(database_path, timeout=10, factory=ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def initialize_database(database_path):
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists() and path.stat().st_size > 0
    if existed:
        with connect_database(path) as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version > SCHEMA_VERSION:
                raise RuntimeError("The database was created by a newer app version.")
            if version < SCHEMA_VERSION:
                backup_path = path.with_name(
                    f"{path.name}.pre-migration-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.bak"
                )
                backup_connection = sqlite3.connect(backup_path)
                try:
                    connection.backup(backup_connection)
                finally:
                    backup_connection.close()

    with connect_database(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS login_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                logged_at TEXT NOT NULL,
                success INTEGER NOT NULL CHECK (success IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS proposal_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login_record_id INTEGER REFERENCES login_records(id),
                created_at TEXT NOT NULL,
                proposal_accepted INTEGER CHECK (proposal_accepted IN (0, 1)),
                proposal_responded_at TEXT,
                date_accepted INTEGER CHECK (date_accepted IN (0, 1)),
                date_responded_at TEXT
            );
            CREATE TABLE IF NOT EXISTS date_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id INTEGER NOT NULL REFERENCES proposal_responses(id),
                preferred_date TEXT NOT NULL DEFAULT '',
                preferred_time TEXT NOT NULL DEFAULT '',
                preferred_location TEXT NOT NULL DEFAULT '',
                activity TEXT NOT NULL DEFAULT '',
                food_or_drink TEXT NOT NULL DEFAULT '',
                message TEXT NOT NULL DEFAULT '',
                submitted_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS media_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section TEXT NOT NULL,
                slot TEXT NOT NULL,
                filename TEXT NOT NULL UNIQUE,
                uploaded_at TEXT NOT NULL,
                UNIQUE (section, slot)
            );
            CREATE TABLE IF NOT EXISTS site_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_login_records_logged_at
                ON login_records(logged_at DESC);
            CREATE INDEX IF NOT EXISTS idx_proposal_responses_created_at
                ON proposal_responses(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_date_plans_submitted_at
                ON date_plans(submitted_at DESC);
            """
        )
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def record_login(database_path, username, success):
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO login_records (username, logged_at, success) VALUES (?, ?, ?)",
            (username[:80], utc_now(), int(success)),
        )
        return cursor.lastrowid


def create_response(database_path, login_record_id=None):
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO proposal_responses (login_record_id, created_at) VALUES (?, ?)",
            (login_record_id, utc_now()),
        )
        return cursor.lastrowid


def set_setting(database_path, key, value):
    with connect_database(database_path) as connection:
        connection.execute(
            "INSERT INTO site_settings (setting_key, setting_value) VALUES (?, ?) "
            "ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value",
            (key, value),
        )


def get_setting(database_path, key, default=""):
    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT setting_value FROM site_settings WHERE setting_key = ?", (key,)
        ).fetchone()
    return row["setting_value"] if row else default
