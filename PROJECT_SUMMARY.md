# Project Summary: HireFlow Agent

## Project Description
* **Project**: HireFlow Agent
* **Team**: Team Vcoders
* **Presenter**: Syed Uzair Mohiuddin (Roll Number: 24885A0542, Branch: CSE, Section: G)
* **Problem Statement**: Recruitment System Chatbot (An AI hiring co-pilot assisting HR recruiters in managing screening, interview preparation, and salary research)
* **Demo Video**: 🔗 [YouTube Walkthrough](https://youtu.be/ExFb-XrhXoY) | 🔗 [Google Drive Backup](https://drive.google.com/file/d/1kb_4XglZjykBweDG5SvNAi07jBuaZBMs/view?usp=sharing)

## Core Features
- **Agentic Workflow**: Multi-node workflow built on LangGraph for state management, intent classification, and memory loops.
- **JD Parser**: Structured information extraction using Gemini 2.5 Flash and Pydantic validation.
- **Resume RAG Screening**: Semantic candidate matching and similarity scoring via ChromaDB vector databases and `all-MiniLM-L6-v2` embeddings.
- **Candidate Ranking**: Strengths, weaknesses, and alignment grading.
- **Interview Generation**: Customized Candidate guide containing technical, project-based, and behavioral questions.
- **Salary Research**: Live market research using the Tavily Search API.
- **Human Approval System**: LangGraph-integrated decision gates (recommends options and pauses for recruiter confirmation before final shortlists or budgets).
- **Streamlit Web UI**: Premium dark-mode dashboard containing status sidebars, tabbed navigation, and candidate metrics.

## Technology Stack
* **Language**: Python
* **Agent Engine**: LangGraph
* **Reasoning model**: Gemini 2.5 Flash
* **Vector Store**: ChromaDB
* **Search API**: Tavily API
* **Frontend**: Streamlit
