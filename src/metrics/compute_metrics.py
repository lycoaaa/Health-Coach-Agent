from __future__ import annotations
import datetime as dt
from typing import Dict, List
import pandas as pd
from database.db_adapter import _get_conn

def _week_start(date: dt.date) -> dt.date:
    return date - dt.timedelta(days=date.weekday())


def _compute_metrics(df: pd.DataFrame) -> Dict[str, float | int]:
    return dict(
        avg_sleep      = df["sleep_hours"].mean()          or 0,
        total_steps    = int(df["steps"].sum()             or 0),
        mood_avg       = df["mood_score"].mean()           or 0,
        exercise_total = int(df["exercise_minutes"].sum()  or 0),
        veggie_avg     = df["veggie_servings"].mean()      or 0,
        water_total    = int(df["water_ml"].sum()          or 0),
        alcohol_days   = int(df["alcohol"].sum()           or 0),
    )


def aggregate_unprocessed_weeks() -> List[dt.date]:
    processed: List[dt.date] = []

    with _get_conn() as conn:
        df_events = pd.read_sql_query("SELECT * FROM events;", conn,
                                      parse_dates=["date"])
        if df_events.empty:
            return processed

        df_events["week_start"] = df_events["date"].apply(_week_start)
        complete_weeks = (
            df_events.groupby("week_start")["date"].nunique()
            .loc[lambda s: s == 7]
            .index
            .tolist()
        )

        existing_weeks = pd.read_sql_query(
            "SELECT week_start FROM weekly_summary;", conn,
            parse_dates=["week_start"]
        )["week_start"].tolist()

        to_process = [w for w in complete_weeks if w not in existing_weeks]
        if not to_process:
            return processed

        for ws in to_process:
            df_week = df_events[df_events["week_start"] == ws]
            metrics = _compute_metrics(df_week)
            _upsert_week(conn, ws, metrics)
            processed.append(ws)

    return processed

def aggregate_last_full_week() -> bool:
    today = dt.date.today()
    last_week_start = _week_start(today) - dt.timedelta(days=7)

    with _get_conn() as conn:
        df_week = pd.read_sql_query(
            "SELECT * FROM events WHERE date >= ? AND date < ?;",
            conn,
            params=(last_week_start, last_week_start + dt.timedelta(days=7)),
            parse_dates=["date"]
        )

        if df_week.shape[0] < 7:          # 不够 7 天，说明数据还没补齐
            return False

        metrics = _compute_metrics(df_week)
        _upsert_week(conn, last_week_start, metrics)
        return True

def _upsert_week(conn, week_start, metrics):
    week_start = week_start.date() if hasattr(week_start, "date") else week_start

    cols = ["week_start"] + list(metrics.keys())
    placeholders = ",".join(["?"] * len(cols))
    update_clause = ",".join([f"{c}=excluded.{c}" for c in cols[1:]])
    sql = (f"INSERT INTO weekly_summary ({','.join(cols)}) "
           f"VALUES ({placeholders}) "
           f"ON CONFLICT(week_start) DO UPDATE SET {update_clause};")

    values = [week_start] + list(metrics.values())
    conn.execute(sql, values)
    conn.commit()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true",
                        help="聚合所有未处理完整周")
    args = parser.parse_args()

    if args.all:
        weeks = aggregate_unprocessed_weeks()
        print(f"processed {weeks}")
    else:
        ok = aggregate_last_full_week()
        print("updated last full week:", ok)
