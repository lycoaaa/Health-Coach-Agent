import datetime as dt
import streamlit as st

from database.db_adapter import insert_event, get_streak

def _today() -> dt.date:
    return dt.date.today()

def render_form() -> None:
    st.sidebar.header("📅 每日健康打卡")

    with st.sidebar.form("daily_checkin", clear_on_submit=False):
        # ──────────── 基本信息 ────────────
        date = st.date_input("打卡日期", value=_today(), format="YYYY-MM-DD")

        # ──────────── 睡眠 ────────────
        st.subheader("😴 睡眠")
        sleep_hours = st.number_input("睡眠时长（小时）", 0.0, 24.0, step=0.5)
        sleep_start = st.time_input("入睡时间", value=dt.time(23, 0))
        sleep_end   = st.time_input("起床时间", value=dt.time(7, 0))

        # ──────────── 饮食 ────────────
        st.subheader("🥗 饮食")
        veggie_servings = st.number_input("蔬果份数（份）", 0, 20, step=1)
        high_fat_meals  = st.number_input("高油/高糖餐次", 0, 10, step=1)
        water_ml        = st.number_input("饮水量（毫升）", 0, 5000, step=100)

        # ──────────── 运动 ────────────
        st.subheader("🏃‍♀️ 运动")
        exercise_minutes = st.number_input("主动运动时长（分钟）", 0, 300, step=5)
        steps            = st.number_input("步行步数", 0, 50000, step=100)

        # ──────────── 情绪 ────────────
        st.subheader("😊 情绪")
        mood_score = st.slider("情绪评分（1-5）", 1, 5, 3)
        mood_note  = st.text_input("一句话备注（选填）")

        # ──────────── 其他补充 ────────────
        st.subheader("📱 其他")
        screen_hours = st.number_input("屏幕时间（小时）", 0.0, 24.0, step=0.5)
        alcohol      = st.checkbox("饮酒")
        caffeine     = st.checkbox("摄入咖啡因")

        submitted = st.form_submit_button("✅ 提交打卡")
        if submitted:
            insert_event(
                date=date,
                sleep_hours=float(sleep_hours),
                sleep_start=str(sleep_start),
                sleep_end=str(sleep_end),
                veggie_servings=int(veggie_servings),
                high_fat_meals=int(high_fat_meals),
                water_ml=int(water_ml),
                exercise_minutes=int(exercise_minutes),
                steps=int(steps),
                mood_score=int(mood_score),
                mood_note=mood_note,
                screen_hours=float(screen_hours),
                alcohol=bool(alcohol),
                caffeine=bool(caffeine),
            )
            st.success("🎉 打卡成功！")

    # ──────────── 连击天数展示 ────────────
    streak_days, month_days, month_filled = get_streak()
    st.sidebar.markdown("---")
    st.sidebar.metric("连续打卡天数", f"{streak_days} 天")
    st.sidebar.progress(month_filled / month_days, text="本月打卡进度")
