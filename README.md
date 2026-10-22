# Research Assistant for College Students (3-Agent System)

Researcher -> Writer -> Reviewer (with a revision loop, max 2 times).

## Setup
1. `python -m venv venv` then activate it
2. `pip install -r requirements.txt`
3. Add your Gemini API key as the `GOOGLE_API_KEY` Replit Secret
4. Run the app: `streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true`
5. Run the tests (evidence for report): `python test_runner.py`

## Files
- `agents.py`: the three agents, the search tool, and the LangGraph workflow
- `app.py`: Streamlit frontend
- `test_runner.py`: runs 5 test topics and saves outputs in `test_outputs/`
