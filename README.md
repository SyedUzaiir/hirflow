# HireFlow Agent 🤖

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Agent_Framework-LangGraph-orange?logo=langchain)](https://github.com/langchain-ai/langgraph)
[![Gemini](https://img.shields.io/badge/LLM-Gemini_2.5_Flash-red?logo=google-gemini)](https://ai.google.dev/)
[![ChromaDB](https://img.shields.io/badge/Vector_DB-ChromaDB-blue)](https://www.trychroma.com/)
[![Tavily](https://img.shields.io/badge/Search_API-Tavily-brightgreen)](https://tavily.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)

> **An Agentic AI Recruitment Assistant powered by LangGraph, RAG semantic search, and Human-in-the-Loop recruiter safeguards.**

---

### 🎥 Live Demo Video & Submission Assets
* **Watch the Walkthrough Video**: 🔗 [Google Drive Demo Video](https://drive.google.com/file/d/1kb_4XglZjykBweDG5SvNAi07jBuaZBMs/view?usp=sharing)
* **Submission Materials**: Please check the [submission/](file:///d:/Projects/HireAgentAI/submission/) folder for screenshots, technical pitch presentation slides, and documentation resources.

---

## 📌 1. Problem Statement

Recruitment professionals manually spend hours on tedious candidate search tasks:
* Reading, parsing, and classifying hundreds of resumes.
* Comparing candidates side-by-side to match specific Job Description (JD) requirements.
* Manually writing custom technical and behavioral interview preparation guides.
* Conducting external salary research on multiple platforms to gauge market averages.

**Traditional Chatbots** only answer general queries—they cannot manage workflow execution, preserve complex states, run external search tools, query local vector databases, or pause for human approval. 

**HireFlow Agent** solves this by shifting from simple chatbot Q&A to a **fully-fledged agentic recruitment workflow** that acts as an intelligent co-pilot for HR professionals.

---

## 🎯 2. Our Solution

HireFlow Agent is designed as a recruiter co-pilot: the **AI recommends, the human decides**. 

### Core Capabilities:
* **Structured JD Parsing**: Extracts role, required skills, and experience constraints using Pydantic structured output models.
* **Semantic Resume Ranking**: Screens candidate resume files using dense vector embeddings in a ChromaDB database.
* **Live Web Salary Research**: Conducts real-time market research using the Tavily Search API.
* **Custom Interview Guides**: Creates candidate-specific interview guides grounded in their resume and JD requirements.
* **JD Rewrite Engine**: Adapts JDs dynamically into Start-up, Friendly, or Corporate tones.
* **Resume Red-Flag Scanner**: Identifies employment gaps, tenure anomalies, and timeline gaps.
* **JD Mismatch Feedback**: Analyzes candidate pool stats to tell recruiters if their requirements are too strict.
* **Recruiter Decision Gates**: Automatically pauses execution to request recruiter approval before final shortlists or budgets.

---

## 🧠 3. Why Agentic AI?

A traditional LLM chatbot processes inputs linearly:
```text
Recruiter ──► Chatbot LLM ──► Text Response
```
In contrast, **HireFlow Agent** utilizes a multi-node workflow driven by **LangGraph**. The LLM is not the entire application—it is a cognitive engine used for reasoning, while the agent controls the state, memory routing, tool calls, and human approvals:

```text
Recruiter 
    │
    ▼
Hybrid Router (Regex / Fuzzy Match / Gemini Fallback)
    │
    ▼
LangGraph State Machine
    ├── JD Parser Node ──► Gemini Structured Extraction
    ├── RAG Search Node ──► ChromaDB Vector Search + Ranking
    ├── Web Search Node ──► Tavily API Live Market Search
    └── Human Approval Gate (Pauses execution for recruiter validation)
```

---

## 🏗️ 4. System Architecture

```text
                               Recruiter
                                   │
                                   ▼
                       Streamlit Web UI / CLI
                                   │
                                   ▼
                            LangGraph Agent
                                   │
                                   ▼
                       3-Level Hybrid Router 
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
    JD Parser Node        Resume Ranking Node       Salary Research Node
         │                         │                         │
     Gemini LLM               ChromaDB RAG              Tavily API
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   ▼
                         Human Approval Gate
```

---

## 🔁 5. Agent Workflow

1. **Router Node**: Normalizes recruiter text (corrects spelling typos, strips symbols) and routes using a 3-level hybrid system:
   * *Level 1*: Direct exact keyword matching (for speed).
   * *Level 2*: Fuzzy token similarity matching via `rapidfuzz` (threshold > 75%).
   * *Level 3*: Gemini 2.5 Flash classifier (for ambiguous natural intent).
2. **JD Parser Node**: Parses raw JD texts into structured Pydantic models.
3. **Resume Screening Agent (RAG)**: Indexes local resumes into ChromaDB using `all-MiniLM-L6-v2` sentence-transformer embeddings, retrieves candidate matches, and grades them.
4. **Salary Agent**: Searches real-time salary ranges using Tavily, formats the search results, and requests a final company budget constraint.
5. **Interview Agent**: Cross-references resumes with JD criteria to generate customized technical and behavioral interview guides.
6. **Human Approval Gate**: Intercepts actions (like shortlisting or budget adjustments), pausing graph execution until the recruiter approves or overrides.

---

## 📊 6. Features Table

| Feature | Technology | Recruiter Purpose |
| :--- | :--- | :--- |
| **JD Parsing** | Gemini + Pydantic | Extract role constraints and skills |
| **Resume Matching** | ChromaDB RAG | Semantic candidate search and grading |
| **Salary Research** | Tavily Web Search | Real-time market compensation ranges |
| **Fuzzy Intent Routing** | `rapidfuzz` | Graceful handling of recruiter spelling mistakes |
| **Human Safeguards** | LangGraph State | Pauses workflow for recruiter approvals |
| **Red Flag Check** | Gemini | Detect employment gaps and short tenures |
| **Side-by-Side Comp** | Gemini | Structured candidate comparisons |
| **JD Mismatch** | Gemini | Spot requirement mismatch against pool |

---

## 🤝 7. Human-in-the-Loop Design

To prevent unchecked AI decision-making (Responsible AI), HireFlow Agent incorporates strict human gates:
* **The AI does NOT**: Automatically shortlist candidates, decide salaries, rewrite active job files, or reject candidates.
* **The AI does**: Grade, search, recommend, explain, and request recruiter approval.

### Examples:
* **Candidate Shortlisting**:
  ```text
  AI Recommendation: "Based on RAG analysis, I recommend Rohan and Anjali."
  Recruiter Action Required: [Approve (YES) / Reject (NO)]
  Recruiter Action: YES -> Shortlist saved to state.
  ```
* **Salary Research**:
  ```text
  Tavily Live Results: ML Engineer average in Bengaluru is ₹15 LPA - ₹40 LPA.
  Recruiter Action Required: "Define company salary budget:"
  Recruiter Input: ₹25 LPA -> Company budget recorded as final source of truth.
  ```

---

## 💻 8. Tech Stack

* **Frontend**: Streamlit
* **Agent Framework**: LangGraph
* **Large Language Model**: Gemini 2.5 Flash (via `google-generativeai`)
* **Vector Database**: ChromaDB
* **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
* **Web Search Tool**: Tavily API
* **Intent Processing**: `rapidfuzz` (Fuzzy logic)
* **Configuration**: `python-dotenv`, `pydantic`
* **CLI Layouts**: `rich` (console tables and debug traces)

---

## 📂 9. Project Structure

```text
HireAgentAI/
├── agents/             # LangGraph core workflow configuration
│   ├── graph.py        # Compiles and builds the StateGraph workflow
│   ├── nodes.py        # Core node logic, LLM prompts, and tool calls
│   └── state.py        # Shared AgentState definition
├── tools/              # Specialized agent utility tool modules
│   ├── rag_tool.py     # ChromaDB vector store wrapper and sentence-transformers loader
│   └── salary_tool.py  # Tavily Web Search API client wrapper
├── models/             # Data schemas
│   └── schemas.py      # Pydantic extraction models for structured LLM outputs
├── data/               # Project database mocks
│   ├── jd/             # Active Job Description document storage
│   └── resumes/        # Raw candidate resume text database (16 mock candidates)
├── docs/               # Technical documents
│   └── ARCHITECTURE_EXPLANATION.md # Comprehensive hackathon judge architectural breakdown
├── main.py             # CLI program entrypoint
├── streamlit_app.py    # Streamlit Web UI dashboard wrapper
└── requirements.txt    # Python dependencies list
```

---

## 🛠️ 10. Installation & Run Guide

### 1. Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/SyedUzaiir/hirflow.git
cd hirflow
```

### 2. Set up and activate a Virtual Environment:
```powershell
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### 3. Install the dependencies:
```bash
pip install -r requirements.txt
```

### 4. Configure API Credentials:
Create a `.env` file in the root directory and add your keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 5. Launch the Interfaces:

#### Option A: Streamlit Web UI (Recommended)
```powershell
.venv\Scripts\python -m streamlit run streamlit_app.py
```
*Loads the recruiter dashboard instantly (optimized with Streamlit resource caching).*

#### Option B: Terminal CLI Interface
```bash
python main.py
```

---

## 💬 11. Demo Flow Example

1. **Start Conversation**:
   Recruiter types: *"Find best applicants"*
2. **Hybrid Router Node**:
   Checks query, detects candidate matching intent, and prints the debug trace panel.
3. **ChromaDB Vector Screening Node**:
   Queries ChromaDB using embedding vectors, grades candidate compatibility, and presents the ranked scorecard.
4. **Human Approval Gate**:
   Stops workflow and asks the recruiter to confirm.
5. **UI Candidate Card Tab**:
   Renders custom candidate cards showing match scores, matched/missing skills, and detailed AI evaluations.

---

## 🏆 12. Hackathon Requirement Mapping

| Evaluation Criteria | Our Implementation | Verified Status |
| :--- | :--- | :--- |
| **RAG Usage** | Vector matching on resumes using `sentence-transformers` and ChromaDB | ✅ Verified |
| **Tool Usage** | Tavily search for live salary data | ✅ Verified |
| **Agentic Workflow** | Multi-node StateGraph routing using LangGraph | ✅ Verified |
| **Smart Routing** | Plain Python applicant counting (skips LLM API calls) | ✅ Verified |
| **Typos & Synonyms** | Hybrid router using keyword mapping + `rapidfuzz` scoring | ✅ Verified |
| **Safeguards** | Pauses execution for human approvals | ✅ Verified |
| **Visually Stunning UI** | Slate-dark mode Streamlit dashboard with metrics and cards | ✅ Verified |

---

## 🚀 13. Future Improvements

* **PDF Parsing**: Add direct PDF extraction tools (`pdfplumber` / `PyPDF2`) to parse native PDF resume uploads.
* **ATS Integrations**: Sync shortlist records directly with Greenhouse, Lever, or Workday APIs.
* **Automated Outreach**: Integrate SMTP/SendGrid to draft and send follow-up technical screening emails.
* **Scheduling**: Embed Cal.com or Google Calendar links to coordinate interview times automatically.
