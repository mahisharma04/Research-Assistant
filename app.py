import streamlit as st

from agents import MAX_REVISIONS, stream_research

st.set_page_config(page_title="Research Assistant", page_icon="📚", layout="wide")
st.title("📚 Research Assistant for College Students")
st.caption("Three agents: Researcher → Writer → Reviewer (fact-check loop)")

topic = st.text_input("Enter a research topic", placeholder="e.g. Impact of sleep on exam performance")
run = st.button("Research", type="primary", disabled=not topic.strip())

if run:
    state = {"revisions": 0, "issues": []}
    status_box = st.status("Agents are working...", expanded=True)

    labels = {
        "researcher": "🔎 Researcher finished: searched the web and wrote notes",
        "writer": "✍️ Writer finished: produced a draft",
        "reviewer": "🧐 Reviewer finished: checked the draft against the notes",
    }

    try:
        for node, update in stream_research(topic.strip()):
            state.update(update)
            msg = labels[node]
            if node == "reviewer":
                msg += f" → **{update['verdict']}**"
                for issue in update.get("issues", []):
                    msg += f"\n  - ⚠️ {issue}"
            status_box.write(msg)
        status_box.update(label="Done", state="complete", expanded=False)
    except Exception as e:
        status_box.update(label="Something went wrong", state="error")
        st.error(f"{type(e).__name__}: {e}")
        st.stop()

    if not state.get("notes"):
        st.warning("No search results were found for this topic. Try rephrasing it.")
        st.stop()

    if state.get("verdict") == "REVISE":
        st.warning(
            f"The Reviewer still had concerns after {MAX_REVISIONS} revisions. "
            "Treat the unsupported claims below with caution."
        )
        for issue in state.get("issues", []):
            st.write(f"- {issue}")
    else:
        st.success(f"Approved by Reviewer after {state['revisions']} revision(s).")

    tab1, tab2, tab3, tab4 = st.tabs(["Final Summary", "Researcher Notes", "Sources", "Agent Log"])
    with tab1:
        st.markdown(state["draft"])
        st.download_button("Download as Markdown", state["draft"], file_name="summary.md")
    with tab2:
        st.markdown(state["notes"])
        st.caption("Queries used: " + " | ".join(state.get("queries", [])))
    with tab3:
        for s in state.get("sources", []):
            st.markdown(f"**[{s['id']}]** [{s['title']}]({s['url']})")
    with tab4:
        for line in state.get("log", []):
            st.write("• " + line)
