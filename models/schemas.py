from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class JobDescriptionSchema(BaseModel):
    role: str = Field(description="The primary job title/role parsed from the JD")
    required_skills: List[str] = Field(description="List of key technical skills required")
    experience_required: str = Field(description="Years or level of experience required (e.g. 5+ years)")
    location: str = Field(description="Location constraints (e.g. San Francisco, CA (Hybrid))")

class CandidateMatchSchema(BaseModel):
    candidate_name: str = Field(description="Name of the candidate")
    match_score: int = Field(description="Percentage score matching the JD, from 0 to 100")
    matched_skills: List[str] = Field(description="List of candidate skills matching the JD")
    missing_skills: List[str] = Field(description="List of required JD skills missing in candidate resume")
    reasoning: str = Field(description="Detailed reason for the match score and candidate fit")

class CandidateComparisonSchema(BaseModel):
    comparison_summary: str = Field(description="Executive summary comparing candidates")
    strengths: Dict[str, List[str]] = Field(description="Candidate name to list of key strengths")
    weaknesses: Dict[str, List[str]] = Field(description="Candidate name to list of key weaknesses")
    final_recommendation: str = Field(description="Final recommendation on who is the better fit and why")

class RedFlagsSchema(BaseModel):
    candidate_name: str = Field(description="Name of the candidate")
    has_red_flags: bool = Field(description="True if employment gaps, missing skills or anomalies exist")
    red_flags: List[str] = Field(description="List of detected anomalies, gaps, or concerns")
    explanation: str = Field(description="Brief explanation of findings")

class RouterOutput(BaseModel):
    intent: str = Field(description="One of: parse_jd, load_resumes, count_applicants, match_candidates, jd_rewrite, interview_questions, salary_research, compare_candidates, unknown")
    target_name: Optional[str] = Field(None, description="Name of candidate if query targets a specific person")
    rewrite_tone: Optional[str] = Field(None, description="Tone for rewriting (startup, professional, friendly, etc.)")
