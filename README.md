# Research Assistant for College Students (3-Agent System)

Researcher -> Writer -> Reviewer (with a revision loop, max 2 times).

## Setup
1. Create and activate a virtual environment, then install dependencies:
   `python -m venv .venv` and `pip install -r requirements.txt`
2. For local use, put your Gemini key in a `.env` file:
   `GOOGLE_API_KEY=your_key_here`
3. Run locally with `streamlit run app.py --server.port 5000`
4. To deploy, create an app at [Streamlit Community Cloud](https://share.streamlit.io/)
   from `mahisharma04/Research-Assistant`, branch `main`, file `app.py`.
   Add this in the app's Settings > Secrets before deploying:
   `GOOGLE_API_KEY = "your_key_here"`
5. Run the tests manually with `python test_runner.py`.

Never commit `.env` or Streamlit `secrets.toml` files. The default model is
`gemini-3.6-flash`; set `GEMINI_MODEL` to use another supported model.

## Files
- `agents.py`: the three agents, the search tool, and the LangGraph workflow
- `app.py`: Streamlit frontend
- `test_runner.py`: runs 5 test topics and saves outputs in `test_outputs/`
