import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.text import Text

# Load environment variables
load_dotenv()

# Add project root to python path to avoid import errors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.graph import build_graph

# Initialize Rich Console
console = Console()

def print_banner():
    banner = """
 ██╗  ██╗██╗██████╗ ███████╗███████╗██╗      ██████╗ ██╗    ██╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗
 ██║  ██║██║██╔══██╗██╔════╝██╔════╝██║     ██╔═══██╗██║    ██║    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
 ███████║██║██████╔╝█████╗  █████╗  ██║     ██║   ██║██║ █╗ ██║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   
 ██╔══██║██║██╔══██╗██╔══╝  ██╔══╝  ██║     ██║   ██║██║███╗██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   
 ██║  ██║██║██║  ██║███████╗██║     ███████╗╚██████╔╝╚███╔███╔╝    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   
 ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   
                                Agentic AI Recruitment Assistant
    """
    console.print(Panel(banner, border_style="cyan", title="Welcome"))

def print_status_dashboard(state):
    role = state.get("role") or "[red]Not Parsed[/red]"
    skills = ", ".join(state.get("required_skills", [])) or "[red]None[/red]"
    total_candidates = state.get("total_candidates", 0)
    resumes_loaded = "[green]Yes[/green]" if state.get("resumes_loaded") else "[red]No[/red]"
    shortlisted = ", ".join([c["name"] for c in state.get("shortlisted_candidates", [])]) or "[yellow]None[/yellow]"
    budget = state.get("company_salary_range") or "[yellow]Not Set[/yellow]"
    dashboard_text = f"""[bold]Parsed Role[/bold]: {role}
[bold]Required Skills[/bold]: {skills}
[bold]Resumes Loaded[/bold]: {resumes_loaded} ({total_candidates} candidates available in db)
[bold]Shortlisted Candidates[/bold]: {shortlisted}
[bold]Company Salary Budget[/bold]: {budget}"""
    
    console.print(Panel(Text.from_markup(dashboard_text), title="[bold cyan]HireFlow System Status[/bold cyan]", border_style="blue"))

def get_initial_state():
    return {
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

def main():
    print_banner()
    
    # Check for keys
    gemini_key = os.getenv("GEMINI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    warnings = []
    if not gemini_key:
        warnings.append("[bold red]Warning: GEMINI_API_KEY is not set. LLM functionalities will fail.[/bold red]")
    if not tavily_key:
        warnings.append("[bold yellow]Warning: TAVILY_API_KEY is not set. Salary research search tool will fail.[/bold yellow]")
        
    if warnings:
        for w in warnings:
            console.print(w)
        console.print("Please set your credentials in a `.env` file or environment.\n")
        
    # Build state graph
    try:
        graph = build_graph()
    except Exception as e:
        console.print(f"[bold red]Failed to construct graph workflow:[/bold red] {e}")
        return
        
    state = get_initial_state()
    
    # Auto-index resumes if database is empty but mock files are there
    resumes_dir = "data/resumes"
    if os.path.exists(resumes_dir) and len(os.listdir(resumes_dir)) > 0:
        console.print("[yellow]Auto-indexing candidate resumes database on startup...[/yellow]")
        from tools.rag_tool import RAGTool
        try:
            rag = RAGTool()
            count = rag.index_resumes(resumes_dir)
            state["resumes_loaded"] = True
            state["total_candidates"] = count
            console.print(f"[green]Successfully auto-indexed {count} resumes.[/green]\n")
        except Exception as e:
            console.print(f"[bold red]Failed to index resumes on startup:[/bold red] {e}\n")
            
    # Auto-load default Job Description if present
    jd_file = "data/jd/backend_jd.txt"
    if os.path.exists(jd_file):
        console.print("[yellow]Auto-loading default backend developer Job Description...[/yellow]")
        with open(jd_file, "r", encoding="utf-8") as f:
            state["raw_jd"] = f.read()
        # Parse it
        try:
            # Run parser node
            from agents.nodes import jd_parser_node
            parsed = jd_parser_node(state)
            state.update(parsed)
            console.print("[green]Default Job Description parsed.[/green]\n")
        except Exception as e:
            console.print(f"[bold red]Failed to parse default JD:[/bold red] {e}\n")
            
    print_status_dashboard(state)
    
    console.print("[italic]Type your request to begin, or type [bold cyan]/help[/bold cyan] for options, [bold cyan]/reset[/bold cyan] to clear state, [bold cyan]exit[/bold cyan] to quit.[/italic]\n")
    
    while True:
        try:
            user_input = Prompt.ask("[bold green]Recruiter[/bold green]").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("[bold cyan]Exiting HireFlow Agent. Goodbye![/bold cyan]")
                break
                
            if user_input.lower() == "/reset":
                state = get_initial_state()
                console.print("[bold yellow]State reset successfully.[/bold yellow]\n")
                print_status_dashboard(state)
                continue
                
            if user_input.lower() == "/help":
                user_input = "help" # Routes to help_node
                
            # Feed input to state
            state["user_query"] = user_input
            state["conversation_history"].append({"role": "user", "content": user_input})
            
            # Invoke graph
            with console.status("[cyan]HireFlow Agent processing...[/cyan]"):
                state = graph.invoke(state)
                
            # Store agent response in history
            state["conversation_history"].append({"role": "assistant", "content": state["response_message"]})
            
            # Print response
            console.print()
            console.print(Panel(Markdown(state["response_message"]), title="[bold cyan]HireFlow Agent[/bold cyan]", border_style="cyan"))
            console.print()
            
            # Human in the loop confirmation prompt
            while state.get("confirmation_required"):
                action = state.get("action_type")
                
                if action == "salary_budget":
                    prompt_label = "[bold green]Provide Company Salary Budget Range (or type 'cancel' to abort)[/bold green]"
                else:
                    prompt_label = "[bold green]Approve Action? (YES/NO or type 'cancel' to abort)[/bold green]"
                    
                recruiter_input = Prompt.ask(prompt_label).strip()
                
                if not recruiter_input:
                    continue
                    
                if recruiter_input.lower() in ["cancel", "abort"]:
                    state["confirmation_required"] = False
                    state["action_type"] = ""
                    state["recruiter_response"] = ""
                    state["response_message"] = "[yellow]Action cancelled by recruiter.[/yellow]"
                    state["conversation_history"].append({"role": "assistant", "content": state["response_message"]})
                    console.print()
                    console.print(Panel(state["response_message"], title="[bold cyan]HireFlow Agent[/bold cyan]", border_style="yellow"))
                    console.print()
                    break
                    
                # Feed response into graph
                state["recruiter_response"] = recruiter_input
                state["user_query"] = recruiter_input
                state["conversation_history"].append({"role": "user", "content": recruiter_input})
                
                with console.status("[cyan]Saving confirmation...[/cyan]"):
                    state = graph.invoke(state)
                    
                state["conversation_history"].append({"role": "assistant", "content": state["response_message"]})
                
                console.print()
                console.print(Panel(Markdown(state["response_message"]), title="[bold cyan]HireFlow Agent[/bold cyan]", border_style="cyan"))
                console.print()
                
            # After operations, print the status dashboard
            print_status_dashboard(state)
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[bold cyan]Exiting HireFlow Agent. Goodbye![/bold cyan]")
            break
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred in CLI loop:[/bold red] {e}\n")

if __name__ == "__main__":
    main()
