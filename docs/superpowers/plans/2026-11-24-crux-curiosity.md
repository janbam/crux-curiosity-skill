# Crux Curiosity Implementation Plan

**Goal** — Build a portable skill that can route research, preserve provenance, test competing explanations, and run reversible optimization under an explicit budget.

**Architecture** — A lean entry point and on-demand Markdown protocols coordinate native tools. The evaluation harness runs separately from the installed bundle.

**Tech stack** — Markdown, standard Agent Skills YAML, Python 3.10+ standard library for optional evaluation utilities, Git, Codex and Claude Code for live tests.

**Spec** — [Architecture](../../architecture.md), [research](../../research.md), and [test contract](../../../testing/main.md).

## Sequence and verification

- [x] Commit foundational research, then this architecture and test contract. Review the architecture independently for evidence, experimental validity, portability and recovery before touching the skill. Record challenge, resolution and residual risk.
- [x] Define seven benchmark tasks and deterministic assertions for budget/stopping, provenance, falsification, validation and honest capability reporting. Run fresh no-skill controls on pressure cases. Capture failures with artifacts and real tool traces.
- [x] Implement `SKILL.md`. Route invocation and modes to `references/operations.md`, `evidence.md`, `agents.md`, `experiments.md`, `autoresearch.md`, and `report.md`. Give each reference one decision area and include reusable ledger records where they are used. Use explicit transitions only at risky or irreversible boundaries.
- [x] Run Agent Skills structural validation, reference/link checks, and actual CLI discovery. The harness should install only the bundle in a disposable checkout and run each condition in a fresh session. Real runs require native tool evidence for worker and experiment claims. Exercise fallback when native workers are unavailable and measure execution and cost where surfaced.
- [x] Verify all seven domains with live tasks. Compare the five treatment arms on at least one objective fixture if runtime permits. Spend the reserved improvement budget on a bounded iteration with a frozen evaluator definition, a recorded failure, and a before/after replay. Run a different case as a regression check and state how independent it is.
- [x] Publish README, installation, configuration, examples, contribution instructions, and honest evaluation results. Report fixture and live coverage separately, review all requested deliverables, commit in atomic increments and push using the verified identity.

No CI service, dependency install, platform agent definitions, scheduled job, or license grant is needed for the first private version. Python fixtures or utilities are justified where a deterministic check or reproducible comparison otherwise has to be rebuilt.
