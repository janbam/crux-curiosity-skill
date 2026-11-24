"""Run one fresh CLI evaluation and retain its raw trace outside the workspace."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time

EVALS = Path(__file__).resolve().parent
DEFAULT_CASES = EVALS / "cases.json"
CASES = json.loads(DEFAULT_CASES.read_text())
VARIANTS = {
    "normal": "",
    "adaptive": "",
    "quick": "mode=quick subagents=0 experiments=0",
    "solo": "mode=deep subagents=0 debate_rounds=0 experiments=0",
    "debate": "mode=deep subagents=4 debate_rounds=1 experiments=0",
    "full": "mode=deep subagents=4 debate_rounds=1 experiments=2 iterations=0",
    "auto": "mode=deep subagents=4 debate_rounds=1 experiments=4 iterations=2 autoresearch=on",
    "fallback": "mode=deep subagents=4 debate_rounds=1 experiments=0",
    "loop": "mode=autoresearch subagents=0 experiments=4 iterations=2",
    "resume": "mode=autoresearch",
}
COMPARISON_ARMS = {
    "normal": "",
    "solo": "mode=deep subagents=0 debate_rounds=0 experiments=0",
    "debate": "mode=deep subagents=2 debate_rounds=1 experiments=0",
    "full": "mode=deep subagents=2 debate_rounds=1 experiments=2 iterations=0",
}


def tool_profile(args):
    if args.case_spec.get("tool_profile"):
        return args.case_spec["tool_profile"]
    return {"algorithm": "benchmark", "recovery": "recovery"}.get(args.case, "read-only")


def installed_skill(workspace, backend):
    discovery = ".agents" if backend == "codex" else ".claude"
    return workspace / discovery / "skills" / "crux-curiosity"


def file_digests(root):
    files = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts[0] == ".git" or "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            files[relative.as_posix()] = f"symlink:{os.readlink(path)}"
        elif path.is_file():
            files[relative.as_posix()] = digest(path)
    return files


def bundle_fingerprint(skill_dir):
    files = file_digests(skill_dir)
    manifest = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {"sha256": hashlib.sha256(manifest).hexdigest(), "files": files}


def prepare(workspace, args):
    subprocess.run(["git", "init", "-q", str(workspace)], check=True)
    fixture = args.case_spec.get("fixture")
    if fixture:
        shutil.copytree(
            args.cases.parent / "fixtures" / fixture, workspace, dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    fixture_hashes = file_digests(workspace)
    if args.variant == "normal":
        return fixture_hashes
    skill_dir = installed_skill(workspace, args.backend)
    skill_dir.mkdir(parents=True)
    shutil.copy2(args.bundle / "SKILL.md", skill_dir)
    license_file = args.bundle / "LICENSE"
    if license_file.is_file():
        shutil.copy2(license_file, skill_dir)
    shutil.copytree(args.bundle / "references", skill_dir / "references")
    return fixture_hashes


def invocation(args):
    request = args.case_spec["request"]
    if args.variant != "normal":
        prefix = "$" if args.backend == "codex" else "/"
        settings = COMPARISON_ARMS if args.matched else VARIANTS
        if args.variant == "adaptive" and args.backend == "codex":
            skill_request = "Use the crux-curiosity skill for this research."
        else:
            options = f" {settings[args.variant]}" if settings[args.variant] else ""
            skill_request = f"{prefix}crux-curiosity{options}"
        searches = 4 if args.live_web else 0
        request = (
            f"{skill_request} "
            f"searches={searches} minutes={args.timeout / 60:.2f} (elapsed target).\n\n{request}"
        )
        if tool_profile(args) == "read-only":
            request += "\nKeep any research records in the final answer for this test."
    if args.matched:
        request += (
            f"\nThe shared ceilings are {args.timeout} seconds, zero web searches, "
            "up to two native workers and two allowed measurement batches. "
            "Use only stages admitted by your task and any narrower limits. "
            "Keep the answer focused on the decision, evidence, caveats, and actual work. "
            "Omit the evaluation condition name, skill name, and mode label."
        )
        if args.variant == "normal":
            request += " Work solo. Use permitted measurements when they would change the answer."
        if args.variant in {"debate", "full"}:
            request += (
                " This condition requires two fresh native workers for distinct first-pass checks. "
                "Dispatch them before synthesizing if the tool is available. Report any actual blocker. "
                "Use a focused critique only if their findings materially disagree."
            )
    return request


def command_line(args):
    profile = tool_profile(args)
    if args.backend == "codex":
        writable = profile != "read-only"
        sandbox = "workspace-write" if writable else "read-only"
        web_search = "live" if args.live_web else "disabled"
        command = [
            "codex", "-a", "never", "exec", "--ignore-user-config",
            "--ephemeral", "--json", "-s", sandbox, "-c", f'web_search="{web_search}"',
            "-c", 'sandbox_workspace_write.network_access=false',
        ]
        if args.variant == "fallback":
            command.extend(["-c", "agents.enabled=false"])
        if args.model:
            command.extend(["--model", args.model])
        return command + ["-"]

    allowed = ["Read", "Glob", "Grep", "Skill"]
    if profile != "read-only":
        allowed.extend(["Write", "Edit"])
    if args.matched or args.variant in {"adaptive", "debate", "full", "auto"}:
        allowed.append("Agent")
    command = [
        "claude", "-p", "--setting-sources", "project", "--strict-mcp-config",
        "--mcp-config", '{"mcpServers":{}}', "--no-session-persistence",
        "--tools", ",".join(allowed), "--effort", "low",
        "--output-format", "stream-json", "--verbose",
        "--permission-mode", "dontAsk",
    ]
    if profile == "benchmark":
        command[command.index("--tools") + 1] += ",Bash"
        command.extend([
            "--allowedTools", "Read,Glob,Grep,Skill,Edit,Write,Bash(python3 bench.py *)",
        ])
    if args.model:
        command.extend(["--model", args.model])
    if args.max_budget_usd is not None:
        command.extend(["--max-budget-usd", str(args.max_budget_usd)])
    return command + ["--"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(command, prompt, workspace, output, timeout):
    started = time.monotonic()
    timed_out = False
    with (output / "events.jsonl").open("w") as stdout, (output / "stderr.log").open("w") as stderr:
        process = subprocess.Popen(
            command, cwd=workspace, stdin=subprocess.PIPE, stdout=stdout,
            stderr=stderr, text=True, start_new_session=True,
        )
        try:
            process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
    return process.returncode, timed_out, round(time.monotonic() - started, 3)


def summarize(trace, backend):
    result = {"usage": None, "model": None, "tools": [], "answer": None}
    for line in trace.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if backend == "codex":
            if kind == "turn.completed":
                result["usage"] = event.get("usage")
            if kind != "item.completed":
                continue
            item = event.get("item", {})
            item_kind = item.get("type")
            if item_kind == "agent_message":
                result["answer"] = item["text"]
            elif item_kind in {"command_execution", "collab_tool_call", "file_change", "mcp_tool_call", "web_search", "dynamic_tool_call"}:
                fields = ("type", "tool", "command", "exit_code", "status", "receiver_thread_ids",
                          "agents_states", "query", "action")
                result["tools"].append({key: item[key] for key in fields if key in item})
        else:
            subtype = event.get("subtype")
            if kind == "system" and subtype == "init":
                result["model"] = event.get("model")
                result["listed_skills"] = event.get("skills")
                result["listed_commands"] = event.get("slash_commands")
            elif kind == "system" and subtype in {"task_started", "task_notification"}:
                keys = ("subtype", "task_id", "status", "tool_use_id")
                task_event = {key: event[key] for key in keys if key in event}
                result.setdefault("native_task_events", []).append(task_event)
            elif kind == "assistant":
                for block in event.get("message", {}).get("content", []):
                    if block.get("type") == "tool_use":
                        tool_input = block.get("input", {})
                        detail_keys = ("file_path", "command", "skill", "subagent_type", "description")
                        result["tools"].append({
                            "tool": block["name"],
                            "id": block.get("id"),
                            **{key: tool_input[key] for key in detail_keys if key in tool_input},
                        })
            elif kind == "result":
                keys = ("result", "usage", "subtype", "duration_ms", "total_cost_usd")
                segment = {key: event[key] for key in keys if key in event}
                segments = result.setdefault("result_segments", [])
                segments.append(segment)
                if len(segments) == 1:
                    result["usage"] = event.get("usage")
                    result["answer"] = event.get("result")
                    result["provider_subtype"] = subtype
                result["provider_terminal_subtype"] = subtype
                result["provider_cost_usd"] = event.get("total_cost_usd")
    return result


def copy_artifacts(workspace, output):
    names = ("membership.py", "membership-research.md", ".research")
    paths = [workspace / name for name in names]
    for path in paths:
        if path.is_file() and not path.is_symlink():
            shutil.copy2(path, output / path.name)
        elif path.is_dir() and not path.is_symlink():
            shutil.copytree(path, output / path.name, symlinks=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backend", choices=("codex", "claude"))
    parser.add_argument("case", help=f"Case ID (defaults include {', '.join(CASES)})")
    parser.add_argument("variant", choices=VARIANTS)
    parser.add_argument("--timeout", type=int, default=150)
    parser.add_argument("--model")
    parser.add_argument("--bundle", type=Path, default=EVALS.parent)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="Trusted case JSON")
    parser.add_argument("--matched", action="store_true", help="Use the four-arm comparison protocol")
    parser.add_argument("--live-web", action="store_true", help="Enable Codex live retrieval for a read-only case")
    parser.add_argument("--max-budget-usd", type=float, help="Claude Code request budget")
    parser.add_argument("--out", type=Path, required=True, help="A new output directory")
    args = parser.parse_args()
    if not 10 <= args.timeout <= 900:
        parser.error("--timeout must be between 10 and 900 seconds")
    if args.matched and args.variant not in COMPARISON_ARMS:
        parser.error("--matched requires normal, solo, debate or full")
    if args.max_budget_usd is not None and not (args.backend == "claude" and 0 < args.max_budget_usd < float("inf")):
        parser.error("--max-budget-usd requires Claude Code and a finite positive amount")
    cases = json.loads(args.cases.read_text())
    if args.case not in cases:
        parser.error(f"unknown case {args.case!r}")
    args.case_spec = cases[args.case]
    if tool_profile(args) not in {"read-only", "benchmark", "recovery"}:
        parser.error("invalid tool profile")
    if args.live_web and (args.backend != "codex" or args.matched or tool_profile(args) != "read-only"):
        parser.error("--live-web requires a non-comparison, read-only Codex case")

    version = subprocess.check_output([args.backend, "--version"], text=True).strip()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    prompt = invocation(args)
    (output / "request.txt").write_text(prompt)
    with tempfile.TemporaryDirectory(prefix="crux-curiosity-") as scratch:
        workspace = Path(scratch)
        fixture_hashes = prepare(workspace, args)
        skill_dir = installed_skill(workspace, args.backend)
        bundle_before = bundle_fingerprint(skill_dir) if args.variant != "normal" else None
        returncode, timeout, elapsed = execute(command_line(args), prompt, workspace, output, args.timeout)
        workspace_after = file_digests(workspace)
        result = summarize(output / "events.jsonl", args.backend)
        result.update({
            "backend": args.backend, "version": version, "case": args.case, "variant": args.variant,
            "elapsed_seconds": elapsed, "returncode": returncode, "timed_out": timeout,
            "matched": args.matched, "live_web": args.live_web, "timeout_seconds": args.timeout,
            "max_budget_usd": args.max_budget_usd,
            "model_override": args.model, "initial_fixture_hashes": fixture_hashes,
            "altered_fixture_files": [
                name for name, before in fixture_hashes.items()
                if workspace_after.get(name) != before
            ],
            "unexpected_approval_file": (workspace / "APPROVED").exists(),
        })
        if bundle_before is not None:
            bundle_after = bundle_fingerprint(skill_dir)
            result["skill_sha256"] = bundle_before["files"]["SKILL.md"]
            result["bundle"] = bundle_before
            result["altered_bundle_files"] = sorted(
                name for name in bundle_before["files"].keys() | bundle_after["files"].keys()
                if bundle_before["files"].get(name) != bundle_after["files"].get(name)
            )
        skill_prefix = skill_dir.relative_to(workspace).as_posix() + "/"
        result["new_workspace_files"] = sorted(
            name for name in workspace_after.keys() - fixture_hashes.keys()
            if bundle_before is None or not name.startswith(skill_prefix)
        )
        copy_artifacts(workspace, output)
    (output / "summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"{args.backend}/{args.case}/{args.variant}: {elapsed:.1f}s, exit {returncode}, {output}")
    return returncode if returncode >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
