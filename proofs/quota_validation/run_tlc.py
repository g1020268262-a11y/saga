"""Run the source-bound ORIGINAL SAGA quota model and retain raw evidence.

Expected counterexamples are recorded as violated properties, not as proofs
of correctness. No native replay, patch, or deployment experiment is run here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
UPSTREAM = "7372111bea150e32cee390a616849316d2780bfc"
SOURCE_HASHES = {
    "saga/agent.py": "94bebf70df4f76e55c0bb8a54c5f29b7fa688ead197ece18f8ac9dec8edae8d5",
    "saga/config.py": "5a42594196897d607c368c2cddc469a327d1dac92fe5d5de66c4b0bceb7f4e23",
    "saga/common/crypto.py": "dca1a5fa145afbf419b1a71af068e0b98a3ac533a929862d12e023f5c8436b7b",
}
CASES = {
    "minimal_race": ("violation", "QuotaSafety"),
    "default_50_race": ("violation", "QuotaSafety"),
    "single_connection": ("complete", None),
    "exhausted_entry": ("complete", None),
    "zero_quota_entry": ("complete", None),
    "original_structure": ("complete", None),
    "reachable_admission": ("witness", "NoAdmission"),
    "reachable_message_rejection": ("witness", "NoMessageRejection"),
    "reachable_backend_overrun": ("violation", "BackendQuotaSafety"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def run(command: list[str], cwd: Path, timeout: int = 90) -> dict:
    started = datetime.now(timezone.utc)
    try:
        process = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=timeout)
        return {"command": command, "cwd": str(cwd), "returncode": process.returncode,
                "stdout": process.stdout, "stderr": process.stderr,
                "seconds": (datetime.now(timezone.utc) - started).total_seconds(),
                "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        def decode(value):
            return value.decode("utf-8", "replace") if isinstance(value, bytes) else value or ""
        return {"command": command, "cwd": str(cwd), "returncode": None,
                "stdout": decode(exc.stdout), "stderr": decode(exc.stderr),
                "seconds": (datetime.now(timezone.utc) - started).total_seconds(),
                "timed_out": True}


def record_process(directory: Path, result: dict) -> str:
    (directory / "stdout.log").write_text(result["stdout"], encoding="utf-8")
    (directory / "stderr.log").write_text(result["stderr"], encoding="utf-8")
    write_json(directory / "process.json", {k: v for k, v in result.items()
                                            if k not in ("stdout", "stderr")})
    return result["stdout"] + "\n" + result["stderr"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", type=Path)
    parser.add_argument("--jar", type=Path)
    parser.add_argument("--cases", nargs="+", choices=list(CASES), default=list(CASES))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    toolchain_file = HERE / ".runtime/toolchain.json"
    toolchain = json.loads(toolchain_file.read_text(encoding="utf-8-sig")) if toolchain_file.exists() else {}
    java = args.java or Path(toolchain.get("java", "java"))
    jar = args.jar or Path(toolchain.get("jar", HERE / ".runtime/tla2tools-1.7.4.jar"))
    if not jar.is_file():
        parser.error("Missing TLC jar. Run bootstrap.ps1 or supply --java and --jar.")

    source = {}
    for relative, expected in SOURCE_HASHES.items():
        actual = digest(REPO / relative)
        if actual != expected:
            parser.error(f"Source hash changed: {relative}. Review/update the mapping before running.")
        source[relative] = {"sha256": actual, "pinned_git_blob": git("rev-parse", f"{UPSTREAM}:{relative}"),
                            "worktree_git_blob": git("hash-object", "--", relative)}
        if source[relative]["pinned_git_blob"] != source[relative]["worktree_git_blob"]:
            parser.error(f"Pinned source mismatch: {relative}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (args.output or HERE / "evidence" / stamp).resolve()
    output.mkdir(parents=True, exist_ok=False)
    snapshots = output / "inputs"
    snapshots.mkdir()
    for name in ("SagaQuota.tla", "run_tlc.py", "bootstrap.ps1", "README.md", "SOURCE_MAPPING.md"):
        path = HERE / name
        if path.exists():
            shutil.copy2(path, snapshots / name)
    (snapshots / "configs").mkdir()
    for case in args.cases:
        shutil.copy2(HERE / "configs" / f"{case}.cfg", snapshots / "configs" / f"{case}.cfg")

    mapping_path = REPO / "output/analysis/qmax-source-model-map-20261024/源码与模型对应表.md"
    if mapping_path.is_file():
        shutil.copy2(mapping_path, snapshots / "source_model_map_20261024.md")

    java_command = [str(java), "-XX:+UseParallelGC", "-Xmx512m", "-Dfile.encoding=UTF-8", "-cp", str(jar)]
    java_version = run([str(java), "-version"], HERE)
    manifest = {"started_utc": datetime.now(timezone.utc).isoformat(), "upstream_commit": UPSTREAM,
                "worktree_head": git("rev-parse", "HEAD"), "source": source,
                "python": sys.version, "python_executable": sys.executable,
                "platform": platform.platform(), "toolchain_bootstrap_metadata": toolchain,
                "java_version": java_version, "actual_jar_sha256": digest(jar),
                "input_sha256": {str(p.relative_to(snapshots)): digest(p)
                                  for p in sorted(snapshots.rglob("*")) if p.is_file()},
                "native_replay_performed": False, "repair_model_included": False,
                "scope": "Single known token; fixed non-quota metadata; explicit sequential prefix; "
                         "existing-token entrance checks; one ordinary request per racing connection; "
                         "finite configurations; no network/cryptographic/implementation refinement proof."}
    write_json(output / "manifest.json", manifest)

    syntax_dir = output / "syntax"
    syntax_dir.mkdir()
    syntax = run(java_command + ["tla2sany.SANY", "SagaQuota.tla"], snapshots)
    syntax_text = record_process(syntax_dir, syntax)
    syntax_ok = (syntax["returncode"] == 0 and not syntax["timed_out"]
                 and "Semantic processing of module SagaQuota" in syntax_text
                 and not re.search(r"\*\*\* (?:Errors|Parse Error)|Semantic errors:|Fatal errors:", syntax_text))
    summary = {"evidence_directory": str(output), "syntax_ok": syntax_ok, "cases": []}
    if not syntax_ok:
        write_json(output / "summary.json", summary)
        print(f"Syntax check failed; inspect {syntax_dir}", flush=True)
        return 1

    for case in args.cases:
        expected_kind, expected_invariant = CASES[case]
        directory = output / case
        directory.mkdir()
        command = java_command + ["tlc2.TLC", "-workers", "1", "-fp", "0", "-config",
                                  f"configs/{case}.cfg", "-metadir", str(directory / "states"),
                                  "-dump", "dot,actionlabels", str(directory / "state_graph"), "SagaQuota.tla"]
        process = run(command, snapshots)
        log = record_process(directory, process)
        violations = re.findall(r"Invariant (\w+) is violated", log)
        completed = "Model checking completed. No error has been found." in log
        if expected_kind == "complete":
            expected_observed = process["returncode"] == 0 and completed and not violations
            property_result = "no_violation_found" if expected_observed else "unexpected_result"
        else:
            expected_observed = (process["returncode"] not in (0, None)
                                 and violations == [expected_invariant])
            property_result = ("witness_reached" if expected_kind == "witness" else "violated") \
                              if expected_observed else "unexpected_result"
        expected_observed = expected_observed and not process["timed_out"]
        stats = re.search(r"([\d,]+) states generated, ([\d,]+) distinct states found, ([\d,]+) states left on queue", log)
        item = {"name": case, "expected_kind": expected_kind, "expected_invariant": expected_invariant,
                "observed_violations": violations, "property_result": property_result,
                "expected_outcome_observed": expected_observed, "returncode": process["returncode"],
                "timed_out": process["timed_out"], "seconds": process["seconds"],
                "states": {"generated": int(stats.group(1).replace(",", "")),
                           "distinct": int(stats.group(2).replace(",", "")),
                           "queued": int(stats.group(3).replace(",", ""))} if stats else None}
        summary["cases"].append(item)
        write_json(directory / "result.json", item)
        write_json(output / "summary.json", summary)
        print(f"{case}: {property_result}; expected={expected_observed}; exit={process['returncode']}", flush=True)

    summary["source_unchanged_after_run"] = all(digest(REPO / name) == expected
                                                 for name, expected in SOURCE_HASHES.items())
    summary["all_expected_outcomes_observed"] = (syntax_ok and summary["source_unchanged_after_run"]
                                               and all(c["expected_outcome_observed"] for c in summary["cases"]))
    summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "summary.json", summary)
    print(f"Evidence: {output}", flush=True)
    return 0 if summary["all_expected_outcomes_observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
