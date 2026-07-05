from langgraph.graph import StateGraph, START, END
from agents.state import AgentState
from agents.nodes import (
    router_node,
    help_node,
    jd_parser_node,
    resume_loader_node,
    applicant_counter_node,
    candidate_matching_node,
    jd_rewrite_node,
    interview_generator_node,
    salary_research_node,
    candidate_comparison_node,
    red_flag_node,
    jd_mismatch_node,
    human_approval_node
)

def build_graph():
    """Compiles the recruitment workflow StateGraph."""
    workflow = StateGraph(AgentState)
    
    # 1. Add all nodes to the workflow
    workflow.add_node("router", router_node)
    workflow.add_node("help_node", help_node)
    workflow.add_node("jd_parser", jd_parser_node)
    workflow.add_node("resume_loader", resume_loader_node)
    workflow.add_node("applicant_counter", applicant_counter_node)
    workflow.add_node("candidate_matching", candidate_matching_node)
    workflow.add_node("jd_rewrite", jd_rewrite_node)
    workflow.add_node("interview_generator", interview_generator_node)
    workflow.add_node("salary_research", salary_research_node)
    workflow.add_node("candidate_comparison", candidate_comparison_node)
    workflow.add_node("red_flag_node", red_flag_node)
    workflow.add_node("jd_mismatch_node", jd_mismatch_node)
    workflow.add_node("human_approval", human_approval_node)
    
    # 2. Add structural entry edge
    workflow.add_edge(START, "router")
    
    # 3. Router conditional transitions
    def route_decision(state: AgentState):
        return state.get("next_node", "help_node")
        
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "help_node": "help_node",
            "jd_parser": "jd_parser",
            "resume_loader": "resume_loader",
            "applicant_counter": "applicant_counter",
            "candidate_matching": "candidate_matching",
            "jd_rewrite": "jd_rewrite",
            "interview_generator": "interview_generator",
            "salary_research": "salary_research",
            "candidate_comparison": "candidate_comparison",
            "red_flag_node": "red_flag_node",
            "jd_mismatch_node": "jd_mismatch_node",
            "human_approval": "human_approval"
        }
    )
    
    # 4. Outgoing edges to END
    workflow.add_edge("help_node", END)
    workflow.add_edge("jd_parser", END)
    workflow.add_edge("resume_loader", END)
    workflow.add_edge("applicant_counter", END)
    workflow.add_edge("candidate_matching", END)
    workflow.add_edge("jd_rewrite", END)
    workflow.add_edge("interview_generator", END)
    workflow.add_edge("salary_research", END)
    workflow.add_edge("candidate_comparison", END)
    workflow.add_edge("red_flag_node", END)
    workflow.add_edge("jd_mismatch_node", END)
    workflow.add_edge("human_approval", END)
    
    # 5. Compile the graph
    return workflow.compile()
