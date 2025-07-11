import streamlit as st
from database.db_adapter import get_profile, upsert_profile

def render_profile_form():
    st.sidebar.markdown("## 👤 个人档案")
    prof = get_profile()

    with st.sidebar.form("profile_form"):
        name  = st.text_input("姓名", prof.get("name", ""))
        gender= st.selectbox("性别", ["男","女","其他"],
                             index=["男","女","其他"].index(prof.get("gender","男")))
        age   = st.number_input("年龄", 12, 100, prof.get("age", 25))
        height= st.number_input("身高 (cm)", 100, 250, prof.get("height_cm", 170))
        weight= st.number_input("体重 (kg)", 30.0, 200.0, prof.get("weight_kg", 65.0))
        occ   = st.text_input("职业", prof.get("occupation", "学生 / 上班族"))
        submitted = st.form_submit_button("保存")
        if submitted:
            upsert_profile(name=name, gender=gender, age=int(age),
                           height_cm=int(height), weight_kg=float(weight),
                           occupation=occ)
            st.success("个人档案已保存！")
