"""Run four matched research conditions and prepare an unlabeled grading packet."""
import argparse
import json
from pathlib import Path
import random
import subprocess
import sys

from run import COMPARISON_ARMS, DEFAULT_BUNDLE, EVALS


def schedule(case_ids, seed):
    assignments = [(case, arm) for case in case_ids for arm in COMPARISON_ARMS]
    random.Random(seed).shuffle(assignments)
    return [(f"answer-{index:02d}", case, arm) for index, (case, arm) in enumerate(assignments, 1)]


def prepare_grading_packet(packet, cases, runs_dir, assignments):
    """Keep the assignment key and tool traces out of the grading directory."""
    case_key = {
        case: {key: cases[case][key] for key in ("request", "checks")}
        for _, case, _ in assignments
    }
    (packet / "cases.json").write_text(json.dumps(case_key, indent=2) + "\n")
    for answer_id, case, _ in assignments:
        summary_path = runs_dir / answer_id / "summary.json"
        summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
        answer = summary.get("answer") or "[No answer captured]"
        (packet / f"{answer_id}.md").write_text(f"Case: {case}\n\n{answer}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backend", choices=("codex", "claude"))
    parser.add_argument("case_ids", nargs="+")
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", required=True, type=Path, help="A new output directory")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--max-budget-usd", type=float, help="Claude Code budget per arm")
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text())
    if len(set(args.case_ids)) != len(args.case_ids) or set(args.case_ids) - cases.keys():
        parser.error("supply distinct IDs from the trusted case file")
    if not 10 <= args.timeout <= 900:
        parser.error("--timeout must be between 10 and 900 seconds")
    budget_options = []
    if args.max_budget_usd is not None:
        if args.backend != "claude" or not 0 < args.max_budget_usd < float("inf"):
            parser.error("--max-budget-usd requires Claude Code and a finite positive amount")
        budget_options = ["--max-budget-usd", str(args.max_budget_usd)]

    assignments = schedule(args.case_ids, args.seed)
    args.out.mkdir(parents=True, exist_ok=False)
    runs_dir = args.out / "runs"
    runs_dir.mkdir()
    packet = args.out / "grade"
    packet.mkdir()
    key = {
        "backend": args.backend,
        "model": args.model,
        "seed": args.seed,
        "timeout_seconds": args.timeout,
        "max_budget_usd": args.max_budget_usd,
        "assignments": {answer_id: {"case": case, "arm": arm} for answer_id, case, arm in assignments},
    }
    (args.out / "arm-key.json").write_text(json.dumps(key, indent=2) + "\n")
    failed = []
    # Serial runs avoid concurrent benchmark activity on the same machine.
    try:
        for answer_id, case, arm in assignments:
            result = subprocess.run([
                sys.executable, str(EVALS / "run.py"), args.backend, case, arm, "--matched",
                "--cases", str(args.cases), "--bundle", str(args.bundle),
                "--timeout", str(args.timeout), "--model", args.model,
                "--out", str(runs_dir / answer_id), *budget_options,
            ], capture_output=True, text=True)
            print(f"{answer_id} ({case}): exit {result.returncode}", flush=True)
            if result.returncode:
                failed.append(answer_id)
                (runs_dir / f"{answer_id}-runner-error.txt").write_text(result.stderr)
    finally:
        prepare_grading_packet(packet, cases, runs_dir, assignments)
    print(f"Grade the answers in {packet} before opening arm-key.json.")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
