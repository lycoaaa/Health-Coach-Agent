import streamlit as st, pandas as pd, altair as alt, datetime as dt
import json
from database.db_adapter import fetch_recent_summaries, fetch_events_of_week
from metrics.compute_metrics import aggregate_unprocessed_weeks
from agent.feedback_agent import generate_weekly_report
from database.db_adapter import get_profile
# ─────────────────────── 日粒度多图 ───────────────────────
METRIC_MAP = {
    "sleep_hours":      "睡眠时长 (h)",
    "steps":            "步数",
    "mood_score":       "情绪评分",
    "exercise_minutes": "运动时长 (min)",
}

def _render_daily_charts(week_start: dt.date) -> None:
    df_day = fetch_events_of_week(week_start)
    if df_day.empty:
        st.info("该周日粒度数据不足。")
        return

    cols = st.columns(2)
    for i, (col, title) in enumerate(METRIC_MAP.items()):
        c = cols[i % 2]
        chart = (
            alt.Chart(df_day)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="日期"),
                y=alt.Y(f"{col}:Q", title=title),
                tooltip=["date", col],
            )
            .properties(height=200)
        )
        c.altair_chart(chart, use_container_width=True)
        if i % 2 == 1:      # 换行
            cols = st.columns(2)

# ─────────────────────── 周粒度双图 ───────────────────────
GROUP_HIGH = ["total_steps", "exercise_total"]
GROUP_LOW  = ["avg_sleep", "mood_avg"]
_RENAME = {
    "total_steps":     "步数",
    "exercise_total":  "运动 (min)",
    "avg_sleep":       "睡眠 (h)",
    "mood_avg":        "情绪评分",
}

def _plot_week_group(df_week: pd.DataFrame, cols, title):
    df_long = df_week.melt(
        id_vars="week_start",
        value_vars=cols,
        var_name="metric",
        value_name="value"
    )
    df_long["metric"] = df_long["metric"].map(_RENAME)
    chart = (
        alt.Chart(df_long)
        .mark_line(point=True)
        .encode(
            x=alt.X("week_start:T", title="周起始"),
            y=alt.Y("value:Q", title="数值"),
            color="metric:N",
            tooltip=["week_start", "metric", "value"]
        )
        .properties(height=250, title=title)
    )
    st.altair_chart(chart, use_container_width=True)

# ───────────────────────── 主入口 ─────────────────────────
def render_dashboard() -> None:
    st.title("📊 每周健康仪表盘")

    aggregate_unprocessed_weeks()

    df_week = fetch_recent_summaries(limit=4)
    if df_week.empty:
        st.info("暂无汇总数据，完成一周打卡后再来看吧！")
        return

    # ------- KPI -------

    cols = st.columns(5)          # 一次性生成 5 列

    latest = df_week.iloc[0]
    cols[0].metric("平均睡眠 (h)",  f"{latest.avg_sleep:.1f}")
    cols[1].metric("总步数",        f"{latest.total_steps:,}")
    cols[2].metric("平均情绪",      f"{latest.mood_avg:.1f}")
    cols[3].metric("运动时间 (min)", f"{latest.exercise_total}")

    profile = get_profile()
    if profile:
        try:
            bmi = round(profile["weight_kg"] / (profile["height_cm"]/100)**2, 1)
            cols[4].metric("BMI", bmi)
        except Exception:
            cols[4].metric("BMI", "—")
    else:
        cols[4].metric("BMI", "—")


    # ------- 本周日粒度 --------
    st.markdown("---")
    st.subheader("🗓 本周逐日趋势")
    _render_daily_charts(latest.week_start)

    # ------- 最近 4 周概览（两张） --------
    st.markdown("---")
    st.subheader("📈 最近 4 周概览")

    col1, col2 = st.columns(2)
    with col1:
        _plot_week_group(df_week, GROUP_HIGH, "高量级指标（步数 / 运动）")
    with col2:
        _plot_week_group(df_week, GROUP_LOW,  "低量级指标（睡眠 / 情绪）")

    # ----- 生成周报按钮 -----
    if st.sidebar.button("📑 生成本周周报"):
        with st.spinner("正在为您生成周报，请稍候…"):
            ok = generate_weekly_report()
        if ok:
            st.success("周报已生成 ✅")
            # 刷新页面，马上展示新建议
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()
        else:
            st.error("生成失败，请检查终端日志")

    # ---------------- 健康建议渲染 ----------------
    suggest_raw = latest.get("suggestions")
    if isinstance(suggest_raw, str) and suggest_raw.strip():
        try:
            data    = json.loads(suggest_raw)
            summary = data.get("summary", "").strip()
            items   = data.get("action_items", [])

            st.markdown("---")
            st.subheader("📝 本周健康建议")
            st.markdown(f"> **{summary}**")

            if items:
                cols = st.columns(len(items))
                week_start = latest.week_start
                for col, it in zip(cols, items):
                    # ── 周期兼容：优先 period_weeks；否则 by_date 退回计算 ──
                    if "period_weeks" in it:
                        weeks = it["period_weeks"]
                    else:
                        end = dt.datetime.strptime(it["by_date"], "%Y-%m-%d").date()
                        weeks = max(1, round((end - week_start).days / 7))

                    motivation = it.get("motivation", "")

                    with col:
                        st.markdown(
                            f"""<div style="border:1px solid #DDD; border-radius:8px; padding:0.7rem">
    <strong>{it['goal']}</strong><br>
    目标值：{it['target']}<br>
    目标周期：{weeks} 周<br>
    <em>{motivation}</em>
    </div>""",
                            unsafe_allow_html=True
                        )
            else:
                st.info("模型未返回行动项。")

        except Exception as e:
            st.warning(f"⚠️ 建议内容解析失败：{e}")
    else:
        st.info("本周暂未生成智能建议。")



