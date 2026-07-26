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

STATEMENTS = [
    # Positive Psychology
    ("Horizon", "I generally expect good outcomes, even when circumstances are uncertain."),
    ("Horizon", "When faced with a setback, I quickly start looking for the silver lining."),
    ("Horizon", "I find it easy to stay hopeful about the future."),
    ("Valuer", "I regularly notice and value the good things in my life and work."),
    ("Valuer", "I make a habit of acknowledging others' contributions."),
    ("Valuer", "I feel a strong sense of appreciation for opportunities that come my way."),
    ("Seeker", "I actively seek out new knowledge, even outside my immediate responsibilities."),
    ("Seeker", "I enjoy exploring how things work at a deeper level."),
    ("Seeker", "I look forward to learning something new almost every day."),
    ("Spark", "I approach my work and projects with energy and enthusiasm."),
    ("Spark", "Others often notice my enthusiasm rubbing off on them."),
    ("Spark", "I rarely feel drained by tasks that genuinely interest me, no matter how long they take."),
    
    # Organizational Psychology
    ("Helm", "People often look to me to take charge when a decision needs to be made."),
    ("Helm", "I can rally a group around a shared goal without much difficulty."),
    ("Helm", "I feel comfortable setting direction for others, even under pressure."),
    ("Weaver", "I genuinely enjoy working with others to accomplish a shared outcome."),
    ("Weaver", "I adjust my own approach to help a team succeed as a whole."),
    ("Weaver", "I find satisfaction in supporting a teammate's success as much as my own."),
    ("Voice", "I can explain complex ideas in ways that are easy for others to understand."),
    ("Voice", "I am comfortable presenting my thoughts to a group, large or small."),
    ("Voice", "People tell me I express myself clearly and persuasively."),
    ("Bridge", "I naturally notice tension in a group and look for ways to ease it."),
    ("Bridge", "I try to find common ground rather than take sides in a disagreement."),
    ("Bridge", "Others often come to me to help mediate disputes."),
    ("Resonator", "I can sense how someone is feeling even before they say anything."),
    ("Resonator", "I find it easy to see a situation from another person's perspective."),
    ("Resonator", "People often say I 'just get' what they're going through."),
    ("Cultivator", "I notice small signs of potential or improvement in others before they notice it themselves."),
    ("Cultivator", "I get satisfaction from helping someone else grow or succeed."),
    ("Cultivator", "I invest time mentoring or coaching others, even without being asked."),
    
    # Industrial/Work Psychology
    ("Driver", "I feel a strong internal push to accomplish something meaningful every day."),
    ("Driver", "I set demanding personal targets and work hard to hit them."),
    ("Driver", "Completing a task well gives me a deep sense of satisfaction."),
    ("Anchor", "I follow through on commitments even when no one is checking on me."),
    ("Anchor", "I prefer to have clear structure and routines in my work."),
    ("Anchor", "People consider me dependable because I deliver what I promise, on time."),
    ("Flex", "I adjust quickly when plans or priorities shift unexpectedly."),
    ("Flex", "I stay effective even when working conditions become unpredictable."),
    ("Flex", "I see change as an opportunity rather than a threat."),
    ("Steward", "I feel a strong sense of ownership over outcomes, even outside my formal role."),
    ("Steward", "I hold myself accountable for mistakes rather than deflecting blame."),
    ("Steward", "When I say I'll do something, I feel psychologically obligated to see it through."),
    ("Fixer", "I'm drawn to diagnosing what's wrong with a broken process or system."),
    ("Fixer", "I get genuine satisfaction from fixing something that others have given up on."),
    ("Fixer", "I can usually identify the root cause of a recurring problem."),
    
    # Cognitive Psychology
    ("Prism", "I like to break down complex problems into smaller, logical parts."),
    ("Prism", "I naturally question assumptions and look for supporting evidence."),
    ("Prism", "I feel most confident in decisions after I've carefully examined the data."),
    ("Mapper", "I can usually see how different parts of a system affect each other."),
    ("Mapper", "I enjoy planning several steps ahead rather than reacting in the moment."),
    ("Mapper", "I often spot patterns or trends that others miss."),
    ("Forge", "I enjoy coming up with original solutions to difficult problems."),
    ("Forge", "I can generate multiple possible approaches before settling on one."),
    ("Forge", "I like experimenting with unconventional ideas, even if they might fail."),
    ("Visionary", "I frequently imagine how things could look years from now."),
    ("Visionary", "I enjoy painting a picture of future possibilities for others."),
    ("Visionary", "Long-range vision comes more naturally to me than short-term details."),
    ("Archivist", "I like collecting a wide range of information before forming a conclusion."),
    ("Archivist", "I enjoy hunting down facts, resources, or references relevant to a topic."),
    ("Archivist", "I retain and connect odd pieces of information that later turn out to be useful."),
    
    # Behavioral Psychology
    ("Steady", "I stay composed and think clearly under stress."),
    ("Steady", "I can manage my emotions effectively during setbacks."),
    ("Steady", "I bounce back quickly after a disappointment or failure."),
    ("Igniter", "I take action on problems before being asked to."),
    ("Igniter", "I look for opportunities to improve things without waiting for instructions."),
    ("Igniter", "I tend to start tasks early rather than waiting until the last moment."),
    ("Grit", "I keep working toward a goal even when progress is slow."),
    ("Grit", "I rarely give up on something I've decided is important."),
    ("Grit", "I stay focused on long-term objectives despite short-term distractions."),
    ("Catalyst", "I prefer to start acting on an idea rather than analyze it endlessly."),
    ("Catalyst", "I often push a group from discussion into action."),
    ("Catalyst", "I get impatient when plans stay theoretical for too long."),
    ("Contender", "I naturally compare my performance against others and want to come out ahead."),
    ("Contender", "Competition energizes me rather than stresses me."),
    ("Contender", "Winning or ranking well matters to me, even in informal situations.")
]

THEME_TO_DOMAIN = {theme: domain for domain, data in TALENTPRISM_DATA.items() for theme in data["themes"]}

# ==========================================
# 2. HELPER FUNCTIONS: SCORING & CHARTS
# ==========================================

def calculate_results(answers):
    theme_scores = {theme: 0 for theme in THEME_TO_DOMAIN.keys()}
    for idx, rating in answers.items():
        theme, _ = STATEMENTS[idx]
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
        st.error("Resend API Key is missing. Check your Render environment settings.")
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

# STEP 1: QUESTIONNAIRE FORM
if not st.session_state.submitted:
    with st.form("assessment_form"):
        st.subheader("1. Candidate Details")
        user_name = st.text_input("Full Name *", value="")

        st.subheader("2. Self-Report Questionnaire")
        st.info("Rate each statement from 1 (Strongly Disagree) to 5 (Strongly Agree) based on how true it is of you.")

        answers = {}
        for idx, (_, statement) in enumerate(STATEMENTS):
            answers[idx] = st.radio(
                f"**Q{idx+1}:** {statement}",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {1: "1 - Strongly Disagree", 2: "2 - Disagree", 3: "3 - Neutral", 4: "4 - Agree", 5: "5 - Strongly Agree"}[x],
                index=2,
                horizontal=True,
                key=f"q_{idx}"
            )

        submit_button = st.form_submit_button("Submit Assessment")

        if submit_button:
            if not user_name.strip():
                st.error("Please enter your name to proceed.")
            else:
                st.session_state.user_name = user_name
                st.session_state.answers = answers
                st.session_state.submitted = True
                st.rerun()

# STEP 2: DASHBOARD & CONDITIONAL EMAIL PROMPT
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
        st.rerun()
