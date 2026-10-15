"""Tasks shared by the dashboard, CLI, and guided demo."""

DEMO_TASK = (
    "Calculate the total cost of 18 agent runs at $0.24 each plus 7 runs at $0.61 each. "
    "Save a short summary to experiment.txt, then read it back to verify it."
)
SAMPLE_TASKS = {
    "Run a small experiment": DEMO_TASK,
    "Check a paragraph": (
        "Count the words and characters in 'Good memory starts with a clear record.' "
        "Save the counts to paragraph.txt and verify the file."
    ),
    "Compare two budgets": (
        "Use the calculator to compare 120 * 0.035 with 80 * 0.062. "
        "Tell me which budget is lower and by how much."
    ),
}
