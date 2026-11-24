# Evaluation suite

[cases.json](cases.json) defines research and recovery exercises with concrete checks. Synthetic fixtures let you rerun conflicting-evidence and measurement cases when network access is unavailable. CLI tests use real hosted models and native tools. The authored inputs and measurements from those inputs have different evidence roles.

## Local checks

```sh
python3 -m unittest discover -s evals -p 'test_*.py'
git diff --check
```

An Agent Skills validator can additionally check the bundle against the [specification](https://agentskills.io/specification). Point it at `skills/crux-curiosity/`.

## Live replays

The runner requires Python 3.10+, Git, a POSIX shell environment, and a logged-in CLI. It makes real requests against the active CLI account, so keep elapsed and provider usage budgets in view. Use only the supplied trusted fixtures and installed bundle when running with these permissions. The runner limits the CLI process group locally. It does not prove cancellation of a remote provider operation or isolate tools from the host by itself.

```sh
python3 evals/run.py codex algorithm normal --out eval-output/codex-normal
python3 evals/run.py codex algorithm auto --timeout 240 --out eval-output/codex-auto
python3 evals/run.py claude qualitative fallback --out eval-output/claude-fallback
```

Each run starts a fresh temporary Git workspace. The `normal` condition installs no bundle. Other conditions copy the `skills/crux-curiosity/` folder into that CLI's native discovery path. The evaluator uses fixture-only inputs. Web search is disabled for the pilot, so these runs exercise local evidence paths. The Claude Code fallback omits Agent and shell tools. The Codex fallback sets `agents.enabled=false`. Run outputs include the exact prompt, provider events, stderr, summary and selected research artifacts. Inspect them before sharing.

To check actual source use, run `python3 evals/run.py codex live-sources adaptive --live-web --out eval-output/live-sources`. The read-only case uses live web retrieval. Review the trace and check pivotal claims against the linked source sections.

| Variant | Intended treatment |
| --- | --- |
| `normal` | Ordinary agent, with the fixture's original permissions |
| `adaptive` | Invoke in natural language without selecting a mode |
| `solo` | Deep and zero agents, debate or experiments |
| `debate` | Deep with four requested workers, bounded critique and zero experiment batches |
| `full` | Deep, workers and critique, and two experiment batches |
| `auto` | Full workflow with two optimization attempts and up to four measurement batches |
| `quick`, `fallback`, `loop`, `resume` | Focused evidence, missing worker capability, a standalone optimization loop, and checkpoint reconciliation |

Treat intended and realized treatment separately. Record actual worker launches, completed checks, budget exceedances, failures, and controls. Score each case check 0 for absent or wrong, 1 for partial, and 2 for substantiated. Compare recommendation, evidence accuracy, novelty, experimental validity and reproduction detail, alongside request duration, observed tool calls and provider tokens when available. Record costs per provider without treating different cache, quota or internal pricing semantics as equivalent. The summary fingerprints every installed bundle file before launch and flags changes to the bundle, fixture files, and other files created in the workspace.

For estimates of marginal benefit, use fresh sessions, the same model and task authorization, randomized or counterbalanced order, matched aggregate budgets, and multiple unpublished tasks. Blind reviewers to labels where possible. Scores on this public fixture set provide regression evidence.

### Matched comparisons

Keep a private case file with the same shape as [cases.json](cases.json). Put optional fixtures in a sibling `fixtures/` directory. Each case can declare `tool_profile` as `read-only` (default for new cases), `benchmark` (fixture writes and `python3 bench.py`), or `recovery` (fixture writes). Treat case files and their executable fixtures as trusted. Only the selected request and fixture go into the agent run. Keep grading checks outside the fixture.

```sh
python3 evals/compare.py claude case-a case-b --cases /private/cases.json \
  --model YOUR_MODEL --seed 41 --timeout 90 --max-budget-usd 0.40 \
  --out eval-output/comparison
```

The runner uses one tool surface per case, a shared elapsed ceiling, and a maximum of two workers and two measurement batches. Worker arms request two first passes to keep the comparison meaningful even on easy cases. Real users still get adaptive routing. Claude Code can apply the same provider budget per arm. Compare the terminal status and actual cost against that budget. A replay reported $0.69 with a $0.65 setting before terminating with a budget error. Check the native trace for actual stages and incomplete runs. Run comparisons serially on a shared benchmark machine.

Give a grader only the files under `grade/`. Score the case checks before opening `arm-key.json` or inspecting traces under `runs/`. Method details in the answers can give away the arm. For each arm, publish the decision, missed constraints, checks, realized tool use, time and cost together. Draw conclusions about the evaluated cases and disclose unfinished or contaminated runs.

## Algorithm measurements

The checked-in baseline and benchmark provide a reproducible experiment. The validation split uses new workloads and edge cases, but the evaluator is visible to the agent. This is out-of-sample evidence if it was untouched during candidate selection. Use separately held artifacts and an external evaluator for stronger claims. Inspect candidate code before running it. To reproduce a run, copy the fixture into a temporary workspace and run:

```sh
python3 bench.py --split search --repeat 9
python3 bench.py --split validation --repeat 9
```

Use the same interpreter and machine conditions for comparisons, and report the raw timings and their variability. Speedups from the recorded fixture need not transfer to other workloads or hosts.

### Guarded optimization

Run the search in a fresh candidate workspace, then review and freeze the candidate. Only the public search fixture is copied into the candidate workspace. Run the final evaluator separately after the search session exits.

```sh
python3 evals/run.py codex guarded-membership loop --out eval-output/guarded
python3 evals/guarded_membership.py \
  evals/fixtures/guarded-candidates/value_index.py \
  evals/fixtures/guarded-candidates/query_index.py \
  eval-output/guarded/membership.py
```

The evaluator generates input from a fresh seed and records hashes and raw samples. It tests exact outputs and unchanged inputs, at least 25% lower wide-workload median, at most 64 KiB additional traced Python allocation, and a small-workload batch p95 guard. It alternates timings with the baseline. Timing samples average each batch's calls. Run only reviewed Python candidates because this local evaluator executes them directly. To replay the published samples' input, pass the recorded seed and the [archived candidate](fixtures/guarded-candidates/missing_queries.py). For a new independent check, use a fresh seed.

### Interrupt and recover

```sh
python3 evals/recovery_replay.py prepare eval-output/crashes
for stage in running recorded; do
  python3 evals/run.py codex "$stage" resume \
    --cases eval-output/crashes/cases.json --out "eval-output/resumed-$stage"
  python3 evals/recovery_replay.py verify eval-output/crashes "eval-output/resumed-$stage" "$stage"
done
```

The controller kills a real local trial process during measurement and after its result is written in two separate fixtures. Each CLI session gets a copy of one fixture. The checker compares the resulting checkpoint, the preserved artifacts and the observed write set. Review the trace for new trial dispatches.
