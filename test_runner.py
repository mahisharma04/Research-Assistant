"""
Runs the 5 planned test topics and saves evidence for the report.
Usage:  python test_runner.py
Output: test_outputs/<topic>.md for each topic + test_outputs/SUMMARY.md
"""
import re
import time
from pathlib import Path

from agents import run_research

TESTS = [
    ("Well-known topic", "Machine learning basics"),
    ("Recent topic", "Latest developments in solar energy"),
    ("Narrow topic", "Impact of sleep on exam performance"),
    ("Vague topic", "Technology"),
    ("Low-information topic", "History of the village of Mulshi's local festivals"),
]

out_dir = Path("test_outputs")
out_dir.mkdir(exist_ok=True)
rows = []

for category, topic in TESTS:
    print(f"\n=== {category}: {topic} ===")
    start = time.time()
    try:
        s = run_research(topic)
        secs = round(time.time() - start, 1)
        slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:50]
        report = (
            f"# {topic}\n\n**Category:** {category}\n"
            f"**Verdict:** {s.get('verdict', 'N/A')}  |  **Revisions:** {s.get('revisions', 0)}  |  "
            f"**Sources:** {len(s.get('sources', []))}  |  **Time:** {secs}s\n\n"
            f"## Agent log\n" + "\n".join(f"- {l}" for l in s.get("log", []))
            + f"\n\n## Final draft\n\n{s.get('draft', '(no draft: no search results)')}\n"
        )
        (out_dir / f"{slug}.md").write_text(report, encoding="utf-8")
        rows.append((category, topic, s.get("verdict", "N/A"), s.get("revisions", 0),
                     len(s.get("sources", [])), secs))
        print("Verdict:", s.get("verdict"), "| Revisions:", s.get("revisions"))
    except Exception as e:
        rows.append((category, topic, f"ERROR: {type(e).__name__}", 0, 0, 0))
        print("Error:", e)

table = "| Category | Topic | Verdict | Revisions | Sources | Time (s) |\n|---|---|---|---|---|---|\n"
table += "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rows)
(out_dir / "SUMMARY.md").write_text(table, encoding="utf-8")
print("\n" + table)
