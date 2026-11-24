"""Offline checks for the bundle, fixture, and CLI evaluation wrapper."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import re
import signal
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

import compare
import guarded_membership
import recovery_replay
import run

ROOT = Path(__file__).resolve().parents[1]
SKILL = run.DEFAULT_BUNDLE


class BundleTests(unittest.TestCase):
    def test_local_markdown_links_resolve(self):
        pages = [
            SKILL / "SKILL.md", ROOT / "README.md", ROOT / "CONTRIBUTING.md",
            ROOT / "evals" / "README.md", ROOT / "docs" / "installation.md",
            ROOT / "docs" / "examples.md", *sorted((SKILL / "references").glob("*.md")),
        ]
        for page in pages:
            content = re.sub(r"^\x60{3}.*?^\x60{3}\s*$", "", page.read_text(), flags=re.MULTILINE | re.DOTALL)
            for target in re.findall(r"\]\(([^)\s]+)\)", content):
                location = urlsplit(target)
                if location.scheme or location.netloc:
                    continue
                destination = page.parent / unquote(location.path) if location.path else page
                with self.subTest(page=page.relative_to(ROOT), target=target):
                    self.assertTrue(destination.exists(), f"Missing Markdown link target: {destination}")
                    if location.fragment and destination.suffix == ".md":
                        headings = re.findall(r"^#{1,6}\s+(.+)$", destination.read_text(), re.MULTILINE)
                        anchors = {re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-") for heading in headings}
                        self.assertIn(unquote(location.fragment), anchors)

    def test_metadata_and_progressive_links(self):
        skill = (SKILL / "SKILL.md").read_text()
        delimiter, metadata, body = skill.split("---\n", 2)
        self.assertEqual(delimiter, "")
        fields = dict(line.split(": ", 1) for line in metadata.strip().splitlines())
        self.assertEqual(fields["name"], "crux-curiosity")
        self.assertEqual(fields["license"], "MIT")
        self.assertTrue((ROOT / "LICENSE").read_text().startswith("MIT License\n"))
        self.assertRegex(fields["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        # The spec requires the skill folder to carry the skill's name.
        self.assertEqual(SKILL.name, fields["name"])
        self.assertLessEqual(len(fields["name"]), 64)
        self.assertTrue(0 < len(fields["description"]) <= 1024)
        self.assertLessEqual(len(body.splitlines()), 100)
        referenced = {Path(path).name for path in re.findall(r"\]\((references/[^)#]+)", body)}
        available = {path.name for path in (SKILL / "references").glob("*.md")}
        self.assertEqual(referenced, available)

    def test_native_bundle_installation_and_control(self):
        for host, folder in [("codex", ".agents"), ("claude", ".claude")]:
            for variant in ["quick", "normal"]:
                with self.subTest(host=host, variant=variant), tempfile.TemporaryDirectory() as scratch:
                    workspace = Path(scratch)
                    args = argparse.Namespace(
                        backend=host, case="algorithm", variant=variant, bundle=SKILL,
                        cases=run.DEFAULT_CASES, case_spec=run.CASES["algorithm"],
                    )
                    initial = run.prepare(workspace, args)
                    skill = workspace / folder / "skills" / "crux-curiosity"
                    self.assertEqual((skill / "SKILL.md").exists(), variant != "normal")
                    self.assertEqual(set(initial), {"membership.py", "bench.py"})
                    self.assertFalse((workspace / "cases.json").exists())
                    if variant != "normal":
                        # The installed bundle is exactly the shipped skill folder, license included.
                        self.assertEqual(run.file_digests(skill), run.file_digests(SKILL))
                        self.assertTrue((skill / "LICENSE").read_text().startswith("MIT License\n"))
                        before = run.bundle_fingerprint(skill)
                        (skill / "references" / "report.md").write_text("changed reference\n")
                        after = run.bundle_fingerprint(skill)
                        self.assertNotEqual(before["sha256"], after["sha256"])
                        self.assertEqual(before["files"]["SKILL.md"], after["files"]["SKILL.md"])


class RunnerTests(unittest.TestCase):
    def test_grading_packet_excludes_assignments_and_tool_traces(self):
        assignments = compare.schedule(["private"], seed=7)
        self.assertEqual({arm for _, _, arm in assignments}, set(run.COMPARISON_ARMS))
        self.assertEqual(assignments, compare.schedule(["private"], seed=7))
        with tempfile.TemporaryDirectory() as scratch:
            output = Path(scratch)
            packet = output / "grade"
            packet.mkdir()
            answer_id, _, arm = assignments[0]
            run_dir = output / answer_id
            run_dir.mkdir()
            (run_dir / "summary.json").write_text(json.dumps({
                "answer": "Use the incumbent.", "variant": arm, "tools": ["private trace"],
            }))
            compare.prepare_grading_packet(
                packet, {"private": {"request": "Task", "checks": ["Rubric"]}}, output, assignments,
            )
            self.assertEqual((packet / f"{answer_id}.md").read_text(), "Case: private\n\nUse the incumbent.\n")
            self.assertIn("Rubric", (packet / "cases.json").read_text())
            self.assertEqual(len(list(packet.iterdir())), 5)

    def test_matched_arms_share_tool_surface_and_hide_rubric(self):
        for host in ("codex", "claude"):
            commands = []
            for variant in run.COMPARISON_ARMS:
                args = argparse.Namespace(
                    backend=host, case="private", variant=variant, timeout=75,
                    matched=True, model="fixed", max_budget_usd=None, live_web=False,
                    case_spec={"request": "Trusted task", "checks": ["private grading key"], "tool_profile": "benchmark"},
                )
                prompt = run.invocation(args)
                self.assertIn("Trusted task", prompt)
                self.assertIn("75 seconds", prompt)
                self.assertNotIn("private grading key", prompt)
                self.assertEqual("requires two fresh native workers" in prompt, variant in {"debate", "full"})
                commands.append(run.command_line(args))
            self.assertTrue(all(command == commands[0] for command in commands))

    def test_timeout_preserves_trace_and_does_not_hang(self):
        with tempfile.TemporaryDirectory() as scratch:
            workspace = Path(scratch)
            command = [sys.executable, "-c", "import time; print('started', flush=True); time.sleep(20)"]
            status, timed_out, elapsed = run.execute(command, "", workspace, workspace, 0.5)
            self.assertTrue(timed_out)
            self.assertNotEqual(status, 0)
            self.assertLess(elapsed, 5)
            self.assertIn("started", (workspace / "events.jsonl").read_text())

    def test_summary_extracts_native_events_without_inventing_them(self):
        fixtures = {
            "codex": [
                {"type": "item.completed", "item": {"type": "collab_tool_call", "tool": "spawn_agent",
                    "status": "completed", "receiver_thread_ids": ["example"]}},
                {"type": "item.completed", "item": {"type": "agent_message", "text": "Example verdict"}},
                {"type": "turn.completed", "usage": {"input_tokens": 41}},
            ],
            "claude": [
                {"type": "system", "subtype": "init", "skills": ["crux-curiosity"], "model": "example"},
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "name": "Task", "input": {"description": "Read independently"}},
                ]}},
                {"type": "system", "subtype": "task_notification", "status": "completed"},
                {"type": "result", "subtype": "success", "result": "Example verdict", "usage": {"input_tokens": 41}},
                {"type": "result", "subtype": "success", "result": "Late reviewer note", "usage": {"input_tokens": 9}},
                {"type": "result", "subtype": "error_max_budget_usd", "total_cost_usd": 0.69},
            ],
        }
        with tempfile.TemporaryDirectory() as scratch:
            trace = Path(scratch) / "events.jsonl"
            for host, events in fixtures.items():
                with self.subTest(host=host):
                    trace.write_text("\n".join(map(json.dumps, events)))
                    result = run.summarize(trace, host)
                    self.assertEqual(result["answer"], "Example verdict")
                    self.assertEqual(result["usage"]["input_tokens"], 41)
                    self.assertEqual(len(result["tools"]), 1)
                    expected_tool = "spawn_agent" if host == "codex" else "Task"
                    self.assertEqual(result["tools"][0]["tool"], expected_tool)
                    if host == "claude":
                        self.assertEqual(result["result_segments"][1]["result"], "Late reviewer note")
                        self.assertEqual(result["native_task_events"][0]["status"], "completed")
                        self.assertEqual(result["provider_subtype"], "success")
                        self.assertEqual(result["provider_terminal_subtype"], "error_max_budget_usd")
                        self.assertEqual(result["provider_cost_usd"], 0.69)

    def test_live_web_remains_read_only_and_records_search_actions(self):
        args = argparse.Namespace(
            backend="codex", case="live-sources", variant="adaptive", timeout=80,
            matched=False, model=None, live_web=True, case_spec=run.CASES["live-sources"],
        )
        command = run.command_line(args)
        self.assertIn('web_search="live"', command)
        self.assertIn("read-only", command)
        self.assertIn("searches=4", run.invocation(args))
        with tempfile.TemporaryDirectory() as scratch:
            trace = Path(scratch) / "events.jsonl"
            item = {"type": "web_search", "query": "official documentation"}
            trace.write_text(json.dumps({"type": "item.completed", "item": item}))
            self.assertEqual(run.summarize(trace, "codex")["tools"], [item])


class FixtureTests(unittest.TestCase):
    def test_real_interruption_preserves_only_published_trial_results(self):
        with tempfile.TemporaryDirectory() as scratch:
            output = Path(scratch) / "cases"
            recovery_replay.prepare(output)
            for stage in recovery_replay.STAGES:
                run_dir = output / "fixtures" / stage / recovery_replay.RUN
                self.assertIn("One launch of T02", (run_dir / "started.md").read_text())
                self.assertIn(
                    f"return code {-signal.SIGKILL}", (run_dir / "process.md").read_text(),
                )
                self.assertEqual((run_dir / "trials" / "T02.md").exists(), stage == "recorded")
                self.assertIn("Active attempt: T02", (run_dir / "state.md").read_text())

    def test_guarded_membership_detects_memory_regression_despite_exact_outputs(self):
        wide, small = guarded_membership.workload(41)
        candidates = ROOT / "evals" / "fixtures" / "guarded-candidates"
        _, value_index = guarded_membership.load_frozen(candidates / "value_index.py")
        _, query_index = guarded_membership.load_frozen(candidates / "query_index.py")
        for candidate in (value_index, query_index):
            self.assertTrue(guarded_membership.exact_match(candidate, wide + small))
        self.assertGreater(guarded_membership.peak_traced_bytes(value_index, wide), guarded_membership.MEMORY_CAP)
        self.assertLessEqual(guarded_membership.peak_traced_bytes(query_index, wide), guarded_membership.MEMORY_CAP)
        self.assertFalse(guarded_membership.exact_match(lambda values, queries: [0] * len(queries), small))

    def test_algorithm_contract(self):
        source = ROOT / "evals" / "fixtures" / "algorithm" / "membership.py"
        spec = importlib.util.spec_from_file_location("membership", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        values = [1, 1, -10**30]
        queries = [0, 1, -10**30, 1, 10**30]
        self.assertEqual(module.batch_membership(values, queries), [False, True, True, True, False])
        self.assertEqual(values, [1, 1, -10**30])
        self.assertEqual(queries, [0, 1, -10**30, 1, 10**30])
        self.assertEqual(module.batch_membership([], []), [])

    def test_profile_fixture_cannot_meet_target_through_parser_only(self):
        source = ROOT / "evals" / "fixtures" / "performance" / "profile.csv"
        with source.open() as stream:
            rows = list(csv.DictReader(stream))
        for state, expected in [("warm", (129, 122)), ("cold", (212, 206))]:
            cohort = [row for row in rows if row["state"] == state]
            self.assertEqual(len(cohort), 30)
            total = sorted(int(row["total_ms"]) for row in cohort)
            no_parse = sorted(int(row["total_ms"]) - int(row["parse_ms"]) for row in cohort)
            self.assertEqual((total[28], no_parse[28]), expected)
            self.assertLess((total[28] - no_parse[28]) / total[28], 0.10)


if __name__ == "__main__":
    unittest.main()
