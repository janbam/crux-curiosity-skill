# Report and handoff

Start with the recommendation, conditions under which it holds, and the outcome the user can act on. Use only sections merited by the task.

1. **Decision and limits.** State the objective, selected solution or portfolio, confidence with reasons, and what would change the recommendation. For consequential hard constraints, record the requirement, a boundary case, the supporting check and whether it passes. Classify unresolved conditions explicitly and do not treat them as satisfied.
2. **Research and reasoning.** Explain key mechanisms and assumptions, the historical or adjacent precedents that transfer, major alternatives and trade-offs. Anchor pivotal claims to evidence or artifact IDs and direct sources. Distinguish sourced facts, observed results, inferences, assumptions and speculation.
3. **Hypotheses and results.** State how material hypotheses were ranked and challenged. Include baseline, experiment method, raw-result paths, measured effects and variability, guards and tested scope. Report failed, invalid, inconclusive, skipped and unverified work honestly.
4. **Reproduction and follow-up.** Give environment, data and revision requirements, authorized commands, and a specific next decision-changing observation where useful. For recoverable work, give run path, state and resume action.
5. **Execution accounting.** Report effective mode, actual workers and isolation, exchange rounds, searches/retrievals, trials and iteration counts, time and tokens if exposed, stop reason, unresolved dissent and dependencies. Mark estimates and unknowns explicitly. Distinguish real tool activity from mock or sequential analysis and identify incomplete stages.

For a quick decision, fold the evidence, uncertainty, and stopping rationale into a few sentences. Retain the full records in durable artifacts when required for audit or resumption.

## When the decision changes

For a close comparison, give the current choice, the assumption carrying it, the condition that favors the best alternative, and the cheapest credible way to check. Derive a numerical threshold only from known constraints and inputs. If priorities or inputs are missing, give a conditional threshold in words and say what would resolve it. For a settled choice, leave this compact.

For example, an event becoming eligible just after a daily batch can wait almost 24 hours before processing. A provider replay window of 24 hours protects some retries. It does not establish a 12-hour delivery deadline. Verify each deadline against its own start and end points.
