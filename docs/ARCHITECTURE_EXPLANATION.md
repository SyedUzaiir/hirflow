# Technical Architecture Documentation: HireFlow Agent

This document provides a comprehensive technical breakdown of **HireFlow Agent - Agentic AI Recruitment Assistant**. It details the system's data structures, LangGraph state machine workflow, ChromaDB vector search setup, and human-in-the-loop logic to serve as a guide for development teams and hackathon judges.

---

## 1. Project Overview

### The Problem We Are Solving
Recruiters spend hours manually filtering hundreds of resumes, looking for specific skills, performing salary benchmarking across regions, checking for employment red flags, and drafting tailored interview questions. This manual process is slow, prone to bias, and leads to high developer-recruiter alignment gaps.

### Why Recruiters Need This
HireFlow Agent acts as a co-pilot, automating repetitive, research-heavy recruiting tasks. Instead of jumping between search engines, spreadsheets, and word processors, the recruiter interacts with a single system that does the heavy lifting, saving hours per candidate search.

### What HireFlow Agent Does
HireFlow Agent is a terminal-based recruitment assistant that performs:
- **Semantic Job Description Parsing**: Extracts key roles, required skills, and constraints from job postings.
- **RAG candidate screening**: Matches candidate resumes semantically against JDs using vector embeddings.
- **Live Salary Benchmarking**: Scrapes real-time salary expectations across locations using search APIs.
- **Interview Guides**: Generates candidate-tailored technical and project-based questions.
- **Anomaly Detection**: Scans resumes for career timeline gaps, missing criteria, and potential red flags.
- **Human-in-the-Loop Safeguards**: Blocks critical hiring steps until approved by a recruiter.

### Why This is an Agentic AI System and Not a Normal Chatbot

Unlike standard chatbots that map user inputs directly to single LLM calls, HireFlow Agent models recruitment as a stateful, branching graph where decisions route dynamically based on conditions, API results, and recruiter feedback.

```text
Normal Chatbot:
User ──► LLM ──► Static Text Answer

Agentic AI System (HireFlow):
            ┌───────────────────┐
            │       User        │
            └─────────┬─────────┘
                      │
                      ▼
            ┌───────────────────┐
            │    Router Node    │
            └─────────┬─────────┘
                      ├───────────────────────────────────────────────────────┐
                      ▼                                                       ▼
            ┌───────────────────┐                                   ┌───────────────────┐
            │   Task Agents     │                                   │   Human Loop      │
            │   (RAG / Search)  │                                   │   (Confirmation)  │
            └─────────┬─────────┘                                   └─────────┬─────────┘
                      │                                                       │
                      └───────────────────────────┬───────────────────────────┘
                                                  ▼
                                        ┌───────────────────┐
                                        │  State Update &   │
                                        │   CLI Dashboard   │
                                        └───────────────────┘
```

---

## 2. Complete System Architecture

```text
                                 [ Recruiter CLI ]
                                         │
                                         ▼
                                 [ LangGraph State ] (Shared Memory)
                                         │
                                         ▼
                                  [ Router Node ] 
                                         │
                 ┌───────────────────────┼────────────────────────┐
                 │                       │                        │
                 ▼                       ▼                        ▼
           [ JD Parser ]           [ Resume Loader ]      [ Applicant Counter ]
                 │                       │                        │
                 ▼                       ▼                        ▼
           Gemini Flash               ChromaDB               Regex Counting
                 │                       │                        │
                 └───────────────────────┼────────────────────────┘
                                         │
                 ┌───────────────────────┼────────────────────────┐
                 │                       │                        │
                 ▼                       ▼                        ▼
       [ Candidate Match ]       [ Candidate Compare ]     [ Interview Generator ]
                 │                       │                        │
                 ▼                       ▼                        ▼
          ChromaDB Query            Gemini Flash             Gemini Flash
                 │                       │                        │
                 └───────────────────────┼────────────────────────┘
                                         │
                 ┌───────────────────────┼────────────────────────┐
                 │                       │                        │
                 ▼                       ▼                        ▼
        [ Salary Research ]       [ Red Flags Scan ]       [ JD Mismatch Scan ]
                 │                       │                        │
                 ▼                       ▼                        ▼
           Tavily Search            Gemini Flash             Gemini Flash
                 │                       │                        │
                 └───────────────────────┼────────────────────────┘
                                         │
                                         ▼
                             [ Human Approval Node ]
                                         │
                                         ▼
                                  [ Response Msg ]
```

### Responsibility of Each Layer
- **CLI Interface (main.py)**: Handles user terminal inputs, formats results using the `rich` library, updates the visual status dashboard, and implements the blocking input loop for recruiter approvals.
- **Shared State (state.py)**: A single source of truth containing memory records (parsed requirements, retrieved candidates, salary figures, conversation history, and confirmation triggers).
- **Task Nodes (nodes.py)**: Specialized executable python logic files. Some nodes run API requests, some query local databases, and others perform deterministic calculations.
- **RAG Engine (rag_tool.py)**: Creates embeddings using a local transformer model and indexes text profiles in a local vector database.
- **Web Search Tool (salary_tool.py)**: Queries real-time salary values across locations using Tavily.

---

## 3. LangGraph Workflow Explanation

### Why We Used LangGraph
LangGraph allows us to define cyclic graphs that integrate agent steps with human-in-the-loop gates. It compiles the steps into a structured execution loop where state passes from node to node deterministically.

### What is StateGraph
A `StateGraph` represents a state machine where nodes execute actions and edges define where the execution moves. It is initialized with a schema defining the shared system memory.

### State Transitions
When a node executes, it returns a dictionary containing values for the fields it modified. LangGraph automatically merges these updates back into the main state, keeping memory persistent across actions.

### Conditional Edges
A conditional edge decides which node to execute next by calling a routing function. The router node inspects the input query, sets `next_node` in the state, and the conditional edge forwards control to the target node.

### Graph Configuration (`agents/graph.py`)
```python
workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("router", router_node)
workflow.add_node("help_node", help_node)
workflow.add_node("jd_parser", jd_parser_node)
workflow.add_node("resume_loader", resume_loader_node)
...

# Add Entry point
workflow.add_edge(START, "router")

# Router conditional routing
workflow.add_conditional_edges("router", lambda state: state.get("next_node", "help_node"))

# Outgoing transitions to END
workflow.add_edge("jd_parser", END)
workflow.add_edge("resume_loader", END)
...
```

---

## 4. Agent State Documentation

| State Key | Type | Description |
| :--- | :--- | :--- |
| `user_query` | `str` | Holds the raw input text from the recruiter. |
| `intent` | `str` | The classified intent parsed by the router. |
| `conversation_history` | `List[Dict[str, str]]` | A running chat log list maintaining context memory across turns. |
| `next_node` | `str` | Dictates the subsequent node to execute. |
| `raw_jd` | `str` | Stores the loaded raw Job Description text. |
| `role` | `str` | The title parsed from the Job Description. |
| `required_skills` | `List[str]` | List of required skills extracted from the JD. |
| `experience_required` | `str` | Experience level extracted from the JD. |
| `location` | `str` | The parsed location constraints. |
| `resumes_loaded` | `bool` | True if the resumes are cached and indexed. |
| `total_candidates` | `int` | Total count of candidate resumes in the database. |
| `matched_candidates` | `List[Dict]` | Ranked candidate matches returned from the RAG search. |
| `shortlisted_candidates`| `List[Dict]` | Set of candidates approved by the recruiter (saved to state). |
| `rewritten_jd` | `str` | The rewritten version of the Job Description. |
| `interview_questions` | `Dict[str, List]` | Personalized interview questions per candidate. |
| `jd_feedback` | `str` | Recommendations identifying JD/resume-pool gaps. |
| `candidate_comparison` | `str` | Head-to-head comparison analysis text. |
| `red_flags` | `Dict[str, List]` | Flagged career anomalies per candidate. |
| `salary_market_data` | `str` | Salary research returned from Tavily web search. |
| `company_salary_range` | `str` | The company budget entered by the recruiter. |
| `confirmation_required`| `bool` | Flag that pauses execution and prompts for recruiter confirmation. |
| `action_type` | `str` | Identifies the confirmation type (`"shortlist"`, `"rewrite_jd"`, `"salary_budget"`). |
| `recruiter_response` | `str` | The recruiter's reply (`"YES"`, `"NO"`, or specific inputs). |
| `response_message` | `str` | The main visual output displayed to the recruiter. |

---

## 5. Node-by-Node Explanation

### 1. Router Node
- **Purpose**: Classifies user queries and decides the next execution path using a robust 3-level hybrid routing engine.
- **Input State**: `user_query`
- **Processing Logic**: 
  - **Query Normalization**: Lowercases the input, removes symbols/punctuation, and corrects common spelling mistakes (e.g. `"canditates"` -> `"candidates"`).
  - **Level 1: Fast Keyword Match**: Compares the normalized query against exact keyword patterns for direct containment routing.
  - **Level 2: Fuzzy Matching**: Uses the `rapidfuzz` library to calculate weighted token similarities. If the WRatio match confidence is greater than 75%, it automatically maps to the target intent.
  - **Level 3: Gemini Classifier Fallback**: If keyword and fuzzy checks fail, it falls back to a Gemini 2.5 Flash query to classify intent.
- **Output State**: `intent`, `next_node`

### 2. JD Parser Node
- **Purpose**: Parses raw JDs into structured criteria.
- **Input State**: `raw_jd` or `user_query`
- **Processing Logic**: Calls Gemini with a Pydantic extraction model to parse role, skills, experience, and location constraints.
- **Output State**: `role`, `required_skills`, `experience_required`, `location`, `response_message`

### 3. Resume Loader Node
- **Purpose**: Ingests resume files and builds the vector database.
- **Input State**: None (searches directory files)
- **Processing Logic**: Reads resume text files from `data/resumes/`, extracts candidate names, generates vectors using sentence-transformers, and inserts records into ChromaDB.
- **Output State**: `resumes_loaded`, `total_candidates`, `response_message`

### 4. Applicant Counter Node
- **Purpose**: Counts applicant profiles in the repository.
- **Input State**: None
- **Processing Logic**: Uses a deterministic Python script to count target files in `data/resumes/` without calling an LLM.
- **Output State**: `total_candidates`, `response_message`

### 5. Candidate Matching Node
- **Purpose**: Matches candidates semantically to the parsed JD requirements.
- **Input State**: `role`, `required_skills`, `experience_required`
- **Processing Logic**: Queries ChromaDB with the parsed JD skills. Generates matching scores, flags missing criteria, and returns candidates for review. Sets `confirmation_required = True`.
- **Output State**: `matched_candidates`, `confirmation_required`, `action_type`, `response_message`

### 6. JD Rewrite Node
- **Purpose**: Adjusts the tone of JDs (e.g. startup, friendly, corporate).
- **Input State**: `role`, `required_skills`, `experience_required`, `user_query`
- **Processing Logic**: Rewrites the parsed JD to the requested tone while maintaining required technical skills. Sets `confirmation_required = True`.
- **Output State**: `rewritten_jd`, `confirmation_required`, `action_type`, `response_message`

### 7. Interview Generator Node
- **Purpose**: Generates personalized candidate interview questions.
- **Input State**: `matched_candidates`, `role`, `required_skills`, `user_query`
- **Processing Logic**: Cross-references the target candidate's resume content with required skills to generate custom technical, project-based, and behavioral questions.
- **Output State**: `interview_questions`, `response_message`

### 8. Salary Research Node
- **Purpose**: Researches market salary benchmarks.
- **Input State**: `role`, `location`
- **Processing Logic**: Queries the Tavily Search API for average salary ranges, displays the web sources, and prompts the recruiter to specify their budget. Sets `confirmation_required = True`.
- **Output State**: `salary_market_data`, `confirmation_required`, `action_type`, `response_message`

### 9. Human Approval Node
- **Purpose**: Commits or rejects actions based on recruiter feedback.
- **Input State**: `recruiter_response`, `action_type`
- **Processing Logic**: 
  - If `YES` for shortlist: Saves candidates to `shortlisted_candidates`.
  - If `YES` for JD rewrite: Overwrites active JD values.
  - For salary budget: Saves the recruiter-provided value as the final budget.
- **Output State**: `shortlisted_candidates` (updated), `company_salary_range`, `confirmation_required = False`

---

## 6. RAG Implementation Details

### Why RAG is Needed
Keyword search fails on synonyms (e.g. missing candidates who write "cloud infrastructure automation" instead of "AWS backend engineer"). Retrieval-Augmented Generation (RAG) resolves this by matching intent.

### Embedding Model: `all-MiniLM-L6-v2`
A lightweight model that embeds text sentences into dense 384-dimensional vector spaces, capturing semantic context.

### ChromaDB Integration
We use ChromaDB as our local persistent database. Resumes are converted into vectors and stored alongside files metadata. Matches are returned using cosine-similarity distances.

```text
JD query: "Python FastAPI PostgreSQL"
     │
     ▼
[ Embedding Model ] ──► Dense Vector
                            │
                            ▼
                     [ ChromaDB ] ──► Cosine Similarity Search ──► Matches
```

---

## 7. Tool Usage Explanation

- **Gemini 2.5 Flash**: Processes complex text parsing, candidate matches reasoning, interview generation, and profile comparisons.
- **Tavily Search**: Fetches real-time web results for local salary benchmarking.
- **ChromaDB**: Acts as the local vector store for semantic matches.
- **Python**: Handles deterministic tasks like file IO and folder counting to optimize performance.

---

## 8. Human-in-the-Loop Design

HireFlow Agent delegates routine research tasks to AI, but keeps recruiters in control of key workflow decisions.

```text
               ┌───────────────────────┐
               │    AI Agent Task      │
               └──────────┬────────────┘
                          │
                          ▼
               ┌───────────────────────┐
               │ Pauses & Sets Gateway │
               │ (confirmation=True)   │
               └──────────┬────────────┘
                          │
                          ▼
               ┌───────────────────────┐
               │  Recruiter Action     │
               │  (YES / NO / Input)   │
               └──────────┬────────────┘
                          │
                          ▼
               ┌───────────────────────┐
               │ Commits to State      │
               └───────────────────────┘
```

- **Shortlisting**: The system ranks candidates and requests confirmation before shortlisting.
- **Salary**: The system fetches market benchmarks, but the final budget range must be set by the recruiter.
- **JD Rewriting**: Tone adjustments must be approved before updating the active JD profile.

---

## 9. Complete User Journey Example

```text
Recruiter: "Find candidates"
  │
  ▼
1. Router Node: Identifies intent as "match_candidates" and forwards to candidate_matching.
  │
  ▼
2. Candidate Matching Node: Reads JD skills and queries the ChromaDB collection.
  │
  ▼
3. ChromaDB Retrieval: Returns the top candidates based on vector similarity.
  │
  ▼
4. Gemini Grading: Ranks the matches, formats the scores, and sets confirmation_required = True.
  │
  ▼
5. User Input Loop: Displays the ranked matches and asks the recruiter to confirm (YES/NO).
  │
  ▼
6. Human Approval Node: Recruiter types "YES". The system saves the shortlist to state and resumes.
```

---

## 10. Hackathon Evaluation Mapping

- **RAG Architecture**: Uses ChromaDB and `all-MiniLM-L6-v2` for semantic search matches.
- **Tool Integration**: Integrates Tavily search for live salaries and python scripts for direct file tracking.
- **Agentic Design**: Implements dynamic routing and state loops via LangGraph nodes.
- **Human in the Loop**: Pauses execution at key stages to confirm recruiter approval before updating state.
- **UX & Formatting**: Formats CLI output panels and tables using `rich`.

---

## 11. Completed Streamlit Web UI

We have implemented a web-based recruiter dashboard inside [streamlit_app.py](file:///d:/Projects/HireAgentAI/streamlit_app.py).

### Key Features
- **Sidebar Status Monitor**: Real-time display of parsed Role, Required Skills, Resumes Loaded count, Shortlisted Candidates list, and final Company Budget.
- **Workflow Path Tracker**: Visual trace highlighting graph execution progress (e.g. `Router ➔ Candidate Matching ➔ Human Approval Gate`).
- **Interactive Chat Interface**: Recruiter chat input mapped directly to the LangGraph execution flow.
- **RAG Candidate Profile Cards**: Custom cards mapping similarity match scores, matched skills, missing skills, and detailed AI reasons.
- **Gate Confirmation Form**: Inline approval controls (YES/NO and budget text inputs) that render dynamically when confirmations are triggered.

To run the Streamlit app:
```powershell
streamlit run streamlit_app.py
```

---

## 12. Future Improvements

- **PDF Parsing**: Add direct PDF parsing libraries (e.g. `pypdf` or `pdfplumber`).
- **Email automation**: Add integrations with services like SendGrid to draft and send candidate emails directly from the assistant interface.
- **Calendar Booking**: Integrate scheduling links (e.g. Cal.com or Google Calendar) to invite candidates to interviews.
