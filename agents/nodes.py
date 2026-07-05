import os
import re
import google.generativeai as genai
from agents.state import AgentState
from tools.rag_tool import RAGTool
from tools.salary_tool import SalaryTool
from models.schemas import (
    JobDescriptionSchema,
    CandidateMatchSchema,
    CandidateComparisonSchema,
    RedFlagsSchema,
    RouterOutput
)

# -----------------
# 1. ROUTER NODE
# -----------------
def normalize_text(text: str) -> str:
    text = text.lower().strip()
    # Remove symbols/punctuation
    text = re.sub(r"[^\w\s]", "", text)
    # Correct common typos
    typo_map = {
        "canditate": "candidate",
        "canditates": "candidates",
        "aplicant": "applicant",
        "aplicants": "applicants",
    }
    words = text.split()
    normalized_words = [typo_map.get(w, w) for w in words]
    return " ".join(normalized_words)

def print_debug_trace(query: str, normalized: str, method: str, intent: str):
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    trace = f"""[bold]Input[/bold]: "{query}"
[bold]Normalized[/bold]: "{normalized}"
[bold]Method[/bold]: {method}
[bold]Intent[/bold]: {intent}"""
    console.print(Panel(trace, title="[bold yellow]Router Debug Trace[/bold yellow]", border_style="yellow"))

def router_node(state: AgentState) -> dict:
    """Decides the intent and determines the next node to execute using a 3-level hybrid router."""
    from rapidfuzz import fuzz
    
    query = state.get("user_query", "").strip()
    
    # If confirmation is pending, route directly to human approval node
    if state.get("confirmation_required"):
        return {
            "intent": "human_response",
            "next_node": "human_approval"
        }
        
    normalized = normalize_text(query)
    
    # Define patterns
    INTENT_PATTERNS = {
        "match_candidates": [
            "find candidates",
            "top candidates",
            "best candidates",
            "rank resumes",
            "screen resumes",
            "match applicants",
            "who should i hire",
            "best profiles",
            "shortlist people",
            "find talent",
            "show me best candidates",
            "show top candidates",
            "best candidates"
        ],
        "applicant_counter": [
            "how many applicants",
            "total resumes",
            "number of candidates",
            "candidate count",
            "how many people applied",
            "how many applicant",
            "how many candidates",
            "count applicants"
        ],
        "salary_research": [
            "salary expectation",
            "market salary",
            "pay range",
            "compensation",
            "package",
            "ctc",
            "how much salary",
            "what package should we offer"
        ],
        "interview_generator": [
            "generate questions",
            "interview questions",
            "prepare interview",
            "ask candidate",
            "technical questions",
            "make questions"
        ],
        "jd_rewrite": [
            "rewrite jd",
            "improve job description",
            "make jd better",
            "change tone",
            "startup version"
        ],
        "candidate_comparison": [
            "compare candidates",
            "compare profiles",
            "who is better",
            "difference between candidates"
        ],
        "red_flags": [
            "find red flags",
            "candidate issues",
            "employment gaps",
            "resume problems",
            "risks",
            "any problems in his resume"
        ],
        "load_resumes": [
            "load resumes",
            "ingest resumes",
            "import resumes"
        ],
        "parse_jd": [
            "parse jd",
            "read jd",
            "parse job description",
            "read job description",
            "load jd",
            "parse active"
        ]
    }
    
    INTENT_TO_NODE = {
        "match_candidates": "candidate_matching",
        "applicant_counter": "applicant_counter",
        "salary_research": "salary_research",
        "interview_generator": "interview_generator",
        "jd_rewrite": "jd_rewrite",
        "candidate_comparison": "candidate_comparison",
        "red_flags": "red_flag_node",
        "load_resumes": "resume_loader",
        "parse_jd": "jd_parser"
    }

    # Level 1: Fast Keyword Match
    for intent, phrases in INTENT_PATTERNS.items():
        for phrase in phrases:
            # Check containment
            if phrase in normalized or normalized in phrase:
                node = INTENT_TO_NODE[intent]
                print_debug_trace(query, normalized, "Keyword Match", intent)
                return {
                    "intent": intent,
                    "next_node": node
                }
                
    # Level 2: Fuzzy Matching
    best_score = 0
    best_intent = None
    
    for intent, phrases in INTENT_PATTERNS.items():
        for phrase in phrases:
            score_ratio = fuzz.ratio(normalized, phrase)
            score_wratio = fuzz.WRatio(normalized, phrase)
            score = max(score_ratio, score_wratio)
            
            if score > best_score:
                best_score = score
                best_intent = intent
                
    if best_score > 75:
        node = INTENT_TO_NODE[best_intent]
        print_debug_trace(query, normalized, f"Fuzzy Match (Score: {best_score:.1f}%)", best_intent)
        return {
            "intent": best_intent,
            "next_node": node
        }
        
    # Level 3: Gemini Intent Classification Fallback
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print_debug_trace(query, normalized, "Fallback Help (API key missing)", "unknown")
        return {
            "intent": "unknown",
            "next_node": "help_node"
        }
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""You are an intent classifier for a recruitment assistant.
Classify this recruiter request:
"{query}"

Choose exactly one of these intents:
- parse_jd
- load_resumes
- count_applicants
- match_candidates
- rewrite_jd
- interview_questions
- salary_research
- compare_candidates
- red_flags
- help

Return only the intent name as plain text (no markdown formatting, no quotes)."""
    try:
        response = model.generate_content(prompt)
        raw_intent = response.text.strip().lower()
        
        # Strip any formatting/quotes
        raw_intent = re.sub(r"[^\w_]", "", raw_intent)
        
        intent_node_map = {
            "parse_jd": "jd_parser",
            "load_resumes": "resume_loader",
            "count_applicants": "applicant_counter",
            "match_candidates": "candidate_matching",
            "rewrite_jd": "jd_rewrite",
            "interview_questions": "interview_generator",
            "salary_research": "salary_research",
            "compare_candidates": "candidate_comparison",
            "red_flags": "red_flag_node",
            "help": "help_node"
        }
        
        # Clean response matching
        matched_intent = None
        for key in intent_node_map.keys():
            if key in raw_intent:
                matched_intent = key
                break
                
        if matched_intent:
            node = intent_node_map[matched_intent]
            print_debug_trace(query, normalized, "Gemini Classifier", matched_intent)
            return {
                "intent": matched_intent,
                "next_node": node
            }
        else:
            print_debug_trace(query, normalized, "Gemini Classifier Fallback", "unknown")
            return {
                "intent": "unknown",
                "next_node": "help_node"
            }
    except Exception as e:
        print_debug_trace(query, normalized, f"Router Error Fallback ({str(e)})", "unknown")
        return {
            "intent": "unknown",
            "next_node": "help_node"
        }


# -----------------
# 2. HELP NODE
# -----------------
def help_node(state: AgentState) -> dict:
    """Helper node that provides guidance on using the recruitment assistant."""
    help_message = """I can assist you with these recruitment tasks:
1. **Parse JD**: Paste a Job Description to parse role, skills, experience, and location constraints.
2. **Load Resumes**: Ingest resumes from `data/resumes/` into the vector database.
3. **Count Applicants**: Ask 'How many applicants?' to check total candidates.
4. **Screen/Find Candidates**: Ask 'Find top candidates' to run a semantic RAG search and match them to the JD.
5. **Compare Candidates**: Ask 'Compare Rahul and Priya' for a head-to-head comparison.
6. **Rewrite JD**: Ask 'Rewrite this JD for startup/friendly/corporate' to rewrite the parsed job description.
7. **Salary Research**: Ask 'What is the salary expectation?' to query current market rates and set your budget.
8. **Interview Questions**: Ask 'Generate interview questions for Rahul' to create tailored candidate interview guides.
9. **Red Flags**: Ask 'Show red flags for Rohan' to scan for employment gaps.
10. **JD Mismatch**: Ask 'Show JD candidate mismatch' to evaluate candidate pool experience levels.
"""
    return {
        "response_message": help_message,
        "next_node": ""
    }


# -----------------
# 3. JD PARSER NODE
# -----------------
def jd_parser_node(state: AgentState) -> dict:
    """Parses raw JD text using Gemini structured output."""
    raw_jd = state.get("raw_jd", "").strip()
    if not raw_jd:
        # Check if default file exists
        default_path = "data/jd/backend_jd.txt"
        if os.path.exists(default_path):
            with open(default_path, "r", encoding="utf-8") as f:
                raw_jd = f.read()
        else:
            return {
                "response_message": "No Job Description found in state. Please provide a JD or create `data/jd/backend_jd.txt`.",
                "next_node": ""
            }
            
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "response_message": "Gemini API Key is missing. Cannot parse JD.",
            "next_node": ""
        }
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""Analyze the following Job Description (JD) text and extract details as structured JSON:
- role: Job title
- required_skills: Key technical skills (list of strings)
- experience_required: Experience constraints (e.g., "5+ years", "Mid-level")
- location: Location constraints (e.g. San Francisco, CA (Hybrid), Remote)

JD Text:
{raw_jd}
"""
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": JobDescriptionSchema
            }
        )
        parsed = JobDescriptionSchema.model_validate_json(response.text)
        
        msg = f"""[bold green]Parsed Job Description successfully![/bold green]
- **Role**: {parsed.role}
- **Required Skills**: {', '.join(parsed.required_skills)}
- **Experience Required**: {parsed.experience_required}
- **Location**: {parsed.location}
"""
        return {
            "raw_jd": raw_jd,
            "role": parsed.role,
            "required_skills": parsed.required_skills,
            "experience_required": parsed.experience_required,
            "location": parsed.location,
            "response_message": msg,
            "next_node": ""
        }
    except Exception as e:
        return {
            "response_message": f"Failed parsing JD with LLM: {str(e)}",
            "next_node": ""
        }


# -----------------
# 4. RESUME LOADER NODE
# -----------------
def resume_loader_node(state: AgentState) -> dict:
    """Loads resumes into the ChromaDB vector database."""
    rag = RAGTool()
    resumes_dir = "data/resumes"
    count = rag.index_resumes(resumes_dir)
    
    msg = f"Indexed {count} resumes from `{resumes_dir}/` into the vector database successfully using `sentence-transformers/all-MiniLM-L6-v2` embeddings."
    return {
        "resumes_loaded": True,
        "total_candidates": count,
        "response_message": msg,
        "next_node": ""
    }


# -----------------
# 5. APPLICANT COUNTER NODE
# -----------------
def applicant_counter_node(state: AgentState) -> dict:
    """Calculates total candidates using basic Python logic without calling Gemini."""
    resumes_dir = "data/resumes"
    count = 0
    if os.path.exists(resumes_dir):
        files = [f for f in os.listdir(resumes_dir) if f.endswith(".txt")]
        count = len(files)
        
    msg = f"There are currently {count} candidate applications registered in `data/resumes/`."
    return {
        "total_candidates": count,
        "response_message": msg,
        "next_node": ""
    }


# -----------------
# 6. CANDIDATE MATCHING NODE (RAG Screening)
# -----------------
def candidate_matching_node(state: AgentState) -> dict:
    """Screen candidates using ChromaDB and rank using Gemini structured scoring."""
    role = state.get("role", "")
    skills = state.get("required_skills", [])
    
    if not role or not skills:
        return {
            "response_message": "Please parse a Job Description first (e.g. paste JD or load default JD) before screening candidates.",
            "next_node": ""
        }
        
    rag = RAGTool()
    # Search ChromaDB
    query_text = f"Role: {role}. Skills: {', '.join(skills)}"
    raw_matches = rag.search_candidates(query_text, n_results=5)
    
    if not raw_matches:
        return {
            "response_message": "No matching candidates found. Make sure resumes are loaded first.",
            "next_node": ""
        }
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "response_message": "Gemini API Key is missing. Cannot perform screening analysis.",
            "next_node": ""
        }
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    analyzed_candidates = []
    
    for candidate in raw_matches:
        resume_text = candidate["resume_text"]
        name = candidate["name"]
        
        prompt = f"""You are an expert recruiter. Grade the candidate's compatibility for the position.
Position Requirements:
- Role: {role}
- Required Skills: {', '.join(skills)}

Candidate Resume:
{resume_text}

Analyze and return JSON matching CandidateMatchSchema:
- candidate_name: {name}
- match_score: (integer 0-100 indicating fit, alignment of skills and experience)
- matched_skills: (skills from JD that candidate has)
- missing_skills: (skills from JD that candidate is missing)
- reasoning: (brief evaluation of strengths and weakness)
"""
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": CandidateMatchSchema
                }
            )
            analyzed = CandidateMatchSchema.model_validate_json(response.text)
            
            candidate_details = {
                "name": analyzed.candidate_name,
                "score": analyzed.match_score,
                "matched_skills": analyzed.matched_skills,
                "missing_skills": analyzed.missing_skills,
                "reasoning": analyzed.reasoning,
                "filepath": candidate["filepath"]
            }
            analyzed_candidates.append(candidate_details)
        except Exception as e:
            # Fallback to vector database score if LLM fails
            analyzed_candidates.append({
                "name": name,
                "score": candidate["score"],
                "matched_skills": [],
                "missing_skills": [],
                "reasoning": "Fallback analysis due to LLM error.",
                "filepath": candidate["filepath"]
            })
            
    # Sort candidates by score descending
    analyzed_candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # Propose top 2 candidates for shortlisting
    top_candidates = [c["name"] for c in analyzed_candidates[:2]]
    
    proposal_text = f"[bold yellow]Candidates Match Screening Complete[/bold yellow]\nHere are the ranked candidate matches:\n"
    for idx, c in enumerate(analyzed_candidates):
        proposal_text += f"\n{idx+1}. **{c['name']}** - Match Score: [bold cyan]{c['score']}%[/bold cyan]"
        proposal_text += f"\n   *Matched Skills*: {', '.join(c['matched_skills']) if c['matched_skills'] else 'None'}"
        proposal_text += f"\n   *Missing Skills*: {', '.join(c['missing_skills']) if c['missing_skills'] else 'None'}"
        proposal_text += f"\n   *Reason*: {c['reasoning']}\n"
        
    proposal_text += f"\n[bold yellow]Action Required:[/bold yellow] I recommend shortlisting **{', '.join(top_candidates)}**.\nDo you approve shortlisting these candidates? (YES/NO)"
    
    return {
        "matched_candidates": analyzed_candidates,
        "confirmation_required": True,
        "action_type": "shortlist",
        "next_node": "human_approval",
        "response_message": proposal_text
    }


# -----------------
# 7. JD REWRITE NODE
# -----------------
def jd_rewrite_node(state: AgentState) -> dict:
    """Rewrites the job description tone using Gemini."""
    role = state.get("role", "")
    skills = state.get("required_skills", [])
    raw_jd = state.get("raw_jd", "")
    user_query = state.get("user_query", "")
    
    if not raw_jd:
        return {
            "response_message": "No Job Description loaded. Please parse a JD first.",
            "next_node": ""
        }
        
    # Detect requested tone from query
    tone = "Startup"
    if "friendly" in user_query.lower():
        tone = "Friendly"
    elif "corporate" in user_query.lower() or "professional" in user_query.lower():
        tone = "Corporate/Professional"
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "response_message": "Gemini API Key is missing. Cannot rewrite JD.",
            "next_node": ""
        }
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""Rewrite the following Job Description (JD) to match a "{tone}" tone.
Retain all original requirements:
- Role: {role}
- Skills: {', '.join(skills)}
- Location: {state.get('location', '')}
- Experience Required: {state.get('experience_required', '')}

Original JD:
{raw_jd}

Return the rewritten JD text.
"""
    try:
        response = model.generate_content(prompt)
        rewritten = response.text.strip()
        
        msg = f"""[bold yellow]JD Rewrite Draft ({tone} Tone)[/bold yellow]:
==================================================
{rewritten}
==================================================

[bold yellow]Action Required:[/bold yellow] Do you approve this JD modification? (YES/NO)
"""
        return {
            "rewritten_jd": rewritten,
            "confirmation_required": True,
            "action_type": "rewrite_jd",
            "next_node": "human_approval",
            "response_message": msg
        }
    except Exception as e:
        return {
            "response_message": f"Failed rewriting JD with LLM: {str(e)}",
            "next_node": ""
        }


# -----------------
# 8. INTERVIEW QUESTION NODE
# -----------------
def interview_generator_node(state: AgentState) -> dict:
    """Generates personalized technical and behavioral interview questions for a candidate."""
    query = state.get("user_query", "").lower()
    
    # Extract candidate name from query
    target_candidate = None
    resumes_list = state.get("matched_candidates", [])
    if not resumes_list:
        resumes_dir = "data/resumes"
        if os.path.exists(resumes_dir):
            files = [f for f in os.listdir(resumes_dir) if f.endswith(".txt")]
            resumes_list = [{"name": f.replace(".txt", "").replace("_", " ").title()} for f in files]
            
    for c in resumes_list:
        name_parts = c["name"].lower().split()
        if any(part in query for part in name_parts if len(part) > 2):
            target_candidate = c["name"]
            break
            
    # Default to the first candidate in matches if not specified
    if not target_candidate:
        if state.get("matched_candidates"):
            target_candidate = state.get("matched_candidates")[0]["name"]
        else:
            return {
                "response_message": "Please specify a candidate name for questions (e.g. 'Generate interview questions for Rahul').",
                "next_node": ""
            }
            
    # Retrieve resume text
    resume_text = ""
    for c in state.get("matched_candidates", []):
        if c["name"].lower() == target_candidate.lower():
            if os.path.exists(c["filepath"]):
                with open(c["filepath"], "r", encoding="utf-8") as f:
                    resume_text = f.read()
            break
            
    if not resume_text:
        resumes_dir = "data/resumes"
        for file in os.listdir(resumes_dir):
            filepath = os.path.join(resumes_dir, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            if target_candidate.lower() in content.lower():
                resume_text = content
                break
                
    if not resume_text:
        return {
            "response_message": f"Could not find resume text for candidate {target_candidate}.",
            "next_node": ""
        }
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "response_message": "Gemini API Key is missing. Cannot generate questions.",
            "next_node": ""
        }
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    role = state.get("role", "Backend Engineer")
    skills = state.get("required_skills", [])
    
    prompt = f"""You are a senior technical interviewer. Generate personalized interview questions for {target_candidate} applying for the {role} position.
Job requirements:
- Required skills: {', '.join(skills)}

Candidate resume:
{resume_text}

Generate:
1. Three Technical Questions (deep-diving into candidate's listed skills matching our requirements)
2. Two Project Questions (asking about specific projects on their resume)
3. One Experience/Behavioral Question (focusing on their experience level)

Format output clearly.
"""
    try:
        response = model.generate_content(prompt)
        questions_text = response.text.strip()
        
        iq = state.get("interview_questions", {})
        if not iq:
            iq = {}
        iq[target_candidate] = questions_text.split("\n")
        
        msg = f"""[bold green]Generated Interview Guide for {target_candidate}[/bold green]
Role: {role}
==================================================
{questions_text}
==================================================
"""
        return {
            "interview_questions": iq,
            "response_message": msg,
            "next_node": ""
        }
    except Exception as e:
        return {
            "response_message": f"Failed generating interview questions: {e}",
            "next_node": ""
        }


# -----------------
# 9. SALARY RESEARCH NODE
# -----------------
def salary_research_node(state: AgentState) -> dict:
    """Uses Tavily to search salary rates, then triggers human confirmation for budget."""
    role = state.get("role", "Backend Engineer")
    location = state.get("location", "San Francisco, CA")
    
    # 1. Web search market rates
    salary_tool = SalaryTool()
    search_data = salary_tool.search_salary_data(role, location)
    
    msg = f"""[bold yellow]Market Salary Research for {role} in {location}[/bold yellow]
{search_data}

[bold yellow]Company Budget Confirmation Required:[/bold yellow]
What is your company's salary budget range for this position? (e.g. $120,000 - $150,000 or 15 - 20 LPA)
"""
    return {
        "salary_market_data": search_data,
        "confirmation_required": True,
        "action_type": "salary_budget",
        "next_node": "human_approval",
        "response_message": msg
    }


# -----------------
# 10. CANDIDATE COMPARISON NODE
# -----------------
def candidate_comparison_node(state: AgentState) -> dict:
    """Performs structured candidate comparison using Gemini."""
    query = state.get("user_query", "").lower()
    
    available_names = []
    resumes_dir = "data/resumes"
    if os.path.exists(resumes_dir):
        for file in os.listdir(resumes_dir):
            filepath = os.path.join(resumes_dir, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            for line in content.splitlines():
                if line.lower().startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                    available_names.append((name, content))
                    break
                    
    to_compare = []
    for name, resume in available_names:
        name_parts = name.lower().split()
        if any(part in query for part in name_parts if len(part) > 2):
            to_compare.append((name, resume))
            
    # Default to top 2 candidates if none specified
    if len(to_compare) < 2:
        matched = state.get("matched_candidates", [])
        if len(matched) >= 2:
            to_compare = []
            for c in matched[:2]:
                if os.path.exists(c["filepath"]):
                    with open(c["filepath"], "r", encoding="utf-8") as f:
                        to_compare.append((c["name"], f.read()))
        else:
            return {
                "response_message": "Please specify at least two candidates to compare (e.g. 'Compare Rahul and Priya') or ensure you run candidates match search first.",
                "next_node": ""
            }
            
    name1, resume1 = to_compare[0]
    name2, resume2 = to_compare[1]
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "response_message": "Gemini API Key is missing. Cannot compare candidates.",
            "next_node": ""
        }
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    role = state.get("role", "Backend Engineer")
    skills = state.get("required_skills", [])
    
    prompt = f"""Compare these two candidates head-to-head for the role of {role} (Required Skills: {', '.join(skills)}):

Candidate 1: {name1}
Resume:
{resume1}

Candidate 2: {name2}
Resume:
{resume2}

Analyze and return JSON matching CandidateComparisonSchema.
"""
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": CandidateComparisonSchema
            }
        )
        parsed = CandidateComparisonSchema.model_validate_json(response.text)
        
        # Safely extract strengths and weaknesses checking keys length first
        keys_str = list(parsed.strengths.keys())
        keys_weak = list(parsed.weaknesses.keys())
        
        strengths1 = parsed.strengths.get(name1, [])
        if not strengths1 and len(keys_str) > 0:
            strengths1 = parsed.strengths.get(keys_str[0], [])
            
        strengths2 = parsed.strengths.get(name2, [])
        if not strengths2 and len(keys_str) > 1:
            strengths2 = parsed.strengths.get(keys_str[1], [])
            
        weaknesses1 = parsed.weaknesses.get(name1, [])
        if not weaknesses1 and len(keys_weak) > 0:
            weaknesses1 = parsed.weaknesses.get(keys_weak[0], [])
            
        weaknesses2 = parsed.weaknesses.get(name2, [])
        if not weaknesses2 and len(keys_weak) > 1:
            weaknesses2 = parsed.weaknesses.get(keys_weak[1], [])
        
        msg = f"""[bold yellow]Head-to-Head Comparison: {name1} vs {name2}[/bold yellow]

**Summary**:
{parsed.comparison_summary}

**Strengths**:
- **{name1}**: {', '.join(strengths1)}
- **{name2}**: {', '.join(strengths2)}

**Weaknesses / Concerns**:
- **{name1}**: {', '.join(weaknesses1)}
- **{name2}**: {', '.join(weaknesses2)}

[bold green]Final Recommendation[/bold green]:
{parsed.final_recommendation}
"""
        return {
            "candidate_comparison": msg,
            "response_message": msg,
            "next_node": ""
        }
    except Exception as e:
        return {
            "response_message": f"Failed comparing candidates: {e}",
            "next_node": ""
        }


# -----------------
# 11. RED FLAGS NODE
# -----------------
def red_flag_node(state: AgentState) -> dict:
    """Scans candidate resumes for potential anomalies or timeline gaps using Gemini."""
    query = state.get("user_query", "").lower()
    
    target_candidate = None
    matched = state.get("matched_candidates", [])
    if not matched:
        resumes_dir = "data/resumes"
        if os.path.exists(resumes_dir):
            files = [f for f in os.listdir(resumes_dir) if f.endswith(".txt")]
            matched = [{"name": f.replace(".txt", "").replace("_", " ").title()} for f in files]
            
    for c in matched:
        name_parts = c["name"].lower().split()
        if any(part in query for part in name_parts if len(part) > 2):
            target_candidate = c["name"]
            break
            
    if not target_candidate:
        if state.get("matched_candidates"):
            target_candidate = state.get("matched_candidates")[0]["name"]
        else:
            return {
                "response_message": "Please specify candidate name to analyze red flags (e.g. 'Show red flags for Rohan').",
                "next_node": ""
            }
            
    resume_text = ""
    for c in state.get("matched_candidates", []):
        if c["name"].lower() == target_candidate.lower():
            if os.path.exists(c["filepath"]):
                with open(c["filepath"], "r", encoding="utf-8") as f:
                    resume_text = f.read()
            break
            
    if not resume_text:
        resumes_dir = "data/resumes"
        for file in os.listdir(resumes_dir):
            filepath = os.path.join(resumes_dir, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            if target_candidate.lower() in content.lower():
                resume_text = content
                break
                
    if not resume_text:
        return {
            "response_message": f"Could not find resume text for candidate {target_candidate}.",
            "next_node": ""
        }
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "response_message": "Gemini API Key is missing. Cannot check red flags.",
            "next_node": ""
        }
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""Review the following candidate's resume for any red flags, such as:
- Employment gaps
- Missing skills relative to typical backend roles
- Inconsistent timeline info
- Short job tenures

Candidate: {target_candidate}
Resume:
{resume_text}

Analyze and return JSON matching RedFlagsSchema.
"""
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": RedFlagsSchema
            }
        )
        parsed = RedFlagsSchema.model_validate_json(response.text)
        
        flag_status = "[bold red]RED FLAGS DETECTED[/bold red]" if parsed.has_red_flags else "[bold green]NO RED FLAGS DETECTED[/bold green]"
        
        msg = f"""[bold yellow]Resume Red Flags Analysis: {target_candidate}[/bold yellow]
Status: {flag_status}

**Flags Identified**:
"""
        if parsed.red_flags:
            for flag in parsed.red_flags:
                msg += f"- {flag}\n"
        else:
            msg += "- None\n"
            
        msg += f"\n**Explanation**: {parsed.explanation}"
        
        rf = state.get("red_flags", {})
        if not rf:
            rf = {}
        rf[target_candidate] = parsed.red_flags
        
        return {
            "red_flags": rf,
            "response_message": msg,
            "next_node": ""
        }
    except Exception as e:
        return {
            "response_message": f"Failed analyzing red flags with LLM: {e}",
            "next_node": ""
        }


# -----------------
# 12. JD MISMATCH NODE
# -----------------
def jd_mismatch_node(state: AgentState) -> dict:
    """Analyzes requirements constraints relative to candidate database profiles."""
    role = state.get("role", "")
    skills = state.get("required_skills", [])
    exp_req = state.get("experience_required", "")
    
    if not role or not skills:
        return {
            "response_message": "Please parse a Job Description first to perform mismatch analysis.",
            "next_node": ""
        }
        
    resumes_dir = "data/resumes"
    all_resumes = []
    if os.path.exists(resumes_dir):
        for file in os.listdir(resumes_dir):
            filepath = os.path.join(resumes_dir, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            all_resumes.append(content[:600]) # Sample profile text
            
    if not all_resumes:
        return {
            "response_message": "No candidate resumes loaded in system.",
            "next_node": ""
        }
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "response_message": "Gemini API Key is missing. Cannot perform mismatch analysis.",
            "next_node": ""
        }
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    resumes_summary = "\n---\n".join(all_resumes)
    
    prompt = f"""Compare the job description requirements against the overall candidate pool profiles.
Job Requirements:
- Role: {role}
- Required Skills: {', '.join(skills)}
- Experience Required: {exp_req}

Applicant Resumes (Truncated):
{resumes_summary}

Analyze:
1. Experience Mismatch: Are requirements too high (e.g. 5+ years but pool has 2-3 years)?
2. Skills Mismatch: Are required skills missing from most candidate profiles?
3. Actionable Advice: How can the recruiter adjust JD constraints to attract better matches?

Provide clear, formatted feedback.
"""
    try:
        response = model.generate_content(prompt)
        feedback = response.text.strip()
        
        msg = f"""[bold yellow]JD-Candidate Pool Mismatch Analysis[/bold yellow]
==================================================
{feedback}
==================================================
"""
        return {
            "jd_feedback": feedback,
            "response_message": msg,
            "next_node": ""
        }
    except Exception as e:
        return {
            "response_message": f"Failed analyzing JD mismatch with LLM: {e}",
            "next_node": ""
        }


# -----------------
# 13. HUMAN APPROVAL NODE
# -----------------
def human_approval_node(state: AgentState) -> dict:
    """Processes approval actions from the recruiter and updates the state."""
    action = state.get("action_type")
    response = state.get("recruiter_response", "").strip().upper()
    
    if action == "shortlist":
        if response in ["YES", "Y", "APPROVE", "OK"]:
            matched = state.get("matched_candidates", [])
            # Shortlist top 2
            top_candidates = matched[:2]
            
            # Save to state
            shortlisted = state.get("shortlisted_candidates", [])
            if not shortlisted:
                shortlisted = []
            
            for tc in top_candidates:
                if tc not in shortlisted:
                    shortlisted.append(tc)
                    
            candidate_names = ", ".join([c["name"] for c in top_candidates])
            msg = f"[bold green]Approval Received![/bold green] Shortlisted candidates: [cyan]{candidate_names}[/cyan] have been saved successfully."
            
            return {
                "shortlisted_candidates": shortlisted,
                "confirmation_required": False,
                "action_type": "",
                "response_message": msg,
                "next_node": ""
            }
        else:
            # Rejection or requested adjustments
            return {
                "confirmation_required": False,
                "action_type": "",
                "response_message": f"Shortlist action cancelled or postponed. Recruiter response: '{state.get('recruiter_response')}'",
                "next_node": ""
            }
            
    elif action == "rewrite_jd":
        if response in ["YES", "Y", "APPROVE", "OK"]:
            rewritten = state.get("rewritten_jd", "")
            
            # Synchronously re-parse rewritten JD
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"Analyze the following Job Description (JD) text and extract details as structured JSON:\n\n{rewritten}"
                try:
                    response_parsed = model.generate_content(
                        prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": JobDescriptionSchema
                        }
                    )
                    parsed = JobDescriptionSchema.model_validate_json(response_parsed.text)
                    return {
                        "raw_jd": rewritten,
                        "role": parsed.role,
                        "required_skills": parsed.required_skills,
                        "experience_required": parsed.experience_required,
                        "location": parsed.location,
                        "confirmation_required": False,
                        "action_type": "",
                        "response_message": "[bold green]Approval Received![/bold green] Job description successfully updated with the rewritten draft and re-parsed.",
                        "next_node": ""
                    }
                except Exception as e:
                    return {
                        "raw_jd": rewritten,
                        "confirmation_required": False,
                        "action_type": "",
                        "response_message": f"Job description updated, but auto-reparsing failed: {e}",
                        "next_node": ""
                    }
            else:
                return {
                    "raw_jd": rewritten,
                    "confirmation_required": False,
                    "action_type": "",
                    "response_message": "Job description updated but could not re-parse due to missing API key.",
                    "next_node": ""
                }
        else:
            return {
                "confirmation_required": False,
                "action_type": "",
                "response_message": "Job Description rewrite draft discarded. Retained original JD details.",
                "next_node": ""
            }
            
    elif action == "salary_budget":
        # Recruiter response contains the budget
        budget_value = state.get("recruiter_response", "").strip()
        
        msg = f"[bold green]Salary Budget Set![/bold green] Company salary budget has been saved as [cyan]'{budget_value}'[/cyan]. This is recorded as the final source of truth."
        
        return {
            "company_salary_range": budget_value,
            "confirmation_required": False,
            "action_type": "",
            "response_message": msg,
            "next_node": ""
        }
        
    return {
        "confirmation_required": False,
        "action_type": "",
        "response_message": "Action processed.",
        "next_node": ""
    }
