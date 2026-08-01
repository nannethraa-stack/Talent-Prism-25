"""
TalentPrism Assessment Engine
Enterprise Adaptive Diagnostic Platform (Streamlit + reportlab)

Run with:  streamlit run talentprism_app.py
"""

import io
import json
import math
import os
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.graphics import shapes
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Question bank (ported from the JS prototype)
# ---------------------------------------------------------------------------
POSITIVE_PSYCHOLOGY = [
    ("p1", "I generally expect good outcomes, even when circumstances are uncertain."),
    ("p2", "When faced with a setback, I quickly start looking for the silver lining."),
    ("p3", "I find it easy to stay hopeful about the future."),
    ("p4", "I regularly notice and value the good things in my life and work."),
    ("p5", "I make a habit of acknowledging others' contributions."),
    ("p6", "I feel a strong sense of appreciation for opportunities that come my way."),
    ("p7", "I actively seek out new knowledge, even outside my immediate responsibilities."),
    ("p8", "I enjoy exploring how things work at a deeper level."),
    ("p9", "I look forward to learning something new almost every day."),
    ("p10", "I approach my work and projects with energy and enthusiasm."),
    ("p11", "Others often notice my enthusiasm rubbing off on them."),
    ("p12", "I rarely feel drained by tasks that genuinely interest me, no matter how long they take."),
    ("p13", "I feel a strong internal push to accomplish something meaningful every day."),
    ("p14", "I set demanding personal targets and work hard to hit them."),
    ("p15", "Completing a task well gives me a deep sense of satisfaction."),
]

LOW_ORG_PSYCHOLOGY = [
    ("lo1", "I tend to view top-down management initiatives with skepticism until clear, operational results are proven."),
    ("lo2", "I worry that organizational policy shifts prioritize executive goals over the practical, daily workload of teams."),
    ("lo3", "I find it difficult to fully commit to leadership's long-term vision when immediate operational hurdles remain unresolved."),
    ("lo4", "When new processes or tools are introduced, my immediate instinct is to identify hidden risks and operational blind spots."),
    ("lo5", "I prefer maintaining established, reliable workflows over adopting new corporate initiatives with unproven track records."),
    ("lo6", "In cross-functional projects, I actively focus on catching potential oversights that others overlook in their optimism."),
    ("lo7", "I tend to double-check peer deliverables independently because I anticipate misalignments or hidden errors."),
    ("lo8", "I deliberately limit my emotional attachment to organizational outcomes to protect myself from burnout when plans shift."),
    ("lo9", "I believe that pointing out system flaws and potential failure points adds more real value than maintaining a positive outlook."),
    ("lo10", "I develop independent contingency plans because I expect organizational support systems to fail during high-pressure periods."),
]

HIGH_ORG_PSYCHOLOGY = [
    ("ho1", "People often look to me to take charge when a decision needs to be made."),
    ("ho2", "I can rally a group around a shared goal without much difficulty."),
    ("ho3", "I feel comfortable setting direction for others, even under pressure."),
    ("ho4", "I genuinely enjoy working with others to accomplish a shared outcome."),
    ("ho5", "I adjust my own approach to help a team succeed as a whole."),
    ("ho6", "I can explain complex ideas in ways that are easy for others to understand."),
    ("ho7", "I naturally notice tension in a group and look for ways to ease it."),
    ("ho8", "I can sense how someone is feeling even before they say anything."),
    ("ho9", "I notice small signs of potential or improvement in others before they notice it themselves."),
    ("ho10", "I get satisfaction from helping someone else grow or succeed."),
]

IND_WORK_PSYCHOLOGY = [
    ("iw1", "I maintain a strong personal push to complete my daily targets, even when I feel disconnected from team goals."),
    ("iw2", "When group discussions delay project progress, I focus on executing my individual tasks to stay productive."),
    ("iw3", "I rely on my own structured routines to deliver quality work when team processes feel chaotic."),
    ("iw4", "People can count on me to meet my specific commitments, even if I prefer not to engage in broader team activities."),
    ("iw5", "I adjust my operational workflow quickly when project conditions shift, even if the team struggles to navigate the change."),
    ("iw6", "I take full personal ownership of my specific deliverables, even when team roles and responsibilities are unclear."),
    ("iw7", "If a mistake occurs in my work, I hold myself accountable directly rather than blaming poor team communication."),
    ("iw8", "When a process fails, I focus on diagnosing the root cause in the workflow rather than getting caught up in team drama."),
    ("iw9", "I enjoy working independently to repair broken systems or processes that others have given up on."),
    ("iw10", "I prefer channeling my energy into fixing technical bottlenecks over managing interpersonal dynamics."),
]

LOW_COGNITIVE_PSYCHOLOGY = [
    ("lc1", "Even when I am struggling to execute a task, I can logically break the complex problem down into clear, smaller parts."),
    ("lc2", "When my daily routine feels unproductive, I rely on objective facts and data rather than emotion to evaluate what went wrong."),
    ("lc3", "I can see how operational bottlenecks in my role impact the broader system, even if I struggle to resolve them personally."),
    ("lc4", "When faced with recurring delivery delays, I recognize the underlying systemic patterns causing the bottleneck."),
    ("lc5", "When standard workflows fail to yield results, I can generate alternative, unconventional solutions."),
    ("lc6", "I maintain a clear mental picture of long-term possibilities, even when day-to-day operational progress is slow."),
    ("lc7", "I gather a wide range of relevant facts and background data before attempting to solve an operational breakdown."),
]

MID_COGNITIVE_PSYCHOLOGY = [
    ("mc1", "Even when moving at high execution speeds, I pause to logically break down complex problems into clear, separable parts."),
    ("mc2", "I systematically pressure-test underlying assumptions and hard data before scaling a solution."),
    ("mc3", "I naturally map out how my high-volume execution impacts adjacent teams, workflows, and long-term systems."),
    ("mc4", "I spot subtle, systemic patterns and emerging bottlenecks several moves before they actually disrupt delivery."),
    ("mc5", "Even when my standard operational routines are working effectively, I actively build and test novel, unconventional solutions."),
    ("mc6", "I ensure my intense daily output is directly tied to a clear, multi-year strategic vision rather than short-term targets."),
    ("mc7", "I systematically gather comprehensive background intel and cross-functional data before locking in a strategic approach."),
]

BEHAVIORAL_SET1 = [
    ("b1_1", "I perform best when project objectives and execution parameters are clearly defined before rollout."),
    ("b1_2", "I consistently follow established processes to ensure quality and prevent operational errors."),
    ("b1_3", "I take personal ownership of meeting my deadlines, even when adjacent team members face delays."),
    ("b1_4", "I adjust my daily work plan smoothly when operational priorities are updated."),
    ("b1_5", "I actively support team consensus even if the chosen direction wasn't my first preference."),
    ("b1_6", "Others can count on me to maintain consistent quality across high-volume routine tasks."),
    ("b1_7", "When an unexpected issue arises, I focus on immediate practical fixes rather than over-complicating the solution."),
    ("b1_8", "I proactively diffuse minor workplace tensions to keep project momentum moving forward."),
    ("b1_9", "I apply constructive feedback promptly to refine my daily execution and output."),
    ("b1_10", "I double-check my deliverables against organizational standards before passing them along the workflow chain."),
]

BEHAVIORAL_SET2 = [
    ("b2_1", "I regularly look past immediate operational bottlenecks to build strategies for multi-year opportunities."),
    ("b2_2", "I make high-stakes decisions confidently even when available data is incomplete or conflicting."),
    ("b2_3", "I actively seek out and rebuild outdated operational architectures, even when current systems appear functional."),
    ("b2_4", "I operate at maximum effectiveness when given complete autonomy over strategy and execution."),
    ("b2_5", "I quickly identify underlying macro trends and system risks across different functional departments."),
    ("b2_6", "I successfully rally senior stakeholders and teams around non-conventional, high-impact visions."),
    ("b2_7", "I am comfortable backing high-reward initiatives that carry significant operational uncertainty."),
    ("b2_8", "When major strategic initiatives stall, I pivot the entire approach without losing momentum toward the core objective."),
    ("b2_9", "I design frameworks that optimize performance across the entire organization, not just individual units."),
    ("b2_10", "I prefer solving complex, multi-layered problems that require completely new paradigms rather than incremental fixes."),
]

# ---------------------------------------------------------------------------
# Archetype engine (ported from the JS prototype)
# ---------------------------------------------------------------------------
ARCHETYPES = {
    "set2": {
        "track": "High-Performance Transformation Track",
        "archetype": "Enterprise Strategist & Systems Innovator",
        "summary": (
            "Demonstrates superior cognitive deconstruction and high-stakes behavioral execution. "
            "Capable of leading broad multi-year technical or business transformation initiatives, "
            "managing stakeholder ambiguity, and designing scalable system architectures."
        ),
        "risk": "Low risk of execution drag, but potential frustration if placed in highly rigid, low-autonomy operational environments.",
        "deploy": "Deploy as Enterprise CTO, Strategic Architecture Lead, or Fractional Transformation Director with full ownership over technical direction and strategic roadmap.",
        "autonomy": "High autonomy required. Avoid micro-management; provide clear end-state objectives.",
    },
    "set1": {
        "track": "Balanced Operational Execution Track",
        "archetype": "Pragmatic Delivery Lead & Systems Integrator",
        "summary": (
            "Displays highly reliable operational discipline, strong process fidelity, and structured execution. "
            "Thrives in bridging abstract strategy with tactical delivery while maintaining quality standards across delivery pipelines."
        ),
        "risk": "May require explicit strategic direction when navigating completely unscripted or highly ambiguous business pivots.",
        "deploy": "Deploy as Program Manager, Delivery Lead, or Senior Systems Specialist in structured environments with clear operational targets.",
        "autonomy": "Provide structured milestones and periodic operational syncs.",
    },
    "set1_baseline": {
        "track": "Defensive Realism & Risk Mitigation Track",
        "archetype": "Critical System Auditor & Risk Specialist",
        "summary": (
            "Exhibits a cautious, risk-averse operational orientation. Highly skilled at identifying blind spots, "
            "edge cases, and architectural flaws, though may slow down fast-paced execution cycles."
        ),
        "risk": "High probability of change resistance or friction with fast-moving cross-functional teams.",
        "deploy": "Assign to QA governance, risk auditing, compliance frameworks, or structured maintenance tasks where risk identification is critical.",
        "autonomy": "Provide structured milestones and periodic operational syncs.",
    },
}

SCALE_LABELS = {1: "Strongly Disagree", 5: "Strongly Agree"}

# ---------------------------------------------------------------------------
# Apple-inspired styling (dark)
# ---------------------------------------------------------------------------
def inject_apple_css():
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
        background-color: #000000;
        color: #f5f5f7;
    }
    .stApp { background: #000000; }
    [data-testid="stApp"] { background: #000000; }
    [data-testid="stAppViewContainer"] { background: #000000; }
    [data-testid="stMain"] { background: #000000; }
    [data-testid="stMainBlockContainer"] { background: #000000; padding-top: 0; }
    .block-container { padding-top: 0; padding-bottom: 2rem; }
    #MainMenu, [data-testid="stToolbar"], [data-testid="stAppToolbar"], [data-testid="stDecoration"],
    [data-testid="stStatusWidget"], footer, [data-testid="stHeader"], header[data-testid="stHeader"],
    [data-testid="stAppHeader"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"] {
        display: none; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stHeader"] [data-testid="stToolbar"] { display: none; }
    .module-title { font-size: 26px; font-weight: 700; color: #ffffff; letter-spacing: -0.4px; line-height: 1.2; }
    .module-sub { font-size: 13px; color: #8e8e93; margin: 4px 0 18px; line-height: 1.4; }
    [data-testid="stSidebar"] { background: #0d0d0d; border-right: 1px solid #1c1c1e; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown {
        color: #f5f5f7;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background: #1c1c1e; border-color: #2c2c2e; color: #f5f5f7;
    }
    .q-card { background: #1c1c1e; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #1c1c1e; border: 1px solid #2c2c2e !important; border-radius: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.45); padding: 16px 18px 14px; margin-bottom: 8px;
    }
    .q-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 12px; }
    .q-text { font-size: 15px; color: #f5f5f7; font-weight: 500; line-height: 1.45; flex: 1; }
    .q-num { display: inline-flex; width: 22px; height: 22px; border-radius: 50%;
        background: #2c2c2e; color: #0a84ff; font-size: 11px; font-weight: 700;
        align-items: center; justify-content: center; margin-right: 9px; vertical-align: middle; }
    .opt { height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center;
        font-size: 13px; font-weight: 600; color: #f5f5f7; width: 100%;
        border: 1px solid #3a3a3c; background: #2c2c2e; box-sizing: border-box; }
    .opt.selected { background: #0a84ff; color: #fff; border-color: #0a84ff;
        box-shadow: 0 2px 10px rgba(10,132,255,0.40); }
    .scale-labels { display: flex; justify-content: space-between; margin-top: 7px;
        font-size: 10px; color: #8e8e93; letter-spacing: .2px; }
    .scale-labels span { padding: 0 2px; }
    .mini-flywheel { flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
    .stButton > button { border-radius: 12px; border: 1px solid #3a3a3c; background: #2c2c2e;
        color: #f5f5f7; font-weight: 600; min-height: 40px; transition: all .18s ease; }
    .stButton > button:hover { background: #3a3a3c; }
    .stButton > button[kind="primary"] { background: #0a84ff; border-color: #0a84ff; color: #fff; }
    .stButton > button[kind="primary"]:hover { background: #0a6cdb; }
    .progress-card { background: #1c1c1e; border: 1px solid #2c2c2e; border-radius: 16px;
        padding: 18px 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.45); position: sticky; top: 70px; }
    .progress-title { font-size: 13px; font-weight: 700; color: #f5f5f7; margin-bottom: 12px;
        letter-spacing: .2px; }
    .progress-module { display: flex; align-items: center; gap: 10px; padding: 7px 0;
        font-size: 12.5px; color: #8e8e93; border-bottom: 1px solid #2c2c2e; }
    .progress-module.done { color: #30d158; }
    .progress-module.active { color: #f5f5f7; font-weight: 600; }
    .progress-dot { width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center;
        justify-content: center; font-size: 10px; font-weight: 700; flex-shrink: 0; }
    .progress-dot.done { background: #30d158; color: #000; }
    .progress-dot.active { background: #0a84ff; color: #fff; }
    .progress-dot.pending { background: #2c2c2e; color: #6e6e73; }
    .report-label { font-size: 11px; font-weight: 700; color: #8e8e93; text-transform: uppercase;
        letter-spacing: .9px; margin: 20px 0 10px; }
    .domain-card { background: #1c1c1e; border: 1px solid #2c2c2e; border-radius: 16px;
        padding: 16px 18px; margin-bottom: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.4); }
    .domain-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
    .domain-name { font-weight: 700; color: #f5f5f7; font-size: 13.5px; }
    .domain-score { color: #a1a1a6; font-weight: 500; }
    .domain-state { display: inline-block; background: #2c2c2e; font-size: 10px; font-weight: 700;
        border-radius: 999px; padding: 3px 10px; margin: 8px 0; letter-spacing: .4px; }
    .blurb { font-size: 12px; color: #8e8e93; line-height: 1.5; margin-top: 2px; }
    [data-testid="stTable"] { border-radius: 12px; overflow: hidden; border: 1px solid #2c2c2e; }
    [data-testid="stTable"] th { background: #2c2c2e; font-size: 11px; color: #a1a1a6; font-weight: 700; }
    [data-testid="stTable"] td { background: #1c1c1e; font-size: 12px; color: #f5f5f7; }
    [data-testid="stAlert"] { background: #1c1c1e; color: #f5f5f7; }
    [data-testid="stProgress"] > div > div > div > div { background: #0a84ff; }
    h1, h2, h3 { color: #f5f5f7; }
    p, li, label { color: #a1a1a6; }
    </style>""", unsafe_allow_html=True)


MODULES = [
    ("Positive Psychology", "pos", "Optimism, gratitude and engagement baseline"),
    ("Organizational Tier", "org", "Leadership synergy and change friction"),
    ("Individual / Work Tier", "ind", "Task dependability and self-directed execution"),
    ("Cognitive Tier", "cog", "Systems thinking and problem deconstruction"),
    ("Behavioral Module", "beh", "Real-world execution and decision confidence"),
]


def render_progress_panel(current: int):
    done_count = min(current - 1, 5)
    st.markdown("<div class='progress-card'>", unsafe_allow_html=True)
    st.markdown("<div class='progress-title'>Assessment Progress</div>", unsafe_allow_html=True)
    st.progress(done_count / 5)
    st.markdown(
        f"<div style='font-size:11px;color:#8e8e93;margin:6px 0 4px'>"
        f"Module {min(current, 5)} of 5 &middot; {done_count} completed</div>",
        unsafe_allow_html=True,
    )
    for i, (name, _key, _desc) in enumerate(MODULES, start=1):
        if i < current:
            cls, sym = "done", "&#10003;"
        elif i == current:
            cls, sym = "active", "&#9679;"
        else:
            cls, sym = "pending", "&#9675;"
        st.markdown(
            f"<div class='progress-module {cls}'>"
            f"<div class='progress-dot {cls}'>{sym}</div>{name}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def flywheel_svg(pct: int, label: str = "Overall Fit", light: bool = False) -> str:
    r, cx, cy, stroke = 82, 110, 110, 18
    circ = 2 * math.pi * r
    off = circ * (1 - pct / 100)
    color = "#30d158" if pct >= 75 else ("#ff9f0a" if pct >= 50 else "#ff453a")
    if light:
        track, text_c, sub_c = "#ececec", "#1d1d1f", "#6e6e73"
    else:
        track, text_c, sub_c = "#2c2c2e", "#ffffff", "#8e8e93"
    return f"""<svg viewBox="0 0 220 220" style="max-width:240px;width:100%">
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{track}" stroke-width="{stroke}"/>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}"
        stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}" stroke-linecap="round"
        transform="rotate(-90 {cx} {cy})"/>
      <text x="{cx}" y="{cy+3}" text-anchor="middle" font-size="36" font-weight="700" fill="{text_c}">{pct}%</text>
      <text x="{cx}" y="{cy+34}" text-anchor="middle" font-size="11" fill="{sub_c}">{label}</text>
    </svg>"""


def mini_flywheel_svg(value: int, maxv: int = 5) -> str:
    """Small radial dial showing the selected scale position for one question."""
    pct = round(value / maxv * 100) if value else 0
    r, cx, cy, stroke = 24, 32, 32, 5
    circ = 2 * math.pi * r
    off = circ * (1 - pct / 100)
    color = "#0a84ff" if value else "#3a3a3c"
    text = str(value) if value else "–"
    return f"""<svg viewBox="0 0 64 64" style="width:52px;height:52px">
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#2c2c2e" stroke-width="{stroke}"/>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke}"
        stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}" stroke-linecap="round"
        transform="rotate(-90 {cx} {cy})"/>
      <text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="16" font-weight="700" fill="#ffffff">{text}</text>
    </svg>"""

# ---------------------------------------------------------------------------
# Streamlit helpers
# ---------------------------------------------------------------------------
st.set_page_config(page_title="TalentPrism Assessment Engine", page_icon="🧠", layout="wide")

DEFAULT_STATE = {
    "step": 0,
    "candidate_name": "",
    "candidate_org": "",
    "pos": 0,
    "org": 0,
    "ind": 0,
    "cog": 0,
    "beh": 0,
    "state_pos": "low",
    "state_org": "mid",
    "state_ind": "mid",
    "state_cog": "mid",
    "active_set": "set1",
}


def reset_session():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# ---------------------------------------------------------------------------
# Results database (silent capture; admin-only view)
# Supports SQLite locally and hosted Postgres in production (DATABASE_URL),
# so stored results survive restarts and redeploys.
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).parent / "talentprism_results.db"
DATABASE_URL = os.environ.get("DATABASE_URL", "")
ADMIN_PASSWORD = os.environ.get("TALENTPRISM_ADMIN_KEY", "talentprism-admin")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    candidate_name TEXT NOT NULL DEFAULT '',
    candidate_org TEXT NOT NULL DEFAULT '',
    pos INTEGER NOT NULL DEFAULT 0,
    org INTEGER NOT NULL DEFAULT 0,
    ind INTEGER NOT NULL DEFAULT 0,
    cog INTEGER NOT NULL DEFAULT 0,
    beh INTEGER NOT NULL DEFAULT 0,
    state_pos TEXT NOT NULL DEFAULT '',
    state_org TEXT NOT NULL DEFAULT '',
    state_ind TEXT NOT NULL DEFAULT '',
    state_cog TEXT NOT NULL DEFAULT '',
    active_set TEXT NOT NULL DEFAULT '',
    overall INTEGER NOT NULL DEFAULT 0,
    top5_json TEXT NOT NULL DEFAULT '[]',
    pdf_blob BLOB
)
"""

_PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    created_at TEXT NOT NULL,
    candidate_name TEXT NOT NULL DEFAULT '',
    candidate_org TEXT NOT NULL DEFAULT '',
    pos INTEGER NOT NULL DEFAULT 0,
    org INTEGER NOT NULL DEFAULT 0,
    ind INTEGER NOT NULL DEFAULT 0,
    cog INTEGER NOT NULL DEFAULT 0,
    beh INTEGER NOT NULL DEFAULT 0,
    state_pos TEXT NOT NULL DEFAULT '',
    state_org TEXT NOT NULL DEFAULT '',
    state_ind TEXT NOT NULL DEFAULT '',
    state_cog TEXT NOT NULL DEFAULT '',
    active_set TEXT NOT NULL DEFAULT '',
    overall INTEGER NOT NULL DEFAULT 0,
    top5_json TEXT NOT NULL DEFAULT '[]',
    pdf_blob BYTEA
)
"""

_INSERT = """
INSERT INTO assessments (
    created_at, candidate_name, candidate_org,
    pos, org, ind, cog, beh,
    state_pos, state_org, state_ind, state_cog,
    active_set, overall, top5_json, pdf_blob
) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph},
          {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
"""

_PG_INSERT = """
INSERT INTO assessments (
    created_at, candidate_name, candidate_org,
    pos, org, ind, cog, beh,
    state_pos, state_org, state_ind, state_cog,
    active_set, overall, top5_json, pdf_blob
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def _using_pg() -> bool:
    return bool(DATABASE_URL)


def _get_conn():
    if _using_pg():
        import psycopg

        return psycopg.connect(DATABASE_URL)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _add_pdf_column():
    """Backfill the pdf_blob column on databases created before it existed."""
    conn = _get_conn()
    try:
        with conn:
            if _using_pg():
                with conn.cursor() as cur:
                    cur.execute(
                        "ALTER TABLE assessments ADD COLUMN IF NOT EXISTS pdf_blob BYTEA"
                    )
            else:
                cols = [r["name"] for r in conn.execute("PRAGMA table_info(assessments)").fetchall()]
                if "pdf_blob" not in cols:
                    conn.execute("ALTER TABLE assessments ADD COLUMN pdf_blob BLOB")
    except Exception:
        pass  # table may not exist yet; init_db creates it
    finally:
        conn.close()


def init_db():
    conn = _get_conn()
    try:
        with conn:
            conn.execute(_PG_SCHEMA if _using_pg() else _SCHEMA)
    finally:
        conn.close()
    _add_pdf_column()


def _fetch_rows(conn, sql):
    if _using_pg():
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    return [dict(r) for r in conn.execute(sql).fetchall()]


def save_assessment():
    """Persist the current session's result. Called once at report time."""
    if st.session_state.get("_result_saved"):
        return
    top5 = [t["name"] for t in build_theme_scores()[:5]]
    try:
        pdf_bytes = build_pdf()
    except Exception:
        pdf_bytes = None
    row = (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        st.session_state.get("candidate_name", ""),
        st.session_state.get("candidate_org", ""),
        st.session_state.get("pos", 0),
        st.session_state.get("org", 0),
        st.session_state.get("ind", 0),
        st.session_state.get("cog", 0),
        st.session_state.get("beh", 0),
        st.session_state.get("state_pos", ""),
        st.session_state.get("state_org", ""),
        st.session_state.get("state_ind", ""),
        st.session_state.get("state_cog", ""),
        st.session_state.get("active_set", ""),
        st.session_state.get("_overall", 0),
        json.dumps(top5),
        pdf_bytes,
    )
    conn = _get_conn()
    try:
        with conn:
            if _using_pg():
                with conn.cursor() as cur:
                    cur.execute(_PG_INSERT, row)
            else:
                conn.execute(_INSERT.format(ph="?"), row)
    finally:
        conn.close()
    st.session_state["_result_saved"] = True


def load_assessments():
    conn = _get_conn()
    try:
        rows = _fetch_rows(conn, "SELECT * FROM assessments ORDER BY id DESC")
    finally:
        conn.close()
    return rows


def render_admin():
    st.markdown(
        "<div style='text-align:center;border-bottom:1px solid #2c2c2e;padding-bottom:10px;margin-bottom:18px'>"
        "<h1 style='margin:0 0 6px 0;color:#ffffff'>TalentPrism Results</h1>"
        "<p style='margin:0;color:#8e8e93'>Stored assessment database</p></div>",
        unsafe_allow_html=True,
    )
    key = st.text_input("Admin key", type="password")
    if not key:
        st.info("Enter the admin key to view results.", icon="🔒")
        return
    if key != ADMIN_PASSWORD:
        st.error("Incorrect admin key.", icon="🔒")
        return
    rows = load_assessments()
    st.success(f"{len(rows)} assessment(s) stored in the database.", icon="✅")
    if not rows:
        st.info("No assessments captured yet.")
        return
    display = []
    for r in rows:
        top5 = ", ".join(json.loads(r["top5_json"] or "[]"))
        display.append({
            "ID": r["id"],
            "Date": r["created_at"],
            "Name": r["candidate_name"],
            "Organisation": r["candidate_org"],
            "Overall": f"{r['overall']}%",
            "Track": r["active_set"],
            "Pos": r["pos"],
            "Org": r["org"],
            "Ind": r["ind"],
            "Cog": r["cog"],
            "Beh": r["beh"],
            "Top 5": top5,
            "PDF": "Yes" if r.get("pdf_blob") else "No",
        })
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("#### 📄 Download PDF reports")
    for r in rows:
        blob = r.get("pdf_blob")
        if not blob:
            continue
        name = r["candidate_name"] or f"candidate_{r['id']}"
        safe = "".join(c for c in name if c.isalnum() or c in " _-").strip() or f"candidate_{r['id']}"
        fname = f"TalentPrism_{safe}_{r['id']}.pdf"
        c1, c2 = st.columns([0.25, 3.75])
        c1.download_button(
            f"PDF #{r['id']}",
            data=bytes(blob),
            file_name=fname,
            mime="application/pdf",
            use_container_width=True,
            key=f"pdf_{r['id']}",
        )
        c2.caption(f"{fname} — {r['created_at']}")

    csv = "id,created_at,candidate_name,candidate_org,overall,active_set,pos,org,ind,cog,beh,state_pos,state_org,state_ind,state_cog,top5\n"
    for r in rows:
        top5 = "; ".join(json.loads(r["top5_json"] or "[]"))
        csv += ",".join(
            str(r[k]) for k in
            ["id", "created_at", "candidate_name", "candidate_org", "overall",
             "active_set", "pos", "org", "ind", "cog", "beh",
             "state_pos", "state_org", "state_ind", "state_cog"]
        ) + f",\"{top5}\"\n"
    st.download_button(
        "⬇️ Download CSV",
        data=csv,
        file_name="talentprism_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.button("⬅️ Back to Assessment", use_container_width=True, on_click=reset_session)


def render_questions(questions, form_key):
    """Render questions as cards with a tick-mark scale and per-question flywheel."""
    values = {}
    for idx, (qid, text) in enumerate(questions, start=1):
        current = st.session_state.get(f"{form_key}_{qid}")
        with st.container(border=True):
            st.markdown(
                f"<div class='q-head'>"
                f"<div class='q-text'><span class='q-num'>{idx}</span>{text}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            cols = st.columns(5, gap="small")
            for v in range(1, 6):
                with cols[v - 1]:
                    if current == v:
                        st.markdown("<div class='opt selected'>&#10003;</div>", unsafe_allow_html=True)
                    else:
                        if st.button(str(v), key=f"{form_key}_{qid}_v{v}", use_container_width=True):
                            st.session_state[f"{form_key}_{qid}"] = v
                            st.rerun()
            st.markdown(
                f"<div class='scale-labels'>"
                f"<span>Strongly Disagree</span><span>Disagree</span><span>Neutral</span>"
                f"<span>Agree</span><span>Strongly Agree</span></div>",
                unsafe_allow_html=True,
            )
        values[qid] = current
    submitted = st.button("Continue", type="primary", use_container_width=True)
    return submitted, values


def form_error() -> bool:
    st.error("Please answer all questions before proceeding.", icon="⚠️")
    return True


def module_title(title: str, subtitle: str = ""):
    st.markdown(
        f"<div class='module-title'>{title}</div>"
        f"<div class='module-sub'>{subtitle}</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Step screens
# ---------------------------------------------------------------------------
def step0():
    module_title(
        "Assessment Intake",
        "Tell us who this report is for. Your details appear on the final report.",
    )
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:14px;font-weight:600;color:#f5f5f7;margin-bottom:14px'>Candidate details</div>",
            unsafe_allow_html=True,
        )
        name = st.text_input(
            "Full name",
            value=st.session_state.get("intake_name", ""),
            key="intake_name",
            placeholder="e.g. Aarav Sharma",
        )
        org = st.text_input(
            "Organisation",
            value=st.session_state.get("intake_org", ""),
            key="intake_org",
            placeholder="e.g. Acme Corporation",
        )
        if st.button("Start Assessment", type="primary", use_container_width=True):
            if not name.strip():
                st.warning("Please enter the candidate's name.", icon="⚠️")
                return
            st.session_state.candidate_name = name.strip()
            st.session_state.candidate_org = org.strip()
            st.session_state.step = 1
            st.rerun()


def step1():
    module_title(
        "Positive Psychology",
        "Optimism, gratitude, curiosity and engagement baseline",
    )
    submitted, values = render_questions(POSITIVE_PSYCHOLOGY, "form_step_1")
    if not submitted:
        return
    if any(v is None for v in values.values()):
        form_error()
        return
    score = sum(values.values())
    st.session_state.pos = score
    st.session_state.state_pos = "low" if score <= 60 else "high"
    st.session_state.step = 2
    st.rerun()


def step2():
    is_low = st.session_state.state_pos == "low"
    questions = LOW_ORG_PSYCHOLOGY if is_low else HIGH_ORG_PSYCHOLOGY
    module_title(
        "Organizational Psychology",
        "Leadership synergy, change adaptation and corporate alignment",
    )
    submitted, values = render_questions(questions, "form_step_2")
    if not submitted:
        return
    if any(v is None for v in values.values()):
        form_error()
        return
    score = sum(values.values())
    st.session_state.org = score
    pct = score / (len(questions) * 5)
    st.session_state.state_org = "low" if pct < 0.5 else ("high" if pct >= 0.75 else "mid")
    st.session_state.step = 3
    st.rerun()


def step3():
    module_title(
        "Individual & Work Psychology",
        "Task dependability, workflow structure and self-directed execution",
    )
    submitted, values = render_questions(IND_WORK_PSYCHOLOGY, "form_step_3")
    if not submitted:
        return
    if any(v is None for v in values.values()):
        form_error()
        return
    score = sum(values.values())
    st.session_state.ind = score
    st.session_state.state_ind = "low" if score <= 30 else ("high" if score >= 40 else "mid")
    st.session_state.step = 4
    st.rerun()


def step4():
    is_low = st.session_state.state_ind == "low"
    questions = LOW_COGNITIVE_PSYCHOLOGY if is_low else MID_COGNITIVE_PSYCHOLOGY
    module_title(
        "Cognitive Psychology",
        "Systems thinking and long-range problem solving",
    )
    submitted, values = render_questions(questions, "form_step_4")
    if not submitted:
        return
    if any(v is None for v in values.values()):
        form_error()
        return
    score = sum(values.values())
    st.session_state.cog = score
    pct = score / (len(questions) * 5)
    st.session_state.state_cog = "high" if pct >= 0.75 else ("mid" if pct >= 0.45 else "low")
    st.session_state.step = 5
    st.rerun()


def step5():
    cog = st.session_state.state_cog
    if cog == "high":
        questions = BEHAVIORAL_SET2
        active_set = "set2"
    elif cog == "mid":
        questions = BEHAVIORAL_SET1
        active_set = "set1"
    else:
        questions = BEHAVIORAL_SET1
        active_set = "set1_baseline"
    st.session_state.active_set = active_set

    module_title(
        "Behavioral Psychology",
        "Real-world execution and decision confidence",
    )
    submitted, values = render_questions(questions, "form_step_5")
    if not submitted:
        return
    if any(v is None for v in values.values()):
        form_error()
        return
    st.session_state.beh = sum(values.values())
    st.session_state.step = 6
    st.rerun()


# ---------------------------------------------------------------------------
# TalentPrism-25 theme bank (report mapping)
# ---------------------------------------------------------------------------
THEMES = {
    "pos": [
        "Horizon", "Valuer", "Seeker", "Spark",
    ],
    "org": [
        "Helm", "Weaver", "Voice", "Bridge", "Resonator", "Cultivator",
    ],
    "ind": [
        "Driver", "Anchor", "Flex", "Steward", "Fixer",
    ],
    "cog": [
        "Prism", "Mapper", "Forge", "Visionary", "Archivist",
    ],
    "beh": [
        "Steady", "Igniter", "Grit", "Catalyst", "Contender",
    ],
}

THEME_BLURBS = {
    "Horizon": "You expect good outcomes ahead, even when circumstances are uncertain.",
    "Valuer": "You notice and openly honor what's good around you.",
    "Seeker": "You chase new knowledge for its own sake.",
    "Spark": "You bring visible energy and enthusiasm into any room.",
    "Helm": "You naturally take charge and set direction for others.",
    "Weaver": "You bind a group into one functioning team.",
    "Voice": "You make complex ideas land clearly with any audience.",
    "Bridge": "You sense tension early and close the gap between people.",
    "Resonator": "You feel what others feel before they say it.",
    "Cultivator": "You spot and grow potential in the people around you.",
    "Driver": "You feel an internal push to accomplish something meaningful every day.",
    "Anchor": "You are the person others can count on to deliver, on time, every time.",
    "Flex": "You bend without breaking when plans or conditions shift.",
    "Steward": "You treat outcomes as personally yours to protect.",
    "Fixer": "You're drawn to diagnosing and repairing what's broken.",
    "Prism": "You break complex problems into clear, logical parts.",
    "Mapper": "You see how the moving pieces of a system connect.",
    "Forge": "You build original solutions rather than reach for the obvious one.",
    "Visionary": "You picture what doesn't exist yet, years before others can see it.",
    "Archivist": "You collect and connect information others overlook.",
    "Steady": "You stay composed and think clearly when pressure rises.",
    "Igniter": "You move on a problem before anyone asks you to.",
    "Grit": "You keep pushing toward a goal long after motivation fades.",
    "Catalyst": "You turn talk into action, fast.",
    "Contender": "You measure yourself against others and want to come out ahead.",
}

DOMAIN_ORDER = [
    ("pos", "Positive Psychology"),
    ("org", "Organizational Psychology"),
    ("ind", "Industrial / Work Psychology"),
    ("cog", "Cognitive Psychology"),
    ("beh", "Behavioral Psychology"),
]


def classify_theme(score: float) -> str:
    if score >= 13:
        return "Dominant Strength"
    if score >= 9:
        return "Supporting Strength"
    return "Growth Area"


def build_theme_scores():
    """Map existing domain scores onto the 25 TalentPrism-25 themes (3-15 scale)."""
    domains = {
        "pos": (st.session_state.pos, 75),
        "org": (st.session_state.org, 50),
        "ind": (st.session_state.ind, 50),
        "cog": (st.session_state.cog, 35),
        "beh": (st.session_state.beh, 50),
    }
    rows = []
    for dkey, _dname in DOMAIN_ORDER:
        raw, dmax = domains[dkey]
        base = (raw / dmax) * 12 + 3  # map to 3-15 scale
        names = THEMES[dkey]
        n = len(names)
        for i, name in enumerate(names):
            spread = (i - (n - 1) / 2) * 0.8  # deterministic within-domain variation
            score = min(15.0, max(3.0, base + spread))
            rows.append(
                {
                    "name": name,
                    "domain": dkey,
                    "domain_label": dict(DOMAIN_ORDER)[dkey],
                    "score": round(score, 1),
                    "cls": classify_theme(score),
                    "blurb": THEME_BLURBS[name],
                }
            )
    rows.sort(key=lambda r: -r["score"])
    return rows


def shade_hex(hex_color: str, factor: float) -> str:
    """Blend a hex color toward white by factor 0..1 (lighter = higher score)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r = min(255, round(r + (255 - r) * (1 - factor)))
    g = min(255, round(g + (255 - g) * (1 - factor)))
    b = min(255, round(b + (255 - b) * (1 - factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def strengths_wheel_svg(theme_rows, overall: int) -> str:
    """TalentPrism-25 Strengths Wheel - 25 wedges grouped by domain, shaded by score."""
    cx, cy, R, r = 200, 200, 184, 116
    domain_colors = {
        "pos": "#34c759",
        "org": "#0a84ff",
        "ind": "#ff9f0a",
        "cog": "#bf5af2",
        "beh": "#ff453a",
    }
    n = len(theme_rows)
    step = 360 / n
    # Build wedges in wheel order (domain grouped)
    wheel = []
    for dkey, _dname in DOMAIN_ORDER:
        for t in theme_rows:
            if t["domain"] == dkey:
                wheel.append(t)
    wedges = ""
    for i, t in enumerate(wheel):
        a0 = math.radians(-90 + i * step)
        a1 = math.radians(-90 + (i + 1) * step)
        x1, y1 = cx + R * math.cos(a0), cy + R * math.sin(a0)
        x2, y2 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        x3, y3 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        x4, y4 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        base = domain_colors[t["domain"]]
        shade = 0.30 + 0.70 * (max(t["score"], 3) - 3) / 12  # 0.30 .. 1.00
        color = shade_hex(base, shade)
        wedges += (
            f'<path d="M {x1:.1f} {y1:.1f} A {R} {R} 0 0 1 {x2:.1f} {y2:.1f} '
            f'L {x3:.1f} {y3:.1f} A {r} {r} 0 0 0 {x4:.1f} {y4:.1f} Z" '
            f'fill="{color}" stroke="#ffffff" stroke-width="1.2"/>'
        )
    # Domain labels - horizontal white pills centered in each domain arc
    labels = ""
    i = 0
    for dkey, dname in DOMAIN_ORDER:
        count = len(THEMES[dkey])
        mid_deg = -90 + (i + count / 2) * step
        mid = math.radians(mid_deg)
        lr = (R + r) / 2
        lx, ly = cx + lr * math.cos(mid), cy + lr * math.sin(mid)
        short = dname.split(" ")[0]
        pw = max(len(short) * 6.4 + 16, 40)
        ph = 22
        lx = max(pw / 2 + 4, min(400 - pw / 2 - 4, lx))
        ly = max(ph / 2 + 4, min(400 - ph / 2 - 4, ly))
        labels += (
            f'<rect x="{lx - pw / 2:.1f}" y="{ly - ph / 2:.1f}" width="{pw:.1f}" height="{ph}" '
            f'rx="{ph / 2:.0f}" fill="#ffffff" fill-opacity="0.94" stroke="#d9d9de" stroke-width="1"/>'
            f'<text x="{lx:.1f}" y="{ly + 4:.1f}" text-anchor="middle" font-size="11.5" '
            f'font-weight="700" fill="#1d1d1f">{short}</text>'
        )
        i += count
    return f"""<svg viewBox="0 0 400 400" style="max-width:380px;width:100%">
      <circle cx="{cx}" cy="{cy}" r="98" fill="#ffffff" stroke="#e5e5ea" stroke-width="1"/>
      {wedges}
      <text x="{cx}" y="{cy+7}" text-anchor="middle" font-size="30" font-weight="800" fill="#1d1d1f">{overall}%</text>
      <text x="{cx}" y="{cy+31}" text-anchor="middle" font-size="11" font-weight="600" fill="#6e6e73">Overall</text>
      {labels}
    </svg>"""


def html_table(rows, style_class="rp-table"):
    head = "".join(f"<th>{c}</th>" for c in rows[0])
    body = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
        for row in rows[1:]
    )
    return f"<table class='{style_class}'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def step6():
    # Entire report is built as one HTML block so the white canvas wraps everything.
    st.markdown("""<style>
    .report-body { background: #ffffff; border-radius: 20px; padding: 26px 30px;
        border: 1px solid #e5e5ea; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }
    .report-label { font-size: 11px; font-weight: 700; color: #6e6e73; text-transform: uppercase;
        letter-spacing: .9px; margin: 22px 0 10px; }
    .domain-card { background: #ffffff; border: 1px solid #e5e5ea; border-radius: 16px;
        padding: 14px 18px; margin-bottom: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
    .domain-name { font-weight: 700; color: #1d1d1f; font-size: 15px; }
    .domain-state { display: inline-block; background: #f2f2f7; font-size: 10px; font-weight: 700;
        border-radius: 999px; padding: 2px 10px; letter-spacing: .4px; }
    .blurb { font-size: 12px; color: #6e6e73; line-height: 1.5; margin-top: 2px; }
    .report-grid { display: flex; gap: 26px; align-items: flex-start; }
    .report-grid .col-w { flex: 1.15; min-width: 0; }
    .report-grid .col-l { flex: 1; min-width: 0; }
    .legend-item { display: flex; align-items: center; gap: 10px; background: #f7f7f9;
        border: 1px solid #e5e5ea; border-radius: 10px; padding: 8px 10px; }
    .legend-swatch { width: 16px; height: 16px; border-radius: 4px; flex-shrink: 0; }
    .legend-text { font-size: 12px; color: #1d1d1f; font-weight: 600; }
    .rp-table { width: 100%; border-collapse: collapse; border: 1px solid #e5e5ea;
        border-radius: 12px; overflow: hidden; font-size: 12px; }
    .rp-table th { background: #f5f5f7; color: #6e6e73; font-weight: 700; font-size: 11px;
        padding: 8px 12px; text-align: left; }
    .rp-table td { background: #ffffff; color: #1d1d1f; padding: 8px 12px; border-top: 1px solid #efeff3; }
    .rp-actions { display: flex; gap: 12px; margin-top: 18px; }
    .rp-actions > * { flex: 1; }
    [data-testid="stDownloadButton"] button,
    .stButton > button {
        border-radius: 12px !important; font-weight: 600 !important;
        min-height: 44px !important; width: 100% !important;
        border: 1px solid #d1d1d6 !important;
    }
    [data-testid="stDownloadButton"] button {
        background: #0a84ff !important; color: #ffffff !important;
        border-color: #0a84ff !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background: #0a6cdb !important; color: #ffffff !important;
    }
    .stButton > button[kind="secondary"], .stButton > button:not([kind]) {
        background: #ffffff !important; color: #1d1d1f !important;
        border-color: #d1d1d6 !important;
    }
    .stButton > button[kind="secondary"]:hover, .stButton > button:not([kind]):hover {
        background: #f2f2f7 !important; color: #1d1d1f !important;
    }
    h1, h2, h3, p, li, label { color: #1d1d1f; }
    </style>""", unsafe_allow_html=True)

    pos, org, ind, cog, beh = (
        st.session_state.pos,
        st.session_state.org,
        st.session_state.ind,
        st.session_state.cog,
        st.session_state.beh,
    )
    total_possible = 75 + 50 + 50 + 35 + 50
    overall = round((pos + org + ind + cog + beh) / total_possible * 100)
    st.session_state["_overall"] = overall
    themes = build_theme_scores()
    top5 = themes[:5]

    save_assessment()

    guide_rows = [
        ("Score Range", "Classification", "What It Means"),
        ("13–15", "Dominant Strength", "A core, highly consistent strength — likely one of your natural go-to talents."),
        ("9–12", "Supporting Strength", "A capable, situational strength you can draw on reliably."),
        ("3–8", "Growth Area", "Not a natural default — an area to build deliberately or delegate."),
    ]

    legend = "".join(
        f"<div class='legend-item'><div class='legend-swatch' style='background:{color}'></div>"
        f"<span class='legend-text'>{name}</span></div>"
        for color, name in [
            ("#34c759", "Positive Psychology"),
            ("#0a84ff", "Organizational Psychology"),
            ("#ff9f0a", "Industrial / Work Psychology"),
            ("#bf5af2", "Cognitive Psychology"),
            ("#ff453a", "Behavioral Psychology"),
        ]
    )

    top5_cards = ""
    for i, t in enumerate(top5):
        color = "#30d158" if t["cls"] == "Dominant Strength" else ("#0a84ff" if t["cls"] == "Supporting Strength" else "#48484a")
        top5_cards += (
            f"<div class='domain-card'><div style='display:flex;align-items:flex-start;gap:12px'>"
            f"<div style='width:34px;height:34px;border-radius:50%;background:#0a84ff22;color:#0a84ff;"
            f"display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:800;flex-shrink:0'>#{i+1}</div>"
            f"<div style='flex:1'>"
            f"<div style='display:flex;align-items:center;gap:8px'>"
            f"<span class='domain-name'>{t['name']}</span>"
            f"<span class='domain-state' style='color:{color};border:1px solid {color}44'>{t['score']}</span>"
            f"</div>"
            f"<div class='blurb'>{t['blurb']}</div>"
            f"</div></div></div>"
        )

    sheet_rows = [("#", "Theme", "Domain", "Score", "Classification")]
    for idx, t in enumerate(themes, start=1):
        sheet_rows.append((str(idx), t["name"], t["domain_label"], f"{t['score']}", t["cls"]))

    cand_name = st.session_state.get("candidate_name", "").strip()
    cand_org = st.session_state.get("candidate_org", "").strip()
    name_html = cand_name if cand_name else "Candidate"
    org_html = cand_org if cand_org else "Organisation not provided"

    report = f"""
    <div class='report-body'>
      <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:14px;border-bottom:1px solid #e5e5ea;padding-bottom:14px;margin-bottom:4px'>
        <div>
          <div class='report-tag' style='display:inline-block;background:#0a84ff12;color:#0a84ff;padding:3px 12px;border-radius:999px;font-size:10.5px;font-weight:700;letter-spacing:.8px'>TALENTPRISM-25 &middot; STRENGTHS REPORT</div>
          <div style='font-size:22px;font-weight:800;color:#1d1d1f;letter-spacing:-.3px;margin-top:8px'>{name_html}</div>
          <div style='font-size:12px;color:#6e6e73;margin-top:2px'>{org_html}</div>
        </div>
        <div style='text-align:right;font-size:12px;color:#6e6e73;flex-shrink:0'>
          <div style='font-size:11px;text-transform:uppercase;letter-spacing:.8px;font-weight:700;color:#6e6e73'>Overall Score</div>
          <div style='font-size:30px;font-weight:800;color:#0a84ff;line-height:1'>{overall}%</div>
        </div>
      </div>
      <div class='report-label'>Scoring &amp; Interpretation Guide</div>
      {html_table(guide_rows)}
      <div class='report-label'>Your Strengths Wheel</div>
      <div class='report-grid'>
        <div class='col-w'>{strengths_wheel_svg(themes, overall)}</div>
        <div class='col-l'>
          <div class='blurb' style='margin-bottom:10px'>All 25 themes, arranged by domain. Lighter shade = higher score.</div>
          {legend}
          <div style='margin-top:14px;padding:12px;background:#f7f7f9;border-radius:12px;border:1px solid #e5e5ea'>
            <div style='font-size:11px;color:#3a3a3c;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px'>Finding your top strengths</div>
            <div style='font-size:12px;color:#3a3a3c;line-height:1.6'>
            Your five highest-scoring themes are your <b style='color:#1d1d1f'>Signature Strengths</b> —
            the talents most likely to show up across situations.</div>
          </div>
        </div>
      </div>
      <div class='report-label'>Top 5 Signature Strengths</div>
      {top5_cards}
      <div class='report-label'>Per-Theme Score Sheet</div>
      {html_table(sheet_rows)}
    </div>
    """
    st.markdown(report, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.download_button(
        "📥 Download PDF Report",
        data=build_pdf(),
        file_name=f"TalentPrism_25_Profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    c2.button("🔄 Start New Session", use_container_width=True, on_click=reset_session)


# ---------------------------------------------------------------------------
# PDF generation (reportlab)
# ---------------------------------------------------------------------------
def pct(value: int, denom: int) -> int:
    return round(value / denom * 100)


def wheel_drawing(theme_rows, overall: int, size: int = 170) -> Drawing:
    """Donut wheel mirroring the on-screen Strengths Wheel SVG."""
    cx, cy = size / 2, size / 2
    R = size * 0.46
    r = R * 0.63
    domain_colors = {
        "pos": "#34c759",
        "org": "#0a84ff",
        "ind": "#ff9f0a",
        "cog": "#bf5af2",
        "beh": "#ff453a",
    }
    wheel = []
    for dkey, _dname in DOMAIN_ORDER:
        for t in theme_rows:
            if t["domain"] == dkey:
                wheel.append(t)
    n = len(wheel)
    step = 360 / n
    d = Drawing(size, size)

    # Annular wedges drawn as polygons (small wedges read fine as chords)
    for i, t in enumerate(wheel):
        a0 = math.radians(-90 + i * step)
        a1 = math.radians(-90 + (i + 1) * step)
        x1, y1 = cx + R * math.cos(a0), cy + R * math.sin(a0)
        x2, y2 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        x3, y3 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        x4, y4 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        fill = shade_hex(domain_colors[t["domain"]], 0.30 + 0.70 * (max(t["score"], 3) - 3) / 12)
        # Approximate arc with a chord (small wedges look fine as polygons)
        d.add(shapes.Polygon(
            points=[
                x1, y1, x2, y2, x3, y3, x4, y4,
            ],
            fillColor=colors.HexColor(fill),
            strokeColor=colors.white,
            strokeWidth=0.7,
        ))
    # Center white disc + overall %
    d.add(shapes.Circle(cx, cy, r * 0.72, fillColor=colors.white, strokeColor=colors.HexColor("#e5e5ea")))
    d.add(String(cx, cy + size * 0.045, f"{overall}%",
                 fontName="Helvetica-Bold", fontSize=size * 0.13, textAnchor="middle", fillColor=colors.HexColor("#1d1d1f")))
    d.add(String(cx, cy - size * 0.055, "Overall",
                 fontName="Helvetica", fontSize=size * 0.055, textAnchor="middle", fillColor=colors.HexColor("#6e6e73")))
    return d


def build_pdf() -> bytes:
    pos, org, ind, cog, beh = (
        st.session_state.pos,
        st.session_state.org,
        st.session_state.ind,
        st.session_state.cog,
        st.session_state.beh,
    )
    total_possible = 75 + 50 + 50 + 35 + 50
    overall = round((pos + org + ind + cog + beh) / total_possible * 100)
    themes = build_theme_scores()
    top5 = themes[:5]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="TalentPrism-25 Strengths Assessment Report",
    )

    base = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "t", parent=base["Title"], fontSize=17, textColor=colors.HexColor("#1d1d1f"), spaceAfter=2
    )
    tag_style = ParagraphStyle(
        "tag", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#0a84ff"),
        fontName="Helvetica-Bold", spaceAfter=6,
    )
    sub_style = ParagraphStyle(
        "sub", parent=base["Normal"], fontSize=9, textColor=colors.HexColor("#6e6e73"), spaceAfter=8
    )
    h3 = ParagraphStyle(
        "h3", parent=base["Heading3"], fontSize=12, textColor=colors.HexColor("#1d1d1f"),
        spaceBefore=14, spaceAfter=6,
    )
    cell = ParagraphStyle("cell", parent=base["Normal"], fontSize=8.6, leading=11.5, alignment=TA_LEFT)
    cell_b = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
    th = ParagraphStyle("th", parent=cell, fontName="Helvetica-Bold", textColor=colors.HexColor("#1d1d1f"))

    story = []

    cand_name = st.session_state.get("candidate_name", "").strip() or "Candidate"
    cand_org = st.session_state.get("candidate_org", "").strip() or "Organisation not provided"
    name_style = ParagraphStyle(
        "nm", parent=base["Normal"], fontSize=13, leading=16,
        fontName="Helvetica-Bold", textColor=colors.HexColor("#1d1d1f"), spaceBefore=2,
    )
    org_style = ParagraphStyle(
        "og", parent=base["Normal"], fontSize=9.5, leading=12,
        textColor=colors.HexColor("#6e6e73"), spaceAfter=8,
    )

    # Header
    story.append(Paragraph("TalentPrism-25", title_style))
    story.append(Paragraph("STRENGTHS ASSESSMENT REPORT", tag_style))
    story.append(Paragraph(cand_name, name_style))
    story.append(Paragraph(cand_org, org_style))
    story.append(Paragraph(
        f"Your Signature Strengths: {', '.join(t['name'] for t in top5)}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0a84ff")))
    story.append(Spacer(1, 8))

    # Overall score line
    hero_cell = ParagraphStyle("herocell", parent=base["Normal"], fontSize=11, leading=15,
                               textColor=colors.HexColor("#1d1d1f"))
    hero_tbl = Table(
        [[Paragraph(f"Overall TalentPrism Score: <b>{overall}%</b>  &nbsp;·&nbsp;  "
                    f"Adaptive Track: <b>{st.session_state.active_set.upper()}</b>", hero_cell)]],
        colWidths=[doc.width],
    )
    hero_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f2f7")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(hero_tbl)
    story.append(Spacer(1, 6))

    # Scoring & Interpretation Guide
    story.append(Paragraph("Scoring &amp; Interpretation Guide", h3))
    guide_rows = [
        [Paragraph("Score Range", th), Paragraph("Classification", th), Paragraph("What It Means", th)],
        [Paragraph("13–15", cell), Paragraph("Dominant Strength", cell), Paragraph("A core, highly consistent strength — likely one of your natural go-to talents.", cell)],
        [Paragraph("9–12", cell), Paragraph("Supporting Strength", cell), Paragraph("A capable, situational strength you can draw on reliably.", cell)],
        [Paragraph("3–8", cell), Paragraph("Growth Area", cell), Paragraph("Not a natural default — an area to build deliberately or delegate.", cell)],
    ]
    t_guide = Table(guide_rows, colWidths=[1.0 * inch, 1.6 * inch, 4.2 * inch])
    t_guide.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e5ea")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d1d6")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_guide)
    story.append(Spacer(1, 6))

    # Strengths Wheel + domain legend
    story.append(Paragraph("Your Strengths Wheel", h3))
    domain_colors = {
        "pos": "#34c759", "org": "#0a84ff", "ind": "#ff9f0a",
        "cog": "#bf5af2", "beh": "#ff453a",
    }
    legend_rows = [[wheel_drawing(themes, overall, size=150),
                    Paragraph("All 25 themes, arranged by domain. "
                              "Lighter shade = higher score.<br/><br/>"
                              "<font color='#34c759'><b>■</b></font> Positive Psychology<br/>"
                              "<font color='#0a84ff'><b>■</b></font> Organizational Psychology<br/>"
                              "<font color='#ff9f0a'><b>■</b></font> Industrial / Work Psychology<br/>"
                              "<font color='#bf5af2'><b>■</b></font> Cognitive Psychology<br/>"
                              "<font color='#ff453a'><b>■</b></font> Behavioral Psychology", cell)]]
    t_wheel = Table(legend_rows, colWidths=[2.4 * inch, 4.4 * inch])
    t_wheel.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t_wheel)
    story.append(Spacer(1, 6))

    # Top 5 Signature Strengths
    story.append(Paragraph("Top 5 Signature Strengths", h3))
    top5_rows = [
        [Paragraph("#", th), Paragraph("Theme", th), Paragraph("Score", th),
         Paragraph("Classification", th), Paragraph("Why it stands out", th)],
    ]
    for i, t in enumerate(top5):
        top5_rows.append([
            Paragraph(str(i + 1), cell_b),
            Paragraph(t["name"], cell_b),
            Paragraph(str(t["score"]), cell),
            Paragraph(t["cls"], cell),
            Paragraph(t["blurb"], cell),
        ])
    t_top5 = Table(top5_rows, colWidths=[0.4 * inch, 1.2 * inch, 0.6 * inch, 1.4 * inch, 3.2 * inch])
    t_top5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e5ea")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d1d6")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_top5)
    story.append(Spacer(1, 6))

    # Per-Theme Score Sheet
    story.append(Paragraph("Per-Theme Score Sheet", h3))
    sheet_rows = [
        [Paragraph("#", th), Paragraph("Theme", th), Paragraph("Domain", th),
         Paragraph("Score", th), Paragraph("Classification", th)],
    ]
    for idx, t in enumerate(themes, start=1):
        sheet_rows.append([
            Paragraph(str(idx), cell),
            Paragraph(t["name"], cell_b),
            Paragraph(t["domain_label"], cell),
            Paragraph(str(t["score"]), cell),
            Paragraph(t["cls"], cell),
        ])
    t_sheet = Table(sheet_rows, colWidths=[0.4 * inch, 1.7 * inch, 1.9 * inch, 0.7 * inch, 1.4 * inch])
    t_sheet.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e5ea")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d1d6")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_sheet)
    story.append(Spacer(1, 6))

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    for key, value in DEFAULT_STATE.items():
        st.session_state.setdefault(key, value)

    inject_apple_css()
    init_db()

    if st.query_params.get("view") == "results":
        render_admin()
        return

    st.markdown(
        "<div style='text-align:center;border-bottom:1px solid #2c2c2e;padding-bottom:10px;margin-bottom:18px'>"
        "<h1 style='margin:0 0 6px 0;color:#ffffff'>TalentPrism Assessment</h1>"
        "<p style='margin:0;color:#8e8e93'>Enterprise Adaptive Diagnostic Platform</p></div>",
        unsafe_allow_html=True,
    )

    step = st.session_state.step
    if step == 0:
        step0()
        return
    qcol, pcol = st.columns([3.3, 1.05], gap="large")
    with qcol:
        if step == 1:
            step1()
        elif step == 2:
            step2()
        elif step == 3:
            step3()
        elif step == 4:
            step4()
        elif step == 5:
            step5()
        elif step == 6:
            step6()
    with pcol:
        render_progress_panel(step)


main()
