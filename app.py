import io
import os
import plotly.graph_objects as go
import reportlab.lib.colors as colors
import resend
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ==========================================
# 1. DATA STRUCTURE & FRAMEWORK DEFINITIONS
# ==========================================

TALENTPRISM_DATA = {
    "Positive Psychology": {
        "color": "#9A7D0A",
        "themes": {
            "Horizon": "You expect good outcomes ahead, even when circumstances are uncertain.",
            "Valuer": "You notice and openly honor what's good around you.",
            "Seeker": "You chase new knowledge for its own sake.",
            "Spark": "You bring visible energy and enthusiasm into any room.",
        },
    },
    "Organizational Psychology": {
        "color": "#1F618D",
        "themes": {
            "Helm": "You naturally take charge and set direction for others.",
            "Weaver": "You bind a group into one functioning team.",
            "Voice": "You make complex ideas land clearly with any audience.",
            "Bridge": "You sense tension early and close the gap between people.",
            "Resonator": "You feel what others feel before they say it.",
            "Cultivator": "You spot and grow potential in the people around you.",
        },
    },
    "Industrial/Work Psychology": {
        "color": "#922B21",
        "themes": {
            "Driver": "You feel an internal push to accomplish something meaningful every day.",
            "Anchor": "You are the person others can count on to deliver, on time, every time.",
            "Flex": "You bend without breaking when plans or conditions shift.",
            "Steward": "You treat outcomes as personally yours to protect, whether or not it's your job.",
            "Fixer": "You're drawn to diagnosing and repairing what's broken.",
        },
    },
    "Cognitive Psychology": {
        "color": "#6C3483",
        "themes": {
            "Prism": "You break complex problems into clear, logical parts.",
            "Mapper": "You see how the moving pieces of a system connect and where they lead.",
            "Forge": "You build original solutions rather than reach for the obvious one.",
            "Visionary": "You picture what doesn't exist yet, years before others can see it.",
            "Archivist": "You collect and connect information others overlook.",
        },
    },
    "Behavioral Psychology": {
        "color": "#117A65",
        "themes": {
            "Steady": "You stay composed and think clearly when pressure rises.",
            "Igniter": "You move on a problem before anyone asks you to.",
            "Grit": "You keep pushing toward a goal long after motivation fades.",
            "Catalyst": "You turn talk into action, fast.",
            "Contender": "You measure yourself against others and want to come out ahead.",
        },
    },
}

STATEMENT_THEMES = [
    # Positive Psychology
    "Horizon", "Horizon", "Horizon",
    "Valuer", "Valuer", "Valuer",
    "Seeker", "Seeker", "Seeker",
    "Spark", "Spark", "Spark",
    
    # Organizational Psychology
    "Helm", "Helm", "Helm",
    "Weaver", "Weaver", "Weaver",
    "Voice", "Voice", "Voice",
    "Bridge", "Bridge", "Bridge",
    "Resonator", "Resonator", "Resonator",
    "Cultivator", "Cultivator", "Cultivator",
    
    # Industrial/Work Psychology
    "Driver", "Driver", "Driver",
    "Anchor", "Anchor", "Anchor",
    "Flex", "Flex", "Flex",
    "Steward", "Steward", "Steward",
    "Fixer", "Fixer", "Fixer",
    
    # Cognitive Psychology
    "Prism", "Prism", "Prism",
    "Mapper", "Mapper", "Mapper",
    "Forge", "Forge", "Forge",
    "Visionary", "Visionary", "Visionary",
    "Archivist", "Archivist", "Archivist",
    
    # Behavioral Psychology
    "Steady", "Steady", "Steady",
    "Igniter", "Igniter", "Igniter",
    "Grit", "Grit", "Grit",
    "Catalyst", "Catalyst", "Catalyst",
    "Contender", "Contender", "Contender"
]

STATEMENTS = [
    # Positive Psychology
    "I generally expect good outcomes, even when circumstances are uncertain.",
    "When faced with a setback, I quickly start looking for the silver lining.",
    "I find it easy to stay hopeful about the future.",
    "I regularly notice and value the good things in my life and work.",
    "I make a habit of acknowledging others' contributions.",
    "I feel a strong sense of appreciation for opportunities that come my way.",
    "I actively seek out new knowledge, even outside my immediate responsibilities.",
    "I enjoy exploring how things work at a deeper level.",
    "I look forward to learning something new almost every day.",
    "I approach my work and projects with energy and enthusiasm.",
    "Others often notice my enthusiasm rubbing off on them.",
    "I rarely feel drained by tasks that genuinely interest me, no matter how long they take.",
    
    # Organizational Psychology
    "People often look to me to take charge when a decision needs to be made.",
    "I can rally a group around a shared goal without much difficulty.",
    "I feel comfortable setting direction for others, even under pressure.",
    "I genuinely enjoy working with others to accomplish a shared outcome.",
    "I adjust my own approach to help a team succeed as a whole.",
    "I find satisfaction in supporting a teammate's success as much as my own.",
    "I can explain complex ideas in ways that are easy for others to understand.",
    "I am comfortable presenting my thoughts to a group, large or small.",
    "People tell me I express myself clearly and persuasively.",
    "I naturally notice tension in a group and look for ways to ease it.",
    "I try to find common ground rather than take sides in a disagreement.",
    "Others often come to me to help mediate disputes.",
    "I can sense how someone is feeling even before they say anything.",
    "I find it easy to see a situation from another person's perspective.",
    "People often say I 'just get' what they're going through.",
    "I notice small signs of potential or improvement in others before they notice it themselves.",
    "I get satisfaction from helping someone else grow or succeed.",
    "I invest time mentoring or coaching others, even without being asked.",
    
    # Industrial/Work Psychology
    "I feel a strong internal push to accomplish something meaningful every day.",
    "I set demanding personal targets and work hard to hit them.",
    "Completing a task well gives me a deep sense of satisfaction.",
    "I follow through on commitments even when no one is checking on me.",
    "I prefer to have clear structure and routines in my work.",
    "People consider me dependable because I deliver what I promise, on time.",
    "I adjust quickly when plans or priorities shift unexpectedly.",
    "I stay effective even when working conditions become unpredictable.",
    "I see change as an opportunity rather than a threat.",
    "I feel a strong sense of ownership over outcomes, even outside my formal role.",
    "I hold myself accountable for mistakes rather than deflecting blame.",
    "When I say I'll do something, I feel psychologically obligated to see it through.",
    "I'm drawn to diagnosing what's wrong with a broken process or system.",
    "I get genuine satisfaction from fixing something that others have given up on.",
    "I can usually identify the root cause of a recurring problem.",
    
    # Cognitive Psychology
    "I like to break down complex problems into smaller, logical parts.",
    "I naturally question assumptions and look for supporting evidence.",
    "I feel most confident in decisions after I've carefully examined the data.",
    "I can usually see how different parts of a system affect each other.",
    "I enjoy planning several steps ahead rather than reacting in the moment.",
    "I often spot patterns or trends that others miss.",
    "I enjoy coming up with original solutions to difficult problems.",
    "I can generate multiple possible approaches before settling on one.",
    "I like experimenting with unconventional ideas, even if they might fail.",
    "I frequently imagine how things could look years from now.",
    "I enjoy painting a picture of future possibilities for others.",
    "Long-range vision comes more naturally to me than short-term details.",
    "I like collecting a wide range of information before forming a conclusion.",
    "I enjoy hunting down facts, resources, or references relevant to a topic.",
    "I retain and connect odd pieces of information that later turn out to be useful.",
    
    # Behavioral Psychology
    "I stay composed and think clearly under stress.",
    "I can manage my emotions effectively during setbacks.",
    "I bounce back quickly after a disappointment or failure.",
    "I take action on problems before being asked to.",
    "I look for opportunities to improve things without waiting for instructions.",
    "I tend to start tasks early rather than waiting until the last moment.",
    "I keep working toward a goal even when progress is slow.",
    "I rarely give up on something I've decided is important.",
    "I stay focused on long-term objectives despite short-term distractions.",
    "I prefer to start acting on an idea rather than analyze it endlessly.",
    "I often push a group from discussion into action.",
    "I get impatient when plans stay theoretical for too long.",
    "I naturally compare my performance against others and want to come out ahead.",
    "Competition energizes me rather than stresses me.",
    "Winning or ranking well matters to me, even in informal situations."
]

THEME_TO_DOMAIN = {theme: domain for domain, data in TALENTPRISM_DATA.items() for theme in data["themes"]}

# ==========================================
# 2. HELPER FUNCTIONS: SCORING & CHARTS
# ==========================================

def calculate_results(answers):
    theme_scores = {theme: 0 for theme in THEME_TO_DOMAIN.keys()}
    for idx, rating in answers.items():
        theme = STATEMENT_THEMES[idx]
        theme_scores[theme] += rating
        
    theme_classifications = {}
    for theme, score in theme_scores.items():
        if score >= 13:
            classification = "Dominant Strength"
        elif score >= 9:
            classification = "Supporting Strength"
        else:
            classification = "Growth Area"
        theme_classifications[theme] = classification

    domain_totals = {domain: 0 for domain in TALENTPRISM_DATA.keys()}
    domain_counts = {domain: 0 for domain in TALENTPRISM_DATA.keys()}
    for theme, score in theme_scores.items():
        domain = THEME_TO_DOMAIN[theme]
        domain_totals[domain] += score
        domain_counts[domain] += 1
        
    domain_averages = {d: round(domain_totals[d] / domain_counts[d], 2) for d in TALENTPRISM_DATA.keys()}
    sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_themes[:5]
    
    return theme_scores, theme_classifications, domain_averages, top_5

def render_strengths_wheel(theme_scores):
    themes = list(theme_scores.keys())
    scores = [theme_scores[t] for t in themes]
    chart_colors = [TALENTPRISM_DATA[THEME_TO_DOMAIN[t]]["color"] for t in themes]

    fig = go.Figure(
        data=go.Barpolar(
            r=scores,
            theta=themes,
            marker_color=chart_colors,
            marker_line_color="white",
            marker_line_width=1.5,
            opacity=0.85
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 15], tickfont=dict(size=9)),
            angularaxis=dict(tickfont=dict(size=10, color="#2C3E50"), direction="clockwise")
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=30, b=30),
        height=500
    )
    return fig

# ==========================================
# 3. PDF GENERATION ENGINE
# ==========================================

def generate_pdf_report(candidate_name, theme_scores, theme_classifications, domain_averages, top_5):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1A252C'), spaceAfter=6)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#566573'), spaceAfter=15)
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1F618D'), spaceBefore=12, spaceAfter=8)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#2C3E50'), leading=13)

    elements = []
    elements.append(Paragraph("<b>TalentPrism-25 Strengths Assessment</b>", title_style))
    elements.append(Paragraph(f"<b>Candidate:</b> {candidate_name} | <b>Framework:</b> TalentPrism-25 (75 Items)", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1F618D'), spaceAfter=15))

    elements.append(Paragraph("Top 5 Signature Strengths", h2_style))
    top_data = [["#", "Theme", "Domain", "Score", "Definition"]]
    for rank, (theme, score) in enumerate(top_5, 1):
        domain = THEME_TO_DOMAIN[theme]
        definition = TALENTPRISM_DATA[domain]["themes"][theme]
        top_data.append([str(rank), theme, domain, f"{score}/15", definition])

    t_top = Table(top_data, colWidths=[20, 80, 120, 50, 270])
    t_top.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F618D')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
    ]))
    elements.append(t_top)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Complete Strengths Matrix (25 Themes)", h2_style))
    matrix_data = [["Domain", "Theme", "Score", "Classification"]]
    
    for domain, data in TALENTPRISM_DATA.items():
        for theme in data["themes"].keys():
            score = theme_scores[theme]
            classification = theme_classifications[theme]
            matrix_data.append([domain, theme, f"{score}/15", classification])

    t_matrix = Table(matrix_data, colWidths=[150, 120, 60, 210])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#EAEDED')),
    ]))
    elements.append(t_matrix)
    elements.append(Spacer(1, 15))

    disclaimer = ("<i>TalentPrism-25 is an original self-reflection framework. "
                  "Not affiliated with, endorsed by, or a substitute for Gallup's CliftonStrengths® assessment.</i>")
    elements.append(Paragraph(disclaimer, ParagraphStyle('Disc', parent=body_style, fontSize=7, textColor=colors.gray)))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# 4. EMAIL SERVICE ENGINE
# ==========================================

def send_results_email(user_name, target_email, pdf_bytes, top_5):
    api_key = st.secrets.get("RESEND_API_KEY") or os.environ.get("RESEND_API_KEY")
    if not api_key:
        st.error("Resend API Key is missing. Check environment settings.")
        return False

    resend.api_key = api_key
    top_5_html = "".join([f"<li><b>{theme}</b> ({THEME_TO_DOMAIN[theme]}): {score}/15</li>" for theme, score in top_5])

    email_body = f"""
    <h3>TalentPrism-25 Assessment Report</h3>
    <p>Hi {user_name},</p>
    <p>Here is your copy of the TalentPrism-25 Strengths Assessment report.</p>
    <h4>Your Top 5 Signature Strengths:</h4>
    <ul>{top_5_html}</ul>
    <p>Your full report PDF is attached to this email.</p>
    """

    try:
        resend.Emails.send({
            "from": "TalentPrism <onboarding@resend.dev>",
            "to": [target_email],
            "subject": f"Your TalentPrism-25 Assessment Report - {user_name}",
            "html": email_body,
            "attachments": [{
                "filename": f"{user_name.replace(' ', '_')}_TalentPrism_Results.pdf",
                "content": list(pdf_bytes)
            }]
        })
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

# ==========================================
# 5. STREAMLIT UI & WORKFLOW
# ==========================================

st.set_page_config(page_title="TalentPrism-25 Assessment Portal", layout="wide")

st.title("TalentPrism-25 Assessment Portal")
st.caption("A 75-Item Strengths Assessment Across Positive, Organizational, Industrial, Cognitive & Behavioral Psychology")

if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "validation_error" not in st.session_state:
    st.session_state.validation_error = []

# STEP 1: QUESTIONNAIRE FORM
if not st.session_state.submitted:
    with st.form("assessment_form"):
        st.subheader("1. Candidate Details")
        user_name = st.text_input("Full Name *", value=st.session_state.get("user_name", ""))

        st.subheader("2. Self-Report Questionnaire")
        st.info("Rate each statement from 1 (Strongly Disagree) to 5 (Strongly Agree). All questions are mandatory.")

        answers = {}
        for idx, statement in enumerate(STATEMENTS):
            q_num = idx + 1
            is_missing = q_num in st.session_state.validation_error
            
            # Anchor wrapper for auto-scrolling
            st.markdown(f"<div id='q-target-{q_num}'></div>", unsafe_allow_html=True)

            if is_missing:
                st.markdown(f"<div style='border-left: 4px solid #ef4444; padding-left: 10px; background-color: #fef2f2; margin-top: 10px;'>", unsafe_allow_html=True)

            answers[idx] = st.radio(
                f"**Q{q_num}:** {statement}",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {1: "1 - Strongly Disagree", 2: "2 - Disagree", 3: "3 - Neutral", 4: "4 - Agree", 5: "5 - Strongly Agree"}[x],
                index=None,  # Forces explicit answer
                horizontal=True,
                key=f"q_{idx}"
            )

            if is_missing:
                st.markdown("</div>", unsafe_allow_html=True)

        submit_button = st.form_submit_button("Submit Assessment")

        if submit_button:
            unanswered_indices = [idx + 1 for idx, v in answers.items() if v is None]
            
            if not user_name.strip():
                st.error("Please enter your Full Name to proceed.")
            elif len(unanswered_indices) > 0:
                st.session_state.validation_error = unanswered_indices
                st.session_state.user_name = user_name
                st.rerun()
            else:
                st.session_state.validation_error = []
                st.session_state.user_name = user_name
                st.session_state.answers = answers
                st.session_state.submitted = True
                st.rerun()

    # POPUP NOTIFICATION & AUTO-SCROLL TO FIRST UNANSWERED QUESTION
    if not st.session_state.submitted and st.session_state.validation_error:
        missing_count = len(st.session_state.validation_error)
        missing_str = ", ".join([f"Q{q_num}" for q_num in st.session_state.validation_error])
        first_missing = st.session_state.validation_error[0]
        
        st.markdown(
            f"""
            <div id="error-popup-overlay" style="
                position: fixed;
                top: 0; left: 0; width: 100vw; height: 100vh;
                background-color: rgba(15, 23, 42, 0.4);
                backdrop-filter: blur(2px);
                z-index: 999998;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div style="
                    background-color: #FFFFFF;
                    color: #0F172A;
                    padding: 24px 28px;
                    border-radius: 12px;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
                    border-top: 5px solid #EF4444;
                    width: 90%;
                    max-width: 420px;
                    font-family: sans-serif;
                    text-align: center;
                ">
                    <h3 style="margin-top: 0; color: #DC2626; font-size: 18px;">⚠️ Assessment Incomplete</h3>
                    <p style="font-size: 14px; color: #475569; line-height: 1.5; margin-bottom: 16px;">
                        You have <b>{missing_count} unanswered question(s)</b>. Click below to jump straight to the first missing item.
                    </p>
                    <div style="font-size: 12px; background: #F1F5F9; padding: 8px 12px; border-radius: 6px; color: #334155; margin-bottom: 20px; max-height: 80px; overflow-y: auto; text-align: left;">
                        <b>Pending Items:</b> {missing_str}
                    </div>
                    <button onclick="
                        document.getElementById('error-popup-overlay').style.display='none';
                        const target = document.getElementById('q-target-{first_missing}');
                        if(target) {{ target.scrollIntoView({{ behavior: 'smooth', block: 'center' }}); }}
                    " style="
                        background-color: #2563EB;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        font-size: 14px;
                        font-weight: bold;
                        border-radius: 6px;
                        cursor: pointer;
                        width: 100%;
                    ">Take Me There</button>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# STEP 2: DASHBOARD & POSITIVE OUTCOMES WHEEL
else:
    theme_scores, theme_classifications, domain_averages, top_5 = calculate_results(st.session_state.answers)
    pdf_bytes = generate_pdf_report(st.session_state.user_name, theme_scores, theme_classifications, domain_averages, top_5)

    st.success(f"Assessment complete, {st.session_state.user_name}!")

    # Action Toolbar
    col_dl, col_blank = st.columns([1, 2])
    with col_dl:
        st.download_button(
            label="📥 Instant Download PDF Report",
            data=pdf_bytes,
            file_name=f"{st.session_state.user_name.replace(' ', '_')}_TalentPrism_Results.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # OPTIONAL EMAIL PROMPT CARD
    with st.expander("✉️ Would you like a copy sent to your email?", expanded=True):
        col_email_input, col_email_btn = st.columns([3, 1])
        with col_email_input:
            recipient_email = st.text_input("Enter your email address", placeholder="name@example.com", label_visibility="collapsed")
        with col_email_btn:
            send_btn = st.button("Send Report", use_container_width=True)

        if send_btn:
            if not recipient_email.strip() or "@" not in recipient_email:
                st.warning("Please enter a valid email address.")
            else:
                with st.spinner("Dispatching report..."):
                    success = send_results_email(st.session_state.user_name, recipient_email.strip(), pdf_bytes, top_5)
                    if success:
                        st.success(f"Report successfully sent to {recipient_email}!")

    st.markdown("---")

    # POSITIVE OUTCOMES HIGHLIGHT BANNER
    dominant_strengths = [t for t, c in theme_classifications.items() if c == "Dominant Strength"]
    st.markdown(
        f"""
        <div style="background-color: #ecfdf5; border: 1px solid #10b981; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="color: #065f46; margin: 0 0 10px 0;">🌟 Positive Strengths Summary</h4>
            <p style="color: #047857; margin: 0;">
                You demonstrated <b>{len(dominant_strengths)} Dominant Strengths</b> (scores ≥ 13/15). 
                Your highest driving domains are highlighted on the TalentPrism Strengths Wheel below.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Visual Dashboard
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Your Top 5 Signature Strengths")
        for rank, (theme, score) in enumerate(top_5, 1):
            domain = THEME_TO_DOMAIN[theme]
            desc = TALENTPRISM_DATA[domain]["themes"][theme]
            st.markdown(f"**{rank}. {theme}** ({domain}) — `{score}/15`")
            st.caption(desc)

        st.subheader("Domain Averages")
        for domain, avg in domain_averages.items():
            st.progress(avg / 15.0, text=f"{domain}: {avg} / 15.0")

    with col_right:
        st.subheader("TalentPrism Strengths Wheel")
        wheel_fig = render_strengths_wheel(theme_scores)
        st.plotly_chart(wheel_fig, use_container_width=True)

    if st.button("Take Assessment Again"):
        st.session_state.submitted = False
        st.session_state.validation_error = []
        st.rerun()
