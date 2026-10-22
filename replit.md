# Research Assistant for College Students

A Streamlit app that researches a topic, writes a source-grounded summary, and checks it with three LangGraph agents.

## Run & Operate

- `streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true` — run the research assistant
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required secret: `GOOGLE_API_KEY` — Google Gemini API key

## Stack

- Python, Streamlit, LangGraph, Google Gemini, and DuckDuckGo Search

## Where things live

- `agents.py` — researcher, writer, reviewer, and LangGraph flow
- `app.py` — Streamlit interface
- `test_runner.py` — optional five-topic test run; run manually

## Architecture decisions

- Research summaries use only snippets returned by web search; source URLs are shown with the result.
- The reviewer may request at most two writer revisions.
- The Gemini credential belongs in Replit Secrets, never in source files.

## Product

Students can enter a topic, follow the three-agent workflow, read the final summary and researcher notes, inspect sources and agent logs, and download the summary as Markdown.

## User preferences

- Preserve the supplied Python libraries and agent workflow; do not add a database, login, or unrelated features.

## Gotchas

- `GOOGLE_API_KEY` must be added to Replit Secrets before running a research request.
- Do not run `test_runner.py` automatically; run it manually when requested.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
