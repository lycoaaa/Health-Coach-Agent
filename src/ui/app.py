
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT.parent / ".env")

import streamlit as st
from form import render_form
from ui.dashboard import render_dashboard
from ui.profile_form import render_profile_form

st.set_page_config(
    page_title="健康习惯教练",
    page_icon="💪",
    layout="wide",
)

render_profile_form()
render_form()
render_dashboard()
