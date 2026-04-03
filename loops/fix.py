import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def agent(prompt_file: str, context: str) -> dict:
    prompt = (ROOT / prompt_file).read_text()
    result = subprocess.run(
        ["claude", "-p", f"{context}\n\n---\n\n{prompt}", "--output-format", "json"],
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def next_open_issue() -> int | None:
    result = subprocess.run(
        ["gh", "issue", "list", "--label", "agent", "--json", "number", "--limit", "1"],
        capture_output=True,
        text=True,
        check=True,
    )
    issues = json.loads(result.stdout)
    return issues[0]["number"] if issues else None


def issue_context(issue_number: int) -> str:
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--json", "number,title,body,labels"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def open_pr(impl: dict) -> None:
    subprocess.run([
        "gh", "pr", "create",
        "--title", impl["pr_title"],
        "--body", impl["pr_body"],
        "--head", impl["branch"],
    ], check=True)


def run_fix(issue_number: int | None = None, max_rounds: int = 10) -> None:
    if issue_number is None:
        issue_number = next_open_issue()
    if issue_number is None:
        print("[fix] no open issues to fix")
        return

    context = issue_context(issue_number)

    for round_n in range(max_rounds):
        # Implement (fresh context window)
        impl = agent("prompts/implement.md", context)

        # Review (fresh context window)
        reviewed = agent("prompts/review.md", json.dumps(impl))

        if reviewed["approved"]:
            open_pr(impl)
            print(f"[fix] issue #{issue_number}: PR opened ({impl['pr_title']})")
            return

        print(f"[fix] round {round_n + 1}: revision needed — {reviewed['feedback']}")
        # Feed reviewer feedback back into next implementation round
        context = json.dumps({"issue": json.loads(issue_context(issue_number)), "feedback": reviewed["feedback"]})

    print(f"[escalate] issue #{issue_number}: did not converge after {max_rounds} rounds", file=sys.stderr)
    sys.exit(1)
