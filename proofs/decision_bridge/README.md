# Authorization Decision Bridge v1

This independent, executable finite semantics layer replaces hand-entered
decision labels for the recorded case with a checked decision pair. It does
not verify Python or introduce a new protocol model. Existing paper sections,
the claim matrix, old models, and historical evidence are unchanged.

## Architecture and commands

From repository root (Python 3, standard library only):

```text
python -B proofs/decision_bridge/run_bridge.py
python -B -m unittest discover -s proofs/decision_bridge -p test_bridge.py -v
```

The default runner only reads archived observations. It creates a NEW timestamped
directory in `proofs/decision_bridge/evidence/` with `input.json`,
`bridge-result.json`, `scenario_turepass_from_bridge.inc`, `summary.txt`, and
`manifest.json`. Existing output directories/files are rejected, never reused.
Agreement cases have no scenario fragment. Unsupported/Invalid specification
inputs produce a status artifact without a decision comparison or fragment;
provenance/binding errors abort with a nonzero exit and no result.

To replay the saved machine-readable input, supply
`--input proofs/decision_bridge/evidence/<run>/input.json`.
An optional `--output <new-repo-relative-directory>` selects a new destination.

```text
concrete input --> independent specification evaluator --> SpecDecision
       |                                                   |
       +--> context-checked production observation --------+--> decision pair
                                                               |
                                                    rechecked scenario fragment
```

## Input and provenance contract

`input.json` contains `context` and `observation`. The context has policy id and
version, an order-sensitive policy hash, source path/hash/commit, initiator,
matcher target, receiver binding, and ordered rules (`id`, zero-based `position`,
`pattern`, integer `budget`). Canonical JSON with sorted keys and compact
separators is hashed with SHA-256; rule arrays retain order. The evaluation
fingerprint hashes the entire context, including rule ids and participant direction.

The matcher target is the initiating identity, **not** the receiving agent.
Historical function observations do not identify a real receiver or policy id.
The bridge therefore assigns a scenario-local policy label and fixes the receiver
to symbolic `aid_A`, explicitly marked as unobserved. This does not establish
ownership of a deployed policy. Both decision branches use this same context.

Observation references contain a repository-relative path, file SHA-256, format,
and (for Stage 1) an actual-result field selector. The loader compares the exact
ordered patterns/budgets and identity. It checks source hash against current
source bytes and source commit against the corresponding Git blob (CRLF/LF
normalized for Git comparison only). The recorded byte hash is not normalized.
Different source revisions require a new, reviewed observation; v1 fails closed.
This requires local Git history containing the recorded commit.

Manifests record execution time, current commit/status, generator version,
script/source/model/observation hashes and output hashes. Uncommitted bridge code
is bound by file hashes, not falsely attributed to HEAD. Hashes provide integrity
binding, not signatures or independent attestation of archive authenticity.

## Independent specification semantics

`bridge.py` does not import the production matcher, use `fnmatch`, or consult the
archive's `expected`/`specificities` fields. For all supported rules it computes
matching and numerical rank, collects matches, and selects the unique maximum.
This implements the documented numerical ordering, not pattern-language containment.

Closed grammar: `*`, exact lowercase ASCII AIDs, and a literal lowercase UID
followed by `:*`. UID grammar is `[a-z0-9._+-]+@[a-z0-9.-]+`; literal agent names
are `[a-z0-9._+-]+`. This intentionally excludes case-folding and path-normalization
ambiguities in cross-platform fnmatch. Specificity is 0 for `*`,
`4*len(uid)+2` for `uid:*`, and `4*len(uid)+8*len(name)` for exact AIDs.

Budgets are integers >= -1 (Boolean values are invalid). The classes are Negative,
Zero, and Positive; only Positive means Allow, using the paper's Provider contact
permission convention. This is not a claim about the receiver's zero-budget check.
No matching rule yields budget 0 / Deny and a null winning rule. Equal highest
scores are Unsupported even when the tied budgets agree. Any unsupported pattern,
including a nonmatching one, rejects the entire evaluation as Unsupported.
Malformed fields/identities/positions/budgets produce Invalid. Neither status is Deny.

## Implementation observations

The default evidence is the unchanged
`proofs/evidence/authz-stage1-20260916T123834944479Z/policy-matcher-sanity.json`.
Its Alice input, not the illustrative Mallory clone, is the concrete counterexample.
The first actual-result field belongs to the stored order; the second belongs to
the **reverse** of that order. The loader never uses `expected` as specification
truth. Rule ids and policy labels are bridge metadata, not historical observations.

Normal allow/deny controls are NEW direct calls of the unmodified production
matcher, archived separately in `observations/20260922T064049858703Z/`.
They are real function observations, not synthetic expected-value fixtures.
`collect_controls.py` is the only component importing production `match`; it is
independent of the spec and is not invoked by the runner or tests. Explicitly
running it creates a fresh observation directory:

```text
python -B proofs/decision_bridge/collect_controls.py
```

The tests replay the pinned control archive. New collections do not silently
replace the selected archive. All collection is function-level, without service,
network, token issuance, or application-message execution.

## Pair comparison and ProVerif adapter

The result includes context/fingerprint, winning rule, rank, spec budget/class/
decision, observed budget/class/decision with source reference, and divergence.
Only successfully bound supported evaluations are compared.

The generator re-evaluates the stored context and reloads the hashed observation;
modified decision labels or comparison flags are rejected. Only Deny/Allow emits:

```text
insert ScenarioSpecDeny(BuggyPolicy, aid_B);
insert ScenarioImplAllow(BuggyPolicy, aid_B);
```

These are existing **table facts**, not new matcher execution events. The fragment
records the evaluation fingerprint; `aid_B` represents the concrete initiator,
`aid_A` the symbolic receiver, and `BuggyPolicy` the scenario-local policy.
The generator checks these insert statements exist in the unchanged turepass
model. The manifest binds that model's hash. This is an adapter interface check,
not proof of equivalence to protocol consumers.

The `.inc` is a text fragment intended to replace the existing two initial inserts
in a future derived model. It is NOT a standalone ProVerif input, and no native
ProVerif include directive is assumed. No full model is generated or verifier run
in v1. The current artifact provides the generated input and its derivation only.

## Limits and claims

Supported: fixed finite ordered policy, fixed identity, unique maximum, the closed
pattern grammar, three budget classes, and the two archived orderings plus controls.
Unsupported: full fnmatch/Python semantics, tied maxima, dynamic policies, concurrent
mutation, quota consumption, token lifecycle, and deployed enforcement correctness.

The layer supports: **the ProVerif scenario input is derived from an independently
evaluated specification decision and a provenance-bound implementation observation
for the same concrete policy evaluation.** The same-evaluation claim concerns the
matched identity, ordered rulebook and source, not an observed service session.

It does NOT establish Python refinement, full matcher correctness, a formal proof
of this evaluator, consumer equivalence, or an end-to-end exploit. The semantics
and adapter are reviewable/tested Python, not mechanically proved translations.
Historical ProVerif evidence does not automatically upgrade: ChatAccept reachability
and its TokenIssue correspondence remain results of the historical model under its
assumptions. This bridge adds no TokenIssue query or new reachability result.
