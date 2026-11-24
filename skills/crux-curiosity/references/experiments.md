# Controlled verification

Find the smallest authorized test that could change the decision. Options include a direct source check, analytical bound, reproducible simulation, microbenchmark, profiling, stress test, small prototype, ablation or controlled comparison. Cite source observations as such. A test executed against toy data gives evidence for that toy setting. Keep a possible real-world follow-up distinct from observed results.

## Before running

Freeze an experiment record so results cannot silently change the goalposts.

```text
Trial ID | H-IDs and decision at stake | authorization + owned paths
Baseline and candidate revision, input/data/config identifiers, environment
Treatment, experimental unit, controls, repeats, seed/order/warm-up strategy
Metric, direction, practical threshold, correctness/resource/no-regression guards
Predictions by hypothesis, identification assumptions and inconclusive outcomes
Evaluation command, timeout and reserved resources | expected outcome actions
Raw log destination | search/confirmation/validation split and access boundary
```

Use the actual incumbent or a credible simplest alternative. Establish correctness before timing. Change one factor for a cheap causal check, or use randomized blocks or a factorial design when interactions matter. Prevent confounding by matching tools, versions, input, resources and measurement window. Randomize or alternate paired orders as appropriate. Measure variance at the independent unit and record warmup, cache, thermal state and resource contention where relevant. Serial measurement can be more valid than parallel runs on the same hardware. Predeclare input selection, stopping/count rules and treatment of failures. Avoid extrapolating microbenchmarks or simulations without an applicability argument.

Review code and provenance. Use safe local fixtures, an isolated scope for edits and timeouts. Restrict network, permissions and secrets where the host supports it. Maintain source and evaluator integrity. A Git worktree isolates file changes but does not sandbox processes. Skip experiments if authorization, safety, or meaningful measurement is absent.

## After running

```text
Trial ID | execution status and command | actual revisions and conditions
Raw samples/errors | measured usage | effect with units and variability
Guard outcomes and validity limits | result (support / weaken / inconclusive / invalid)
Observed effect vs causal interpretation | H-ID updates | next decision
```

Verify raw results and errors against the frozen protocol. Report paired effects, sample sizes, distribution or interval as appropriate and baseline values alongside deltas. A significance calculation cannot correct nonindependent units, selection on the maximum, changed measurement or confounding. For exploratory runs, state what further check would be needed to trust a result. A failed command is an execution outcome. Record whether it actually tests the scientific hypothesis.

For a quantitative test that cannot run, provide the exact constraint and optionally a protocol. For qualitative or value-laden work, compare mechanisms and alternatives with evidence, costs, sensitivity to priorities, reversible options and a concrete next observation. Leave unmeasured outcomes unverified.
