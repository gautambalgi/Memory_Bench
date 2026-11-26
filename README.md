# MemoryBench

MemoryBench is a Python and Streamlit workbench for testing what an AI assistant remembers across chats. It uses a Python tutor to compare three memory approaches and lets you inspect what the tutor saw, how it answered, and why each test passed or failed.

## What I built

| View | What you can do |
| --- | --- |
| **Run dashboard** | Give an agent a task and inspect its tool calls, results, errors, and timing. The agent can calculate, count words, and work with files in its run workspace. |
| **Study Assistant** | Practice Python and switch between **Session only**, which uses the current chat, **Saved summary**, which carries a short learner summary into a new chat, and **Retrieved notes**, which looks up individual notes relevant to each question. |
| **Compare** | See the same scenarios side by side, including each tutor's reply, the memory it received, pass or fail reasons, timing, tokens, and estimated cost. |

## What I tested

I validated the agent's tools, error recovery, workspace isolation, and run exports. Then I ran seven Study Assistant scenarios with the same model across all three memory modes. The scenarios test tutoring behavior, recall across chats, updated facts, relevance, and learner isolation.

| Result | Session only | Saved summary | Retrieved notes |
| --- | ---: | ---: | ---: |
| Correct recall across chats | 0/2 | 2/2 | 2/2 after retry |
| Scenarios passed | 7/7 | 6/7 | 7/7 after retry |

Session only passed its recall checks by asking for missing context. Both memory modes recalled the learner's study topic and updated exam date. Saved summary brought up an unrelated study group. Retrieved notes left it out, and its first recall attempt needed a retry after an incomplete model response.

[Agent validation](reports/MemoryBench-V0-validation.md) · [Study scenarios](scenarios/README.md) · [Session-only baseline](reports/Study-Assistant-baseline-v1.md) · [Saved-summary results](reports/Study-Assistant-saved-summary-v1.md) · [Retrieved-notes results](reports/Study-Assistant-retrieved-notes-v1.md)

## Try it locally

Use Python 3.11 or newer. Clone the repo, then create and activate a virtual environment.

```bash
git clone https://github.com/gautambalgi/Memory_Bench.git
cd Memory_Bench
python -m venv .venv
```

Activate it with `source .venv/bin/activate` on macOS or Linux, or `.\.venv\Scripts\Activate.ps1` in Windows PowerShell. Then run:

```bash
python -m pip install -e .
python -m streamlit run app.py
```

Open [localhost:8501](http://localhost:8501). **Compare** and **Guided demo** work without a key. For a live experiment or the **Study Assistant**, expand **OpenAI API key** in the sidebar, enter your own key, and select **Use key for this session**. Live requests are billed to the account that owns the active key. See [.env.example](.env.example) for local configuration.

Runs and learner memory are stored locally in SQLite. Learner profiles are designed for local testing. Anyone with access to the same app instance can select a profile.

## Next

The public demo entry point is `streamlit_demo.py`. It opens **Try a memory scenario**, where visitors can switch memory modes and inspect recorded replies without an API key. **Compare** shows the full results, and **Guided demo** runs the scripted agent example within each visitor's session.

A repeatable runner for all three memory modes is planned.
