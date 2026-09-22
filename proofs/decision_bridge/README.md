# Authorization Decision Bridge v1.1.1

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

For a NEW independent full-model verification archive, commit reviewed bridge
changes first and start from a clean working tree:

```text
python -B proofs/decision_bridge/run_verification.py --proverif proverif
```

Use `--proverif <installed-executable>` if it is not on PATH. No absolute local
tool path is archived: manifests record its basename, executable byte hash,
version, and command with repository-relative model path. The default timeout is
3600 seconds (`--timeout`). This runner creates
`proofs/evidence/authz-bridge-turepass-<timestamp>/` and actually invokes ProVerif;
the earlier `run_bridge.py` remains a lightweight replay/fragment-only command.

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
ordered patterns/budgets and identity. It reads `git show <base_commit>:<source>`
and checks the archived byte hash against three explicitly enumerated encodings:
raw Git blob, uniform LF, and uniform CRLF. It records which encoding matched,
the raw blob hash, normalized LF hash, and archived byte hash separately. It never
claims that unequal raw hashes are equal. Mixed-EOL encodings not matching these
candidates are rejected. Missing historical revision or mismatched blob fails closed.

Historical source revision may differ from current checkout source, and this does
not invalidate replay as long as the archived observation is correctly bound to
the historical Git revision. **Current source equality is NOT required for
historical replay.** Current source hash/equality are informational manifest fields,
not part of the historical decision pair. Even a missing current matcher does not
invalidate the historical binding. The local Git history must contain the revision.

Manifests record execution time, current commit/status, generator version,
script/model/observation hashes and output hashes. The formal runner rejects dirty
trees before creating output and records the actual bridge code commit. `git_status:
clean` refers to this pre-run state; the post-run status honestly records the new
untracked archive. Code commit and subsequent evidence commit are separate, avoiding
a self-referential commit hash. Development archives remain unchanged.
Hashes provide integrity binding, not signatures or independent attestation of
archive authenticity. They do not protect against coordinated rewriting of all
input provenance by an untrusted archive author.

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

The `.inc` is not standalone ProVerif input; no native include directive is assumed.
In v1.1.1, `generate_model.py` produces a complete `.pv` from the frozen
turepass template, pinned by its raw SHA-256. It rechecks the serialized decision
pair, splits the source into prefix and suffix around a uniquely located frozen
scenario block, and constructs `prefix + generated_block + suffix`. The generated
block comes from the revalidated bridge generator, not the old template block.
Missing/duplicate scenario regions and template hash mismatches fail closed.

Version distinction: v1.1 validated a pre-existing scenario interface and ran a
derived full model. In v1.1.1, the scenario region of the executed model is
reconstructed from the independently derived decision pair. No new template file
is needed: the historical model remains the hash-pinned read-only source.

Exactly three comments are normalized in the derived body only:
the session-isolation claim becomes "Fresh symbolic token for this modeled execution";
the claim about cryptographic checks becomes a ChatAccept-to-TokenIssue correspondence
description; the end-to-end attack query label becomes a ChatAccept reachability
description under the modeled divergence. Historical comments remain untouched.
The explicit UTF-8 comment replacement whitelist requires each original exactly once.

The structure checker compares exact bytes against the permitted transformation,
rather than stripping arbitrary comments. It rejects changes to queries, events,
processes, channels, token logic, extra statements, and unapproved comments.
The header binds evaluation fingerprint, exact bridge-result bytes hash, template
path/hash, generated scenario block hash and bridge version. Tests exercise each
of these rejection boundaries; these executable checks are not a refinement proof.

The executed bridge-derived model reconstructs its authorization-divergence scenario
block from the checked decision pair; all other protocol semantics and queries remain
frozen. The three approved comment changes do not alter ProVerif statements.

`run_verification.py` saves that model, input, decision pair, a run-start record,
actual verifier stdout/stderr/version, test logs, summary and final manifest.
Archive-local `.gitattributes` preserves the exact model/output bytes in Git checkouts.
It extracts the two `RESULT` lines from NEW stdout and checks ChatAccept reachability
and the ChatAccept-to-TokenIssue correspondence. Missing/unknown/additional results,
nonzero exit, timeout, failed tests or changes to tracked input files prevent a
successful run status. No standalone TokenIssue query is added. A failed run is
retained as failed evidence, never converted to success or replaced with old stdout.

This separates five layers: historical observation provenance; informational current
source state; independently derived decision pair; generated full model; and new
ProVerif execution. A verified source binding alone does not prove the other layers.

## Limits and claims

Supported: fixed finite ordered policy, fixed identity, unique maximum, the closed
pattern grammar, three budget classes, and the two archived orderings plus controls.
Unsupported: full fnmatch/Python semantics, tied maxima, dynamic policies, concurrent
mutation, quota consumption, token lifecycle, and deployed enforcement correctness.

After a successful formal run, the layer supports: **the specification decision is
independently derived from the concrete ordered policy input, the implementation-side
decision is bound to an archived execution of the production matcher at a specific
historical source revision, and the resulting checked decision pair is used to generate
and execute a derived ProVerif consequence model.** The same-evaluation claim concerns
the matched identity, ordered rulebook and source, not an observed service session.

It does NOT establish Python refinement, full matcher correctness, a formal proof
of this evaluator, consumer equivalence, or an end-to-end exploit. The semantics
and adapter are reviewable/tested Python, not mechanically proved translations.
Historical ProVerif evidence does not automatically upgrade: ChatAccept reachability
and its TokenIssue correspondence remain results of the historical model under its
assumptions. A new derived-model run is separate corroborating execution evidence,
not an upgrade of old results. This bridge adds no TokenIssue query, full matcher
correctness claim, deployed policy ownership claim, current upstream vulnerability
status claim, or correctness claim for arbitrary policies.
