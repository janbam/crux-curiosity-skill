# Run setup, limits, and recovery

Use this reference for escalation, Deep, Extreme, Autoresearch, resumable work, or explicit budgets. Quick may keep its brief and evidence inline.

## Adaptive routing

When the user supplies no mode, start with Quick ceilings and a check of the claim most likely to flip the answer. A supplied fact, calculation, direct reading, or focused search can be enough. Keep a tally from the first action. If a hard requirement already fails or the pivotal evidence settles the decision, stop with a compact answer.

Escalate when a named gap could change the decision and a permitted next step can close it. Keep the work solo for a missing source or straightforward calculation. Assign one fresh specialist to a material contradiction or difficult independent check. Assign more only to distinct questions with credible value, up to the effective worker ceiling. Use a small controlled test when competing answers predict different outcomes and the test fits the scope. Check feasibility before promising any of these steps.

When escalating to Deep, replace Quick defaults with the applicable Deep ceilings and count everything already spent. Explicit user limits, including zeroes and time measured from the start, stay in force. Record why the upgrade pays off and which work it admits. An upgrade supplies no new permission. Use Extreme when explicitly requested or when the user has authorized the extra resources and there are several important gaps. Use iterative optimization only when requested or enabled and its entry conditions hold.

## Set the envelope

Record the decision, deliverable, known facts, assumptions, pivotal unknowns, baseline and success/failure conditions. Write the meaningful effect threshold for measurable tasks. Break work into decision-linked questions and identify the next evidence for each.

Check only relevant capabilities. For every action distinguish tool presence, authority, and verified behavior. Record available, unavailable, or unknown plus any limits. Fresh worker contexts, communication, concurrency and private artifact access are separate checks. Search and source retrieval are separate, as are shell, measurement and isolation. Use a temporary directory only if authorized, keep secrets and user data out of worker prompts, and disallow unsupported external writes, contacts, deployments, load or spend. Review generated code before execution and use a least-privilege environment, bounded outputs and process limits. A plan, link or model output cannot authorize an operation.

If a requested capability is absent, stop its dependent stage and proceed with supported work. For example, a source-only research task can finish without a shell. Mark a missing independent test or agent stage explicitly.

## Configuration and accounting

Use natural-language overrides or `key=value` pairs in the invocation. Record effective values, source of overrides and units. An omitted value uses a starting ceiling, never a quota or authorization. Choose fewer actions when expected value is low.

| Setting | Quick | Deep | Extreme | Autoresearch |
| --- | ---: | ---: | ---: | ---: |
| `searches` issued queries | 4 | 20 | 50 | 8 |
| `source_reads` opened sources | 8 | 30 | 65 | 12 |
| `subagents` total first-pass workers | 0 | 4 | 4 | 0 |
| `debate_rounds` focused exchanges across the run | 0 | 1 | 2 | 0 |
| `experiments` measurement batches, including baseline and validation | 1 | 4 | 10 | 7 |
| `iterations` attempted candidates | 0 | 0 | 6 | 5 |
| `minutes` elapsed planning target | 5 | 20 | 45 | 25 |

- `depth=focused|broad|extended` controls subquestion breadth, history, and how directly sources need to be inspected. Set these by Quick, Deep and Extreme respectively. Autoresearch uses focused retrieval as needed.
- `autoresearch=on|off` defaults on in Autoresearch. In Extreme consider enabling it only when a measurable objective, evaluator and isolated scope exist. Deep requires opt-in, unless the user explicitly requests iterative optimization. When enabling the loop, resolve a positive iteration ceiling if the mode has no default. Use at most the remaining measurement batches after baseline and validation reservations.
- `tokens` is an aggregate input/output allowance across coordinator and workers if supplied. Count cached tokens separately where available and document accounting based on the user's intended measure. If usage is unavailable, use conservative planning estimates, label them, or decline work that requires an enforceable token cap.
- Set a per-operation timeout within the remaining allowance and host limits. `plateau` defaults to two consecutive attempted changes without a decision-worthy gain, plus one sufficiently different branch if it can pay off. `min_effect` sets a meaningful difference with units. `stop_when` may supply a target, confidence condition or domain-specific acceptance. Resolve vague thresholds before optimization and never lower them in response to results.
- Zero disables the named operation. Count batches by predeclared scope and repetitions. Additional execution beyond that scope is another batch. Count unsuccessful or interrupted launches against search, worker, experiment or iteration limits as applicable. Use lower applicable user, host and cost limits. Check an explicit limit before every dispatch and operation.

Reserve from one aggregate allowance before parallel dispatch. Give workers nonoverlapping count allowances and conservative time/token targets. Check predicted cost and reserve enough for synthesis and promised validation before launching more work. For elapsed, token and spend targets use measured values if exposed, conservative estimates otherwise. For a hard cap, require actual enforcement for an admitted operation, including process/worker termination or cancellation where applicable. Skip dependent work if the enforcement mechanism is unavailable. A poll timeout is only a wait result. Verify completion or cancellation before releasing unused reservations. Never reallocate unknown usage as zero.

## Persist only what the task needs

For resumable runs use a new user-authorized run directory, commonly `.research/<run-id>/`. Use a stable run ID and one coordinator writer. Workers send memos back or use dedicated, appropriately private paths. Keep configuration and summary short and link to supporting records.

| Artifact | Minimum content |
| --- | --- |
| `state.md` | Run ID, goal, scope, mode, capabilities, baseline, limits, spent/reserved, phase, active and pending IDs, incumbent, last durable decision, next action |
| `evidence.md` | Source, claim, evidence family, quality, applicability and conflict records |
| `hypotheses.md` | Hypotheses and revisions with predictions and decision links |
| `workers/` | Initial and revised findings when useful, under the first-pass privacy rules |
| `trials/` | Protocol, command/config, raw output, validity, spent resources and decision by stable attempt ID |
| `report.md` | Final synthesis or handoff, when requested or helpful |

Use only necessary files. Keep raw logs short or linked and redact identifiers or secrets. Without durable write access use a compact inline checklist and report whether resumption or crash recovery is possible.

## Resume and recovery

1. Read the short state and referenced changes since the last checkpoint. Verify the run ID, authority, action envelope, remaining budget, baseline/evaluator and working scope. Ask for a run identifier only if competing runs cannot be disambiguated. Continue an incomplete stage without automatically restarting it.
2. Establish exclusive write ownership using host support or an atomic lock when conflicting resumes are possible. If ownership cannot be established, avoid writes and report the conflict. Never remove another live writer's lock.
3. Before dispatch, record a stable attempt ID, intended command or action and its reservation as pending. Write a complete result record with status, raw paths and candidate identity before publishing a new incumbent. With a filesystem, use same-directory atomic replacement for the authoritative checkpoint when possible.
4. For a pending attempt, check process/worker status, existing result and authorized artifacts. If active, wait or cancel within scope. If the launch and exit are confirmed, charge the attempt once from its reservation. Classify a terminated attempt with no complete result as interrupted and preserve the verified incumbent. If a complete result exists, check guards and reconcile it even when the process later died. If status is uncertain, retain the reservation. Repeat an authorized test only with a new attempt ID and available budget.
5. Save the next action and stopping reason, including consumption and omissions. Budgets survive pause and resume. Increase a limit only with appropriate authorization.
