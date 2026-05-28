import sys
sys.stdout.reconfigure(encoding='utf-8')

import streamlit as st

st.set_page_config(page_title="Puzzle Solver", layout="centered")

st.markdown("""
<style>
    body, .stApp { background-color: #FFFFFF; color: #1E293B; }
    h1, h2, h3 { color: #1E293B; }
    .stTabs [data-baseweb="tab"] { color: #1E293B; }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #D97706 !important; }
    .stButton > button {
        background-color: #D97706;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.4rem 1.2rem;
    }
    .stButton > button:hover { background-color: #B45309; }
    .step-card {
        background: #F8FAFC;
        border-left: 4px solid #D97706;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0 6px 6px 0;
        font-family: monospace;
        white-space: pre-wrap;
    }
    .missing-card {
        background: #FEF2F2;
        border-left: 4px solid #DC2626;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0 6px 6px 0;
    }
    .success-card {
        background: #F0FDF4;
        border-left: 4px solid #16A34A;
        padding: 0.75rem 1rem;
        border-radius: 0 6px 6px 0;
    }
</style>
""", unsafe_allow_html=True)

from ui.create import render_create
from ui.solve import render_solve

tab1, tab2 = st.tabs(["➕ Crear", "🔍 Resolver"])
with tab1:
    render_create()
with tab2:
    render_solve()
