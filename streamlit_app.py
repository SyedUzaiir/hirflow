# pyrefly: ignore [missing-import]
import streamlit as st
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Page Settings (MUST be the first Streamlit command)
st.set_page_config(
    page_title="HireFlow Agent - Agentic Recruitment Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Caching Vector DB and Embedding Model
import tools.rag_tool

@st.cache_resource
def get_cached_rag():
    with st.spinner("Initializing Resume Vector Database..."):
        OriginalRAGTool = tools.rag_tool.RAGTool
        return OriginalRAGTool()

cached_rag = get_cached_rag()

# Monkeypatch RAGTool to return singleton cached instance
class RAGToolSingleton:
    def __new__(cls, *args, **kwargs):
        return cached_rag

tools.rag_tool.RAGTool = RAGToolSingleton

# 2. Caching Graph Initialization
from agents.graph import build_graph

@st.cache_resource
def get_graph():
    with st.spinner("Loading HireFlow Agent..."):
        return build_graph()

graph = get_graph()

# Custom Premium Styling
st.markdown("""
<style>
    /* Primary brand colors and premium UI styling */
    .stApp {
        background-color: #0d0e12;
        color: #e2e8f0;
    }
    .stSidebar {
        background-color: #151821 !important;
        border-right: 1px solid #272c3d;
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    .candidate-card {
        background-color: #171b26;
        border: 1px solid #2a3148;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .agent-trace-badge {
        background-color: #1e293b;
        color: #38bdf8;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-family: monospace;
        border: 1px solid #0284c7;
        display: inline-block;
        margin-bottom: 15px;
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "state" not in st.session_state:
    st.session_state.state = {
        "user_query": "",
        "intent": "",
        "conversation_history": [],
        "next_node": "",
        "raw_jd": "",
        "role": "",
        "required_skills": [],
        "experience_required": "",
        "location": "",
        "resumes_loaded": False,
        "total_candidates": 0,
        "matched_candidates": [],
        "shortlisted_candidates": [],
        "rewritten_jd": "",
        "interview_questions": {},
        "jd_feedback": "",
        "candidate_comparison": "",
        "red_flags": {},
        "salary_market_data": "",
        "company_salary_range": "",
        "skill_trends": [],
        "confirmation_required": False,
        "action_type": "",
        "recruiter_response": "",
        "response_message": ""
    }
    
    # Auto-load default Job Description text on startup (fast load without API call)
    jd_file = "data/jd/backend_jd.txt"
    if os.path.exists(jd_file):
        with open(jd_file, "r", encoding="utf-8") as f:
            st.session_state.state["raw_jd"] = f.read()
            
    # Set default values and candidate counts using fast Python OS calls
    resumes_dir = "data/resumes"
    if os.path.exists(resumes_dir):
        files = [f for f in os.listdir(resumes_dir) if f.endswith(".txt")]
        st.session_state.state["total_candidates"] = len(files)
        st.session_state.state["resumes_loaded"] = True

if "chat_history" not in st.session_state:
    # Set default welcoming message
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": "👋 **Welcome to HireFlow Agent!**\n\nTo start screening candidates, please first **parse your Job Description** (go to the **Active Job Description** tab and click **Parse Default JD** or paste your own!). After that, feel free to ask me to **'Find top candidates'**, compare profiles, prepare interview questions, or check market salary ranges!"
        }
    ]

# --- Helper Functions ---
def handle_query(query: str):
    if not query:
        return
    # Log user message
    st.session_state.chat_history.append({"role": "user", "content": query})
    st.session_state.state["user_query"] = query
    st.session_state.state["conversation_history"].append({"role": "user", "content": query})
    
    # Execute Graph
    st.session_state.state = graph.invoke(st.session_state.state)
    
    # Log assistant response
    response = st.session_state.state.get("response_message", "")
    # Remove CLI colors/formatting from markdown response if present
    response = clean_formatting(response)
    st.session_state.state["conversation_history"].append({"role": "assistant", "content": response})
    st.session_state.chat_history.append({"role": "assistant", "content": response})

def submit_confirmation(response_val: str):
    # Log recruiter response
    st.session_state.chat_history.append({"role": "user", "content": f"Confirmed: {response_val}"})
    st.session_state.state["recruiter_response"] = response_val
    st.session_state.state["user_query"] = response_val
    st.session_state.state["conversation_history"].append({"role": "user", "content": response_val})
    
    # Execute Graph
    st.session_state.state = graph.invoke(st.session_state.state)
    
    # Log response
    response = st.session_state.state.get("response_message", "")
    response = clean_formatting(response)
    st.session_state.state["conversation_history"].append({"role": "assistant", "content": response})
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.rerun()

def submit_cancel():
    st.session_state.state["confirmation_required"] = False
    st.session_state.state["action_type"] = ""
    st.session_state.state["recruiter_response"] = ""
    cancel_msg = "Action cancelled by recruiter."
    st.session_state.state["response_message"] = cancel_msg
    st.session_state.state["conversation_history"].append({"role": "assistant", "content": cancel_msg})
    st.session_state.chat_history.append({"role": "assistant", "content": cancel_msg})
    st.rerun()

def clean_formatting(text: str) -> str:
    # Remove all Rich style CLI formatting tags (e.g. [bold yellow], [cyan])
    text = re.sub(r"\[\/?([a-zA-Z0-9_\s#]+)\]", "", text)
    return text.strip()

def format_salary_response(text: str):
    # 1. Clean the text: remove markdown headers, excessive whitespace, image patterns
    clean_text = re.sub(r'#+\s*', '', text)  # remove ## etc
    clean_text = re.sub(r'Image\s*\d+:[^.\n]*', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'image\s*\d+:[^.\n]*', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # 2. Extract sources (domains)
    urls = re.findall(r'https?://(?:www\.)?([a-zA-Z0-9.-]+)(?:\S*)', text)
    unique_domains = []
    for domain in urls:
        # clean domain
        d = domain.split('/')[0].strip()
        if d and d not in unique_domains:
            # Format nicely
            if "ambitionbox" in d.lower():
                name = "AmbitionBox"
            elif "glassdoor" in d.lower():
                name = "Glassdoor"
            elif "indeed" in d.lower():
                name = "Indeed"
            elif "payscale" in d.lower():
                name = "PayScale"
            else:
                name = d.split('.')[0].capitalize()
            
            entry = f"{name} ({d})"
            if entry not in unique_domains:
                unique_domains.append(entry)
            
    # 3. Split into sentences and find useful insights
    sentences = re.split(r'(?<=[.!?])\s+', clean_text)
    insights = []
    seen = set()
    
    keywords = ["salary", "range", "average", "compensation", "lpa", "usd", "location", "l/yr", "lakhs", "₹", "$"]
    
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        # Remove raw URLs from sentence
        s_clean = re.sub(r'https?://\S+', '', s_clean).strip()
        # Remove excess punctuation or symbols
        s_clean = re.sub(r'[*_`#]', '', s_clean)
        s_clean = re.sub(r'\s+', ' ', s_clean)
        
        # Check if it has key terms and is not an image description or copyright note
        s_lower = s_clean.lower()
        if any(kw in s_lower for kw in keywords):
            if "image" not in s_lower and "unlock background" not in s_lower and "monthly in-hand" not in s_lower:
                if len(s_clean) > 25 and len(s_clean) < 300 and s_lower not in seen:
                    # Clean starting hyphens if any
                    s_clean = re.sub(r'^[-\s•*]+', '', s_clean)
                    insights.append(s_clean)
                    seen.add(s_lower)
                    
    # Limit insights count
    insights = insights[:4]
    
    # 4. Extract or guess market range
    # Search for ranges like "₹39.2 Lakhs to ₹57.8 Lakhs" or "₹15 LPA - ₹40 LPA"
    range_match = re.search(r'(?:Rs\.?|₹|\$)\s?\d+(?:\.\d+)?\s?(?:LPA|L|Lakhs?|k|M|million|thousand|yr|/yr)?\s?(?:-|to)\s?(?:Rs\.?|₹|\$)?\s?\d+(?:\.\d+)?\s?(?:LPA|L|Lakhs?|k|M|million|thousand|yr|/yr)?', clean_text, re.IGNORECASE)
    if range_match:
        market_range = range_match.group(0)
    else:
        # Check if we can find any Lakhs/LPA numbers
        lakhs_match = re.findall(r'(?:Rs\.?|₹|\$)?\s?\d+(?:\.\d+)?\s?(?:LPA|Lakhs?)', clean_text, re.IGNORECASE)
        if len(lakhs_match) >= 2:
            market_range = f"{lakhs_match[0]} - {lakhs_match[1]}"
        elif len(lakhs_match) == 1:
            market_range = f"{lakhs_match[0]} (Average)"
        else:
            market_range = "₹15 LPA - ₹40 LPA (Estimated)"
        
    return {
        "market_range": market_range,
        "insights": insights,
        "sources": unique_domains[:3]
    }

def render_formatted_salary(raw_text: str):
    role = st.session_state.state.get("role") or "Machine Learning Engineer"
    location = st.session_state.state.get("location") or "Bengaluru"
    
    # Format the data
    formatted = format_salary_response(raw_text)
    
    st.markdown("### 💰 Salary Market Research")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Role:**\n{role}")
    with col2:
        st.info(f"**Location:**\n{location}")
        
    st.metric(label="Market Range", value=formatted["market_range"])
    
    st.markdown("**Key Insights:**")
    if formatted["insights"]:
        for insight in formatted["insights"]:
            st.markdown(f"• {insight}")
    else:
        st.markdown(f"• Standard compensation package for a {role} role in {location} location.")
        
    st.markdown("**Sources:**")
    if formatted["sources"]:
        for i, source in enumerate(formatted["sources"], 1):
            st.markdown(f"{i}. {source}")
    else:
        st.markdown("1. Search Engine Results")
        
    # Expander showing original complete response
    with st.expander("🔍 View raw Tavily data"):
        st.text(raw_text)

# --- SIDEBAR: SYSTEM STATUS DASHBOARD ---
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/null/artificial-intelligence.png", width=70)
    st.title("HireFlow Status")
    st.markdown("---")
    
    # Display state attributes
    role = st.session_state.state.get("role") or "Not Parsed"
    st.markdown(f"**Parsed Role:**\n`{role}`")
    
    skills = st.session_state.state.get("required_skills", [])
    skills_text = ", ".join(skills) if skills else "None"
    st.markdown(f"**Required Skills:**\n`{skills_text}`")
    
    resume_count = st.session_state.state.get("total_candidates", 0)
    st.metric(label="Resumes in Database", value=resume_count)
    
    shortlisted = st.session_state.state.get("shortlisted_candidates", [])
    st.markdown("**Shortlisted Candidates:**")
    if shortlisted:
        for c in shortlisted:
            st.markdown(f"- 🎓 **{c['name']}** ({c['score']}% match)")
    else:
        st.caption("No candidates shortlisted yet.")
        
    budget = st.session_state.state.get("company_salary_range") or "Not Set"
    st.markdown(f"**Company Salary Budget:**\n`{budget}`")
    
    st.markdown("---")
    # Quick Commands Manual
    st.markdown("### 💡 Quick Inputs")
    st.caption("- 'Find top candidates'")
    st.caption("- 'What is the salary expectation?'")
    st.caption("- 'Compare Rahul and Priya'")
    st.caption("- 'Generate interview questions for Rohan'")
    st.caption("- 'Show red flags for Vikram'")
    
    if st.button("Reset Session State", use_container_width=True):
        st.session_state.state = {
            "user_query": "",
            "intent": "",
            "conversation_history": [],
            "next_node": "",
            "raw_jd": "",
            "role": "",
            "required_skills": [],
            "experience_required": "",
            "location": "",
            "resumes_loaded": True,
            "total_candidates": resume_count,
            "matched_candidates": [],
            "shortlisted_candidates": [],
            "rewritten_jd": "",
            "interview_questions": {},
            "jd_feedback": "",
            "candidate_comparison": "",
            "red_flags": {},
            "salary_market_data": "",
            "company_salary_range": "",
            "skill_trends": [],
            "confirmation_required": False,
            "action_type": "",
            "recruiter_response": "",
            "response_message": ""
        }
        st.session_state.chat_history = [
            {"role": "assistant", "content": "🔄 System state reset. Job Description cached. Ready for query inputs!"}
        ]
        st.rerun()

# --- MAIN CONTENT AREA ---
st.title("💼 HireFlow Agent")
st.caption("Agentic AI Assistant managing recruitment pipelines with RAG semantic scoring & recruiter safeguards")

# Determine active workflow trace
trace_steps = ["Router"]
intent = st.session_state.state.get("intent")
intent_to_label = {
    "parse_jd": "JD Parser",
    "load_resumes": "Resume Loader",
    "count_applicants": "Applicant Counter",
    "match_candidates": "Candidate Matching",
    "jd_rewrite": "JD Rewrite",
    "interview_questions": "Interview Generator",
    "salary_research": "Salary Research",
    "compare_candidates": "Candidate Comparison",
    "red_flags": "Red Flags Scan",
    "help": "Help Node",
    "unknown": "Help Node"
}
if intent in intent_to_label:
    trace_steps.append(intent_to_label[intent])
if st.session_state.state.get("confirmation_required"):
    trace_steps.append("Human Approval Gate")

trace_display = " ➔ ".join(trace_steps)
st.markdown(f"<div class='agent-trace-badge'>Workflow Route: {trace_display}</div>", unsafe_allow_html=True)

# Main Navigation Tabs
tab1, tab2, tab3 = st.tabs(["💬 Conversation Hub", "🎯 Ranked Match Candidates", "📄 Active Job Description"])

# --- TAB 1: CONVERSATION HUB ---
with tab1:
    # Display Confirmation alert at top of chat if pending
    confirmation_required = st.session_state.state.get("confirmation_required", False)
    action_type = st.session_state.state.get("action_type", "")
    
    if confirmation_required:
        if action_type == "salary_budget":
            st.warning("⚠️ **Recruiter Action Confirmation Required**")
            raw_data = st.session_state.state.get("salary_market_data", "")
            render_formatted_salary(raw_data)
            
            st.markdown("### 👤 Recruiter Decision Required")
            budget_val = st.text_input("Enter your company salary budget range:", placeholder="e.g. $130,000 - $160,000 or 15 - 20 LPA", key="budget_input_field")
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Save Budget", type="primary", use_container_width=True):
                    if budget_val:
                        submit_confirmation(budget_val)
            with col2:
                if st.button("Cancel Operation", use_container_width=True):
                    submit_cancel()
        else:
            st.warning("⚠️ **Recruiter Action Confirmation Required**")
            confirm_text = clean_formatting(st.session_state.state.get("response_message", ""))
            st.markdown(confirm_text)
            
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("Approve (YES)", type="primary", use_container_width=True):
                    submit_confirmation("YES")
            with col2:
                if st.button("Reject (NO)", type="secondary", use_container_width=True):
                    submit_confirmation("NO")
            with col3:
                if st.button("Cancel Action", use_container_width=True):
                    submit_cancel()
        st.markdown("---")

    # Chat Display
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and "Market Salary Research for" in msg["content"]:
                raw_data = st.session_state.state.get("salary_market_data", "")
                if raw_data:
                    render_formatted_salary(raw_data)
                else:
                    st.markdown(msg["content"])
            else:
                st.markdown(msg["content"])
            
    # Chat Input (Enabled only when no approval is pending)
    if not confirmation_required:
        if prompt := st.chat_input("Ask HireFlow Agent a task..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            handle_query(prompt)
            st.rerun()

# --- TAB 2: CANDIDATE MATCHING CARDS ---
with tab2:
    matched = st.session_state.state.get("matched_candidates", [])
    if matched:
        st.subheader("Ranked Candidates (RAG Matchmaking Search)")
        for i, c in enumerate(matched, 1):
            st.markdown(f"""
            <div class="candidate-card">
                <h4 style="margin: 0 0 8px 0; color: #38bdf8;">{i}. {c.get('name', 'Unknown')}</h4>
                <p style="margin: 0 0 12px 0; font-size: 14px; color: #94a3b8;">Filepath: {c.get('filepath', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress bar for score
            score = c.get("score", 0)
            st.progress(score / 100.0, text=f"Match Score: {score}%")
            
            # Display matching/missing skills
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"**Matched Skills:**\n{', '.join(c.get('matched_skills', [])) or 'None'}")
            with col2:
                st.error(f"**Missing Skills:**\n{', '.join(c.get('missing_skills', [])) or 'None'}")
                
            # Display reasoning text
            st.info(f"**AI Reasoning:**\n{c.get('reasoning', '')}")
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("No candidates matches screened yet. Ask the agent **'Find top candidates'** in the chat to screen applicants.")

# --- TAB 3: ACTIVE JOB DESCRIPTION ---
with tab3:
    st.subheader("Current Parsed Job Description")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Parsed JD Requirements:**")
        st.markdown(f"- **Parsed Role:** {role}")
        st.markdown(f"- **Parsed Skills:** {skills_text}")
        st.markdown(f"- **Parsed Experience:** {st.session_state.state.get('experience_required') or 'Not Set'}")
        st.markdown(f"- **Parsed Location:** {st.session_state.state.get('location') or 'Not Set'}")
        
        st.markdown("---")
        st.text_area("Source JD Document", value=st.session_state.state.get("raw_jd", ""), height=300, disabled=True)
        if st.button("Parse Default JD (Gemini)", use_container_width=True):
            with st.spinner("Parsing job description..."):
                from agents.nodes import jd_parser_node
                parsed = jd_parser_node(st.session_state.state)
                st.session_state.state.update(parsed)
                st.success("Default Job Description parsed successfully!")
                st.rerun()
    with col2:
        st.markdown("📝 **Upload a Job Description**")
        jd_input = st.text_area("Paste new Job Description text here:", height=250)
        if st.button("Parse Job Description", type="primary", use_container_width=True):
            if jd_input:
                # Set raw JD in state
                st.session_state.state["raw_jd"] = jd_input
                # Run parser node
                from agents.nodes import jd_parser_node
                parsed = jd_parser_node(st.session_state.state)
                st.session_state.state.update(parsed)
                st.success("New Job Description parsed successfully!")
                st.rerun()
