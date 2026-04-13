"""
SQLite database access layer.
All DB interaction goes through these functions; no SQL lives elsewhere.
"""

import sqlite3
from .constants import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT NOT NULL,
                date     TEXT NOT NULL,
                location TEXT,
                notes    TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                type            TEXT NOT NULL,
                direction       TEXT NOT NULL,
                fields          INTEGER,
                actual_dist_mm  REAL,
                encoder_dist_mm REAL,
                duration_ms     REAL,
                angle_mean      REAL,
                angle_median    REAL,
                gyro_variance   REAL,
                note            TEXT
            )
        """)
        conn.commit()


# ── sessions ───────────────────────────────────────────────────────────────────

def db_get_sessions():
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM sessions ORDER BY date DESC, id DESC"
        ).fetchall()


def db_create_session(name: str, date: str, location: str, notes: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (name, date, location, notes) VALUES (?,?,?,?)",
            (name, date, location, notes),
        )
        conn.commit()
        return cur.lastrowid


def db_update_session(session_id: int, name: str, date: str,
                      location: str, notes: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET name=?, date=?, location=?, notes=? WHERE id=?",
            (name, date, location, notes, session_id),
        )
        conn.commit()


def db_delete_session(session_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM entries WHERE session_id=?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        conn.commit()


def db_get_session(session_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM sessions WHERE id=?", (session_id,)
        ).fetchone()


# ── entries ────────────────────────────────────────────────────────────────────

def db_get_entries(session_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM entries WHERE session_id=? ORDER BY id",
            (session_id,),
        ).fetchall()


def db_create_entry(session_id: int, data: dict) -> None:
    cols = [
        "session_id", "type", "direction", "fields", "actual_dist_mm",
        "encoder_dist_mm", "duration_ms", "angle_mean", "angle_median",
        "gyro_variance", "note",
    ]
    vals = [session_id] + [data.get(c) for c in cols[1:]]
    with get_conn() as conn:
        conn.execute(
            f"INSERT INTO entries ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
            vals,
        )
        conn.commit()


def db_update_entry(entry_id: int, data: dict) -> None:
    sets = ",".join(f"{k}=?" for k in data)
    vals = list(data.values()) + [entry_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE entries SET {sets} WHERE id=?", vals)
        conn.commit()


def db_delete_entry(entry_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
        conn.commit()
