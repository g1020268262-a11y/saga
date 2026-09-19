Symbolic Formal Verification of the SAGA protocol

# Authorization Audit Status

The current authorization-audit record is
[AUDIT_STATUS.md](AUDIT_STATUS.md). It supersedes older interim statements that
described the matcher bypass as unproved.

Current boundary:

- matcher implementation-level bypass: confirmed by
  [test_matcher_bug.py](test_matcher_bug.py) and the earlier direct matcher
  evidence in
  [policy-matcher-sanity.json](evidence/authz-stage1-20260916T123834944479Z/policy-matcher-sanity.json).
- authorization gate / protocol consequence modeling: partially complete.
- full service-level end-to-end exploit: next stage.

# Reproduction Steps
1. Install the [nix package manager](https://nixos.org/download/)
2. Navigate to the current directory, and run `nix develop`. You will get dropped into a devshell with [ProVerif](https://en.wikipedia.org/wiki/ProVerif) and [Verifpal](https://verifpal.com/). Feel free to execute another shell if you don't like `bash`.
3. Run `proverif proverif/agent_communication.vp` to (automatically) prove authentication and security for Saga. The `time` module reported `proverif agent_communication.pv real 6m35.669s user 6m26.630s sys	0m4.721s` on an X1 Carbon Gen 5, i7-7600U, 16gb ddr4, running NixOS 25.11.
4. `proverif/registration.pv` implements just the SAGA agent registration protocol with a single peer. Run `proverif proverif/registration.pv` to (automatically) prove authentication for the SAGA registration protocol.

## Verifpal models
We also include `verifpal` models of the agent communication and registration protocols. One may run `verifpal verify verifpal/registration.vp` and `verifpal verify verifpal/agent_communication.vp`. However, **this will take forever** as verifpal is much slower than proverif for active attackers.
