import copy
import unittest
from unittest.mock import patch
import json
from bridge import (ROOT, ARCHIVE, read, digest, make_context, build, evaluate,
                    generate, policy_hash, write_json, verify_historical_source, current_source_state, SOURCE, MODEL)
from generate_model import derive_model
from run_verification import summarize
import tempfile
from pathlib import Path

CONTROLS = "proofs/decision_bridge/observations/20260922T064049858703Z"


def historical(reverse=False):
    data = read(ARCHIVE)
    context = make_context(list(reversed(data["rules"])) if reverse else data["rules"], data["aid"],
                           data["source_sha256"], data["base_commit"], "stage1-alice")
    reference = {"path": ARCHIVE, "sha256": digest((ROOT / ARCHIVE).read_bytes()), "format": "stage1",
                 "field": "actual_wildcard_allow_then_specific_deny" if reverse else "actual_specific_deny_then_wildcard_allow"}
    return context, reference


class BridgeTests(unittest.TestCase):
    def test_historical_replay_does_not_require_current_source_match(self):
        real_read = Path.read_bytes
        def changed_current(path):
            return b"hypothetical later matcher repair\n" if path == ROOT / SOURCE else real_read(path)
        context, ref = historical()
        with patch.object(Path, "read_bytes", changed_current):
            result = build(context, ref)
            self.assertTrue(result["divergence"])
            self.assertFalse(current_source_state(context["source_sha256"])["current_source_matches_historical"])

    def test_missing_historical_commit(self):
        with self.assertRaises(ValueError):
            verify_historical_source("0" * 40, "0" * 64)

    def test_wrong_historical_blob(self):
        context, _ = historical()
        with patch("bridge.git", return_value=b"unrelated historical contents\n"):
            with self.assertRaises(ValueError):
                verify_historical_source(context["source_commit"], context["source_sha256"])

    def test_explicit_eol_verification(self):
        with patch("bridge.git", return_value=b"a\nb\n"):
            binding = verify_historical_source("1" * 40, digest(b"a\r\nb\r\n"))
            self.assertEqual(binding["verified_byte_encoding"], "uniform-CRLF")
            self.assertNotEqual(binding["historical_git_blob_sha256"], binding["archived_source_byte_sha256"])
            with self.assertRaises(ValueError):
                verify_historical_source("1" * 40, digest(b"a\r\nb\n"))

    def test_full_model_preserves_source(self):
        data = json.dumps(build(*historical())).encode()
        generated = derive_model(data)
        header, body = generated.split(b"*)\n", 1)
        self.assertEqual(body, (ROOT / MODEL).read_bytes())
        self.assertIn(digest(data).encode(), header)

    def test_full_model_rejects_tampered_pair(self):
        result = build(*historical())
        result["impl_observed"]["budget"] = -1
        with self.assertRaises(ValueError):
            derive_model(json.dumps(result).encode())

    def test_frozen_template_check(self):
        data = json.dumps(build(*historical())).encode()
        with patch("generate_model.TEMPLATE_SHA256", "0" * 64):
            with self.assertRaises(ValueError):
                derive_model(data)

    def test_result_parser_not_missing_or_unknown(self):
        # Parser fixtures only; these are NOT verifier evidence.
        output = ("RESULT event(ChatAccept(r,s,t,m)) ==> event(TokenIssue(r,s,t)) is true.\n"
                  "RESULT not event(ChatAccept(r,s,t,m)) is false.\n")
        self.assertTrue(summarize(output)["chat_accept_reachable"])
        self.assertTrue(summarize(output)["chat_accept_implies_token_issue"])
        self.assertTrue(summarize(output)["expected_query_set"])
        self.assertFalse(summarize("")["expected_query_set"])
        self.assertFalse(summarize(output.replace(" is false.", " cannot be proved."))["chat_accept_reachable"])

    def test_real_counterexample(self):
        result = build(*historical())
        self.assertEqual(result["spec"]["budget"], -1)
        self.assertEqual(result["spec"]["specificity"], 70)
        self.assertEqual(result["impl_observed"]["budget"], 10)
        self.assertTrue(result["divergence"])
        self.assertIn("insert ScenarioImplAllow(BuggyPolicy, aid_B);", generate(result))

    def test_reverse(self):
        result = build(*historical(True))
        self.assertEqual(result["spec"]["decision"], "Deny")
        self.assertEqual(result["impl_observed"]["decision"], "Deny")
        self.assertFalse(result["divergence"])
        self.assertIsNone(generate(result))

    def control(self, name, decision):
        path = CONTROLS + "/" + name + ".json"
        data = read(path)
        context = make_context(data["rules"], data["aid"], data["source_sha256"], data["base_commit"], name)
        result = build(context, {"path": path, "sha256": digest((ROOT / path).read_bytes()), "format": "bridge-observation-v1"})
        self.assertEqual(result["spec"]["decision"], decision)
        self.assertEqual(result["impl_observed"]["decision"], decision)
        self.assertFalse(result["divergence"])
        self.assertIsNone(generate(result))

    def test_normal_allow(self):
        self.control("allow", "Allow")

    def test_normal_deny(self):
        self.control("deny", "Deny")

    def test_unsupported_even_when_nonmatching(self):
        context, ref = historical()
        for pattern in ("bob@*.com:*", "alice@example.com:a?ent", "alice@example.com:[a-z]", "Alice@example.com:*"):
            with self.subTest(pattern=pattern):
                context["rules"][0]["pattern"] = pattern
                self.assertEqual(build(context, ref)["status"], "Unsupported")

    def test_tie(self):
        context, _ = historical()
        context["rules"][1]["pattern"] = context["rules"][0]["pattern"]
        self.assertEqual(evaluate(context)["status"], "Unsupported")

    def test_invalid(self):
        base, _ = historical()
        for field, value in (("budget", True), ("budget", -2), ("position", 1), ("pattern", None)):
            context = copy.deepcopy(base)
            context["rules"][0][field] = value
            self.assertEqual(evaluate(context)["status"], "Invalid")
        self.assertEqual(evaluate({})["status"], "Invalid")

    def test_zero_no_match_and_exact(self):
        context, _ = historical()
        for rules, budget in (([], 0), ([{"pattern": "bob@example.com:*", "budget": 10}], 0),
                              ([{"pattern": "*", "budget": 0}], 0),
                              ([{"pattern": "alice@example.com:agent", "budget": 10}], 10)):
            context["rules"] = [{"id": str(i), "position": i, **r} for i, r in enumerate(rules)]
            self.assertEqual(evaluate(context)["budget"], budget)

    def test_context_mismatch(self):
        for field, value in (("target", "bob@example.com:agent"), ("source_sha256", "0" * 64),
                              ("policy_hash", "0" * 64), ("source_commit", "0" * 40), ("receiver", "aid_B")):
            context, ref = historical()
            context[field] = value
            with self.assertRaises(ValueError):
                build(context, ref)
        context, ref = historical(True)
        ref["field"] = "actual_specific_deny_then_wildcard_allow"
        with self.assertRaises(ValueError):
            build(context, ref)

    def test_archive_hash_and_expected_rejected(self):
        context, ref = historical()
        ref["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            build(context, ref)
        context, ref = historical()
        ref["field"] = "expected_under_documented_most_specific_semantics"
        with self.assertRaises(ValueError):
            build(context, ref)

    def test_generator_recomputes(self):
        result = build(*historical())
        result["spec"]["decision"] = "Allow"
        with self.assertRaises(ValueError):
            generate(result)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            write_json(path, {"original": True})
            with self.assertRaises(FileExistsError):
                write_json(path, {})


if __name__ == "__main__":
    unittest.main()
