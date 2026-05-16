# app.py
import streamlit as st
import json
import re
from groq import Groq

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Appraise — Talent Discovery",
    page_icon="👁️",
    layout="centered"
)

# ── Groq client ──────────────────────────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { max-width: 720px; }
    .stApp { background-color: #0f0f1a; color: #e8e8f0; }
    .block-container { padding-top: 2rem; }

    .appraise-title {
        font-size: 2.8rem; font-weight: 700; text-align: center;
        background: linear-gradient(135deg, #7F77DD, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .appraise-sub {
        text-align: center; color: #9090b0; font-size: 1rem; margin-bottom: 2rem;
    }
    .section-badge {
        display: inline-block; background: #1e1e3a; color: #7F77DD;
        border: 1px solid #7F77DD44; border-radius: 20px;
        padding: 3px 14px; font-size: 0.78rem; font-weight: 600;
        letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.5rem;
    }
    .progress-label {
        color: #9090b0; font-size: 0.82rem; text-align: right; margin-bottom: 0.3rem;
    }
    .stat-row {
        display: flex; align-items: center; margin-bottom: 10px; gap: 12px;
    }
    .stat-name { width: 140px; font-size: 0.88rem; color: #c0c0d8; flex-shrink: 0; }
    .stat-bar-bg {
        flex: 1; height: 8px; background: #2a2a40; border-radius: 4px; overflow: hidden;
    }
    .stat-bar-fill { height: 100%; border-radius: 4px; }
    .stat-val { width: 32px; text-align: right; font-size: 0.85rem; font-weight: 600; color: #a0a0c8; }

    .archetype-box {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #7F77DD55; border-radius: 16px;
        padding: 1.5rem; margin-bottom: 1.2rem; text-align: center;
    }
    .archetype-title {
        font-size: 1.7rem; font-weight: 700; color: #a78bfa; margin-bottom: 0.4rem;
    }
    .archetype-summary { color: #c0c0d8; font-size: 0.95rem; line-height: 1.6; }

    .insight-card {
        background: #14142a; border: 1px solid #2a2a44;
        border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
    }
    .insight-label {
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; margin-bottom: 0.4rem;
    }
    .insight-text { color: #d0d0e8; font-size: 0.92rem; line-height: 1.6; }

    .career-card {
        background: #14142a; border: 1px solid #2a2a44;
        border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.7rem;
        display: flex; align-items: flex-start; gap: 14px;
    }
    .career-icon { font-size: 1.8rem; flex-shrink: 0; }
    .career-title { font-weight: 600; font-size: 1rem; color: #e8e8f8; margin-bottom: 3px; }
    .career-why { color: #9090b0; font-size: 0.87rem; line-height: 1.5; }

    .warning-card {
        background: #1f1208; border: 1px solid #D85A3044;
        border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
    }
    .next-card {
        background: #081a12; border: 1px solid #1D9E7555;
        border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
    }

    div[data-testid="stRadio"] label { color: #d0d0e8 !important; }
    div[data-testid="stTextArea"] textarea {
        background: #14142a !important; color: #e8e8f0 !important;
        border: 1px solid #2a2a44 !important; border-radius: 10px !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #7F77DD, #534AB7) !important;
        color: white !important; border: none !important;
        border-radius: 10px !important; font-weight: 600 !important;
        padding: 0.6rem 2rem !important; width: 100%;
    }
    .stButton > button:hover { opacity: 0.9 !important; }
</style>
""", unsafe_allow_html=True)

# ── Questions data ────────────────────────────────────────────────────────────
QUESTIONS = [
    {
        "section": "Ingenuity", "type": "choice", "key": "problem_style",
        "text": "When you face a completely new problem, what's your instinct?",
        "sub": "Choose the option that feels most natural — not the 'right' answer.",
        "opts": ["Dive in and figure it out as I go", "Research deeply before touching anything",
                 "Ask people who've done it before", "Find a creative workaround or reframe it"]
    },
    {
        "section": "Ingenuity", "type": "text", "key": "ingenuity_story",
        "text": "Describe a time you solved something others couldn't.",
        "sub": "What made you see it differently? Be specific — school, work, anything counts.",
        "placeholder": "e.g. Everyone was stuck on the group project until I suggested..."
    },
    {
        "section": "Ingenuity", "type": "choice", "key": "learning_style",
        "text": "Which describes you best when learning something new?",
        "sub": "Pick the one that makes you nod.",
        "opts": ["I connect it to things I already know", "I need to do it hands-on immediately",
                 "I visualize systems and flows", "I teach it to someone else to understand it"]
    },
    {
        "section": "Leadership", "type": "choice", "key": "group_role",
        "text": "In a group, which role do you naturally drift into?",
        "sub": "Be honest — not what you think you should be.",
        "opts": ["I take charge and set direction", "I keep everyone connected and motivated",
                 "I challenge assumptions and play devil's advocate", "I execute brilliantly and let others lead"]
    },
    {
        "section": "Leadership", "type": "choice", "key": "conflict_style",
        "text": "When someone you care about makes a bad decision, what do you do?",
        "sub": "Your honest reaction — not your ideal self.",
        "opts": ["Tell them directly, even if uncomfortable", "Ask questions to help them see it themselves",
                 "Support them and stay ready if it fails", "Research alternatives and present options"]
    },
    {
        "section": "Leadership", "type": "text", "key": "leadership_reputation",
        "text": "What have people come to you for help with, repeatedly throughout your life?",
        "sub": "Not what you studied — what people actually seek you out for.",
        "placeholder": "e.g. Friends always ask me to mediate, explain things simply, plan events..."
    },
    {
        "section": "Ambition", "type": "text", "key": "ambition_gap",
        "text": "What's the gap between who you are now and who you want to be in 10 years?",
        "sub": "Be ambitious — this is private.",
        "placeholder": "e.g. Right now I'm reactive. In 10 years I want to be building something that matters..."
    },
    {
        "section": "Ambition", "type": "text", "key": "intrinsic_drive",
        "text": "What would you keep doing even if you never got paid or recognized for it?",
        "sub": "The thing that doesn't need external validation.",
        "placeholder": "e.g. I'd keep building side projects, writing, coaching my teammates..."
    },
    {
        "section": "Ambition", "type": "choice", "key": "failure_response",
        "text": "How do you respond when you fail at something important to you?",
        "sub": "Your real pattern, not the ideal.",
        "opts": ["Analyze what went wrong immediately", "Need time to process, then come back stronger",
                 "Talk it through with someone I trust", "Pivot fast and find another path"]
    },
    {
        "section": "Prowess", "type": "choice", "key": "peak_environment",
        "text": "Which environment makes you feel most alive and capable?",
        "sub": "Think about the last time you felt genuinely in your element.",
        "opts": ["High-pressure, fast-moving situations", "Deep solo focus on complex problems",
                 "Building and energizing a team", "Creating something from nothing"]
    },
    {
        "section": "Prowess", "type": "text", "key": "natural_prowess",
        "text": "What do you do better than most people you know — even without formal training?",
        "sub": "Think broadly: memory, persuasion, reading people, fixing things, spatial thinking...",
        "placeholder": "e.g. I'm unusually good at reading how people feel in a room before they say anything..."
    },
    {
        "section": "Prowess", "type": "choice", "key": "mastery_target",
        "text": "Which skill do you want to be in the top 1% of in 5 years?",
        "sub": "The one that genuinely excites you, not the most prestigious.",
        "opts": ["Strategic thinking and systems design", "Building and leading high-performing teams",
                 "Technical mastery in my field", "Creating things people love and remember"]
    },
    {
        "section": "Purpose", "type": "text", "key": "purpose_pain",
        "text": "What problems in the world genuinely make you angry or sad?",
        "sub": "The injustices or inefficiencies that personally bother you — big or small.",
        "placeholder": "e.g. It frustrates me that talented people never get discovered because of where they're from..."
    },
    {
        "section": "Purpose", "type": "text", "key": "purpose_dream",
        "text": "If you had unlimited resources and couldn't fail, what would you build?",
        "sub": "No practical constraints — dream answer.",
        "placeholder": "e.g. A school that teaches kids how to think, not just what to think..."
    },
    {
        "section": "Purpose", "type": "choice", "key": "legacy",
        "text": "How do you most want to be remembered by people who knew you?",
        "sub": "Not your title — your character and impact.",
        "opts": ["The person who built something that lasted", "The person who made others better",
                 "The person who told the truth when others didn't", "The person who solved the problem no one else could"]
    },
]

SECTION_COLORS = {
    "Ingenuity": "#7F77DD",
    "Leadership": "#1D9E75",
    "Ambition": "#D85A30",
    "Prowess": "#378ADD",
    "Purpose": "#BA7517",
}

# ── Session state init ────────────────────────────────────────────────────────
if "step" not in st.session_state:
    st.session_state.step = 0          # 0 = intro, 1-15 = questions, 16 = results
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "profile" not in st.session_state:
    st.session_state.profile = None
if "roadmap" not in st.session_state:
    st.session_state.roadmap = None

# ── Helpers ───────────────────────────────────────────────────────────────────
def stat_bar_html(name, value, color):
    return f"""
    <div class="stat-row">
        <div class="stat-name">{name}</div>
        <div class="stat-bar-bg">
            <div class="stat-bar-fill" style="width:{value}%; background:{color};"></div>
        </div>
        <div class="stat-val">{value}</div>
    </div>"""

def build_answer_summary():
    lines = []
    for q in QUESTIONS:
        a = st.session_state.answers.get(q["key"])
        if a:
            if q["type"] == "choice":
                lines.append(f"Q: {q['text']}\nA: {q['opts'][a]}")
            else:
                lines.append(f"Q: {q['text']}\nA: {a}")
    return "\n\n".join(lines)

def call_groq(prompt, max_tokens=1200):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content

def analyze_profile():
    summary = build_answer_summary()
    prompt = f"""You are the "Appraisal" skill from the anime "As a Reincarnated Aristocrat". You see people's true stats, hidden talents, and potential — including what society overlooks.

Analyze these answers carefully and return ONLY valid JSON. No markdown, no backticks, no explanation. Just the JSON object.

PERSON'S ANSWERS:
{summary}

Return this exact JSON structure:
{{
  "archetype": "2-3 word archetype title (e.g. The Strategic Visionary)",
  "archetype_summary": "2 sentences describing who this person fundamentally is and their core superpower",
  "stats": {{
    "ingenuity": <integer 0-100>,
    "leadership": <integer 0-100>,
    "ambition": <integer 0-100>,
    "prowess": <integer 0-100>,
    "purpose_clarity": <integer 0-100>
  }},
  "hidden_talent": "1 specific hidden or underestimated talent they likely have — something they may not fully realize",
  "flow_zone": "The specific environment and work type where they enter flow state most easily",
  "top_careers": [
    {{"title": "Job title", "why": "1 sentence explaining the match", "icon": "single relevant emoji"}},
    {{"title": "Job title", "why": "1 sentence explaining the match", "icon": "single relevant emoji"}},
    {{"title": "Job title", "why": "1 sentence explaining the match", "icon": "single relevant emoji"}},
    {{"title": "Job title", "why": "1 sentence explaining the match", "icon": "single relevant emoji"}}
  ],
  "warning": "1 honest blind spot or risk that could hold them back if unaddressed",
  "next_step": "The single most important action they should take in the next 30 days to move toward their purpose"
}}"""

    raw = call_groq(prompt)
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)

def generate_roadmap(profile):
    prompt = f"""Based on this talent profile, create a detailed 6-month career roadmap.

Profile:
- Archetype: {profile['archetype']}
- Stats: {json.dumps(profile['stats'])}
- Hidden talent: {profile['hidden_talent']}
- Flow zone: {profile['flow_zone']}
- Top careers: {', '.join([c['title'] for c in profile['top_careers']])}
- Warning: {profile['warning']}

Write a practical 6-month roadmap with:
1. The best career to pursue from the list and why
2. Month 1-2: Foundation (what to learn, build, or start)
3. Month 3-4: Momentum (first real projects or opportunities)
4. Month 5-6: Breakthrough (how to get noticed or land the role)
5. Top 3 skills to develop
6. Top 3 resources (books, courses, communities)
7. One person archetype to find as a mentor

Be specific, practical, and energizing. Format with clear headers using markdown."""

    return call_groq(prompt, max_tokens=1500)

# ── SCREEN 0: Intro ───────────────────────────────────────────────────────────
if st.session_state.step == 0:
    st.markdown('<div class="appraise-title">👁️ Appraise</div>', unsafe_allow_html=True)
    st.markdown('<div class="appraise-sub">Uncover your hidden talents, stat profile, and the careers where you\'ll truly excel — inspired by the Appraisal Skill from <em>As a Reincarnated Aristocrat</em></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="insight-card"><div class="insight-label" style="color:#7F77DD;">⚡ Raw Potential</div><div class="insight-text" style="font-size:0.82rem;">See your true ceiling, not just where you are now</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="insight-card"><div class="insight-label" style="color:#1D9E75;">⚔️ Core Aptitude</div><div class="insight-text" style="font-size:0.82rem;">Discover your natural domain of mastery</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="insight-card"><div class="insight-label" style="color:#D85A30;">🗺️ Career Path</div><div class="insight-text" style="font-size:0.82rem;">Match to careers where you\'ll genuinely excel</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**15 questions · ~5 minutes · AI-powered analysis**", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Begin Appraisal →"):
        st.session_state.step = 1
        st.rerun()

# ── SCREENS 1–15: Questions ───────────────────────────────────────────────────
elif 1 <= st.session_state.step <= 15:
    q_idx = st.session_state.step - 1
    q = QUESTIONS[q_idx]
    color = SECTION_COLORS.get(q["section"], "#7F77DD")

    # Progress
    pct = int((q_idx / 15) * 100)
    st.markdown(f'<div class="progress-label">{q_idx + 1} / 15</div>', unsafe_allow_html=True)
    st.progress(pct / 100)
    st.markdown(f'<div class="section-badge" style="color:{color};border-color:{color}44;">{q["section"]}</div>', unsafe_allow_html=True)

    st.markdown(f"### {q['text']}")
    st.markdown(f"*{q['sub']}*")
    st.markdown("<br>", unsafe_allow_html=True)

    answer = None
    if q["type"] == "choice":
        current = st.session_state.answers.get(q["key"])
        idx_default = current if current is not None else 0
        choice = st.radio("", q["opts"], index=idx_default, key=f"radio_{q_idx}", label_visibility="collapsed")
        answer = q["opts"].index(choice)
    else:
        current_text = st.session_state.answers.get(q["key"], "")
        answer = st.text_area("", value=current_text, placeholder=q.get("placeholder", ""), height=120, key=f"text_{q_idx}", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_next = st.columns([1, 2])

    with col_back:
        if q_idx > 0:
            if st.button("← Back"):
                st.session_state.step -= 1
                st.rerun()

    with col_next:
        is_valid = answer is not None if q["type"] == "choice" else (len(str(answer).strip()) >= 10)
        label = "Next →" if st.session_state.step < 15 else "See My Results →"
        if st.button(label, disabled=not is_valid):
            st.session_state.answers[q["key"]] = answer
            st.session_state.step += 1
            st.rerun()

    # Save answer on any interaction
    if answer is not None:
        st.session_state.answers[q["key"]] = answer

# ── SCREEN 16: Results ────────────────────────────────────────────────────────
elif st.session_state.step == 16:
    if st.session_state.profile is None:
        with st.spinner("Appraising your profile... measuring ingenuity, calculating stats, identifying hidden talents..."):
            try:
                st.session_state.profile = analyze_profile()
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                if st.button("Try again"):
                    st.session_state.profile = None
                    st.rerun()
                st.stop()

    p = st.session_state.profile

    # Archetype
    st.markdown(f"""
    <div class="archetype-box">
        <div class="archetype-title">{p['archetype']}</div>
        <div class="archetype-summary">{p['archetype_summary']}</div>
    </div>""", unsafe_allow_html=True)

    # Stats
    st.markdown("#### 📊 Your Stat Sheet")
    stat_colors = {"ingenuity": "#7F77DD", "leadership": "#1D9E75", "ambition": "#D85A30", "prowess": "#378ADD", "purpose_clarity": "#BA7517"}
    stat_labels = {"ingenuity": "Ingenuity", "leadership": "Leadership", "ambition": "Ambition", "prowess": "Prowess", "purpose_clarity": "Purpose Clarity"}
    bars_html = "".join([stat_bar_html(stat_labels[k], v, stat_colors[k]) for k, v in p["stats"].items()])
    st.markdown(f'<div class="insight-card">{bars_html}</div>', unsafe_allow_html=True)

    # Hidden talent + flow zone
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="insight-card"><div class="insight-label" style="color:#a78bfa;">✨ Hidden Talent</div><div class="insight-text">{p["hidden_talent"]}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="insight-card"><div class="insight-label" style="color:#f59e0b;">🔥 Flow Zone</div><div class="insight-text">{p["flow_zone"]}</div></div>', unsafe_allow_html=True)

    # Careers
    st.markdown("#### 💼 Careers Where You'll Excel")
    for c in p["top_careers"]:
        st.markdown(f'<div class="career-card"><div class="career-icon">{c["icon"]}</div><div><div class="career-title">{c["title"]}</div><div class="career-why">{c["why"]}</div></div></div>', unsafe_allow_html=True)

    # Warning + Next step
    st.markdown(f'<div class="warning-card"><div class="insight-label" style="color:#D85A30;">⚠️ Blind Spot to Watch</div><div class="insight-text">{p["warning"]}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="next-card"><div class="insight-label" style="color:#1D9E75;">🎯 Your Next Move (next 30 days)</div><div class="insight-text">{p["next_step"]}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Roadmap
    st.markdown("#### 🗺️ 6-Month Career Roadmap")
    if st.session_state.roadmap is None:
        if st.button("Generate My Roadmap →"):
            with st.spinner("Building your personalized 6-month roadmap..."):
                st.session_state.roadmap = generate_roadmap(p)
            st.rerun()
    else:
        st.markdown(st.session_state.roadmap)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Retake Assessment"):
        st.session_state.step = 0
        st.session_state.answers = {}
        st.session_state.profile = None
        st.session_state.roadmap = None
        st.rerun()
