import os
import sqlite3
import datetime as dt
from pathlib import Path
from typing import Tuple, Any

import pandas as pd

ROOT_DIR     = Path(__file__).resolve().parents[2]       # 仓库根路径
DATA_DIR     = ROOT_DIR / "data"
DB_PATH      = DATA_DIR / "db.sqlite"
DATE_FMT_SQL = "%Y-%m-%d"

DATA_DIR.mkdir(parents=True, exist_ok=True)

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES,
                           check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def _ensure_schema() -> None:
    """首次运行时建表。"""
    create_events_sql = """
    CREATE TABLE IF NOT EXISTS events (
        date            DATE PRIMARY KEY,
        sleep_hours     REAL,
        sleep_start     TEXT,
        sleep_end       TEXT,
        veggie_servings INTEGER,
        high_fat_meals  INTEGER,
        water_ml        INTEGER,
        exercise_minutes INTEGER,
        steps           INTEGER,
        mood_score      INTEGER,
        mood_note       TEXT,
        screen_hours    REAL,
        alcohol         INTEGER,
        caffeine        INTEGER,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );"""

    create_weekly_sql = """
    CREATE TABLE IF NOT EXISTS weekly_summary (
        week_start      DATE PRIMARY KEY,
        avg_sleep       REAL,
        total_steps     INTEGER,
        mood_avg        REAL,
        exercise_total  INTEGER,
    
        veggie_avg      REAL,   
        water_total     INTEGER,
        alcohol_days    INTEGER,
    
        suggestions     TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );"""

    create_profile_sql = """
    CREATE TABLE IF NOT EXISTS user_profile (
        id          INTEGER PRIMARY KEY CHECK (id = 1),
        name        TEXT,
        gender      TEXT CHECK (gender IN ('男','女','其他')),
        age         INTEGER,
        height_cm   INTEGER,
        weight_kg   REAL,
        occupation  TEXT,
        updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    with _get_conn() as conn:
        conn.execute(create_events_sql)
        conn.execute(create_weekly_sql)
        conn.execute(create_profile_sql)
        conn.commit()

_ensure_schema()

def insert_event(**kwargs: Any) -> None:
    cols = ",".join(kwargs.keys())
    placeholders = ",".join(["?"] * len(kwargs))
    update_clause = ",".join([f"{c}=excluded.{c}" for c in kwargs.keys()])

    sql = (f"INSERT INTO events ({cols}) VALUES ({placeholders}) "
           f"ON CONFLICT(date) DO UPDATE SET {update_clause};")

    values = list(kwargs.values())
    with _get_conn() as conn:
        conn.execute(sql, values)
        conn.commit()


def get_streak() -> Tuple[int, int, int]:
    today = dt.date.today()
    with _get_conn() as conn:
        # 连续天数：从今天开始向前回溯
        streak = 0
        cursor = conn.cursor()
        while True:
            d = today - dt.timedelta(days=streak)
            cursor.execute("SELECT 1 FROM events WHERE date = ?", (d,))
            if cursor.fetchone():
                streak += 1
            else:
                break

        # 本月信息
        first_day = today.replace(day=1)
        next_month = (first_day + dt.timedelta(days=32)).replace(day=1)
        month_days = (next_month - first_day).days

        cursor.execute(
            "SELECT COUNT(*) FROM events "
            "WHERE date >= ? AND date < ?;",
            (first_day, next_month)
        )
        month_filled, = cursor.fetchone()

    return streak, month_days, month_filled


def fetch_recent_summaries(limit: int = 4) -> pd.DataFrame:

    sql = ("SELECT week_start, avg_sleep, total_steps, mood_avg, "
           "exercise_total, suggestions "
           "FROM weekly_summary "
           "ORDER BY week_start DESC "
           "LIMIT ?;")

    with _get_conn() as conn:
        df = pd.read_sql_query(sql, conn, params=(limit,))
    return df

def fetch_events_of_week(week_start: dt.date) -> pd.DataFrame:
    with _get_conn() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM events WHERE date >= ? AND date < ? ORDER BY date",
            conn,
            params=(week_start, week_start + dt.timedelta(days=7)),
            parse_dates=["date"],
        )
    return df

def upsert_profile(**kwargs):
    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join("?" for _ in kwargs)
    sql = f"INSERT INTO user_profile (id,{cols}) VALUES (1,{placeholders}) " \
          f"ON CONFLICT(id) DO UPDATE SET " + ", ".join(f"{c}=excluded.{c}" for c in kwargs)
    with _get_conn() as c:
        c.execute(sql, list(kwargs.values()))
        c.commit()

def get_profile() -> dict:
    with _get_conn() as c:
        row = c.execute("SELECT * FROM user_profile WHERE id=1").fetchone()
    return dict(row) if row else {}

if __name__ == "__main__":
    """简单 CLI：python -m database.db_adapter show-events"""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["show-events", "show-sum"])
    args = parser.parse_args()

    if args.cmd == "show-events":
        with _get_conn() as c:
            df = pd.read_sql_query("SELECT * FROM events ORDER BY date DESC", c)
        print(df)

    elif args.cmd == "show-sum":
        print(fetch_recent_summaries())
