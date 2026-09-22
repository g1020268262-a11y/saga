import copy
import unittest
from bridge import (ROOT, ARCHIVE, read, digest, make_context, build, evaluate,
                    generate, policy_hash, write_json)
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
