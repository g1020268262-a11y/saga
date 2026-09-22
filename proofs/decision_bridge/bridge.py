"""Finite specification evaluator and observation-bound scenario adapter. No matcher import."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = "decision-bridge-1"
SOURCE = "saga/common/contact_policy.py"
ARCHIVE = "proofs/evidence/authz-stage1-20260916T123834944479Z/policy-matcher-sanity.json"
MODEL = "proofs/proverif/agent_communication_authz_chat_turepass.pv"
IDENTITY = re.compile(r"[a-z0-9._+-]+@[a-z0-9.-]+:[a-z0-9._+-]+\Z")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())


def relative_file(name):
    if not isinstance(name, str) or "\\" in name or Path(name).is_absolute():
        raise ValueError("Expected repository-relative POSIX path")
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("Missing or out-of-repository input")
    return path


def read(name):
    return json.loads(relative_file(name).read_text(encoding="utf-8"))


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def budget_decision(budget):
    if type(budget) is not int or budget < -1:
        raise ValueError("Invalid budget (integer >= -1 required)")
    return {"budget": budget, "budget_class": "Positive" if budget > 0 else "Negative" if budget < 0 else "Zero",
            "decision": "Allow" if budget > 0 else "Deny"}


def evaluate(context):
    """Closed grammar: lowercase ASCII exact AID, literal UID:*, or *."""
    try:
        if not isinstance(context, dict) or not IDENTITY.fullmatch(context["target"]):
            raise ValueError("Invalid concrete target")
        rules = context["rules"]
        if not isinstance(rules, list):
            raise ValueError("Rules must be an ordered list")
        ids = set()
        matches = []
        unsupported = False
        for pos, rule in enumerate(rules):
            if not isinstance(rule, dict) or type(rule["position"]) is not int or rule["position"] != pos:
                raise ValueError("Invalid rule position")
            if not isinstance(rule["id"], str) or not rule["id"] or rule["id"] in ids:
                raise ValueError("Invalid or duplicate rule id")
            ids.add(rule["id"])
            budget_decision(rule["budget"])
            pattern = rule["pattern"]
            if not isinstance(pattern, str):
                raise ValueError("Pattern must be a string")
            if pattern == "*":
                rank, matched = 0, True
            elif IDENTITY.fullmatch(pattern):
                uid, name = pattern.split(":")
                rank, matched = 4 * len(uid) + 8 * len(name), pattern == context["target"]
            elif pattern.endswith(":*") and IDENTITY.fullmatch(pattern[:-1] + "x"):
                uid = pattern[:-2]
                rank, matched = 4 * len(uid) + 2, context["target"].split(":")[0] == uid
            else:
                unsupported = True
                continue
            if matched:
                matches.append((rank, rule))
        if unsupported:
            return {"status": "Unsupported", "reason": "Pattern outside closed grammar"}
        top = max((rank for rank, _ in matches), default=None)
        winners = [rule for rank, rule in matches if rank == top]
        if len(winners) > 1:
            return {"status": "Unsupported", "reason": "Equal highest specificity"}
        winner = winners[0] if winners else None
        return {"status": "OK", "winning_rule": winner["id"] if winner else None,
                "specificity": top, **budget_decision(winner["budget"] if winner else 0)}
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return {"status": "Invalid", "reason": str(exc)}


def policy_hash(context):
    return fingerprint(context["rules"])


def make_context(rules, aid, source_hash, source_commit, policy_id):
    context = {"policy_id": policy_id, "policy_version": "1", "initiator": aid, "target": aid,
               "receiver": "aid_A", "receiver_binding": "symbolic policy owner; not recorded by matcher",
               "source": SOURCE, "source_sha256": source_hash, "source_commit": source_commit,
               "rules": [{"id": f"r{i}", "position": i, **r} for i, r in enumerate(rules)]}
    context["policy_hash"] = policy_hash(context)
    return context


def load_observation(context, reference):
    data = read(reference["path"])
    if digest(relative_file(reference["path"]).read_bytes()) != reference["sha256"]:
        raise ValueError("Observation hash mismatch")
    if reference["format"] == "stage1":
        field = reference["field"]
        if field not in ("actual_specific_deny_then_wildcard_allow", "actual_wildcard_allow_then_specific_deny"):
            raise ValueError("Not an actual observation field")
        rules = data["rules"] if field == "actual_specific_deny_then_wildcard_allow" else list(reversed(data["rules"]))
        aid, budget = data["aid"], data[field]
    elif reference["format"] == "bridge-observation-v1":
        rules, aid, budget = data["rules"], data["aid"], data["actual_budget"]
    else:
        raise ValueError("Unknown observation format")
    concrete_rules = [{"pattern": r["pattern"], "budget": r["budget"]} for r in context["rules"]]
    if fingerprint(rules) != fingerprint(concrete_rules) or aid != context["target"]:
        raise ValueError("Observation policy/order/identity mismatch")
    if (data["source"], data["source_sha256"], data["base_commit"]) != (SOURCE, context["source_sha256"], context["source_commit"]):
        raise ValueError("Observation source context mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", data["base_commit"]):
        raise ValueError("Invalid source revision")
    current = relative_file(SOURCE).read_bytes()
    if digest(current) != data["source_sha256"]:
        raise ValueError("Current source differs from observation source")
    # Git normalizes text to LF, whereas the historical Windows hash binds CRLF bytes.
    blob = git("show", data["base_commit"] + ":" + SOURCE)
    if blob.replace(b"\r\n", b"\n") != current.replace(b"\r\n", b"\n"):
        raise ValueError("Recorded revision does not match source (LF normalized)")
    return {**budget_decision(budget), "observation": reference}


def build(context, reference):
    spec = evaluate(context)
    if spec["status"] != "OK":
        return {"status": spec["status"], "spec": spec}
    if (context["target"] != context["initiator"] or context["receiver"] != "aid_A"
            or context["receiver_binding"] != "symbolic policy owner; not recorded by matcher"
            or context["policy_hash"] != policy_hash(context)
            or not context["policy_id"] or not context["policy_version"] or context["source"] != SOURCE):
        raise ValueError("Invalid evaluation context")
    observed = load_observation(context, reference)
    return {"status": "OK", "generator_version": VERSION, "context": context,
            "evaluation_fingerprint": fingerprint(context), "spec": spec, "impl_observed": observed,
            "divergence": spec["decision"] != observed["decision"]}


def generate(result):
    """Recompute instead of trusting stored decision labels or divergence boolean."""
    checked = build(result["context"], result["impl_observed"]["observation"])
    if checked != result:
        raise ValueError("Decision pair differs from recomputed evidence")
    if (result["spec"]["decision"], result["impl_observed"]["decision"]) != ("Deny", "Allow"):
        return None
    model = relative_file(MODEL).read_text(encoding="utf-8")
    inserts = "insert ScenarioSpecDeny(BuggyPolicy, aid_B);\ninsert ScenarioImplAllow(BuggyPolicy, aid_B);\n"
    if any(line not in model for line in inserts.splitlines()):
        raise ValueError("Existing model scenario interface changed")
    return ("(* Derived scenario fragment; not a standalone model or new verifier result.\n"
            f"   evaluation_sha256: {result['evaluation_fingerprint']}\n"
            "   Initiator -> aid_B; symbolic receiver -> aid_A; policy -> BuggyPolicy.\n"
            "   Replace the two initial scenario inserts in a future derived model. *)\n" + inserts)


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
