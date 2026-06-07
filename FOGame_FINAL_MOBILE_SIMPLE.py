
import os
import json
import hashlib
import pandas as pd
import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ============================================================
# CONFIG
# ============================================================

DATA_PATH = "Clean NBA Data.csv"
LOGO_PATH = "baileybi_logo.png"

# ============================================================
# OPENAI API KEY - ONLY PASTE YOUR KEY ON THIS ONE LINE
# ============================================================
# 1. Revoke any key you pasted into chat.
# 2. Create a brand-new key.
# 3. Paste it between the quotes below.
# 4. Do NOT paste your key anywhere else in this file.
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")

# Internal placeholder. Do not edit this line.
PLACEHOLDER_API_KEY = "PASTE_YOUR_NEW_OPENAI_API_KEY_HERE"

SALARY_CAP_LEVELS = {
    "Salary Cap": 165_000_000,
    "Salary Floor": 149_000_000,
    "Luxury Tax Level": 201_000_000,
    "First Apron": 209_000_000,
    "Second Apron": 222_000_000,
    "Custom": 350_000_000,
}

DEFAULT_SALARY_CAP = SALARY_CAP_LEVELS["Second Apron"]

ROSTER_SLOTS = [
    "Starting PG",
    "Starting SG",
    "Starting SF",
    "Starting PF",
    "Starting C",
    "6th Man",
    "Bench 1",
    "Bench 2",
    "Bench 3",
    "Bench 4",
    "Bench 5",
    "Two-Way 1",
    "Two-Way 2",
    "Bench 6",
    "Bench 7",
]

MIN_RESULTS_PLAYERS = 9
DEFAULT_ROSTER_SIZE = 13
MAX_ROSTER_SIZE = 15

REQUIRED_COLUMNS = [
    "Player", "Team", "Pos", "Salary",
    "MP", "PTS", "AST", "TRB", "STL", "BLK", "TOV",
    "FG%", "3P%", "eFG%", "TS%", "PER", "USG%",
    "OBPM", "DBPM", "BPM", "VORP",
    "Impact_Score", "Value_Score"
]


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="NBA Front Office Simulator",
    page_icon="🏀",
    layout="wide"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>
.stApp {
    background: #020617;
    color: #f8fafc;
}

.block-container {
    padding-top: 2.2rem;
    max-width: 1750px;
}

.main-title {
    font-size: 42px;
    font-weight: 950;
    color: #f8fafc;
    margin-bottom: 4px;
    letter-spacing: -0.04em;
}

.sub-title {
    font-size: 17px;
    color: #94a3b8;
    margin-bottom: 24px;
}

.section-title {
    color: #f8fafc;
    font-size: 23px;
    font-weight: 900;
    margin-top: 12px;
    margin-bottom: 12px;
}

.metric-card {
    background: linear-gradient(145deg, #111827, #020617);
    border: 1px solid #1e293b;
    border-radius: 18px;
    padding: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,.25);
    min-height: 92px;
}

.metric-label {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .06em;
}

.metric-value {
    color: #f8fafc;
    font-size: 24px;
    font-weight: 950;
    word-break: normal;
    white-space: nowrap;
    margin-top: 4px;
}

.roster-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 12px 14px;
    margin-bottom: 10px;
}

.roster-slot {
    font-size: 12px;
    color: #38bdf8;
    font-weight: 950;
    letter-spacing: .04em;
    text-transform: uppercase;
}

.roster-player {
    font-size: 16px;
    color: #f8fafc;
    font-weight: 900;
    margin-top: 2px;
}

.roster-detail {
    font-size: 13px;
    color: #94a3b8;
    margin-top: 3px;
}

.fit-good {
    color: #22c55e;
    font-weight: 900;
}

.fit-bad {
    color: #ef4444;
    font-weight: 900;
}

.fit-neutral {
    color: #facc15;
    font-weight: 900;
}

.report-shell {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 18px;
    padding: 24px;
    line-height: 1.65;
}

.small-note {
    color: #64748b;
    font-size: 13px;
    line-height: 1.55;
    margin-bottom: 12px;
}

div[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

.draft-board-note {
    color: #94a3b8;
    font-size: 13px;
    margin-top: -4px;
    margin-bottom: 10px;
}

div[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid #1e293b;
}

div[data-testid="stDataFrame"] * {
    font-size: 14px;
}


.hero-wrap {
    background:
        radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 35%),
        linear-gradient(135deg, #020617 0%, #0f172a 52%, #111827 100%);
    border: 1px solid #1e293b;
    border-radius: 26px;
    padding: 26px 30px;
    margin-bottom: 26px;
    box-shadow: 0 18px 45px rgba(0,0,0,.32);
}

.hero-grid {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 24px;
    align-items: center;
}

.hero-logo {
    width: 112px;
    height: 112px;
    object-fit: contain;
    border-radius: 24px;
    background: rgba(15, 23, 42, 0.45);
    padding: 10px;
    border: 1px solid rgba(148, 163, 184, 0.25);
}

.hero-eyebrow {
    color: #38bdf8;
    font-size: 13px;
    font-weight: 950;
    letter-spacing: .14em;
    text-transform: uppercase;
    margin-bottom: 4px;
}

.hero-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 14px;
}

.hero-badge {
    background: rgba(14, 165, 233, 0.13);
    border: 1px solid rgba(56, 189, 248, 0.24);
    color: #bae6fd;
    padding: 7px 11px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
}

.brand-sidebar {
    background: linear-gradient(145deg, #020617, #0f172a);
    border: 1px solid #1e293b;
    border-radius: 18px;
    padding: 14px;
    margin-bottom: 18px;
    text-align: center;
}

.brand-sidebar img {
    max-width: 120px;
    margin: 0 auto 8px auto;
}

.brand-sidebar-title {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 950;
    letter-spacing: .08em;
}

.brand-sidebar-sub {
    color: #94a3b8;
    font-size: 11px;
    margin-top: 2px;
}

.visual-strip {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin: 16px 0 26px 0;
}

.visual-tile {
    background: linear-gradient(145deg, #0f172a, #020617);
    border: 1px solid #1e293b;
    border-radius: 18px;
    padding: 16px;
    min-height: 96px;
    box-shadow: 0 10px 25px rgba(0,0,0,.22);
}

.visual-icon {
    font-size: 28px;
    margin-bottom: 6px;
}

.visual-title {
    color: #f8fafc;
    font-size: 15px;
    font-weight: 950;
}

.visual-copy {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 4px;
    line-height: 1.35;
}

.metric-card, .roster-card {
    transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease;
}

.metric-card:hover, .roster-card:hover, .visual-tile:hover {
    transform: translateY(-2px);
    border-color: rgba(56, 189, 248, 0.45);
    box-shadow: 0 14px 34px rgba(14, 165, 233, 0.10);
}

@media (max-width: 900px) {
    .hero-grid {
        grid-template-columns: 1fr;
        text-align: center;
    }
    .hero-logo {
        margin: 0 auto;
    }
    .visual-strip {
        grid-template-columns: 1fr 1fr;
    }
}


/* ============================================================
   MOBILE RESPONSIVE POLISH
   ============================================================ */

.mobile-only {
    display: none;
}

.desktop-only {
    display: block;
}

@media (max-width: 900px) {
    .block-container {
        padding-top: 1rem;
        padding-left: 0.85rem;
        padding-right: 0.85rem;
        max-width: 100%;
    }

    .main-title {
        font-size: 30px;
        line-height: 1.05;
        letter-spacing: -0.045em;
    }

    .sub-title {
        font-size: 14px;
        line-height: 1.45;
        margin-bottom: 12px;
    }

    .hero-wrap {
        padding: 18px 16px;
        border-radius: 20px;
        margin-bottom: 16px;
    }

    .hero-grid {
        grid-template-columns: 1fr;
        gap: 12px;
        text-align: center;
    }

    .hero-logo {
        width: 92px;
        height: 92px;
        margin: 0 auto;
    }

    .hero-eyebrow {
        font-size: 11px;
    }

    .hero-badges {
        justify-content: center;
        gap: 7px;
    }

    .hero-badge {
        font-size: 10px;
        padding: 6px 8px;
    }

    .visual-strip {
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin: 12px 0 18px 0;
    }

    .visual-tile {
        padding: 12px;
        min-height: 86px;
        border-radius: 14px;
    }

    .visual-icon {
        font-size: 22px;
    }

    .visual-title {
        font-size: 13px;
    }

    .visual-copy {
        font-size: 10.5px;
    }

    .section-title {
        font-size: 20px;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .metric-card {
        padding: 13px;
        border-radius: 15px;
        min-height: 82px;
        margin-bottom: 8px;
    }

    .metric-label {
        font-size: 10px;
    }

    .metric-value {
        font-size: 21px;
        white-space: normal;
    }

    .roster-card {
        padding: 11px 12px;
        border-radius: 14px;
        margin-bottom: 8px;
    }

    .roster-slot {
        font-size: 11px;
    }

    .roster-player {
        font-size: 15px;
    }

    .roster-detail {
        font-size: 12px;
        line-height: 1.35;
    }

    .draft-board-note {
        font-size: 12px;
    }

    div[data-testid="stDataFrame"] {
        max-width: 100%;
        overflow-x: auto;
    }

    div[data-testid="stDataFrame"] * {
        font-size: 12px !important;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 0.75rem;
    }

    .stButton > button {
        width: 100%;
        border-radius: 12px;
        min-height: 42px;
    }

    .stSelectbox, .stMultiSelect, .stTextInput, .stSlider {
        margin-bottom: 8px;
    }

    .report-shell {
        padding: 16px;
        border-radius: 16px;
        line-height: 1.55;
    }

    h1 {
        font-size: 30px !important;
        line-height: 1.12 !important;
    }

    h2 {
        font-size: 24px !important;
    }

    h3 {
        font-size: 20px !important;
    }

    p, li {
        font-size: 15px !important;
        line-height: 1.55 !important;
    }

    .mobile-only {
        display: block;
    }

    .desktop-only {
        display: none;
    }
}

@media (max-width: 560px) {
    .main-title {
        font-size: 26px;
    }

    .hero-logo {
        width: 78px;
        height: 78px;
    }

    .visual-strip {
        grid-template-columns: 1fr;
    }

    .metric-value {
        font-size: 19px;
    }

    .section-title {
        font-size: 18px;
    }

    .roster-player {
        font-size: 14px;
    }

    .roster-detail {
        font-size: 11.5px;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 12px;
    }
}


/* Mobile draft simplification */
.mobile-draft-panel {
    display: none;
}

@media (max-width: 900px) {
    .desktop-draft-board {
        display: none !important;
    }

    .mobile-draft-panel {
        display: block;
        background: linear-gradient(145deg, #0f172a, #020617);
        border: 1px solid #1e293b;
        border-radius: 18px;
        padding: 14px;
        margin-bottom: 16px;
        box-shadow: 0 12px 28px rgba(0,0,0,.24);
    }

    .mobile-draft-title {
        color: #f8fafc;
        font-size: 17px;
        font-weight: 950;
        margin-bottom: 4px;
    }

    .mobile-draft-copy {
        color: #94a3b8;
        font-size: 12px;
        line-height: 1.4;
        margin-bottom: 12px;
    }

    .mobile-player-preview {
        background: #020617;
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 11px 12px;
        margin: 10px 0 12px 0;
    }

    .mobile-player-name {
        color: #f8fafc;
        font-size: 16px;
        font-weight: 950;
    }

    .mobile-player-meta {
        color: #94a3b8;
        font-size: 12px;
        margin-top: 3px;
        line-height: 1.35;
    }
}


/* Mobile filters callout */
.mobile-filter-callout {
    display: none;
}

@media (max-width: 900px) {
    .mobile-filter-callout {
        display: block;
        background: linear-gradient(135deg, #0284c7, #0ea5e9);
        color: #ffffff;
        border: 1px solid rgba(186, 230, 253, 0.55);
        border-radius: 16px;
        padding: 14px 16px;
        margin: 0 0 16px 0;
        text-align: center;
        box-shadow: 0 14px 32px rgba(14, 165, 233, 0.25);
    }

    .mobile-filter-title {
        font-size: 16px;
        font-weight: 950;
        letter-spacing: .02em;
        margin-bottom: 3px;
    }

    .mobile-filter-copy {
        font-size: 12px;
        font-weight: 750;
        opacity: .95;
        line-height: 1.35;
    }
}


/* Mobile roster popover helper */
.mobile-roster-callout {
    display: none;
}

@media (max-width: 900px) {
    .mobile-roster-callout {
        display: block;
        background: linear-gradient(135deg, #111827, #0f172a);
        color: #ffffff;
        border: 1px solid rgba(148, 163, 184, 0.35);
        border-radius: 16px;
        padding: 13px 15px;
        margin: 0 0 14px 0;
        text-align: center;
        box-shadow: 0 14px 32px rgba(0, 0, 0, 0.25);
    }

    .mobile-roster-title {
        font-size: 16px;
        font-weight: 950;
        margin-bottom: 3px;
    }

    .mobile-roster-copy {
        font-size: 12px;
        color: #cbd5e1;
        line-height: 1.35;
    }
}


/* Roster popover cards */
.popover-roster-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 12px 14px;
    margin-bottom: 10px;
}

.popover-roster-slot {
    font-size: 12px;
    color: #38bdf8;
    font-weight: 950;
    letter-spacing: .04em;
    text-transform: uppercase;
}

.popover-roster-player {
    font-size: 16px;
    color: #f8fafc;
    font-weight: 900;
    margin-top: 2px;
}

.popover-roster-detail {
    font-size: 13px;
    color: #94a3b8;
    margin-top: 3px;
    line-height: 1.35;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# DATA
# ============================================================

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"Missing required columns from CSV: {missing}")
        st.stop()

    numeric_cols = [
        "Salary", "G", "MP", "PTS", "AST", "TRB", "STL", "BLK", "TOV",
        "FG%", "3P%", "3P", "3PA", "eFG%", "TS%", "PER", "USG%",
        "OBPM", "DBPM", "BPM", "VORP", "Impact_Score", "Value_Score"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "3PA" not in df.columns:
        df["3PA"] = 0

    if "3P" not in df.columns:
        df["3P"] = 0

    df["Salary_M"] = df["Salary"] / 1_000_000

    # Clean draft-board display fields
    df["Salary Display"] = df["Salary"].apply(lambda x: f"${x / 1_000_000:.1f}M")
    df["PPG"] = df["PTS"].round(1)
    df["APG"] = df["AST"].round(1)
    df["RPG"] = df["TRB"].round(1)
    df["FG% Display"] = (df["FG%"] * 100).round(1).astype(str) + "%"
    df["3P% Display"] = (df["3P%"] * 100).round(1).astype(str) + "%"
    df["TS% Display"] = (df["TS%"] * 100).round(1).astype(str) + "%"

    df["Display"] = df.apply(
        lambda r: f"{r['Player']} | {r['Team']} | {r['Pos']} | ${r['Salary_M']:.1f}M",
        axis=1
    )

    return df


try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(
        f"Could not find `{DATA_PATH}`. Put this app file in the same folder as your CSV."
    )
    st.stop()


# ============================================================
# PRESET CURRENT ROSTERS
# ============================================================

PRESET_ROSTERS = {
    'Current Atlanta': [
        ('Starting PG', 'C. McCollum'),
        ('Starting SG', 'N. Alexander-Walker'),
        ('Starting SF', 'D. Daniels'),
        ('Starting PF', 'J. Johnson'),
        ('Starting C', 'O. Okongwu'),
        ('6th Man', 'G. Vincent'),
        ('Bench 1', 'C. Kispert'),
        ('Bench 2', 'J. Kuminga'),
        ('Bench 3', 'M. Gueye'),
        ('Bench 4', 'J. Landale'),
        ('Bench 5', 'Z. Risacher'),
        ('Two-Way 1', 'K. Wallace'),
        ('Two-Way 2', 'A. Newell'),
        ('Bench 6', 'T. Bradley'),
        ('Bench 7', 'B. Hield'),
    ],
    'Current Boston': [
        ('Starting PG', 'D. White'),
        ('Starting SG', 'J. Brown'),
        ('Starting SF', 'S. Hauser'),
        ('Starting PF', 'J. Tatum'),
        ('Starting C', 'N. Queta'),
        ('6th Man', 'P. Pritchard'),
        ('Bench 1', 'B. Scheierman'),
        ('Bench 2', 'J. Walsh'),
        ('Bench 3', 'N. Vucevic'),
        ('Bench 4', 'D. Banton'),
        ('Bench 5', 'H. Gonzalez'),
        ('Two-Way 1', 'L. Garza'),
        ('Two-Way 2', 'M. Shulga'),
        ('Bench 6', 'R. Harper Jr.'),
        ('Bench 7', 'A. Williams'),
    ],
    'Current Brooklyn': [
        ('Starting PG', 'E. Demin'),
        ('Starting SG', 'D. Powell'),
        ('Starting SF', 'M. Porter Jr.'),
        ('Starting PF', 'N. Clowney'),
        ('Starting C', 'N. Claxton'),
        ('6th Man', 'B. Saraf'),
        ('Bench 1', 'T. Mann'),
        ('Bench 2', 'Z. Williams'),
        ('Bench 3', 'D. Wolf'),
        ('Bench 4', 'D. Sharpe'),
        ('Bench 5', 'N. Traore'),
        ('Two-Way 1', 'J. Minott'),
        ('Two-Way 2', 'T. Etienne'),
        ('Bench 6', 'M. Smith'),
        ('Bench 7', 'J. Wilson'),
    ],
    'Current Charlotte': [
        ('Starting PG', 'L. Ball'),
        ('Starting SG', 'K. Knueppel'),
        ('Starting SF', 'B. Miller'),
        ('Starting PF', 'M. Bridges'),
        ('Starting C', 'M. Diabate'),
        ('6th Man', 'C. White'),
        ('Bench 1', 'J. Green'),
        ('Bench 2', 'S. James'),
        ('Bench 3', 'G. Williams'),
        ('Bench 4', 'R. Kalkbrenner'),
        ('Bench 5', 'T. Mann'),
        ('Two-Way 1', 'T. Salaun'),
        ('Two-Way 2', 'X. Tillman'),
        ('Bench 6', 'L. McNeeley'),
        ('Bench 7', 'P. Hall'),
    ],
    'Current Chicago': [
        ('Starting PG', 'J. Giddey'),
        ('Starting SG', 'T. Jones'),
        ('Starting SF', 'I. Okoro'),
        ('Starting PF', 'M. Buzelis'),
        ('Starting C', 'J. Smith'),
        ('6th Man', 'R. Dillingham'),
        ('Bench 1', 'C. Sexton'),
        ('Bench 2', 'L. Miller'),
        ('Bench 3', 'P. Williams'),
        ('Bench 4', 'Z. Collins'),
        ('Bench 5', 'A. Simons'),
        ('Two-Way 1', 'G. Yabusele'),
        ('Two-Way 2', 'N. Richards'),
        ('Bench 6', 'N. Essengue'),
        ('Bench 7', 'L. Olbrich'),
    ],
    'Current Cleveland': [
        ('Starting PG', 'J. Harden'),
        ('Starting SG', 'D. Mitchell'),
        ('Starting SF', 'M. Strus'),
        ('Starting PF', 'E. Mobley'),
        ('Starting C', 'J. Allen'),
        ('6th Man', 'D. Schroder'),
        ('Bench 1', 'S. Merrill'),
        ('Bench 2', 'J. Tyson'),
        ('Bench 3', 'D. Wade'),
        ('Bench 4', 'C. Porter Jr.'),
        ('Bench 5', 'K. Ellis'),
        ('Two-Way 1', 'N. Tomlin'),
        ('Two-Way 2', 'T. Bryant'),
        ('Bench 6', 'T. Proctor'),
        ('Bench 7', 'L. Nance Jr.'),
    ],
    'Current Dallas': [
        ('Starting PG', 'K. Irving'),
        ('Starting SG', 'M. Christie'),
        ('Starting SF', 'C. Flagg'),
        ('Starting PF', 'P. Washington'),
        ('Starting C', 'D. Lively II'),
        ('6th Man', 'B. Williams'),
        ('Bench 1', 'N. Marshall'),
        ('Bench 2', 'K. Thompson'),
        ('Bench 3', 'K. Middleton'),
        ('Bench 4', 'D. Gafford'),
        ('Bench 5', 'R. Nembhard Jr.'),
        ('Two-Way 1', 'C. Martin'),
        ('Two-Way 2', 'M. Bagley III'),
        ('Bench 6', 'J. Poulakidas'),
        ('Bench 7', 'M. Cisse'),
    ],
    'Current Denver': [
        ('Starting PG', 'J. Murray'),
        ('Starting SG', 'C. Braun'),
        ('Starting SF', 'C. Johnson'),
        ('Starting PF', 'A. Gordon'),
        ('Starting C', 'N. Jokic'),
        ('6th Man', 'B. Brown'),
        ('Bench 1', 'T. Hardaway Jr.'),
        ('Bench 2', 'P. Watson'),
        ('Bench 3', 'S. Jones'),
        ('Bench 4', 'T. Jones'),
        ('Bench 5', 'J. Strawther'),
        ('Two-Way 1', 'J. Valanciunas'),
        ('Two-Way 2', 'J. Pickett'),
        ('Bench 6', 'Z. Nnaji'),
        ('Bench 7', 'K. Simpson'),
    ],
    'Current Detroit': [
        ('Starting PG', 'C. Cunningham'),
        ('Starting SG', 'D. Robinson'),
        ('Starting SF', 'A. Thompson'),
        ('Starting PF', 'T. Harris'),
        ('Starting C', 'J. Duren'),
        ('6th Man', 'D. Jenkins'),
        ('Bench 1', 'C. LeVert'),
        ('Bench 2', 'I. Stewart'),
        ('Bench 3', 'M. Sasser'),
        ('Bench 4', 'J. Green'),
        ('Bench 5', 'P. Reed'),
        ('Two-Way 1', 'K. Huerter'),
        ('Two-Way 2', 'R. Holland II'),
        ('Bench 6', 'T. Smith'),
        ('Bench 7', 'I. Jones'),
    ],
    'Current Golden State': [
        ('Starting PG', 'S. Curry'),
        ('Starting SG', 'B. Podziemski'),
        ('Starting SF', 'G. Santos'),
        ('Starting PF', 'D. Green'),
        ('Starting C', 'K. Porzingis'),
        ('6th Man', 'G. Payton II'),
        ('Bench 1', 'D. Melton'),
        ('Bench 2', 'A. Horford'),
        ('Bench 3', 'P. Spencer'),
        ('Bench 4', 'W. Richard'),
        ('Bench 5', 'C. Bassey'),
        ('Two-Way 1', 'L. Cryer'),
        ('Two-Way 2', 'M. Leons'),
        ('Bench 6', 'Q. Post'),
        ('Bench 7', 'N. Williams'),
    ],
    'Current Houston': [
        ('Starting PG', 'F. VanVleet'),
        ('Starting SG', 'A. Thompson'),
        ('Starting SF', 'K. Durant'),
        ('Starting PF', 'J. Smith Jr.'),
        ('Starting C', 'A. Sengun'),
        ('6th Man', 'R. Sheppard'),
        ('Bench 1', 'T. Eason'),
        ('Bench 2', 'D. Finney-Smith'),
        ('Bench 3', 'S. Adams'),
        ('Bench 4', 'A. Holiday'),
        ('Bench 5', 'J. Okogie'),
        ('Two-Way 1', 'J. Tate'),
        ('Two-Way 2', 'C. Capela'),
        ('Bench 6', 'J. Davison'),
        ('Bench 7', 'J. Green'),
    ],
    'Current Indiana': [
        ('Starting PG', 'T. Haliburton'),
        ('Starting SG', 'A. Nembhard'),
        ('Starting SF', 'A. Nesmith'),
        ('Starting PF', 'P. Siakam'),
        ('Starting C', 'I. Zubac'),
        ('6th Man', 'T. McConnell'),
        ('Bench 1', 'B. Sheppard'),
        ('Bench 2', 'J. Walker'),
        ('Bench 3', 'O. Toppin'),
        ('Bench 4', 'M. Potter'),
        ('Bench 5', 'J. Furphy'),
        ('Two-Way 1', 'K. Brown'),
        ('Two-Way 2', 'J. Huff'),
        ('Bench 6', 'Q. Jackson'),
        ('Bench 7', 'K. Jones'),
    ],
    'Current LA Clippers': [
        ('Starting PG', 'D. Garland'),
        ('Starting SG', 'K. Dunn'),
        ('Starting SF', 'K. Leonard'),
        ('Starting PF', 'D. Jones Jr.'),
        ('Starting C', 'B. Lopez'),
        ('6th Man', 'J. Miller'),
        ('Bench 1', 'B. Mathurin'),
        ('Bench 2', 'K. Sanders'),
        ('Bench 3', 'J. Collins'),
        ('Bench 4', 'I. Jackson'),
        ('Bench 5', 'N. Batum'),
        ('Two-Way 1', 'Y. Niederhauser'),
        ('Two-Way 2', 'B. Bogdanovic'),
        ('Bench 6', 'N. Omier'),
        ('Bench 7', 'T. Washington Jr.'),
    ],
    'Current LA Lakers': [
        ('Starting PG', 'L. Doncic'),
        ('Starting SG', 'A. Reaves'),
        ('Starting SF', 'M. Smart'),
        ('Starting PF', 'L. James'),
        ('Starting C', 'D. Ayton'),
        ('6th Man', 'L. Kennard'),
        ('Bench 1', 'R. Hachimura'),
        ('Bench 2', 'J. Vanderbilt'),
        ('Bench 3', 'J. Hayes'),
        ('Bench 4', 'J. LaRavia'),
        ('Bench 5', 'M. Kleber'),
        ('Two-Way 1', 'B. James'),
        ('Two-Way 2', 'A. Thiero'),
        ('Bench 6', 'D. Timme'),
        ('Bench 7', 'N. Smith Jr.'),
    ],
    'Current Memphis': [
        ('Starting PG', 'J. Morant'),
        ('Starting SG', 'C. Coward'),
        ('Starting SF', 'J. Wells'),
        ('Starting PF', 'S. Aldama'),
        ('Starting C', 'Z. Edey'),
        ('6th Man', 'S. Pippen Jr.'),
        ('Bench 1', 'T. Jerome'),
        ('Bench 2', 'K. Caldwell-Pope'),
        ('Bench 3', 'T. Hendricks'),
        ('Bench 4', 'O. Prosper'),
        ('Bench 5', 'J. Small'),
        ('Two-Way 1', 'G. Jackson'),
        ('Two-Way 2', 'W. Clayton Jr.'),
        ('Bench 6', 'C. Spencer'),
        ('Bench 7', 'R. Rupert'),
    ],
    'Current Miami': [
        ('Starting PG', 'D. Mitchell'),
        ('Starting SG', 'T. Herro'),
        ('Starting SF', 'N. Powell'),
        ('Starting PF', 'A. Wiggins'),
        ('Starting C', 'B. Adebayo'),
        ('6th Man', 'K. Jakucionis'),
        ('Bench 1', 'P. Larsson'),
        ('Bench 2', 'J. Jaquez Jr.'),
        ('Bench 3', 'S. Fontecchio'),
        ('Bench 4', 'K. Ware'),
        ('Bench 5', 'D. Smith'),
        ('Two-Way 1', 'N. Jovic'),
        ('Two-Way 2', 'K. Johnson'),
        ('Bench 6', 'M. Gardner'),
        ('Bench 7', 'J. Young'),
    ],
    'Current Milwaukee': [
        ('Starting PG', 'R. Rollins'),
        ('Starting SG', 'K. Porter Jr.'),
        ('Starting SF', 'K. Kuzma'),
        ('Starting PF', 'G. Antetokounmpo'),
        ('Starting C', 'M. Turner'),
        ('6th Man', 'A. Green'),
        ('Bench 1', 'O. Dieng'),
        ('Bench 2', 'B. Portis'),
        ('Bench 3', 'J. Sims'),
        ('Bench 4', 'C. Ryan'),
        ('Bench 5', 'G. Trent Jr.'),
        ('Two-Way 1', 'T. Prince'),
        ('Two-Way 2', 'P. Nance'),
        ('Bench 6', 'T. Antetokounmpo'),
        ('Bench 7', 'G. Harris'),
    ],
    'Current Minnesota': [
        ('Starting PG', 'A. Dosunmu'),
        ('Starting SG', 'A. Edwards'),
        ('Starting SF', 'J. McDaniels'),
        ('Starting PF', 'J. Randle'),
        ('Starting C', 'R. Gobert'),
        ('6th Man', 'M. Conley'),
        ('Bench 1', 'T. Shannon Jr.'),
        ('Bench 2', 'N. Reid'),
        ('Bench 3', 'B. Hyland'),
        ('Bench 4', 'J. Clark'),
        ('Bench 5', 'K. Anderson'),
        ('Two-Way 1', 'J. Beringer'),
        ('Two-Way 2', 'Z. Pullin'),
        ('Bench 6', 'J. Phillips'),
        ('Bench 7', 'R. Zikarsky'),
    ],
    'Current New Orleans': [
        ('Starting PG', 'D. Murray'),
        ('Starting SG', 'T. Murphy III'),
        ('Starting SF', 'S. Bey'),
        ('Starting PF', 'Z. Williamson'),
        ('Starting C', 'H. Jones'),
        ('6th Man', 'J. Fears'),
        ('Bench 1', 'D. Queen'),
        ('Bench 2', 'Y. Missi'),
        ('Bench 3', 'T. Alexander'),
        ('Bench 4', 'J. Hawkins'),
        ('Bench 5', 'M. Peavy'),
        ('Two-Way 1', 'K. Matkovic'),
        ('Two-Way 2', 'J. Poole'),
        ('Bench 6', 'B. McGowens'),
        ('Bench 7', 'K. Looney'),
    ],
    'Current New York': [
        ('Starting PG', 'J. Brunson'),
        ('Starting SG', 'J. Hart'),
        ('Starting SF', 'M. Bridges'),
        ('Starting PF', 'O. Anunoby'),
        ('Starting C', 'K. Towns'),
        ('6th Man', 'M. McBride'),
        ('Bench 1', 'L. Shamet'),
        ('Bench 2', 'J. Clarkson'),
        ('Bench 3', 'M. Robinson'),
        ('Bench 4', 'J. Alvarado'),
        ('Bench 5', 'M. Diawara'),
        ('Two-Way 1', 'A. Hukporti'),
        ('Two-Way 2', 'T. Kolek'),
        ('Bench 6', 'J. Sochan'),
        ('Bench 7', 'P. Dadiet'),
    ],
    'Current Oklahoma City': [
        ('Starting PG', 'S. Gilgeous-Alexander'),
        ('Starting SG', 'L. Dort'),
        ('Starting SF', 'J. Williams'),
        ('Starting PF', 'C. Holmgren'),
        ('Starting C', 'I. Hartenstein'),
        ('6th Man', 'A. Mitchell'),
        ('Bench 1', 'J. McCain'),
        ('Bench 2', 'C. Wallace'),
        ('Bench 3', 'A. Caruso'),
        ('Bench 4', 'K. Williams'),
        ('Bench 5', 'T. Sorber'),
        ('Two-Way 1', 'I. Joe'),
        ('Two-Way 2', 'A. Wiggins'),
        ('Bench 6', 'B. Carlson'),
        ('Bench 7', 'N. Topic'),
    ],
    'Current Orlando': [
        ('Starting PG', 'J. Suggs'),
        ('Starting SG', 'D. Bane'),
        ('Starting SF', 'F. Wagner'),
        ('Starting PF', 'P. Banchero'),
        ('Starting C', 'W. Carter Jr.'),
        ('6th Man', 'A. Black'),
        ('Bench 1', 'J. Cain'),
        ('Bench 2', 'T. da Silva'),
        ('Bench 3', 'G. Bitadze'),
        ('Bench 4', 'J. Carter'),
        ('Bench 5', 'J. Howard'),
        ('Two-Way 1', 'J. Isaac'),
        ('Two-Way 2', 'M. Wagner'),
        ('Bench 6', 'J. Richardson'),
        ('Bench 7', 'N. Penda'),
    ],
    'Current Philadelphia': [
        ('Starting PG', 'T. Maxey'),
        ('Starting SG', 'V. Edgecombe'),
        ('Starting SF', 'K. Oubre Jr.'),
        ('Starting PF', 'P. George'),
        ('Starting C', 'J. Embiid'),
        ('6th Man', 'Q. Grimes'),
        ('Bench 1', 'D. Barlow'),
        ('Bench 2', 'A. Drummond'),
        ('Bench 3', 'J. Edwards'),
        ('Bench 4', 'A. Bona'),
        ('Bench 5', 'K. Lowry'),
        ('Two-Way 1', 'D. Terry'),
        ('Two-Way 2', 'J. Walker'),
        ('Bench 6', 'T. Watford'),
        ('Bench 7', 'T. Martin'),
    ],
    'Current Phoenix': [
        ('Starting PG', 'D. Booker'),
        ('Starting SG', 'J. Green'),
        ('Starting SF', 'J. Goodwin'),
        ('Starting PF', 'D. Brooks'),
        ('Starting C', 'M. Williams'),
        ('6th Man', 'C. Gillespie'),
        ('Bench 1', 'G. Allen'),
        ('Bench 2', "R. O'Neale"),
        ('Bench 3', 'O. Ighodaro'),
        ('Bench 4', 'J. Bouyea'),
        ('Bench 5', 'H. Highsmith'),
        ('Two-Way 1', 'R. Dunn'),
        ('Two-Way 2', 'K. Maluach'),
        ('Bench 6', 'R. Fleming'),
        ('Bench 7', 'A. Coffey'),
    ],
    'Current Portland': [
        ('Starting PG', 'S. Henderson'),
        ('Starting SG', 'J. Holiday'),
        ('Starting SF', 'T. Camara'),
        ('Starting PF', 'D. Avdija'),
        ('Starting C', 'D. Clingan'),
        ('6th Man', 'S. Sharpe'),
        ('Bench 1', 'M. Thybulle'),
        ('Bench 2', 'J. Grant'),
        ('Bench 3', 'R. Williams III'),
        ('Bench 4', 'K. Murray'),
        ('Bench 5', 'S. Cissoko'),
        ('Two-Way 1', 'B. Wesley'),
        ('Two-Way 2', 'V. Krejci'),
        ('Bench 6', 'Y. Hansen'),
        ('Bench 7', 'D. Lillard'),
    ],
    'Current Sacramento': [
        ('Starting PG', 'R. Westbrook'),
        ('Starting SG', 'Z. LaVine'),
        ('Starting SF', 'D. DeRozan'),
        ('Starting PF', 'K. Murray'),
        ('Starting C', 'D. Sabonis'),
        ('6th Man', 'M. Monk'),
        ('Bench 1', 'N. Clifford'),
        ('Bench 2', 'D. Hunter'),
        ('Bench 3', 'P. Achiuwa'),
        ('Bench 4', 'M. Raynaud'),
        ('Bench 5', 'D. Carter'),
        ('Two-Way 1', 'D. Cardwell'),
        ('Two-Way 2', 'K. Hayes'),
        ('Bench 6', 'D. Plowden'),
        ('Bench 7', 'D. Eubanks'),
    ],
    'Current San Antonio': [
        ('Starting PG', 'D. Fox'),
        ('Starting SG', 'S. Castle'),
        ('Starting SF', 'D. Vassell'),
        ('Starting PF', 'J. Champagnie'),
        ('Starting C', 'V. Wembanyama'),
        ('6th Man', 'D. Harper'),
        ('Bench 1', 'K. Johnson'),
        ('Bench 2', 'C. Bryant'),
        ('Bench 3', 'H. Barnes'),
        ('Bench 4', 'L. Kornet'),
        ('Bench 5', 'J. McLaughlin'),
        ('Two-Way 1', 'M. Plumlee'),
        ('Two-Way 2', 'D. Jones Garcia'),
        ('Bench 6', 'L. Waters III'),
        ('Bench 7', 'K. Olynyk'),
    ],
    'Current Toronto': [
        ('Starting PG', 'I. Quickley'),
        ('Starting SG', 'B. Ingram'),
        ('Starting SF', 'R. Barrett'),
        ('Starting PF', 'S. Barnes'),
        ('Starting C', 'J. Poeltl'),
        ('6th Man', 'J. Shead'),
        ('Bench 1', 'J. Walter'),
        ('Bench 2', 'J. Battle'),
        ('Bench 3', 'C. Murray-Boyles'),
        ('Bench 4', 'S. Mamukelashvili'),
        ('Bench 5', 'A. Lawson'),
        ('Two-Way 1', 'G. Dick'),
        ('Two-Way 2', 'J. Mogbo'),
        ('Bench 6', 'T. Jackson-Davis'),
        ('Bench 7', 'C. Hepburn'),
    ],
    'Current Utah': [
        ('Starting PG', 'K. George'),
        ('Starting SG', 'A. Bailey'),
        ('Starting SF', 'L. Markkanen'),
        ('Starting PF', 'J. Jackson Jr.'),
        ('Starting C', 'W. Kessler'),
        ('6th Man', 'I. Collier'),
        ('Bench 1', 'C. Williams'),
        ('Bench 2', 'B. Sensabaugh'),
        ('Bench 3', 'K. Filipowski'),
        ('Bench 4', 'J. Nurkic'),
        ('Bench 5', 'E. Harkless'),
        ('Two-Way 1', 'J. Konchar'),
        ('Two-Way 2', 'B. Mbeng'),
        ('Bench 6', 'K. Love'),
        ('Bench 7', 'B. Hinson'),
    ],
    'Current Washington': [
        ('Starting PG', 'T. Young'),
        ('Starting SG', 'K. George'),
        ('Starting SF', 'B. Coulibaly'),
        ('Starting PF', 'A. Davis'),
        ('Starting C', 'A. Sarr'),
        ('6th Man', 'B. Carrington'),
        ('Bench 1', 'T. Johnson'),
        ('Bench 2', 'W. Riley'),
        ('Bench 3', 'J. Champagnie'),
        ('Bench 4', 'T. Vukcevic'),
        ('Bench 5', 'S. Cooper'),
        ('Two-Way 1', 'J. Hardy'),
        ('Two-Way 2', 'C. Whitmore'),
        ('Bench 6', 'D. Russell'),
        ('Bench 7', 'J. Watkins'),
    ],
}


def normalize_name_for_match(name: str) -> str:
    return (
        str(name)
        .lower()
        .replace(".", "")
        .replace("'", "")
        .replace("’", "")
        .replace("-", " ")
        .replace("ć", "c")
        .replace("č", "c")
        .replace("š", "s")
        .replace("ž", "z")
        .replace("ģ", "g")
        .replace("ņ", "n")
        .replace("ā", "a")
        .replace("í", "i")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("č", "c")
        .replace("ć", "c")
        .strip()
    )


def split_name_parts(name: str):
    cleaned = normalize_name_for_match(name)
    parts = [p for p in cleaned.split() if p]
    return parts


def abbreviated_name_match(short_name: str, full_name: str) -> bool:
    """
    Matches depth-chart names like:
    S. Curry -> Stephen Curry
    J. Williams -> Jalen/Jaylin Williams when exact full name is unavailable
    L. Doncic -> Luka Doncic
    K. Caldwell-Pope -> Kentavious Caldwell-Pope
    """
    short_raw = str(short_name).strip()
    short_clean = normalize_name_for_match(short_raw)
    full_parts = split_name_parts(full_name)

    if not full_parts:
        return False

    short_parts = split_name_parts(short_raw)

    # If uploaded name is already full-ish, use containment.
    if len(short_parts) >= 2 and len(short_parts[0]) > 1:
        return short_clean == normalize_name_for_match(full_name) or short_clean in normalize_name_for_match(full_name)

    # Initial + last name matching.
    # Example: S Curry should match Stephen Curry.
    if len(short_parts) >= 2 and len(short_parts[0]) == 1:
        first_initial = short_parts[0][0]
        last_from_short = " ".join(short_parts[1:])

        full_first_initial = full_parts[0][0]
        full_last = " ".join(full_parts[1:])

        if first_initial == full_first_initial and last_from_short == full_last:
            return True

        # Allow suffix differences: J. Jackson Jr -> Jaren Jackson Jr.
        if first_initial == full_first_initial and last_from_short in full_last:
            return True

        # Allow multi-part last names where the final token is enough.
        if first_initial == full_first_initial and full_parts[-1] == short_parts[-1]:
            return True

    return False


def find_player_row(player_name: str, player_df: pd.DataFrame):
    target = normalize_name_for_match(player_name)
    normalized = player_df["Player"].apply(normalize_name_for_match)

    # Exact normalized match first.
    exact = player_df[normalized == target]
    if len(exact) > 0:
        return exact.iloc[0]

    # Full-name contains fallback.
    contains = player_df[normalized.str.contains(target, na=False)]
    if len(contains) > 0:
        return contains.iloc[0]

    # Initial + last name fallback.
    matches = player_df[player_df["Player"].apply(lambda full: abbreviated_name_match(player_name, full))]
    if len(matches) > 0:
        # Prefer highest minutes if multiple players share last/initial patterns.
        if "MP" in matches.columns:
            return matches.sort_values("MP", ascending=False).iloc[0]
        return matches.iloc[0]

    # Last-name fallback only when unique.
    parts = split_name_parts(player_name)
    if len(parts) >= 2:
        last = parts[-1]
        last_matches = player_df[normalized.apply(lambda x: x.split()[-1] == last if x.split() else False)]
        if len(last_matches) == 1:
            return last_matches.iloc[0]
        elif len(last_matches) > 1 and "MP" in last_matches.columns:
            return last_matches.sort_values("MP", ascending=False).iloc[0]

    return None


def load_preset_roster(preset_name: str, roster_size: int, player_df: pd.DataFrame):
    loaded = {}
    missing = []

    for slot, player_name in PRESET_ROSTERS[preset_name][:roster_size]:
        row = find_player_row(player_name, player_df)

        if row is None:
            missing.append(player_name)
            continue

        player = row.to_dict()
        player["Slot"] = slot

        fit, notes = calculate_position_fit(pd.Series(player), slot)
        player["Fit_Adjustment"] = fit
        player["Fit_Notes"] = "; ".join(notes)

        loaded[slot] = player

    return loaded, missing



# ============================================================
# BASIC HELPERS
# ============================================================

def money(x) -> str:
    try:
        return f"${float(x) / 1_000_000:.1f}M"
    except Exception:
        return "$0.0M"


def pct(x) -> str:
    try:
        return f"{float(x) * 100:.1f}%"
    except Exception:
        return "0.0%"


def normalize(value, low, high) -> float:
    if high == low:
        return 50.0
    return max(0.0, min(100.0, ((value - low) / (high - low)) * 100.0))


def score_to_grade(score: float) -> str:
    if score >= 97:
        return "A+"
    if score >= 92:
        return "A"
    if score >= 87:
        return "A-"
    if score >= 82:
        return "B+"
    if score >= 77:
        return "B"
    if score >= 72:
        return "B-"
    if score >= 67:
        return "C+"
    if score >= 62:
        return "C"
    return "D"



def wins_to_grade(wins: int) -> str:
    if wins >= 78:
        return "A+"
    if wins >= 70:
        return "A"
    if wins >= 62:
        return "A-"
    if wins >= 55:
        return "B+"
    if wins >= 50:
        return "B"
    if wins >= 45:
        return "B-"
    if wins >= 40:
        return "C+"
    if wins >= 35:
        return "C"
    return "D"


def get_slot_role(slot: str) -> str:
    if slot == "Starting PG":
        return "PG"
    if slot == "Starting SG":
        return "SG"
    if slot == "Starting SF":
        return "SF"
    if slot == "Starting PF":
        return "PF"
    if slot == "Starting C":
        return "C"
    if slot == "6th Man":
        return "SIXTH_MAN"
    if "Two-Way" in slot:
        return "TWO_WAY"
    return "BENCH"


# ============================================================
# ARCHETYPES / FIT ENGINE
# ============================================================

def is_floor_spacer(row) -> bool:
    return row["3P%"] >= 0.37 and row["3PA"] >= 4


def is_reliable_shooter(row) -> bool:
    return row["3P%"] >= 0.35 and row["3PA"] >= 3


def is_point_forward(row) -> bool:
    return row["Pos"] in ["SF", "PF", "C"] and row["AST"] >= 4.5 and row["BPM"] >= 2


def is_small_ball_forward(row) -> bool:
    # No height column needed: rebounding + defensive value + wing/guard classification.
    return (
        row["Pos"] in ["SG", "SF"] and
        row["TRB"] >= 6.5 and
        row["DBPM"] >= 0.5
    )


def is_big_with_guard_skills(row) -> bool:
    return row["Pos"] in ["PF", "C"] and row["AST"] >= 4.0 and row["OBPM"] >= 1.5


def custom_defense_score(row) -> float:
    """
    Defensive model that balances:
    - production: steals, blocks, rebounds
    - advanced signal: DBPM
    - role context: wing stopper, rim protector, guard defender
    - minutes: avoids low-minute players winning best defender
    - manual real-world correction for elite defenders

    This prevents DBPM/rebounding-only cases like Jokic beating Kawhi/Giannis
    as the best defender on a stacked roster.
    """
    name = str(row["Player"]).lower()
    pos = str(row["Pos"])
    mp = float(row.get("MP", 0))
    dbpm = float(row.get("DBPM", 0))
    stl = float(row.get("STL", 0))
    blk = float(row.get("BLK", 0))
    trb = float(row.get("TRB", 0))

    # Base production/advanced blend
    score = (
        dbpm * 4.5 +
        stl * 5.0 +
        blk * 5.5 +
        trb * 0.60 +
        mp * 0.18
    )

    # Defensive role bonuses
    if pos in ["SG", "SF"] and stl >= 1.2 and mp >= 24:
        score += 5.0  # wing/POA stopper signal

    if pos in ["PF", "C"] and blk >= 1.2 and trb >= 7:
        score += 5.5  # rim protector / backline signal

    if pos in ["PF", "C"] and stl >= 1.0 and blk >= 1.0:
        score += 3.5  # versatile frontcourt disruption

    if pos in ["PG", "SG"] and stl >= 1.2 and dbpm >= 0:
        score += 3.0  # guard pressure

    # Minutes reliability: prevent low-minute defensive noise
    if mp < 15:
        score -= 10
    elif mp < 20:
        score -= 5

    # Real-world defender correction
    elite_defender_bonus = {
        "victor wembanyama": 12.0,
        "anthony davis": 10.5,
        "giannis antetokounmpo": 10.0,
        "kawhi leonard": 10.0,
        "bam adebayo": 9.5,
        "rudy gobert": 9.5,
        "jrue holiday": 8.5,
        "alex caruso": 8.0,
        "evan mobley": 8.0,
        "jaden mcdaniels": 7.5,
        "herb jones": 7.5,
        "og anunoby": 7.5,
        "draymond green": 7.0,
        "jarrett allen": 6.5,
        "lu dort": 6.5,
        "isaac okoro": 5.0,
        "derrick white": 5.5,
        "jaylen brown": 4.0,
    }

    for player_name, bonus in elite_defender_bonus.items():
        if player_name in name:
            score += bonus
            break

    # Jokic is smart and strong defensively, but he should not be treated as a
    # better pure defender than elite stoppers/rim protectors.
    if "nikola jokic" in name:
        score -= 8.0

    return round(score, 2)


def defender_leader_score(row) -> float:
    """
    Used only for the 'Best Defender' card.
    This values actual defensive responsibility and minutes more than box-score noise.
    """
    name = str(row["Player"]).lower()
    pos = str(row["Pos"])
    score = custom_defense_score(row)

    score += float(row.get("MP", 0)) * 0.35
    score += float(row.get("STL", 0)) * 3.5
    score += float(row.get("BLK", 0)) * 4.0
    score += float(row.get("TRB", 0)) * 0.75

    # Prefer proven defensive archetypes.
    if pos in ["SF", "PF"] and float(row.get("MP", 0)) >= 25:
        score += 4.0
    if pos == "C" and float(row.get("BLK", 0)) >= 1.0:
        score += 4.0

    # Strong manual leader boost for known top defenders.
    leader_bonus = {
        "victor wembanyama": 15,
        "anthony davis": 13,
        "giannis antetokounmpo": 12,
        "kawhi leonard": 12,
        "bam adebayo": 11,
        "rudy gobert": 11,
        "jrue holiday": 9,
        "alex caruso": 9,
        "evan mobley": 9,
        "og anunoby": 8,
        "herb jones": 8,
        "jaden mcdaniels": 8,
        "lu dort": 7,
    }

    for player_name, bonus in leader_bonus.items():
        if player_name in name:
            score += bonus
            break

    if "nikola jokic" in name:
        score -= 12

    return round(score, 2)


def calculate_position_fit(row, slot: str) -> tuple[int, list[str]]:
    """
    Allows any player at any slot, then rewards or penalizes fit.
    Fit range is capped from -12 to +12.
    """
    slot_role = get_slot_role(slot)
    pos = row["Pos"]

    ast = float(row["AST"])
    trb = float(row["TRB"])
    stl = float(row["STL"])
    blk = float(row["BLK"])
    three_pct = float(row["3P%"])
    three_pa = float(row["3PA"])
    ts = float(row["TS%"])
    obpm = float(row["OBPM"])
    dbpm = float(row["DBPM"])
    bpm = float(row["BPM"])
    pts = float(row["PTS"])
    tov = float(row["TOV"])

    fit = 0
    notes = []

    # ----------------------------
    # STARTING PG
    # ----------------------------
    if slot_role == "PG":
        if ast >= 7:
            fit += 5
            notes.append("elite lead-guard playmaking")
        elif ast >= 5:
            fit += 3
            notes.append("strong creation for PG duties")
        elif ast < 3:
            fit -= 6
            notes.append("low assist profile for a lead guard")

        if obpm >= 3:
            fit += 3
            notes.append("high-end offensive engine")

        if is_point_forward(row):
            fit += 4
            notes.append("point-forward boost")

        if is_big_with_guard_skills(row):
            fit += 2
            notes.append("big with unusual passing skill")

        if pos == "C" and ast < 4:
            fit -= 9
            notes.append("center with limited guard skills at PG")

        if pos in ["PF", "C"] and three_pct < 0.32 and three_pa >= 1.5:
            fit -= 3
            notes.append("spacing concern at PG")

        if tov >= 3.5 and ast < 6:
            fit -= 2
            notes.append("turnover concern for lead-handler role")

    # ----------------------------
    # STARTING SG
    # ----------------------------
    elif slot_role == "SG":
        if is_floor_spacer(row):
            fit += 5
            notes.append("elite shooting guard spacing")
        elif is_reliable_shooter(row):
            fit += 3
            notes.append("reliable wing shooting")

        if pts >= 20:
            fit += 3
            notes.append("high-level scoring punch")
        elif pts >= 15:
            fit += 2
            notes.append("secondary scoring")

        if obpm >= 2:
            fit += 2
            notes.append("positive offensive creation")

        if three_pct < 0.32 and three_pa >= 2:
            fit -= 5
            notes.append("poor shooting fit at SG")

        if pos == "C":
            fit -= 8
            notes.append("center playing far out of position at SG")

        if pos == "PF" and ast < 3 and three_pa < 2:
            fit -= 5
            notes.append("limited guard skill fit at SG")

    # ----------------------------
    # STARTING SF
    # ----------------------------
    elif slot_role == "SF":
        if bpm >= 3:
            fit += 3
            notes.append("high-impact wing fit")
        if dbpm >= 1:
            fit += 2
            notes.append("plus defensive wing profile")
        if is_reliable_shooter(row):
            fit += 2
            notes.append("keeps spacing viable at SF")
        if pts >= 18:
            fit += 2
            notes.append("strong wing scoring")

        if pos == "PG" and dbpm < 0 and trb < 5:
            fit -= 5
            notes.append("small guard size/defense concern at SF")

        if pos == "C" and three_pa < 2 and ast < 4:
            fit -= 5
            notes.append("limited perimeter skill at SF")

    # ----------------------------
    # STARTING PF
    # ----------------------------
    elif slot_role == "PF":
        if trb >= 7:
            fit += 3
            notes.append("strong forward rebounding")
        if dbpm >= 1:
            fit += 3
            notes.append("plus frontcourt defense")
        if ts >= 0.60:
            fit += 2
            notes.append("efficient frontcourt scoring")

        if is_small_ball_forward(row):
            fit += 4
            notes.append("small-ball PF rebounding/defense boost")

        if pos == "SF" and trb >= 6 and dbpm >= 0.5:
            fit += 2
            notes.append("wing-to-PF versatility")

        if pos == "PG":
            fit -= 7
            notes.append("small guard playing PF")
        elif pos == "SG" and not is_small_ball_forward(row):
            fit -= 4
            notes.append("guard lacks PF rebounding/defensive profile")

        if trb < 5 and pos in ["PG", "SG"]:
            fit -= 4
            notes.append("low rebounding for PF role")

    # ----------------------------
    # STARTING C
    # ----------------------------
    elif slot_role == "C":
        if trb >= 9:
            fit += 5
            notes.append("elite center rebounding")
        elif trb >= 7:
            fit += 3
            notes.append("solid center rebounding")

        if blk >= 1.5:
            fit += 4
            notes.append("strong rim protection")
        elif blk >= 1.0:
            fit += 2
            notes.append("useful shot blocking")

        if dbpm >= 1.5:
            fit += 3
            notes.append("plus interior defense")

        if pos in ["PG", "SG"]:
            fit -= 10
            notes.append("guard playing center")
        elif pos == "SF" and trb < 7:
            fit -= 6
            notes.append("wing lacks center rebounding profile")

        if trb < 5:
            fit -= 5
            notes.append("low rebounding for center")
        if blk < 0.5 and dbpm < 0:
            fit -= 3
            notes.append("limited rim protection")

    # ----------------------------
    # SIXTH MAN
    # ----------------------------
    elif slot_role == "SIXTH_MAN":
        if pts >= 15:
            fit += 4
            notes.append("bench scoring punch")
        if obpm >= 1.5:
            fit += 3
            notes.append("second-unit creator")
        if is_reliable_shooter(row):
            fit += 2
            notes.append("bench spacing")
        if bpm >= 2:
            fit += 2
            notes.append("starter-quality sixth man")
        if pts < 8 and obpm < 0:
            fit -= 3
            notes.append("limited sixth-man offense")

    # ----------------------------
    # BENCH
    # ----------------------------
    elif slot_role == "BENCH":
        if bpm >= 1:
            fit += 3
            notes.append("positive bench impact")
        if is_reliable_shooter(row):
            fit += 2
            notes.append("bench shooting value")
        if dbpm >= 1:
            fit += 2
            notes.append("defensive bench value")
        if pts >= 12:
            fit += 2
            notes.append("bench scoring")
        if bpm < -3:
            fit -= 4
            notes.append("weak rotation impact")

    # ----------------------------
    # TWO-WAY
    # ----------------------------
    elif slot_role == "TWO_WAY":
        # Two-way slots should not carry the team. Reward cheap value/developmental depth.
        if row["Salary"] <= 5_000_000:
            fit += 3
            notes.append("low-cost two-way depth")
        if bpm >= 0:
            fit += 2
            notes.append("positive depth impact")
        if row["MP"] <= 18 and row["Salary"] <= 8_000_000:
            fit += 2
            notes.append("realistic low-minute roster slot")
        if row["Salary"] >= 20_000_000:
            fit -= 5
            notes.append("expensive player in two-way slot")
        if bpm < -4:
            fit -= 3
            notes.append("poor two-way impact")

    fit = int(max(-12, min(12, fit)))

    if not notes:
        notes.append("neutral positional fit")

    return fit, notes[:3]



def calculate_player_quality_score(row) -> float:
    """
    Determines player quality without over-relying on BPM.
    BPM is useful, but it can be affected by team context and role.
    This score leans on production, efficiency, impact score, defense, minutes, and role.
    """
    score = 0.0

    score += normalize(row["Impact_Score"], 20, 95) * 0.28
    score += normalize(row["PTS"], 5, 32) * 0.17
    score += normalize(row["AST"], 1, 10) * 0.12
    score += normalize(row["TRB"], 2, 13) * 0.11
    score += normalize(row["TS%"], 0.50, 0.68) * 0.11
    score += normalize(custom_defense_score(row), 0, 30) * 0.10
    score += normalize(row["MP"], 12, 36) * 0.07
    score += normalize(row["BPM"], -2, 10) * 0.04

    # Penalize statistical noise from tiny roles.
    if row["MP"] < 15:
        score -= 14
    elif row["MP"] < 20:
        score -= 7

    # A role player can be valuable, but should not be labeled the best player
    # over true franchise-level players unless the full profile supports it.
    if row["USG%"] < 16 and row["PTS"] < 12 and row["AST"] < 4:
        score -= 8

    # Manual star correction for players whose box/advanced stats may be affected
    # by team context, role, injuries, or roster environment.
    star_names = {
        "nikola jokic": 9,
        "shai gilgeous-alexander": 9,
        "luka doncic": 9,
        "giannis antetokounmpo": 9,
        "jayson tatum": 8,
        "anthony edwards": 8,
        "victor wembanyama": 8,
        "lebron james": 7,
        "stephen curry": 7,
        "kevin durant": 7,
        "anthony davis": 7,
        "joel embiid": 7,
        "kawhi leonard": 6,
        "devin booker": 6,
        "donovan mitchell": 6,
        "jalen brunson": 6,
        "jaylen brown": 5,
        "bam adebayo": 5,
        "cade cunningham": 5,
        "ja morant": 5,
        "lamelo ball": 4,
        "paolo banchero": 5,
        "tyrese haliburton": 6,
        "trae young": 5,
        "damian lillard": 5,
        "kyrie irving": 5,
        "jaren jackson jr": 5,
        "jaren jackson jr.": 5,
    }

    name = str(row["Player"]).lower()
    for star_name, bonus in star_names.items():
        if star_name in name:
            score += bonus
            break

    return round(max(0, min(100, score)), 2)


def get_player_role(row) -> str:
    roles = []
    quality = row.get("Player_Quality", calculate_player_quality_score(row))

    if quality >= 82:
        roles.append("MVP-Level Star")
    elif quality >= 72:
        roles.append("All-NBA Caliber")
    elif quality >= 62:
        roles.append("All-Star Caliber")
    elif quality >= 52:
        roles.append("High-Level Starter")
    elif quality >= 42:
        roles.append("Rotation Contributor")

    if is_floor_spacer(row):
        roles.append("Elite Floor Spacer")
    elif is_reliable_shooter(row):
        roles.append("Reliable Shooter")

    if row["AST"] >= 7:
        roles.append("Primary Playmaker")
    elif row["AST"] >= 5:
        roles.append("Secondary Playmaker")
    elif row["AST"] >= 4 and row["Pos"] in ["PF", "C"]:
        roles.append("Frontcourt Connector")

    if custom_defense_score(row) >= 25:
        roles.append("Defensive Anchor")
    elif custom_defense_score(row) >= 18 or row["DBPM"] >= 1:
        roles.append("Plus Defender")

    if row["TRB"] >= 9:
        roles.append("High-End Rebounder")
    elif row["TRB"] >= 7:
        roles.append("Rebounder")

    if not roles:
        roles.append("Depth Piece")

    return ", ".join(roles[:3])

def fit_label(fit: int) -> str:
    if fit >= 5:
        return "Great Fit"
    if fit >= 1:
        return "Good Fit"
    if fit >= -2:
        return "Neutral Fit"
    if fit >= -6:
        return "Poor Fit"
    return "Bad Fit"


def fit_color_class(fit: int) -> str:
    if fit >= 1:
        return "fit-good"
    if fit <= -3:
        return "fit-bad"
    return "fit-neutral"


def get_roster_talent_context(roster_df: pd.DataFrame) -> dict:
    """
    Uses current-season stats only to identify when a roster is historically stacked.
    """
    df = roster_df.copy()
    if "Player_Quality" not in df.columns:
        df["Player_Quality"] = df.apply(calculate_player_quality_score, axis=1)

    elite = int((df["Player_Quality"] >= 78).sum())
    stars = int((df["Player_Quality"] >= 68).sum())
    high_level = int((df["Player_Quality"] >= 56).sum())
    twenty_ppg = int((df["PTS"] >= 20).sum())
    top5_quality = float(df["Player_Quality"].nlargest(5).mean())
    top8_quality = float(df["Player_Quality"].nlargest(8).mean())

    is_historic = elite >= 4 or stars >= 7 or (top5_quality >= 72 and high_level >= 8)
    is_superteam = elite >= 3 or stars >= 5 or top5_quality >= 68

    return {
        "elite_count": elite,
        "star_count": stars,
        "high_level_count": high_level,
        "twenty_ppg_count": twenty_ppg,
        "top5_quality": round(top5_quality, 1),
        "top8_quality": round(top8_quality, 1),
        "is_superteam": is_superteam,
        "is_historic": is_historic,
    }


def talent_adjusted_fit(raw_fit: int, roster_df: pd.DataFrame) -> int:
    """
    On normal teams, fit matters a lot.
    On absurd superstar teams, one weird slot should not crater the projection.
    """
    context = get_roster_talent_context(roster_df)

    if raw_fit >= 0:
        return raw_fit

    if context["is_historic"]:
        return int(round(raw_fit * 0.35))
    if context["is_superteam"]:
        return int(round(raw_fit * 0.55))
    return raw_fit


def build_unique_fit_note(row, slot: str, raw_fit: int, adjusted_fit: int, roster_df: pd.DataFrame | None = None) -> str:
    """
    More human-readable, player/context-aware fit notes for the table.
    """
    name = row["Player"]
    pos = row["Pos"]
    slot_role = get_slot_role(slot)
    pts = float(row["PTS"])
    ast = float(row["AST"])
    trb = float(row["TRB"])
    three_pct = float(row["3P%"])
    three_pa = float(row["3PA"])
    quality = row.get("Player_Quality", calculate_player_quality_score(row))

    context = get_roster_talent_context(roster_df) if roster_df is not None else {
        "is_superteam": False,
        "is_historic": False,
        "star_count": 0,
        "elite_count": 0,
    }

    notes = []

    if slot_role == "PG":
        if ast >= 7:
            notes.append(f"{name} gives this slot real lead-guard creation and control.")
        elif ast >= 5:
            notes.append(f"{name} can handle secondary creation duties without breaking the offense.")
        elif pos in ["SF", "PF", "C"] and ast >= 4:
            notes.append(f"{name} is more of a point-forward hub than a traditional guard.")
        else:
            notes.append(f"{name} is not a natural table-setter, so this slot asks a lot of his decision-making.")

    elif slot_role == "SG":
        if pts >= 22:
            notes.append(f"{name} brings star-level scoring pressure next to the primary initiator.")
        elif three_pct >= 0.37 and three_pa >= 4:
            notes.append(f"{name} fits cleanly as a spacing guard who keeps driving lanes open.")
        else:
            notes.append(f"{name} can function here, but the value depends on shooting and off-ball discipline.")

    elif slot_role == "SF":
        if pts >= 20 and trb >= 5:
            notes.append(f"{name} gives the wing spot scoring punch with enough size/activity to survive bigger matchups.")
        elif three_pct >= 0.36 and three_pa >= 3:
            notes.append(f"{name} provides useful wing spacing and does not crowd the floor.")
        else:
            notes.append(f"{name} is playable at the wing, though the team may need stronger creation or defense elsewhere.")

    elif slot_role == "PF":
        if trb >= 7 and quality >= 55:
            notes.append(f"{name} has enough rebounding and talent to work as a modern frontcourt piece.")
        elif pos in ["SG", "SF"] and trb >= 6:
            notes.append(f"{name} profiles as a small-ball forward who can help on the glass.")
        else:
            notes.append(f"{name} is a creative PF choice and needs surrounding size to protect the matchup.")

    elif slot_role == "C":
        if pos in ["PG", "SG"] and context["is_historic"]:
            notes.append(f"{name} is obviously undersized at center, but this historic talent base can hide the mismatch in many lineups.")
        elif pos in ["PG", "SG"] and context["is_superteam"]:
            notes.append(f"{name} is not a real center, but the surrounding stars reduce how damaging the mismatch is.")
        elif pos in ["PG", "SG"]:
            notes.append(f"{name} at center is a major size and rebounding risk.")
        elif trb >= 8 or row["BLK"] >= 1:
            notes.append(f"{name} gives the center spot legitimate interior presence.")
        else:
            notes.append(f"{name} can fill center minutes, but the team may need more rim protection around him.")

    elif slot_role == "SIXTH_MAN":
        if quality >= 65:
            notes.append(f"{name} as sixth man is a luxury; he can tilt bench minutes like a starter.")
        elif pts >= 15:
            notes.append(f"{name} gives the second unit scoring punch.")
        else:
            notes.append(f"{name} gives the bench a defined role, but not a true carry option.")

    elif slot_role == "BENCH":
        if quality >= 70:
            notes.append(f"{name} coming off the bench is an overwhelming depth advantage.")
        elif quality >= 55:
            notes.append(f"{name} gives the bench starter-level stability.")
        elif three_pct >= 0.37 and three_pa >= 3:
            notes.append(f"{name} adds useful shooting to stabilize reserve groups.")
        else:
            notes.append(f"{name} is best used as a matchup-dependent rotation piece.")

    elif slot_role == "TWO_WAY":
        if row["Salary"] >= 20_000_000 and context["is_historic"]:
            notes.append(f"{name} is far too talented for a two-way slot, but this roster is so loaded that stars are being squeezed down the depth chart.")
        elif row["Salary"] >= 20_000_000:
            notes.append(f"{name} is too expensive and too important for a two-way role.")
        elif quality >= 45:
            notes.append(f"{name} is strong developmental/depth value for this slot.")
        else:
            notes.append(f"{name} fits as a low-cost depth piece.")

    if raw_fit < -3 and adjusted_fit > raw_fit:
        notes.append("Penalty softened because the roster has enough top-end talent to cover some role awkwardness.")

    return " ".join(notes[:2])



# ============================================================
# ROLE-WEIGHTED TEAM SCORING
# ============================================================

ROLE_WEIGHTS = {
    "Starting PG": 1.45,
    "Starting SG": 1.35,
    "Starting SF": 1.35,
    "Starting PF": 1.35,
    "Starting C": 1.45,
    "6th Man": 1.05,
    "Bench 1": 0.85,
    "Bench 2": 0.75,
    "Bench 3": 0.65,
    "Bench 4": 0.55,
    "Bench 5": 0.45,
    "Two-Way 1": 0.15,
    "Two-Way 2": 0.15,
    "Bench 6": 0.35,
    "Bench 7": 0.30,
}


def add_role_weights(roster_df: pd.DataFrame) -> pd.DataFrame:
    roster_df = roster_df.copy()
    roster_df["Role_Weight"] = roster_df["Slot"].map(ROLE_WEIGHTS).fillna(0.5)
    return roster_df


def weighted_average(roster_df: pd.DataFrame, col: str) -> float:
    weights = roster_df["Role_Weight"]
    if weights.sum() == 0:
        return float(roster_df[col].mean())
    return float((roster_df[col] * weights).sum() / weights.sum())


def calculate_rebounding_score(roster_df: pd.DataFrame) -> float:
    return (
        normalize(weighted_average(roster_df, "TRB"), 3, 12) * 0.72 +
        normalize(weighted_average(roster_df, "BLK"), 0.1, 2.2) * 0.13 +
        normalize(weighted_average(roster_df, "Custom_Defense"), 2, 30) * 0.15
    )


def calculate_versatility_score(roster_df: pd.DataFrame) -> float:
    """
    Measures how many different roster problems the team can solve.
    This helps teams like OKC/Orlando/Miami that win with two-way depth,
    defense, switchability, shooting, and role clarity.
    """
    versatile = 0
    for _, row in roster_df.iterrows():
        skill_count = 0

        if row["PTS"] >= 15:
            skill_count += 1
        if row["AST"] >= 4:
            skill_count += 1
        if row["TRB"] >= 6:
            skill_count += 1
        if row["3P%"] >= 0.36 and row["3PA"] >= 3:
            skill_count += 1
        if row["Custom_Defense"] >= 16 or row["DBPM"] >= 1:
            skill_count += 1
        if row["TS%"] >= 0.58:
            skill_count += 1
        if row["Fit_Adjustment"] >= 2:
            skill_count += 1

        if skill_count >= 4:
            versatile += 1.00
        elif skill_count == 3:
            versatile += 0.65
        elif skill_count == 2:
            versatile += 0.35

    base = normalize(versatile, 2, 8)

    # Extra reward for having competent two-way pieces in the actual rotation.
    rotation = roster_df[~roster_df["Slot"].str.contains("Two-Way", na=False)]
    positive_rotation = len(rotation[(rotation["Player_Quality"] >= 48) & (rotation["Fit_Adjustment"] >= 0)])
    base += normalize(positive_rotation, 4, 10) * 0.25

    return max(0, min(100, base))


def calculate_star_power_score(roster_df: pd.DataFrame) -> float:
    """
    Star power should not only mean MVP candidates.
    It should also reward All-Star level players, high-end starters,
    strong scoring options, and players who can realistically carry parts of a season.
    This helps teams like Miami where Bam, Herro, and Powell provide real star/near-star value
    without being Jokic/Luka/Giannis-level superstars.
    """
    top1 = roster_df["Player_Quality"].nlargest(1).mean()
    top3 = roster_df["Player_Quality"].nlargest(3).mean()
    top5 = roster_df["Player_Quality"].nlargest(5).mean()

    elite_count = len(roster_df[roster_df["Player_Quality"] >= 78])
    star_count = len(roster_df[roster_df["Player_Quality"] >= 66])
    high_level_count = len(roster_df[roster_df["Player_Quality"] >= 56])

    twenty_ppg_count = len(roster_df[roster_df["PTS"] >= 20])
    eighteen_ppg_count = len(roster_df[roster_df["PTS"] >= 18])

    # Two-way frontcourt stars/near-stars can be underrated by scoring-only formulas.
    two_way_bigs = len(
        roster_df[
            (roster_df["Pos"].isin(["PF", "C"])) &
            (roster_df["PTS"] >= 16) &
            (roster_df["TRB"] >= 7) &
            ((roster_df["Custom_Defense"] >= 18) | (roster_df["DBPM"] >= 1))
        ]
    )

    score = (
        normalize(top1, 48, 88) * 0.20 +
        normalize(top3, 42, 82) * 0.28 +
        normalize(top5, 36, 76) * 0.20 +
        normalize(star_count, 0, 4) * 0.12 +
        normalize(high_level_count, 1, 7) * 0.08 +
        normalize(twenty_ppg_count, 0, 4) * 0.06 +
        normalize(eighteen_ppg_count, 1, 6) * 0.04 +
        normalize(two_way_bigs, 0, 2) * 0.02
    )

    # Slight bump for teams with several credible top options but no MVP-level superstar.
    if elite_count == 0 and high_level_count >= 3:
        score += 8
    elif elite_count == 1 and high_level_count >= 3:
        score += 5

    return round(max(0, min(100, score)), 1)


def calculate_depth_score(roster_df: pd.DataFrame) -> float:
    bench_df = roster_df[~roster_df["Slot"].isin([
        "Starting PG", "Starting SG", "Starting SF", "Starting PF", "Starting C"
    ])]

    if len(bench_df) == 0:
        return 50

    # Bench 1-5 and 6th man matter far more than two-way slots.
    bench_df = add_role_weights(bench_df)
    quality = weighted_average(bench_df, "Player_Quality")
    impact = weighted_average(bench_df, "Impact_Score")
    fit = weighted_average(bench_df, "Fit_Adjustment")
    shooting = weighted_average(bench_df, "TS%")

    return (
        normalize(quality, 28, 72) * 0.43 +
        normalize(impact, 20, 75) * 0.24 +
        normalize(fit, -4, 8) * 0.18 +
        normalize(shooting, 0.50, 0.65) * 0.15
    )


def roster_pillar_identity(metrics: dict) -> str:
    wins = metrics["projected_wins"]
    if wins >= 78:
        return "All-Time Superteam"
    if wins >= 70:
        return "Championship Favorite"
    if wins >= 58:
        return "Elite Contender"
    if wins >= 50:
        return "Strong Playoff Contender"
    if wins >= 43:
        return "Playoff-Level Team"
    if wins >= 36:
        return "Play-In Team"
    return "Developmental Roster"


# ============================================================
# TEAM METRICS
# ============================================================

def calculate_team_metrics(roster_df: pd.DataFrame, salary_cap: int) -> dict:
    roster_df = roster_df.copy()

    fit_results = roster_df.apply(
        lambda row: calculate_position_fit(row, row["Slot"]),
        axis=1
    )
    roster_df["Raw_Fit_Adjustment"] = [x[0] for x in fit_results]
    roster_df["Custom_Defense"] = roster_df.apply(custom_defense_score, axis=1)
    roster_df["Player_Quality"] = roster_df.apply(calculate_player_quality_score, axis=1)

    talent_context = get_roster_talent_context(roster_df)

    roster_df["Fit_Adjustment"] = roster_df["Raw_Fit_Adjustment"].apply(
        lambda x: talent_adjusted_fit(int(x), roster_df)
    )
    roster_df["Fit_Notes"] = roster_df.apply(
        lambda row: build_unique_fit_note(
            row,
            row["Slot"],
            int(row["Raw_Fit_Adjustment"]),
            int(row["Fit_Adjustment"]),
            roster_df
        ),
        axis=1
    )

    roster_df = add_role_weights(roster_df)
    payroll = roster_df["Salary"].sum()

    # Pillar 1: Creation
    creation_score = (
        normalize(weighted_average(roster_df, "AST"), 1.5, 8.5) * 0.33 +
        normalize(weighted_average(roster_df, "PTS"), 7, 29) * 0.22 +
        normalize(weighted_average(roster_df, "Impact_Score"), 25, 92) * 0.20 +
        normalize(weighted_average(roster_df, "TS%"), 0.52, 0.68) * 0.15 +
        normalize(weighted_average(roster_df, "TOV") * -1, -4, -1) * 0.10
    )

    # Pillar 2: Shooting
    shooting_score = (
        normalize(weighted_average(roster_df, "3P%"), 0.30, 0.42) * 0.38 +
        normalize(weighted_average(roster_df, "3PA"), 1.5, 7.5) * 0.24 +
        normalize(weighted_average(roster_df, "TS%"), 0.52, 0.68) * 0.24 +
        normalize(weighted_average(roster_df, "eFG%"), 0.48, 0.62) * 0.14
    )

    # Pillar 3: Defense
    defense_score = (
        normalize(weighted_average(roster_df, "Custom_Defense"), 2, 30) * 0.42 +
        normalize(weighted_average(roster_df, "STL"), 0.3, 1.8) * 0.15 +
        normalize(weighted_average(roster_df, "BLK"), 0.1, 2.4) * 0.17 +
        normalize(weighted_average(roster_df, "TRB"), 3, 12) * 0.16 +
        normalize(weighted_average(roster_df, "DBPM"), -2, 4) * 0.10
    )

    # Pillar 4: Rebounding
    rebounding_score = calculate_rebounding_score(roster_df)

    # Pillar 5: Star / top-end talent
    star_power_score = calculate_star_power_score(roster_df)

    # Additional talent concentration score using only current-season stats.
    top5_quality = roster_df["Player_Quality"].nlargest(5).mean()
    top8_quality = roster_df["Player_Quality"].nlargest(8).mean()
    top5_impact = roster_df["Impact_Score"].nlargest(5).mean()
    top8_impact = roster_df["Impact_Score"].nlargest(8).mean()

    talent_concentration_score = (
        normalize(top5_quality, 50, 88) * 0.36 +
        normalize(top8_quality, 42, 82) * 0.24 +
        normalize(top5_impact, 45, 92) * 0.24 +
        normalize(top8_impact, 36, 85) * 0.16
    )

    # Pillar 6: Depth
    depth_score = calculate_depth_score(roster_df)

    # Pillar 7: Fit
    fit_score = 50 + (weighted_average(roster_df, "Fit_Adjustment") * 4.5)
    fit_score = max(0, min(100, fit_score))

    # Pillar 8: Versatility
    versatility_score = calculate_versatility_score(roster_df)

    weighted_quality = weighted_average(roster_df, "Player_Quality")
    value_score = normalize(weighted_average(roster_df, "Value_Score"), 3, 16)

    # Final basketball-first model.
    # Talent should drive the simulator. Fit matters, but should not bury a roster
    # with multiple real stars and strong rotation pieces.
    overall_score = (
        talent_concentration_score * 0.27 +
        star_power_score * 0.23 +
        creation_score * 0.15 +
        defense_score * 0.14 +
        depth_score * 0.09 +
        shooting_score * 0.05 +
        rebounding_score * 0.03 +
        fit_score * 0.025 +
        versatility_score * 0.015
    )

    # More realistic contender curve.
    # Good playoff rosters should land in the 50s, elite cores in the 60s,
    # and stacked superteams in the 70s/80s.
    projected_wins = round(20 + (overall_score / 100) * 62)

    elite_count = talent_context["elite_count"]
    star_count = talent_context["star_count"]
    high_level_count = talent_context["high_level_count"]

    # Talent floors: strong star groups should not be treated like .500 teams
    # just because one slot is imperfect.
    if talent_context["is_historic"]:
        projected_wins = max(projected_wins, 78)
        overall_score = max(overall_score, 95)
    elif elite_count >= 3 or star_count >= 6:
        projected_wins = max(projected_wins, 72)
        overall_score = max(overall_score, 90)
    elif star_count >= 4 and high_level_count >= 7:
        projected_wins = max(projected_wins, 66)
        overall_score = max(overall_score, 84)
    elif star_count >= 3 and high_level_count >= 5:
        projected_wins = max(projected_wins, 60)
        overall_score = max(overall_score, 80)
    elif star_count >= 2 and high_level_count >= 5 and depth_score >= 50:
        projected_wins = max(projected_wins, 55)
        overall_score = max(overall_score, 76)
    elif high_level_count >= 4 and depth_score >= 55:
        projected_wins = max(projected_wins, 50)
        overall_score = max(overall_score, 72)

    # Balanced-team boost for rosters that win through no glaring weakness.
    pillar_scores = [
        creation_score, shooting_score, defense_score, rebounding_score,
        depth_score, fit_score, versatility_score
    ]
    if min(pillar_scores) >= 55 and defense_score >= 65 and depth_score >= 60:
        projected_wins += 5
        overall_score += 2.0
    elif min(pillar_scores) >= 50 and depth_score >= 55 and fit_score >= 60:
        projected_wins += 3
        overall_score += 1.0

    # Star trio / offensive core bonus.
    if star_count >= 3 and creation_score >= 55:
        projected_wins += 5
        overall_score += 1.8
    elif star_count >= 2 and creation_score >= 60 and depth_score >= 50:
        projected_wins += 3
        overall_score += 1.0

    # Elite balanced contender boost.
    # A team with multiple high-end players, shooting, defense, and depth
    # should not be stuck in the high-50s.
    top4_quality = roster_df["Player_Quality"].nlargest(4).mean()
    top6_quality = roster_df["Player_Quality"].nlargest(6).mean()
    strong_rotation_count = len(roster_df[roster_df["Player_Quality"] >= 50])
    high_minutes_quality = len(roster_df[(roster_df["Player_Quality"] >= 55) & (roster_df["MP"] >= 24)])

    if top4_quality >= 66 and top6_quality >= 58 and strong_rotation_count >= 7:
        projected_wins = max(projected_wins, 64)
        overall_score = max(overall_score, 86)
    elif top4_quality >= 62 and top6_quality >= 55 and strong_rotation_count >= 6:
        projected_wins = max(projected_wins, 60)
        overall_score = max(overall_score, 82)
    elif top4_quality >= 58 and strong_rotation_count >= 6 and defense_score >= 55:
        projected_wins = max(projected_wins, 56)
        overall_score = max(overall_score, 78)

    # Extra reward for elite two-way cores.
    if high_minutes_quality >= 4 and defense_score >= 60 and creation_score >= 58:
        projected_wins += 3
        overall_score += 1.2

    # Cap penalty matters, but it should not erase basketball dominance.
    # The AI report will discuss the financial cost separately.
    if payroll > salary_cap:
        if talent_context["is_historic"]:
            penalty = min(3, int((payroll - salary_cap) / 75_000_000))
        elif talent_context["is_superteam"]:
            penalty = min(5, int((payroll - salary_cap) / 50_000_000))
        elif star_count >= 3:
            penalty = min(5, int((payroll - salary_cap) / 45_000_000))
        else:
            penalty = min(7, int((payroll - salary_cap) / 30_000_000))

        projected_wins -= max(0, penalty - 1)
        overall_score -= penalty * 0.25

    # Final calibration boost: earlier versions were grading strong rosters
    # roughly 18-20 wins too harshly.
    projected_wins += 20
    overall_score += 7.5

    projected_wins = max(15, min(82, projected_wins))
    overall_score = max(0, min(100, overall_score))

    # Best Shooter should reward both efficiency and volume.
    # This prevents low-volume high-percentage players from beating true high-gravity shooters.
    roster_df["Shooter_Score"] = (
        roster_df["3P%"] * 100 * 0.62
        + roster_df["3PA"] * 4.75
        + roster_df["TS%"] * 100 * 0.14
        + roster_df["PTS"] * 0.20
    )

    qualified_shooters = roster_df[roster_df["3PA"] >= 3.0]
    if len(qualified_shooters) > 0:
        best_shooter = qualified_shooters.sort_values(
            "Shooter_Score",
            ascending=False
        ).iloc[0]
    else:
        best_shooter = roster_df.sort_values(
            "Shooter_Score",
            ascending=False
        ).iloc[0]

    best_contract = roster_df.sort_values("Value_Score", ascending=False).iloc[0]
    worst_contract = roster_df.sort_values("Value_Score", ascending=True).iloc[0]
    best_player = roster_df.sort_values("Player_Quality", ascending=False).iloc[0]
    roster_df["Defender_Leader_Score"] = roster_df.apply(defender_leader_score, axis=1)
    qualified_defenders = roster_df[roster_df["MP"] >= 20]
    if len(qualified_defenders) > 0:
        best_defender = qualified_defenders.sort_values("Defender_Leader_Score", ascending=False).iloc[0]
    else:
        best_defender = roster_df.sort_values("Defender_Leader_Score", ascending=False).iloc[0]
    worst_fit = roster_df.sort_values("Fit_Adjustment", ascending=True).iloc[0]
    best_fit = roster_df.sort_values("Fit_Adjustment", ascending=False).iloc[0]

    identity = roster_pillar_identity({"projected_wins": projected_wins})
    if talent_context["is_historic"]:
        identity = "Historic Superteam"

    return {
        "payroll": payroll,
        "remaining_cap": salary_cap - payroll,
        "salary_cap": salary_cap,
        "overall_score": round(overall_score, 1),
        "grade": wins_to_grade(projected_wins),
        "projected_wins": projected_wins,
        "creation_score": round(creation_score, 1),
        "offense_score": round(creation_score, 1),
        "defense_score": round(defense_score, 1),
        "shooting_score": round(shooting_score, 1),
        "playmaking_score": round(creation_score, 1),
        "rebounding_score": round(rebounding_score, 1),
        "star_power": round(star_power_score, 1),
        "star_power_score": round(star_power_score, 1),
        "talent_concentration_score": round(talent_concentration_score, 1),
        "depth_score": round(depth_score, 1),
        "fit_score": round(fit_score, 1),
        "versatility_score": round(versatility_score, 1),
        "value_score": round(value_score, 1),
        "weighted_quality": round(weighted_quality, 1),
        "identity": identity,
        "avg_ts": weighted_average(roster_df, "TS%"),
        "avg_3p": weighted_average(roster_df, "3P%"),
        "avg_bpm": weighted_average(roster_df, "BPM"),
        "avg_obpm": weighted_average(roster_df, "OBPM"),
        "avg_dbpm": weighted_average(roster_df, "DBPM"),
        "total_vorp": roster_df["VORP"].sum(),
        "elite_count": elite_count,
        "star_count": star_count,
        "high_level_count": high_level_count,
        "twenty_ppg_count": talent_context["twenty_ppg_count"],
        "best_contract": best_contract["Player"],
        "worst_contract": worst_contract["Player"],
        "best_player": best_player["Player"],
        "best_shooter": best_shooter["Player"],
        "best_defender": best_defender["Player"],
        "best_fit": best_fit["Player"],
        "worst_fit": worst_fit["Player"],
        "roster_with_fit": roster_df,
    }

def build_team_summary(roster_df: pd.DataFrame, metrics: dict) -> dict:
    roster_fit_df = metrics["roster_with_fit"].copy()

    players = []
    for _, row in roster_fit_df.iterrows():
        players.append({
            "name": row["Player"],
            "slot": row["Slot"],
            "slot_role": get_slot_role(row["Slot"]),
            "actual_position": row["Pos"],
            "team": row["Team"],
            "salary": money(row["Salary"]),
            "points": round(row["PTS"], 1),
            "assists": round(row["AST"], 1),
            "rebounds": round(row["TRB"], 1),
            "steals": round(row["STL"], 1),
            "blocks": round(row["BLK"], 1),
            "three_point_percentage": pct(row["3P%"]),
            "three_point_attempts": round(row["3PA"], 1),
            "true_shooting": pct(row["TS%"]),
            "PER": round(row["PER"], 1),
            "OBPM": round(row["OBPM"], 1),
            "DBPM": round(row["DBPM"], 1),
            "BPM": round(row["BPM"], 1),
            "VORP": round(row["VORP"], 1),
            "impact_score": round(row["Impact_Score"], 1),
            "value_score": round(row["Value_Score"], 1),
            "custom_defense_score": round(row["Custom_Defense"], 1),
            "player_quality_score": round(row.get("Player_Quality", calculate_player_quality_score(row)), 1),
            "fit_adjustment": int(row["Fit_Adjustment"]),
            "fit_label": fit_label(int(row["Fit_Adjustment"])),
            "fit_notes": row["Fit_Notes"],
            "role": get_player_role(row),
        })

    return {
        "team_metrics": {
            "salary_cap": money(metrics["salary_cap"]),
            "payroll": money(metrics["payroll"]),
            "remaining_cap": money(metrics["remaining_cap"]),
            "salary_cap_raw": metrics["salary_cap"],
            "payroll_raw": metrics["payroll"],
            "remaining_cap_raw": metrics["remaining_cap"],
            "projected_wins": metrics["projected_wins"],
            "overall_score": metrics["overall_score"],
            "grade": metrics["grade"],
            "identity": metrics["identity"],
            "creation_score": metrics["creation_score"],
            "offense_score": metrics["offense_score"],
            "defense_score": metrics["defense_score"],
            "shooting_score": metrics["shooting_score"],
            "playmaking_score": metrics["playmaking_score"],
            "rebounding_score": metrics["rebounding_score"],
            "star_power": metrics["star_power"],
            "talent_concentration_score": metrics.get("talent_concentration_score", 0),
            "top_end_score": metrics.get("top_end_score", metrics["star_power"]),
            "superstar_score": metrics.get("superstar_score", 50),
            "weighted_quality": metrics.get("weighted_quality", 0),
            "elite_count": metrics.get("elite_count", 0),
            "star_count": metrics.get("star_count", 0),
            "high_level_count": metrics.get("high_level_count", 0),
            "twenty_ppg_count": metrics.get("twenty_ppg_count", 0),
            "depth_score": metrics["depth_score"],
            "value_score": metrics["value_score"],
            "fit_score": metrics["fit_score"],
            "versatility_score": metrics["versatility_score"],
            "average_TS": pct(metrics["avg_ts"]),
            "average_3P": pct(metrics["avg_3p"]),
            "average_BPM": round(metrics["avg_bpm"], 2),
            "average_OBPM": round(metrics["avg_obpm"], 2),
            "average_DBPM": round(metrics["avg_dbpm"], 2),
            "total_VORP": round(metrics["total_vorp"], 2),
            "best_contract": metrics["best_contract"],
            "worst_contract": metrics["worst_contract"],
            "best_player": metrics["best_player"],
            "best_shooter": metrics["best_shooter"],
            "best_defender": metrics["best_defender"],
            "best_fit": metrics["best_fit"],
            "worst_fit": metrics["worst_fit"],
        },
        "players": players
    }



def build_report_groups(team_summary: dict) -> dict:
    """
    Creates roster-aware context so each AI report is unique.
    No hardcoded player examples. Everything comes from the drafted roster.
    """
    players = team_summary["players"]
    metrics = team_summary["team_metrics"]

    def sf(value):
        try:
            if isinstance(value, str):
                return float(value.replace("%", "").replace("$", "").replace("M", ""))
            return float(value)
        except Exception:
            return 0.0

    def top_by(key, n=5, reverse=True):
        return sorted(players, key=lambda p: sf(p.get(key, 0)), reverse=reverse)[:n]

    def pct_to_float(value):
        if isinstance(value, str):
            return sf(value.replace("%", ""))
        return sf(value) * 100

    core_players = top_by("player_quality_score", 6)

    creators = sorted(
        players,
        key=lambda p: (
            sf(p.get("assists", 0)) * 0.45 +
            sf(p.get("points", 0)) * 0.18 +
            sf(p.get("OBPM", 0)) * 0.17 +
            sf(p.get("player_quality_score", 0)) * 0.20
        ),
        reverse=True
    )[:6]

    shooters = sorted(
        [p for p in players if sf(p.get("three_point_attempts", 0)) >= 2.0],
        key=lambda p: (
            pct_to_float(p.get("three_point_percentage", "0%")) * 0.50 +
            sf(p.get("three_point_attempts", 0)) * 4.0 +
            sf(p.get("points", 0)) * 0.40
        ),
        reverse=True
    )[:6]

    defenders = sorted(
        players,
        key=lambda p: (
            sf(p.get("custom_defense_score", 0)) * 0.45 +
            sf(p.get("rebounds", 0)) * 1.5 +
            sf(p.get("blocks", 0)) * 4.0 +
            sf(p.get("steals", 0)) * 3.0 +
            sf(p.get("player_quality_score", 0)) * 0.15
        ),
        reverse=True
    )[:6]

    rebounders = sorted(players, key=lambda p: sf(p.get("rebounds", 0)), reverse=True)[:5]
    rim_protectors = sorted(players, key=lambda p: sf(p.get("blocks", 0)), reverse=True)[:5]
    value_players = sorted(players, key=lambda p: sf(p.get("value_score", 0)), reverse=True)[:5]
    best_fits = sorted(players, key=lambda p: sf(p.get("fit_adjustment", 0)), reverse=True)[:5]
    fit_concerns = sorted(players, key=lambda p: sf(p.get("fit_adjustment", 0)))[:5]

    starters = [p for p in players if p.get("slot", "").startswith("Starting")]
    bench = [p for p in players if p.get("slot_role") in ["SIXTH_MAN", "BENCH", "TWO_WAY"]]
    two_way = [p for p in players if p.get("slot_role") == "TWO_WAY"]

    # Dynamic roster fingerprint.
    projected_wins = int(metrics.get("projected_wins", 0))
    offense = sf(metrics.get("offense_score", 0))
    defense = sf(metrics.get("defense_score", 0))
    shooting = sf(metrics.get("shooting_score", 0))
    playmaking = sf(metrics.get("playmaking_score", 0))
    depth = sf(metrics.get("depth_score", 0))
    fit = sf(metrics.get("fit_score", 0))
    star_count = int(metrics.get("star_count", 0))
    elite_count = int(metrics.get("elite_count", 0))

    if projected_wins >= 70 or elite_count >= 3:
        roster_type = "superteam"
    elif defense >= 68 and depth >= 55 and star_count < 3:
        roster_type = "defense-and-depth team"
    elif shooting >= 72 and offense >= 65:
        roster_type = "spacing-heavy offensive team"
    elif fit >= 68 and depth >= 60:
        roster_type = "balanced team built on fit and depth"
    elif offense >= 72 and defense < 55:
        roster_type = "offense-first team with defensive questions"
    elif defense >= 70 and offense < 58:
        roster_type = "defense-first team with creation concerns"
    elif projected_wins >= 43:
        roster_type = "competitive playoff-level roster"
    else:
        roster_type = "developmental or incomplete roster"

    # Dynamic strengths.
    strengths = []
    if offense >= 70:
        strengths.append("high-end offensive creation")
    if shooting >= 70:
        strengths.append("floor spacing")
    if defense >= 68:
        strengths.append("defensive versatility")
    if depth >= 60:
        strengths.append("rotation depth")
    if fit >= 65:
        strengths.append("lineup fit")
    if elite_count >= 3:
        strengths.append("overwhelming star power")
    if playmaking >= 65:
        strengths.append("multiple decision-makers")
    if not strengths:
        strengths = ["salary flexibility", "defined roles", "development upside"]

    # Dynamic concerns.
    concerns = []
    if offense < 58:
        concerns.append("lack of elite half-court creation")
    if defense < 58:
        concerns.append("defensive reliability")
    if shooting < 58:
        concerns.append("spacing consistency")
    if playmaking < 55:
        concerns.append("playmaking burden")
    if depth < 45:
        concerns.append("bench reliability")
    if fit < 55:
        concerns.append("positional fit")
    if star_count >= 6:
        concerns.append("role sacrifice among high-usage players")
    if not concerns:
        concerns = ["playoff matchup execution", "health", "late-game role clarity"]

    # Trait hints based only on actual selected players.
    trait_map = {}
    for p in players:
        traits = []
        pos = p.get("actual_position", "")
        slot = p.get("slot", "")
        pts = sf(p.get("points", 0))
        ast = sf(p.get("assists", 0))
        reb = sf(p.get("rebounds", 0))
        blk = sf(p.get("blocks", 0))
        stl = sf(p.get("steals", 0))
        three_pa = sf(p.get("three_point_attempts", 0))
        three_pct = pct_to_float(p.get("three_point_percentage", "0%"))
        fit_adj = sf(p.get("fit_adjustment", 0))

        if ast >= 7:
            traits.append("primary table-setter")
        elif ast >= 5:
            traits.append("secondary creator")
        if pts >= 25:
            traits.append("high-volume scorer")
        elif pts >= 18:
            traits.append("reliable scorer")
        if three_pct >= 37 and three_pa >= 5:
            traits.append("high-volume spacer")
        elif three_pct >= 36 and three_pa >= 3:
            traits.append("credible spacer")
        if reb >= 8:
            traits.append("strong rebounder")
        if blk >= 1.2:
            traits.append("rim protection presence")
        if stl >= 1.2:
            traits.append("active hands defensively")
        if fit_adj >= 5:
            traits.append("clean positional fit")
        elif fit_adj <= -3:
            traits.append("fit risk")
        if pos in ["C", "PF"] and ast >= 4:
            traits.append("frontcourt passer")
        if pos in ["SG", "SF"] and reb >= 6:
            traits.append("wing rebounding")
        if "Two-Way" in slot:
            traits.append("developmental/depth role")

        trait_map[p["name"]] = traits[:5] if traits else ["rotation piece"]

    return {
        "roster_type": roster_type,
        "dynamic_strengths": strengths[:5],
        "dynamic_concerns": concerns[:5],
        "trait_map": trait_map,
        "core_players": core_players,
        "primary_creators": creators,
        "spacing_group": shooters,
        "defensive_group": defenders,
        "rebounding_group": rebounders,
        "rim_protection_group": rim_protectors,
        "bench_unit": bench,
        "starters": starters,
        "two_way_slots": two_way,
        "best_fit_combinations": best_fits,
        "fit_concerns": fit_concerns,
        "best_value_contracts": value_players,
        "top_end_core": core_players[:6],
        "creation_spacing_pairs": {
            "creators": creators[:4],
            "spacers": shooters[:4]
        },
        "defense_frontcourt_pairs": {
            "defenders": defenders[:4],
            "frontcourt": rebounders[:5]
        }
    }


# ============================================================
# REPORT GENERATION
# ============================================================

def fallback_report(team_summary: dict) -> str:
    """
    Built-in non-AI report used only when no OpenAI API key is available.
    The true autonomous report requires the API key.
    """
    m = team_summary["team_metrics"]
    players = team_summary["players"]

    creators = sorted(players, key=lambda p: (p["assists"], p["points"]), reverse=True)[:4]
    shooters = sorted(
        [p for p in players if p["three_point_attempts"] >= 2],
        key=lambda p: (float(str(p["three_point_percentage"]).replace("%", "")), p["three_point_attempts"]),
        reverse=True
    )[:4]
    defenders = sorted(players, key=lambda p: (p["rebounds"] + p["blocks"] + p["steals"]), reverse=True)[:5]

    def names(group):
        return ", ".join([p["name"] for p in group]) if group else "no clear group"

    report = f"""
# Executive Summary

This roster projects as a **{m['identity']}** with a **{m['grade']}** grade and **{m['projected_wins']} projected wins**. Payroll sits at **{m['payroll']}** against a **{m['salary_cap']}** cap.

This built-in report is a basic fallback. For the full autonomous ChatGPT-style report, set your OpenAI API key and click Generate AI Report again.

# Offensive Identity

The primary offensive pressure comes from **{names(creators)}**. The key spacing pieces are **{names(shooters)}**.

This offense will work best when the creators force the defense to rotate and the shooters punish late closeouts.

# Defensive Blueprint

The defensive structure is most likely shaped by **{names(defenders)}**. The question is whether this group has enough point-of-attack resistance, rebounding, and back-line support to survive against better offenses.

# Final Verdict

The projection makes sense if the team's best traits show up consistently. If the roster lacks elite creation, rim protection, or role clarity, those weaknesses will show up quickly over a full season.
"""
    return report

def generate_ai_report(team_summary: dict) -> str:
    """
    AI report generation with real autonomy.

    The app provides:
    - full 13-man roster
    - selected role slots
    - clean player stats
    - team result metrics

    The model decides what actually matters.
    The only fixed structure is the four required headings.
    """
    api_key = OPENAI_API_KEY.strip()

    if OpenAI is None:
        return fallback_report(team_summary)

    if api_key == PLACEHOLDER_API_KEY or not api_key:
        return fallback_report(team_summary)

    client = OpenAI(api_key=api_key)

    # Keep the payload clean. Do not pre-label "top creators", "top defenders",
    # "best shooter", etc. Let the AI reason from the roster.
    ai_payload = {
        "team_result": {
            "draft_grade": team_summary["team_metrics"]["grade"],
            "projected_wins": team_summary["team_metrics"]["projected_wins"],
            "team_identity": team_summary["team_metrics"]["identity"],
            "payroll": team_summary["team_metrics"]["payroll"],
            "salary_cap": team_summary["team_metrics"]["salary_cap"],
            "remaining_cap": team_summary["team_metrics"].get("remaining_cap"),
            "salary_context": {
                "payroll_formatted": team_summary["team_metrics"]["payroll"],
                "salary_cap_formatted": team_summary["team_metrics"]["salary_cap"],
                "remaining_cap_formatted": team_summary["team_metrics"]["remaining_cap"],
                "payroll_raw": team_summary["team_metrics"].get("payroll_raw"),
                "salary_cap_raw": team_summary["team_metrics"].get("salary_cap_raw"),
                "remaining_cap_raw": team_summary["team_metrics"].get("remaining_cap_raw"),
                "format_rule": "Always write salaries like $211.7M, $222.0M, or $10.3M. Never write 211.7millionagainsta222 million cap."
            },
            "overall_score": team_summary["team_metrics"]["overall_score"],
            "category_scores": {
                "creation": team_summary["team_metrics"].get("creation_score", team_summary["team_metrics"].get("offense_score")),
                "shooting": team_summary["team_metrics"]["shooting_score"],
                "defense": team_summary["team_metrics"]["defense_score"],
                "rebounding": team_summary["team_metrics"].get("rebounding_score"),
                "star_power": team_summary["team_metrics"].get("star_power"),
                "depth": team_summary["team_metrics"]["depth_score"],
                "fit": team_summary["team_metrics"]["fit_score"],
                "versatility": team_summary["team_metrics"].get("versatility_score"),
                "talent_concentration": team_summary["team_metrics"].get("talent_concentration_score"),
            }
        },
        "roster": [
            {
                "slot": p["slot"],
                "player": p["name"],
                "listed_position": p["actual_position"],
                "team": p["team"],
                "salary": p["salary"],
                "ppg": p["points"],
                "apg": p["assists"],
                "rpg": p["rebounds"],
                "spg": p["steals"],
                "bpg": p["blocks"],
                "three_point_percentage": p["three_point_percentage"],
                "three_point_attempts": p["three_point_attempts"],
                "true_shooting": p["true_shooting"],
                "role": p["role"],
                "fit_label": p["fit_label"],
                "fit_notes": p["fit_notes"],
            }
            for p in team_summary["players"]
        ],
        "instructions": {
            "required_headings": [
                "Executive Summary",
                "Offensive Identity",
                "Defensive Blueprint",
                "Salary Cap Analysis",
                "Final Verdict"
            ],
            "autonomy": "You decide what the roster's real story is. Do not follow a hidden template.",
            "important": [
                "Only mention players on this roster.",
                "Do not mention outside examples.",
                "Do not use a generic report pattern.",
                "Do not force equal coverage of every stat category.",
                "Explain why the projected wins make sense.",
                "Use basketball language first and stats second.",
                "Use stats naturally and sparingly.",
                "Do not mention custom defensive score, BPM, DBPM, OBPM, player quality score, or fit adjustment numbers.",
                "Do not say the same phrases every report.",
                "Make the report feel like a fresh answer from ChatGPT to this specific roster."
            ]
        }
    }

    prompt = f"""
You are ChatGPT acting as an NBA front office analyst.

Write a fresh, original scouting report for the custom roster below.

You have autonomy. Think about the roster first, then write the report.
Do not simply fill in a template.
Do not write the same kind of report every time.
Do not just change the names from a previous report.

You must use exactly these five section headings and no others:

# Executive Summary
# Offensive Identity
# Defensive Blueprint
# Salary Cap Analysis
# Final Verdict

Within those four sections, you decide what matters most.

Before writing, silently identify the roster's biggest basketball story:
- Is this a defense-and-depth team?
- Is it a superteam or historic superteam?
- Is it a shooting-heavy team?
- Is it a team with good role players but no true offensive engine?
- Is it positionally weird?
- Is it deep but lacking top-end talent?
- Is it talented but poorly balanced?

Build the entire report around that specific story.

Strict rules:
- Only discuss players who are actually on the roster.
- Never mention outside player examples.
- Do not mention custom defensive score, BPM, DBPM, OBPM, player quality score, or fit adjustment numbers.
- You may mention normal basketball stats naturally, especially PPG/APG/RPG and shooting percentages.
- Do not overhype the team if the projected wins are low.
- If the projection is around 40 wins, write like this is a competitive but flawed team.
- If the projection is around 50 wins, write like this is a strong playoff team with limitations.
- If the projection is 60+ wins, write like this is a serious contender.
- If the projection is 70+ wins, write like this is a dominant superteam.
- If the identity says Historic Superteam, make the report feel like the roster has broken normal roster-building rules.
- Explain role fit using the actual selected slots: Starting PG, Starting SG, Starting SF, Starting PF, Starting C, 6th Man, Bench, Two-Way.
- If a player is out of position, explain how that affects the roster.
- Avoid repetitive phrases like "the roster is built around" unless it truly fits.
- Sound like a real basketball analyst, not a spreadsheet.
- Evaluate the roster as both a basketball team and a front-office asset.
- In Salary Cap Analysis, discuss payroll, salary cap level, cap flexibility, luxury-tax/apron pressure, best-value contracts, and expensive contracts when relevant.
- Do not simply list salaries; explain what the financial structure means for team-building.
- Always format money cleanly, like "$211.7M payroll against a $222.0M cap."
- Never write salary text without spaces, such as "211.7millionagainsta222 million cap."

Roster and team data:
{json.dumps(ai_payload, indent=2)}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=1.05
    )

    return response.output_text

def get_team_hash(team_summary: dict) -> str:
    raw = json.dumps(team_summary, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


# ============================================================
# SESSION STATE
# ============================================================

if "roster" not in st.session_state:
    st.session_state.roster = {}

if "reports" not in st.session_state:
    st.session_state.reports = {}

if "player_select_reset" not in st.session_state:
    st.session_state.player_select_reset = 0

if "sidebar_select_reset" not in st.session_state:
    st.session_state.sidebar_select_reset = 0

if "roster_size" not in st.session_state:
    st.session_state.roster_size = DEFAULT_ROSTER_SIZE

# Always define active roster slots before any header, popover, sidebar, or layout code uses it.
active_roster_slots = ROSTER_SLOTS[:st.session_state.roster_size]


# ============================================================
# HEADER
# ============================================================

import base64

def image_to_base64(path: str) -> str:
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

_logo_b64 = image_to_base64(LOGO_PATH)

if _logo_b64:
    st.markdown(
        f"""
        <div class="hero-wrap">
            <div class="hero-grid">
                <img class="hero-logo" src="data:image/png;base64,{_logo_b64}" />
                <div>
                    <div class="hero-eyebrow">BaileyBI Presents</div>
                    <div class="main-title">NBA Front Office Simulator</div>
                    <div class="sub-title">Build an NBA roster with real salaries, flexible positions, fit boosts/penalties, and AI scouting reports.</div>
                    <div class="hero-badges">
                        <span class="hero-badge">🏀 Real Salaries</span>
                        <span class="hero-badge">📊 Advanced Metrics</span>
                        <span class="hero-badge">🧠 AI Scouting</span>
                        <span class="hero-badge">💼 Cap Strategy</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown('<div class="main-title">NBA Front Office Simulator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Build an NBA roster with real salaries, flexible positions, fit boosts/penalties, and AI scouting reports.</div>',
        unsafe_allow_html=True
    )

st.markdown(
    """
    <div class="visual-strip">
        <div class="visual-tile">
            <div class="visual-icon">💼</div>
            <div class="visual-title">Front Office Mode</div>
            <div class="visual-copy">Balance talent, payroll, roles, and cap pressure.</div>
        </div>
        <div class="visual-tile">
            <div class="visual-icon">📈</div>
            <div class="visual-title">Roster Scoring</div>
            <div class="visual-copy">Creation, defense, depth, fit, and star power.</div>
        </div>
        <div class="visual-tile">
            <div class="visual-icon">🎯</div>
            <div class="visual-title">Flexible Positions</div>
            <div class="visual-copy">Play anyone anywhere and grade the fit.</div>
        </div>
        <div class="visual-tile">
            <div class="visual-icon">🧠</div>
            <div class="visual-title">AI Reports</div>
            <div class="visual-copy">Generate unique front-office scouting analysis.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="mobile-filter-callout">
        <div class="mobile-filter-title">⚙️ Filters & Salary Cap</div>
        <div class="mobile-filter-copy">Tap the arrow in the top-left corner to open filters, player search, sort options, and salary cap levels.</div>
    </div>
    """,
    unsafe_allow_html=True
)

if OPENAI_API_KEY.strip() != PLACEHOLDER_API_KEY:
    st.success("OpenAI API key loaded. Autonomous AI reports are enabled.")
else:
    st.warning("OpenAI API key not found. Paste your NEW key into the single OPENAI_API_KEY line near the top of the script.")

# Mobile roster shortcut
st.markdown(
    """
    <div class="mobile-roster-callout">
        <div class="mobile-roster-title">📋 Current Roster</div>
        <div class="mobile-roster-copy">Use the roster popover below to check your team without scrolling.</div>
    </div>
    """,
    unsafe_allow_html=True
)

active_roster_slots = ROSTER_SLOTS[:st.session_state.get("roster_size", DEFAULT_ROSTER_SIZE)]
roster_rows_mobile = list(st.session_state.roster.values())
payroll_mobile = sum([p.get("Salary", 0) for p in roster_rows_mobile])
current_salary_cap_for_popover = st.session_state.get("active_salary_cap", DEFAULT_SALARY_CAP)
remaining_mobile = current_salary_cap_for_popover - payroll_mobile

with st.popover(f"📋 View Roster ({len(roster_rows_mobile)}/{st.session_state.roster_size})", use_container_width=True):
    st.markdown(f"**Payroll:** {money(payroll_mobile)}")
    st.markdown(f"**Remaining:** {money(remaining_mobile)}")

    for slot in active_roster_slots:
        if slot in st.session_state.roster:
            p = st.session_state.roster[slot]
            st.markdown(
                f"""
                <div class="popover-roster-card">
                    <div class="popover-roster-slot">{slot}</div>
                    <div class="popover-roster-player">{p['Player']}</div>
                    <div class="popover-roster-detail">
                        {p['Team']} | Listed {p['Pos']} | {money(p['Salary'])}<br>
                        {float(p['PTS']):.1f} PPG | {float(p['AST']):.1f} APG | {float(p['TRB']):.1f} RPG
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"Remove {p['Player']}",
                key=f"popover_remove_{slot}_{p['Player']}"
            ):
                del st.session_state.roster[slot]
                st.session_state.reports = {}
                st.rerun()
        else:
            st.markdown(
                f"""
                <div class="popover-roster-card">
                    <div class="popover-roster-slot">{slot}</div>
                    <div class="popover-roster-player">Empty Slot</div>
                    <div class="popover-roster-detail">Select any player. Fit will be graded after placement.</div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    if _logo_b64:
        st.markdown(
            f"""
            <div class="brand-sidebar">
                <img src="data:image/png;base64,{_logo_b64}" />
                <div class="brand-sidebar-title">BAILEYBI</div>
                <div class="brand-sidebar-sub">Data. Insight. Impact.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.header("⚙️ Filters & Salary Cap")
    st.caption("Use these controls to search players, filter the draft pool, and change the active salary level.")

    roster_size = st.selectbox(
    "Roster Size",
    list(range(9, 16)),
        index=list(range(9, 16)).index(st.session_state.roster_size),
        help="Results unlock once you draft at least 9 players. You can build up to 15."
    )
    st.session_state.roster_size = roster_size
    active_roster_slots = ROSTER_SLOTS[:st.session_state.roster_size]

    # Remove players from slots outside the selected roster size.
    for slot in list(st.session_state.roster.keys()):
        if slot not in active_roster_slots:
            del st.session_state.roster[slot]
            st.session_state.reports = {}

    preset_choice = st.selectbox(
        "Preset Current Rosters",
        ["None"] + list(PRESET_ROSTERS.keys())
    )

    if st.button("Load Preset Roster", type="secondary"):
        if preset_choice == "None":
            st.warning("Choose a preset roster first.")
        else:
            loaded, missing = load_preset_roster(preset_choice, roster_size, df)
            st.session_state.roster = loaded
            st.session_state.reports = {}
            if missing:
                st.warning("Preset loaded, but these players were not found in your dataset: " + ", ".join(missing))
            st.rerun()

    cap_choice = st.selectbox(
        "Salary Level",
        list(SALARY_CAP_LEVELS.keys()),
        index=list(SALARY_CAP_LEVELS.keys()).index("Second Apron")
    )

    if cap_choice == "Custom":
        salary_cap = st.number_input(
            "Custom Salary Cap",
            min_value=100_000_000,
            max_value=700_000_000,
            value=SALARY_CAP_LEVELS["Custom"],
            step=5_000_000,
            format="%d"
        )
    else:
        salary_cap = SALARY_CAP_LEVELS[cap_choice]

    st.session_state.active_salary_cap = salary_cap

    st.caption(
        f"Active level: {cap_choice} — ${salary_cap / 1_000_000:.0f}M"
    )

    st.markdown(
        """
        <div class="small-note">
        Salary Cap: $165M<br>
        Salary Floor: $149M<br>
        Luxury Tax: $201M<br>
        First Apron: $209M<br>
        Second Apron: $222M
        </div>
        """,
        unsafe_allow_html=True
    )

    search = st.text_input("Search Player")

    teams = sorted(df["Team"].unique())
    selected_teams = st.multiselect("Filter Teams", teams, default=[])

    positions = sorted(df["Pos"].unique())
    selected_positions = st.multiselect("Filter Listed Positions", positions, default=[])

    min_minutes = st.slider("Minimum Minutes Per Game", 0, 40, 10)

    sort_label = st.selectbox(
        "Sort Players By",
        ["PPG", "APG", "RPG", "FG%", "3P%", "TS%", "Salary"],
        index=0
    )

    SORT_MAP = {
        "PPG": "PTS",
        "APG": "AST",
        "RPG": "TRB",
        "FG%": "FG%",
        "3P%": "3P%",
        "TS%": "TS%",
        "Salary": "Salary",
    }

    sort_by = SORT_MAP[sort_label]

    sidebar_player_pool = df.copy()

    if search:
        sidebar_player_pool = sidebar_player_pool[
            sidebar_player_pool["Player"].str.contains(search, case=False, na=False)
        ]

    if selected_teams:
        sidebar_player_pool = sidebar_player_pool[sidebar_player_pool["Team"].isin(selected_teams)]

    if selected_positions:
        sidebar_player_pool = sidebar_player_pool[sidebar_player_pool["Pos"].isin(selected_positions)]

    sidebar_player_pool = sidebar_player_pool[sidebar_player_pool["MP"] >= min_minutes]
    sidebar_player_pool = sidebar_player_pool.sort_values(sort_by, ascending=False)

    st.divider()
    st.subheader("Quick Add")

    selected_players_sidebar = [v["Player"] for v in st.session_state.roster.values()]
    sidebar_available_players = sidebar_player_pool[
        ~sidebar_player_pool["Player"].isin(selected_players_sidebar)
    ]

    sidebar_open_slots = [slot for slot in active_roster_slots if slot not in st.session_state.roster]

    if len(sidebar_open_slots) == 0:
        st.success("Roster full.")
    elif len(sidebar_available_players) == 0:
        st.warning("No available players match your filters.")
    else:
        sidebar_selected_slot = st.selectbox(
            "Roster Slot",
            sidebar_open_slots,
            key="sidebar_quick_slot"
        )

        sidebar_selected_player_name = st.selectbox(
            "Player",
            sidebar_available_players["Player"].tolist(),
            key=f"sidebar_quick_player_{st.session_state.sidebar_select_reset}"
        )

        if st.button("Add Player", type="primary", key="sidebar_add_player"):
            sidebar_selected_player = sidebar_available_players[
                sidebar_available_players["Player"] == sidebar_selected_player_name
            ].iloc[0].to_dict()

            sidebar_selected_player["Slot"] = sidebar_selected_slot

            fit, notes = calculate_position_fit(
                pd.Series(sidebar_selected_player),
                sidebar_selected_slot
            )

            sidebar_selected_player["Fit_Adjustment"] = fit
            sidebar_selected_player["Fit_Notes"] = "; ".join(notes)

            st.session_state.roster[sidebar_selected_slot] = sidebar_selected_player
            st.session_state.reports = {}
            st.session_state.sidebar_select_reset += 1
            st.rerun()

    if st.button("Clear Roster"):
        st.session_state.roster = {}
        st.session_state.reports = {}
        st.rerun()


# ============================================================
# LAYOUT
# ============================================================

left, right = st.columns([1, 1], gap="large")


# ============================================================
# PLAYER POOL
# ============================================================

with left:
    st.markdown('<div class="section-title">Player Pool</div>', unsafe_allow_html=True)

    player_pool = df.copy()

    if search:
        player_pool = player_pool[player_pool["Player"].str.contains(search, case=False, na=False)]

    if selected_teams:
        player_pool = player_pool[player_pool["Team"].isin(selected_teams)]

    if selected_positions:
        player_pool = player_pool[player_pool["Pos"].isin(selected_positions)]

    player_pool = player_pool[player_pool["MP"] >= min_minutes]
    player_pool = player_pool.sort_values(sort_by, ascending=False)

    st.markdown(
        """
        <div class="mobile-draft-panel">
            <div class="mobile-draft-title">Quick Draft</div>
            <div class="mobile-draft-copy">Search a player, choose the roster slot, and add them. Results unlock at 13 players, with room to build up to 15.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    selected_players = [v["Player"] for v in st.session_state.roster.values()]
    available_players = player_pool[~player_pool["Player"].isin(selected_players)]
    open_slots = [slot for slot in active_roster_slots if slot not in st.session_state.roster]

    if len(available_players) == 0:
        st.warning("No available players match your current filters.")
    else:
        player_name_options = [""] + available_players["Player"].tolist()

        selected_player_name = st.selectbox(
            "Search / Select Player",
            player_name_options,
            index=0,
            key=f"main_player_select_{st.session_state.player_select_reset}",
            placeholder="Type or select a player"
        )

        if selected_player_name:
            selected_player_preview = available_players[
                available_players["Player"] == selected_player_name
            ].iloc[0]

            st.markdown(
                f"""
                <div class="mobile-player-preview">
                    <div class="mobile-player-name">{selected_player_preview['Player']}</div>
                    <div class="mobile-player-meta">
                        {selected_player_preview['Pos']} | {money(selected_player_preview['Salary'])}<br>
                        {selected_player_preview['PPG']:.1f} PPG | {selected_player_preview['APG']:.1f} APG | {selected_player_preview['RPG']:.1f} RPG
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        selected_slot = st.selectbox(
            "Roster Slot",
            open_slots if open_slots else ["Roster Full"],
            key="main_slot_select"
        )

        st.caption("Any player can play any slot. The scoring engine applies fit boosts and penalties.")

        if st.button("Add to Roster", type="primary", key="main_add_to_roster"):
            if not selected_player_name:
                st.warning("Select a player first.")
            elif selected_slot == "Roster Full":
                st.warning("Your roster is already full.")
            elif selected_slot in st.session_state.roster:
                st.warning("That roster slot is already filled.")
            else:
                selected_player = available_players[available_players["Player"] == selected_player_name].iloc[0].to_dict()
                selected_player["Slot"] = selected_slot

                fit, notes = calculate_position_fit(pd.Series(selected_player), selected_slot)
                selected_player["Fit_Adjustment"] = fit
                selected_player["Fit_Notes"] = "; ".join(notes)

                st.session_state.roster[selected_slot] = selected_player
                st.session_state.reports = {}
                st.session_state.player_select_reset += 1
                st.rerun()


# ============================================================
# ROSTER PANEL
# ============================================================

with right:
    st.markdown('<div class="section-title">Roster Summary</div>', unsafe_allow_html=True)

    roster_rows = list(st.session_state.roster.values())
    payroll = sum([p.get("Salary", 0) for p in roster_rows])
    remaining = salary_cap - payroll

    c1, c2 = st.columns(2, gap="medium")

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Payroll</div>
                <div class="metric-value">{money(payroll)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Remaining</div>
                <div class="metric-value">{money(remaining)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.progress(min(payroll / salary_cap, 1.0))

    if payroll > salary_cap:
        st.error("You are over the salary cap. Your team can still be scored, but it may receive a penalty.")

    st.caption("Use the 📋 View Roster dropdown near the top to review all 13 slots without scrolling.")


# ============================================================
# RESULTS
# ============================================================

st.divider()

if len(st.session_state.roster) >= MIN_RESULTS_PLAYERS:
    roster_df = pd.DataFrame(list(st.session_state.roster.values()))

    # Ensure Slot is correct from dict keys.
    for slot in active_roster_slots:
        if slot in st.session_state.roster:
            roster_df.loc[roster_df["Player"] == st.session_state.roster[slot]["Player"], "Slot"] = slot

    metrics = calculate_team_metrics(roster_df, salary_cap)
    roster_fit_df = metrics["roster_with_fit"]
    team_summary = build_team_summary(roster_df, metrics)

    st.markdown('<div class="section-title">Team Results</div>', unsafe_allow_html=True)

    a, b, c, d, e = st.columns(5)

    with a:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Draft Grade</div>
                <div class="metric-value">{metrics['grade']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with b:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Projected Wins</div>
                <div class="metric-value">{metrics['projected_wins']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Overall Score</div>
                <div class="metric-value">{metrics['overall_score']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with d:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Fit Score</div>
                <div class="metric-value">{metrics['fit_score']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with e:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Team Identity</div>
                <div class="metric-value" style="font-size:18px;">{metrics['identity']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-title">Category Grades</div>', unsafe_allow_html=True)

    grade_df = pd.DataFrame({
        "Category": [
            "Creation", "Shooting", "Defense", "Rebounding",
            "Star / Top-End Talent", "Talent Concentration", "Depth", "Position Fit", "Versatility"
        ],
        "Score": [
            metrics["creation_score"], metrics["shooting_score"], metrics["defense_score"],
            metrics["rebounding_score"], metrics["star_power_score"], metrics["talent_concentration_score"],
            metrics["depth_score"], metrics["fit_score"], metrics["versatility_score"]
        ]
    })

    st.bar_chart(grade_df.set_index("Category"))

    st.markdown('<div class="section-title">Key Contributors</div>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.info(f"Best Player: {metrics['best_player']}")

    with k2:
        st.info(f"Best Shooter: {metrics['best_shooter']}")

    with k3:
        st.info(f"Best Defender: {metrics['best_defender']}")

    with k4:
        st.info(f"Best Contract: {metrics['best_contract']}")

    f1, f2 = st.columns(2)
    with f1:
        st.success(f"Best Positional Fit: {metrics['best_fit']}")
    with f2:
        st.warning(f"Biggest Fit Concern: {metrics['worst_fit']}")

    st.markdown('<div class="section-title">Player Role & Fit Breakdown</div>', unsafe_allow_html=True)

    role_data = []
    for _, row in roster_fit_df.iterrows():
        role_data.append({
            "Slot": row["Slot"],
            "Player": row["Player"],
            "Listed Pos": row["Pos"],
            "Role": get_player_role(row),
            "Salary": money(row["Salary"]),
            "Fit": f"{fit_label(int(row['Fit_Adjustment']))} ({int(row['Fit_Adjustment']):+d})",
            "Fit Notes": row["Fit_Notes"],
            "3P%": pct(row["3P%"]),
            "TS%": pct(row["TS%"]),
            "Quality": round(row["Player_Quality"], 1),
        })

    st.dataframe(pd.DataFrame(role_data), use_container_width=True, height=360)

    st.markdown('<div class="section-title">AI Scouting Report</div>', unsafe_allow_html=True)

    team_hash = get_team_hash(team_summary)

    if st.button("Generate AI Report", type="primary"):
        with st.spinner("Generating scouting report..."):
            st.session_state.reports[team_hash] = generate_ai_report(team_summary)

    if team_hash in st.session_state.reports:
        st.markdown(st.session_state.reports[team_hash])
    else:
        st.caption("Click Generate AI Report to create a full front-office scouting report.")

else:
    st.warning(
        f"Draft at least {MIN_RESULTS_PLAYERS} players to generate team results. Current roster: {len(st.session_state.roster)}/{st.session_state.roster_size}."
    )
