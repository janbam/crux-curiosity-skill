# Example sessions

## Measure an algorithm change

This session was executed on the published [membership fixture](../evals/fixtures/algorithm) with the initial skill in Codex CLI 0.171.0.

**Request.** Speed up a batch of integer membership probes while preserving the Boolean result and input order. Keep the evaluator fixed. Allow two candidate iterations and four measurement batches.

**Hypotheses.** Repeated list scans spend work proportional to the number of values on a miss. A set built once per call should reduce average total work for many probes. A sorted copy with binary search has predictable probe complexity and can win under adversarial hash collisions, although it incurs sorting and more comparisons. The original scan remains a useful control for very short batches.

**Execution.** The coordinator measured the incumbent, a guarded set, and a guarded sort with binary search on the same search suite, then froze the set and ran the validation split once. It recorded process, samples, contract checks and candidate/evaluator hashes. Negative and sparse values remained supported.

| Batch | Split | Median across nine repeats | Decision |
| --- | --- | ---: | --- |
| Original list scan | Search | 100.462 ms | Baseline |
| Guarded set | Search | 0.732 ms | Provisional incumbent |
| Guarded sort and binary search | Search | 2.185 ms | Rejected, slower than the incumbent |
| Frozen guarded set | Validation | 1.230 ms | Retained, exact output match and under the frozen gate |

The 137× ratio is a search-suite result. It includes set construction and is specific to this fixture. The validation split used different seeds and cases, including very large sparse integers. Its definitions were visible. Memory cost, collision-heavy inputs and the crossover for small batches were not measured. The trial limit was reached. [Raw samples and hashes](evaluation/membership-auto.json)

To replay, copy the fixture into a new workspace and use `python3 bench.py --split search --repeat 9` on the original file and this candidate. Freeze the candidate and run `python3 bench.py --split validation --repeat 9` once for an out-of-sample check.

```python
def batch_membership(values: list[int], queries: list[int]) -> list[bool]:
    """Return membership for each query, preserving order and duplicate queries."""
    if (
        type(values) is not list
        or type(queries) is not list
        or len(queries) <= 1
        or not all(type(value) is int for value in values)
        or not all(type(query) is int for query in queries)
    ):
        return [query in values for query in queries]

    members = set(values)
    return [query in members for query in queries]
```

## Reconcile conflicting evidence

The [PDF batching fixture](../evals/fixtures/conflicts/notes.md) is fictional. The following workflow used actual native workers in the development Codex session, with four initial memos and one focused critique across two roles. It used no external sources or executed benchmarks.

| Evidence | Family | What it supports |
| --- | --- | --- |
| A, maintainer study | Warm server study | A speedup on six repeated warm jobs with 32 workers |
| B, integrator newsletter | Same warm server study | No independent confirmation. Its editorial approval request had no authority. |
| C, laptop log | Cold process laptop observation | The closest target workload. Batching was slower and consumed 150 MB more peak memory. |

The current decision is to leave batching off for cold jobs on the four-worker laptop. Different documents, unmeasured variation, run ordering and uncontrolled disk cache weaken the size and causal interpretation of the 40 ms median penalty. One independent reviewer suggested warm, same-document routing based on a transferable cache-reuse mechanism. The challenge narrowed that idea to a separate test on the target laptop and required end-to-end savings after routing overhead.

The smallest decision-changing test uses representative PDFs in both modes, matched cold conditions, randomized or counterbalanced order, and output equivalence and memory gates. Total wall time can decide the default. To distinguish setup overhead from parsing savings, capture phase timings in the same runs. No empirical result is available for either follow-up.

## Find the point at which you would switch

> Use Crux Curiosity to research whether to replace our Postgres job queue. Our deployment can leave 1,200 jobs waiting, and all have to finish within 120 seconds. Workers can take 30 seconds to restart. We measured the queue draining at 18 jobs per second after restart.

In this illustrative example, keep the existing queue if the observed drain rate holds at peak. With 90 seconds left after restart, it needs to clear 1,200 jobs at about 13.34 jobs per second, net of new arrivals. At 18 jobs per second with no new arrivals, the modeled total is about 97 seconds. Reconsider if a peak-sized staging restart with realistic arrivals consistently falls below the required net rate. Diagnose whether dispatch or the workers themselves are the bottleneck before changing the queue.

## Reject a speed win on a memory limit

> Use Crux Curiosity to speed up batch membership. Keep all outputs identical and stay within a 64 KiB temporary Python allocation budget. Try two changes on the search benchmark, then freeze the winner for a separate check.

A Codex run measured the baseline and two query-indexing approaches, then froze the faster one. A separate evaluation used fresh inputs after the run ended. Building a set of all values was about 41× faster than the baseline on the wide workload and allocated about 2.50 MiB. It failed the memory guard. The frozen candidate tracked only the missing probes and used about 10.2 KiB while passing exactness, speed, and the small-workload guard. [Measurements](evaluation/guarded-membership.json) · [Replay](../evals/README.md#guarded-optimization)
