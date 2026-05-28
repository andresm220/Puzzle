import sys
sys.stdout.reconfigure(encoding='utf-8')

import streamlit as st

st.set_page_config(page_title="Puzzle Solver", layout="centered")

st.markdown("""
<style>
    /* ── Base ── */
    body, .stApp, .main, section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
    }

    /* ── Typography ── */
    h1, h2, h3, h4, h5, h6 { color: #1E293B !important; }
    p, li, span, small { color: #1E293B !important; }
    code {
        background-color: #E2E8F0 !important;
        color: #1E293B !important;
        padding: 2px 5px !important;
        border-radius: 4px !important;
    }
    [data-testid="stMarkdownContainer"] * { color: #1E293B !important; }
    .stCaption, [data-testid="stCaptionContainer"] { color: #475569 !important; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { background-color: #FFFFFF !important; }
    .stTabs [data-baseweb="tab"] { color: #475569 !important; background: transparent !important; }
    .stTabs [aria-selected="true"] {
        color: #1E293B !important;
        border-bottom: 3px solid #D97706 !important;
    }

    /* ── Text inputs & textareas ── */
    input, textarea {
        background-color: #F1F5F9 !important;
        color: #1E293B !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
    }
    input::placeholder, textarea::placeholder { color: #94A3B8 !important; }
    [data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="base-input"] {
        background-color: #F1F5F9 !important;
        border: 1px solid #CBD5E1 !important;
    }

    /* ── Number input stepper buttons ── */
    [data-testid="stNumberInputStepDown"],
    [data-testid="stNumberInputStepUp"] {
        background-color: #E2E8F0 !important;
        color: #1E293B !important;
        border: none !important;
    }

    /* ── Selectbox / dropdown ── */
    [data-baseweb="select"] > div,
    [data-baseweb="select"] [role="combobox"],
    [data-baseweb="select"] input {
        background-color: #F1F5F9 !important;
        color: #1E293B !important;
        border: 1px solid #CBD5E1 !important;
    }
    /* Dropdown menu (portal) */
    [data-baseweb="popover"] [role="option"],
    [data-baseweb="menu"] li {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
    }
    [data-baseweb="popover"] [role="option"]:hover,
    [data-baseweb="menu"] li:hover {
        background-color: #E2E8F0 !important;
    }

    /* ── Radio buttons ── */
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] p,
    [data-testid="stRadio"] span { color: #1E293B !important; }

    /* ── Checkboxes ── */
    [data-testid="stCheckbox"] label,
    [data-testid="stCheckbox"] p,
    [data-testid="stCheckbox"] span { color: #1E293B !important; }

    /* ── Progress bar ── */
    [data-testid="stProgressBar"] > div { background-color: #D97706 !important; }
    [data-testid="stProgressBar"] { background-color: #E2E8F0 !important; }

    /* ── Alerts / info / warning / error ── */
    [data-testid="stAlert"] { color: #1E293B !important; }
    [data-testid="stAlert"] p { color: inherit !important; }

    /* ── Divider ── */
    hr { border-color: #E2E8F0 !important; }

    /* ── Buttons ── */
    .stButton > button {
        background-color: #D97706 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.4rem 1.2rem !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover { background-color: #B45309 !important; }
    .stButton > button:disabled {
        background-color: #CBD5E1 !important;
        color: #94A3B8 !important;
    }

    /* ── Form submit button ── */
    [data-testid="stFormSubmitButton"] > button {
        background-color: #D97706 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover { background-color: #B45309 !important; }

    /* ── Custom result cards ── */
    .step-card {
        background: #F8FAFC;
        color: #1E293B;
        border-left: 4px solid #D97706;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0 6px 6px 0;
        font-family: monospace;
        white-space: pre-wrap;
    }
    .missing-card {
        background: #FEF2F2;
        color: #7F1D1D;
        border-left: 4px solid #DC2626;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0 6px 6px 0;
    }
    .success-card {
        background: #F0FDF4;
        color: #14532D;
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
