"""Check the original-code dual-ledger/delivery extension, retaining evidence."""

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from run_tlc import HERE, REPO, SOURCE_HASHES, UPSTREAM, digest, git, record_process, run, write_json


MODEL = "SagaQuotaDelivery"
CASES = {
    "normal_single": ("complete", None, "normal_control"),
    "concurrent_race": ("violation", "ReceiverQuotaSafety", "receiver_safety"),
    "request_abort": ("violation", "QuiescentAgreement", "candidate_accounting"),
    "request_abort_after_progress": ("violation", "QuiescentAgreementAfterProgress", "candidate_accounting"),
    "request_abort_consumption": ("violation", "NoUnadmittedConsumption", "candidate_accounting"),
    "response_abort": ("complete", None, "accounting_control"),
    "send_error": ("complete", None, "accounting_control"),
    "response_abort_witness": ("witness", "NoResponseAbort", "reachability"),
    "send_error_witness": ("witness", "NoSendError", "reachability"),
    "mixed_structure": ("complete", None, "structural_only"),
}
PRESERVED_MODELS = {
    "SagaQuota.tla": "b0a473eeaabf5a32e45648a8713487504485d3e60404c2f1f9cf01528982592b",
    "SagaQuota_Annotated.tla": "98db802d54b2e95eb74f73b581ff5f0f71df9b6ef719cec4468c9ab63f783a4d",
}


def extract_trace(log: str, path: Path) -> dict:
    """Model-specific extraction of scalar values; raw TLC output is authoritative."""
    headers = list(re.finditer(r"(?m)^State (\d+): <([^\r\n]+)>\s*$", log))
    states = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(log)
        body = log[header.end():end]
        footer = re.search(r"(?m)^[\d,]+ states generated,", body)
        if footer:
            body = body[:footer.start()]
        state = {"number": int(header.group(1)), "action_location": header.group(2),
                 "raw_state": body.strip()}
        for field in ("senderRemaining", "receiverRemaining", "faultCount"):
            match = re.search(r"(?m)^/\\ " + field + r" = (\d+)\s*$", body)
            if not match:
                raise ValueError(f"Cannot extract {field} from state {state['number']}")
            state[field] = int(match.group(1))
        states.append(state)
    if states:
        write_json(path / "trace.json", {"derivation": "Scalar extraction from raw TLC stdout; not a native replay.",
                                        "source_log_sha256": digest(path / "stdout.log"), "states": states})
        rows = ["# TLC 状态轨迹摘录", "", "由本目录 stdout.log 提取；不是原生代码重放。", "",
                "| 状态 | 到达动作 | B 余额 | A 余额 | 故障数 |",
                "|---:|---|---:|---:|---:|"]
        for state in states:
            action = "Init" if state["action_location"] == "Initial predicate" else state["action_location"].split()[0]
            rows.append(f"| {state['number']} | {action} | {state['senderRemaining']} | "
                        f"{state['receiverRemaining']} | {state['faultCount']} |")
        (path / "trace.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return {"trace_states": len(states), "last_state": states[-1] if states else None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="+", choices=list(CASES), default=list(CASES))
    parser.add_argument("--java", type=Path)
    parser.add_argument("--jar", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    toolchain_path = HERE / ".runtime/toolchain.json"
    toolchain = json.loads(toolchain_path.read_text(encoding="utf-8-sig")) if toolchain_path.exists() else {}
    java = args.java or Path(toolchain.get("java", "java"))
    jar = args.jar or Path(toolchain.get("jar", HERE / ".runtime/tla2tools-1.7.4.jar"))
    if not jar.is_file():
        parser.error("Run bootstrap.ps1 or specify --java and --jar.")

    source = {}
    for relative, expected in SOURCE_HASHES.items():
        actual = digest(REPO / relative)
        pinned = git("rev-parse", f"{UPSTREAM}:{relative}")
        worktree = git("hash-object", "--", relative)
        if actual != expected or pinned != worktree:
            parser.error(f"Source/mapping mismatch: {relative}")
        source[relative] = {"sha256": actual, "pinned_git_blob": pinned, "worktree_git_blob": worktree}
    for name, expected in PRESERVED_MODELS.items():
        if digest(HERE / name) != expected:
            parser.error(f"Earlier model changed; review its baseline: {name}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (args.output or HERE / "evidence" / f"delivery-{stamp}").resolve()
    output.mkdir(parents=True, exist_ok=False)
    inputs = output / "inputs"
    (inputs / "delivery_configs").mkdir(parents=True)
    for name in (f"{MODEL}.tla", "run_delivery_tlc.py", "run_tlc.py", "DELIVERY_MODEL.md"):
        shutil.copy2(HERE / name, inputs / name)
    for case in args.cases:
        shutil.copy2(HERE / "delivery_configs" / f"{case}.cfg", inputs / "delivery_configs" / f"{case}.cfg")
    java_command = [str(java), "-XX:+UseParallelGC", "-Xmx512m", "-Dfile.encoding=UTF-8", "-cp", str(jar)]
    manifest = {"started_utc": datetime.now(timezone.utc).isoformat(), "upstream_commit": UPSTREAM,
                "worktree_head": git("rev-parse", "HEAD"), "source": source,
                "python": sys.version, "python_executable": sys.executable, "platform": platform.platform(),
                "toolchain_metadata": toolchain, "actual_jar_sha256": digest(jar),
                "java_version": run([str(java), "-version"], HERE),
                "input_sha256": {str(p.relative_to(inputs)): digest(p)
                                  for p in sorted(inputs.rglob("*")) if p.is_file()},
                "preserved_models_sha256": PRESERVED_MODELS,
                "native_replay_performed": False, "repair_implemented": False,
                "scope": "Finite original-code dual-ledger model with explicit bounded connection aborts; "
                         "candidate quiescent accounting properties distinguished from receiver quota safety."}
    write_json(output / "manifest.json", manifest)

    syntax_dir = output / "syntax"
    syntax_dir.mkdir()
    syntax = run(java_command + ["tla2sany.SANY", f"{MODEL}.tla"], inputs)
    syntax_text = record_process(syntax_dir, syntax)
    syntax_ok = (syntax["returncode"] == 0 and not syntax["timed_out"]
                 and f"Semantic processing of module {MODEL}" in syntax_text
                 and not re.search(r"\*\*\* (?:Errors|Parse Error)|Semantic errors:|Fatal errors:", syntax_text))
    summary = {"evidence_directory": str(output), "model": MODEL, "syntax_ok": syntax_ok, "cases": []}
    if not syntax_ok:
        write_json(output / "summary.json", summary)
        print(f"SANY failed. Evidence: {output}", flush=True)
        return 1

    for case in args.cases:
        expected_kind, expected_invariant, category = CASES[case]
        directory = output / case
        directory.mkdir()
        command = java_command + ["tlc2.TLC", "-workers", "1", "-fp", "0", "-config",
                                  f"delivery_configs/{case}.cfg", "-metadir", str(directory / "states"),
                                  "-dump", "dot,actionlabels", str(directory / "state_graph"), f"{MODEL}.tla"]
        process = run(command, inputs)
        log = record_process(directory, process)
        violations = re.findall(r"Invariant (\w+) is violated", log)
        completed = "Model checking completed. No error has been found." in log
        if expected_kind == "complete":
            matched = process["returncode"] == 0 and completed and not violations
            result = "no_violation_found" if matched else "unexpected_result"
        else:
            matched = process["returncode"] not in (0, None) and violations == [expected_invariant]
            result = ("witness_reached" if expected_kind == "witness" else "violated") if matched else "unexpected_result"
        matched = matched and not process["timed_out"]
        stats = re.search(r"([\d,]+) states generated, ([\d,]+) distinct states found, ([\d,]+) states left on queue", log)
        item = {"name": case, "category": category, "expected_kind": expected_kind,
                "expected_invariant": expected_invariant, "observed_violations": violations,
                "property_result": result, "expected_outcome_observed": matched,
                "returncode": process["returncode"], "timed_out": process["timed_out"],
                "seconds": process["seconds"], "states":
                {"generated": int(stats.group(1).replace(",", "")),
                 "distinct": int(stats.group(2).replace(",", "")),
                 "queued": int(stats.group(3).replace(",", ""))} if stats else None}
        item.update(extract_trace(process["stdout"], directory))
        summary["cases"].append(item)
        write_json(directory / "result.json", item)
        write_json(output / "summary.json", summary)
        print(f"{case}: {result}; category={category}; expected={matched}; exit={process['returncode']}", flush=True)

    summary["source_unchanged_after_run"] = all(digest(REPO / p) == h for p, h in SOURCE_HASHES.items())
    summary["earlier_models_unchanged"] = all(digest(HERE / p) == h for p, h in PRESERVED_MODELS.items())
    summary["all_expected_outcomes_observed"] = (syntax_ok and summary["source_unchanged_after_run"]
                                               and summary["earlier_models_unchanged"]
                                               and all(c["expected_outcome_observed"] for c in summary["cases"]))
    summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "summary.json", summary)
    print(f"Evidence: {output}", flush=True)
    return 0 if summary["all_expected_outcomes_observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
