# SAGA Authorization Audit Status

Updated: 2026-09-19

This file is the current status record for the SAGA authorization audit. Older
stage reports remain valid as evidence for the run they describe, but their
"not yet proved" statements must be read against this newer status.

## Current Conclusion

The matcher implementation-level authorization bypass has been reproduced and
confirmed. The remaining work is not to prove that matcher bug again; it is to
connect the concrete matcher counterexample to the ProVerif authorization model
with a stricter semantic mapping.

The current boundary is:

- matcher bug: proved at implementation/function level.
- protocol impact: modeled with explicit authorization-divergence assumptions.
- full end-to-end exploit: next stage.

## Stage 1: Original ProVerif Communication Model

Status: complete.

Evidence:

- [AUTHORIZATION_DIAGNOSTIC.zh-CN.md](AUTHORIZATION_DIAGNOSTIC.zh-CN.md)
- [verification-summary.txt](evidence/authz-stage1-20260916T123834944479Z/verification-summary.txt)

Result:

- The original authentication properties remain `true`.
- Token secrecy remains `true`.
- The added authorization correspondence fails in the diagnostic model, showing
  that the original authentication and secrecy proof does not establish
  authorization soundness.

Scope:

- This stage is a proof-coverage diagnostic.
- It is not a matcher implementation proof.
- It stops at token receipt and does not model final chat-message acceptance.

## Stage 2: Authorization Gate Abstraction Model

Status: complete, but it is a control experiment.

Evidence:

- [AUTHORIZATION_CHAT_GATES.zh-CN.md](AUTHORIZATION_CHAT_GATES.zh-CN.md)
- [verification-summary.txt](evidence/authz-chat-gates-20260918T023621017067Z/verification-summary.txt)

Result:

- Provider authorization and receiver authorization are split into separate gate
  controls.
- The models show how different gate locations affect reachability of
  `ProviderRelease`, `TokenIssue`, and `ChatAccept`.

Scope:

- This stage validates the authorization-control placement abstraction.
- It does not execute or formally prove the Python matcher.
- It does not compute concrete contact rulebook specificity.

## Stage 3: Matcher Implementation Vulnerability

Status: complete.

Key evidence:

- [test_matcher_bug.py](test_matcher_bug.py)
- [policy-matcher-sanity.json](evidence/authz-stage1-20260916T123834944479Z/policy-matcher-sanity.json)

The confirmed counterexample is:

```json
[
  {
    "pattern": "mallory@example.com:*",
    "budget": -1
  },
  {
    "pattern": "*",
    "budget": 10
  }
]
```

Under the documented most-specific-rule semantics, the specific deny rule should
win:

```text
SpecDecision: deny
Expected budget: -1
```

The current matcher behavior returns the later wildcard allow:

```text
ImplementationDecision: allow
Actual budget: 10
```

Therefore:

```text
Implementation decision != Specification decision
```

Conclusion:

`test_matcher_bug.py` demonstrates the order-dependent bypass with the
specific-deny-then-wildcard-allow rulebook. The earlier direct evidence file
`policy-matcher-sanity.json` also records a direct call of the unmodified
`saga/common/contact_policy.py` matcher with the same mismatch pattern: expected
deny, actual allow.

VULNERABILITY CONFIRMED:

Order-dependent authorization bypass succeeded.

Scope:

- This proves the matcher implementation-level decision mismatch.
- It does not by itself prove a full Provider/Agent service-level exploit.

## Stage 4: Attack Trace / ProVerif Authorization Consequence Model

Status: in progress / partially complete.

Evidence currently present:

- [agent_communication_authz_chat_turepass.pv](proverif/agent_communication_authz_chat_turepass.pv)
- [turetrace](evidence/turetrace)

Current model capability:

- It expresses `ScenarioSpecDeny`.
- It expresses `ScenarioImplAllow`.
- It propagates the implementation-side allow assumption through:

```text
ScenarioImplAllow
  -> ProviderRelease
  -> TokenIssue
  -> ChatAccept
```

The saved trace reaches `ChatAccept` while also recording the intended
specification-side deny scenario. This is useful evidence of protocol-layer
consequence under the abstracted matcher mismatch.

Scope:

- `ScenarioImplAllow` is an abstraction of the matcher bug, not the Python
  matcher itself.
- The model currently represents the authorization divergence as fixed scenario
  facts.
- The next step is to make the mapping from the real rulebook and matcher result
  to these formal events explicit and auditable.

## Outdated Assessment Correction

Previous assessment outdated: matcher evidence was later confirmed through
test-matcher.

Old conclusion to remove from the current status:

```text
No proof of matcher bypass.
```

Correct current conclusion:

```text
The matcher implementation-level bypass has been reproduced and confirmed
through test_matcher_bug.py / matcher test evidence.

The remaining work is not to prove the matcher bug. The remaining work is to
connect the matcher counterexample with the ProVerif authorization consequence
model through a stricter semantic mapping.
```

## TODO / Next Steps

1. Establish the matcher-to-formal-event mapping:

```text
SpecDecision(A, B, deny)
ImplDecision(A, B, allow)
```

2. Map the concrete rulebook into the model:

```text
mallory@example.com:*
*
```

3. Prove the complete modeled chain:

```text
Spec deny
+ Impl allow
+ TokenIssue
+ ChatAccept
```

4. Archive a structured Stage 4 evidence directory with the model, command,
   ProVerif output, manifest, and hashes.

5. Only after that mapping is explicit, consider a service-level end-to-end PoC
   that records Provider access, OTK release, token issue, and chat acceptance
   in the running implementation.
