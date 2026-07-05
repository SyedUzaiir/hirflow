from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    # Conversation Control
    user_query: str
    intent: str
    conversation_history: List[Dict[str, str]]  # list of {"role": "user"/"assistant", "content": "..."}
    next_node: str
    
    # JD Details
    raw_jd: str
    role: str
    required_skills: List[str]
    experience_required: str
    location: str
    
    # Resumes
    resumes_loaded: bool
    total_candidates: int
    
    # RAG & Matching
    matched_candidates: List[Dict[str, Any]]
    shortlisted_candidates: List[Dict[str, Any]]  # Saved after recruiter approves YES
    
    # Generation & Analysis
    rewritten_jd: str
    interview_questions: Dict[str, List[str]]  # Candidate Name -> Questions
    jd_feedback: str
    candidate_comparison: str
    red_flags: Dict[str, List[str]]            # Candidate Name -> Gaps/Warnings
    
    # External Data & Salary
    salary_market_data: str
    company_salary_range: str                  # Final recruiter provided salary
    skill_trends: List[str]
    
    # Human Loop / Control
    confirmation_required: bool
    action_type: str                           # "shortlist", "rewrite_jd", "salary_budget"
    recruiter_response: str                    # YES/NO or text feedback
    response_message: str                      # Main text content to display to the user
