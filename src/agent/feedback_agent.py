from __future__ import annotations
import json, datetime as dt, pathlib, sys, traceback
from typing import Dict, Any

from agent.call_local_llm import call_local_llm    # 也可以用你已有的llm封装
from database.db_adapter import _get_conn
from agent.prompt_templates import build_prompt
from agent.report_schema import WeeklyReport
from database.db_adapter import get_profile
from agent.prompt_templates import SYSTEM_INSTRUCT, WHO_GUIDE

import re
from typing import Optional
from agent.report_schema import WeeklyReport

RETRY_LIMIT = 2

def _personal_context(p: dict) -> str:
    if not p:
        return "（用户未填写档案）"
    bmi = round(p["weight_kg"] / (p["height_cm"]/100)**2, 1)
    return (
        f"- 姓名: {p.get('name','--')}\n"
        f"- 性别: {p.get('gender','--')}  年龄: {p.get('age','--')} 岁\n"
        f"- 身高: {p['height_cm']} cm  体重: {p['weight_kg']} kg  BMI: {bmi}\n"
        f"- 职业: {p.get('occupation','--')}"
    )

def _latest_summary() -> Dict[str, Any]:
    with _get_conn() as c:
        row = c.execute(
            "SELECT * FROM weekly_summary ORDER BY week_start DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else {}

def _to_markdown_table(row: Dict[str, Any]) -> str:
    md = (
        "| 指标 | 数值 |\n|------|------|\n"
        f"| 平均睡眠 (h) | {row['avg_sleep']:.1f} |\n"
        f"| 总步数 | {row['total_steps']:,} |\n"
        f"| 平均情绪 | {row['mood_avg']:.1f} |\n"
        f"| 运动时长 (min) | {row['exercise_total']} |\n"
        f"| 日均蔬果 (份) | {row.get('veggie_avg', 0):.1f} |\n"
        f"| 总饮水 (ml) | {row.get('water_total', 0)} |\n"
        f"| 饮酒天数 | {row.get('alcohol_days', 0)} |\n"
    )
    return md

def _fill_defaults(data: dict, default_weeks: int = 4) -> dict:
    for it in data.get("action_items", []):
        if not it.get("period_weeks") and not it.get("by_date"):
            it["period_weeks"] = default_weeks
    return data

_JSON_RE = re.compile(r"\{.*\}", re.S)          # 贪婪匹配首段 JSON

def _validate_llm_output(raw: str) -> Optional[WeeklyReport]:
    try:
        m = _JSON_RE.search(raw)
        if not m:
            raise ValueError("no JSON found")
        data = json.loads(m.group())

        for it in data.get("action_items", []):
            if not it.get("period_weeks") and not it.get("by_date"):
                it["period_weeks"] = 4

        return WeeklyReport.parse_obj(data)

    except Exception as e:
        print("validation error:", e)
        return None


def generate_weekly_report() -> bool:
    row = _latest_summary()
    if not row:
        print("No weekly_summary row found.")
        return False

    stat_table_md = _to_markdown_table(row)
    personal_md   = _personal_context(get_profile())
    prompt = (
        f"{SYSTEM_INSTRUCT}\n\n"
        "## 个人档案\n"
        f"{personal_md}\n\n"
        "## 本周统计\n"
        f"{stat_table_md}\n\n"
        "## WHO 指南\n"
        f"{WHO_GUIDE}\n"
    )

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            llm_resp = call_local_llm(prompt).strip()
            report   = _validate_llm_output(llm_resp)
            if report:
                _write_back(row["week_start"], llm_resp)
                print("✓ weekly report saved.")
                return True
            raise ValueError("validation failed")
        except Exception as e:
            print(f"attempt {attempt}/{RETRY_LIMIT} failed:", e)
            if attempt == RETRY_LIMIT:
                traceback.print_exc()
    return False


def _write_back(week_start: dt.date | str, suggestions_json: str) -> None:
    if isinstance(week_start, dt.datetime):
        week_start = week_start.date()
    if isinstance(week_start, str):
        week_start = dt.datetime.strptime(week_start, "%Y-%m-%d").date()

    with _get_conn() as c:
        c.execute(
            "UPDATE weekly_summary SET suggestions = ? WHERE week_start = ?",
            (suggestions_json, week_start)
        )
        c.commit()

# uick test
if __name__ == "__main__":
    ok = generate_weekly_report()
    sys.exit(0 if ok else 1)
