"""
Research Assistant for College Students: 3-agent system built with LangGraph.

Agents:
  1. Researcher -> plans search queries, calls the web search tool, writes cited notes
  2. Writer     -> turns the notes into a structured summary (uses ONLY the notes)
  3. Reviewer   -> checks every claim against the notes; approves or sends back for revision

Flow:  Researcher -> Writer -> Reviewer
       Reviewer says REVISE (max 2 times) -> back to Writer
       Reviewer says APPROVED             -> END
"""
import json
import os
import re
from typing import List, TypedDict

from dotenv import load_dotenv
from ddgs import DDGS
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

load_dotenv()

MAX_REVISIONS = 2
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")  # reads GOOGLE_API_KEY from env


# ---------------------------------------------------------------- shared state
class ResearchState(TypedDict, total=False):
    topic: str
    queries: List[str]
    sources: List[dict]      # [{id, title, url, snippet}]
    notes: str
    draft: str
    verdict: str             # "APPROVED" or "REVISE"
    issues: List[str]
    revisions: int
    log: List[str]


# ---------------------------------------------------------------------- helpers
def _llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=MODEL, temperature=None)


def _ask(system: str, user: str) -> str:
    resp = _llm().invoke([("system", system), ("human", user)])
    content = resp.content
    if isinstance(content, list):  # some versions return a list of parts
        content = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return content.strip()


# ------------------------------------------------------------------------ tool
def web_search(query: str, max_results: int = 4) -> List[dict]:
    """Tool used by the Researcher agent. Returns title, url, snippet."""
    try:
        results = DDGS().text(query, max_results=max_results)
    except Exception:
        return []
    return [
        {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
        for r in results
    ]


# ----------------------------------------------------------------------- agents
def researcher(state: ResearchState) -> dict:
    topic = state["topic"]

    raw = _ask(
        "You plan web searches for a college student's research task. "
        "Return exactly 3 different, specific search queries, one per line, no numbering.",
        f"Topic: {topic}",
    )
    queries = [q.strip("-*0123456789. ").strip() for q in raw.splitlines() if q.strip()][:3]

    sources, seen = [], set()
    for q in queries:
        for r in web_search(q):
            if r["url"] and r["url"] not in seen:
                seen.add(r["url"])
                sources.append({"id": len(sources) + 1, **r})

    if not sources:
        return {
            "queries": queries, "sources": [], "notes": "",
            "log": state.get("log", []) + ["Researcher: no search results found."],
        }

    results_text = "\n\n".join(
        f"[{s['id']}] {s['title']}\nURL: {s['url']}\n{s['snippet']}" for s in sources
    )
    notes = _ask(
        "You are a research assistant. Using ONLY the search results given, write concise "
        "bullet-point notes about the topic. After each fact add its source number like [2]. "
        "Do not add facts that are not in the results.",
        f"Topic: {topic}\n\nSearch results:\n{results_text}",
    )
    return {
        "queries": queries,
        "sources": sources,
        "notes": notes,
        "log": state.get("log", []) + [f"Researcher: ran {len(queries)} searches, kept {len(sources)} sources."],
    }


def writer(state: ResearchState) -> dict:
    revision_block = ""
    if state.get("issues"):
        issues = "\n".join(f"- {i}" for i in state["issues"])
        revision_block = (
            f"\n\nYour previous draft:\n{state['draft']}\n\n"
            f"The Reviewer found these problems. Fix ALL of them (remove or correct the claims):\n{issues}"
        )

    draft = _ask(
        "You are an academic writer helping a college student. Write a clear summary using ONLY "
        "the notes provided. Structure: ## Overview, ## Key Points, ## Details, ## Conclusion. "
        "Keep the source citations like [1] next to the claims. If the notes are thin, say so "
        "instead of inventing information.",
        f"Topic: {state['topic']}\n\nNotes:\n{state['notes']}{revision_block}",
    )
    n = state.get("revisions", 0)
    label = "first draft" if not state.get("issues") else f"revision {n}"
    return {"draft": draft, "log": state.get("log", []) + [f"Writer: produced {label}."]}


def reviewer(state: ResearchState) -> dict:
    raw = _ask(
        "You are a strict fact-checker. Compare the DRAFT against the NOTES. A claim is "
        "unsupported if it does not appear in the notes. Respond with ONLY JSON like:\n"
        '{"verdict": "APPROVED" or "REVISE", "issues": ["issue 1", "issue 2"]}\n'
        "Use APPROVED only if every claim is supported by the notes.",
        f"NOTES:\n{state['notes']}\n\nDRAFT:\n{state['draft']}",
    )
    try:
        data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        verdict = "REVISE" if str(data.get("verdict", "")).upper() == "REVISE" else "APPROVED"
        issues = [str(i) for i in data.get("issues", [])]
    except Exception:
        verdict, issues = "APPROVED", ["Reviewer output could not be parsed; treated as approved."]

    revisions = state.get("revisions", 0) + (1 if verdict == "REVISE" else 0)
    return {
        "verdict": verdict,
        "issues": issues if verdict == "REVISE" else [],
        "revisions": revisions,
        "log": state.get("log", []) + [f"Reviewer: {verdict} ({len(issues)} issue(s))."],
    }


def route_after_review(state: ResearchState) -> str:
    if state["verdict"] == "REVISE" and state["revisions"] <= MAX_REVISIONS:
        return "writer"
    return END


# ------------------------------------------------------------------------ graph
def build_graph():
    g = StateGraph(ResearchState)
    g.add_node("researcher", researcher)
    g.add_node("writer", writer)
    g.add_node("reviewer", reviewer)
    g.set_entry_point("researcher")
    g.add_conditional_edges("researcher", lambda s: "writer" if s.get("notes") else END)
    g.add_edge("writer", "reviewer")
    g.add_conditional_edges("reviewer", route_after_review, {"writer": "writer", END: END})
    return g.compile()


def stream_research(topic: str):
    """Yields (node_name, state_update) as each agent finishes. Used by the UI."""
    app = build_graph()
    initial = {"topic": topic, "revisions": 0, "issues": [], "log": []}
    for step in app.stream(initial, stream_mode="updates"):
        for node, update in step.items():
            yield node, update


def run_research(topic: str) -> ResearchState:
    """Runs the full pipeline and returns the final merged state."""
    state: ResearchState = {"topic": topic, "revisions": 0, "issues": [], "log": []}
    for _, update in stream_research(topic):
        state.update(update)
    return state
