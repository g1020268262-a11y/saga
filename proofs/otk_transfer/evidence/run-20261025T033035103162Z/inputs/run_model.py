"""Run the focused SAGA OTK-transfer model and retain native Tamarin evidence.

Use Python 3 inside the WSL distribution containing Tamarin/Maude; see README.
Only this directory's new evidence directory is written. No SAGA code is run.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MODEL = HERE / "saga_otk_transfer.spthy"
SOURCE_PATHS = [
    "saga/provider/provider.py", "saga/agent.py", "saga/common/crypto.py",
    "saga/common/contact_policy.py", "saga/config.py",
]
LEMMA_TYPES = {
    "normal_B_completes": "exists-trace",
    "normal_C_completes": "exists-trace",
    "transfer_after_C_exhaustion_completes": "exists-trace",
    "provider_per_sender_issuance_limit": "all-traces",
    "provider_issues_each_OTK_once": "all-traces",
    "receiver_consumes_each_OTK_once": "all-traces",
    "accepted_request_has_matching_token_and_decryption": "all-traces",
    "long_term_keys_not_disclosed": "all-traces",
    "successful_use_requires_issue_to_same_sender": "all-traces",
    "sender_uses_at_most_one_distinct_OTK": "all-traces",
}
CASES = {
    "forwarding": [],
    "no_forwarding": ["-DNO_FORWARD"],
    "deny_C": ["-DDENY_C"],
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def expected(case: str, lemma: str) -> str:
    if lemma == "transfer_after_C_exhaustion_completes":
        return "verified" if case == "forwarding" else "falsified"
    if lemma == "normal_C_completes" and case == "deny_C":
        return "falsified"
    if lemma in {"successful_use_requires_issue_to_same_sender",
                 "sender_uses_at_most_one_distinct_OTK"} and case == "forwarding":
        return "falsified"
    return "verified"


def run(command: list[str], directory: Path, name: str, timeout: int) -> dict:
    started = time.monotonic()
    timed_out = False
    with (directory / f"{name}.stdout.txt").open("wb") as out, \
            (directory / f"{name}.stderr.txt").open("wb") as err:
        process = subprocess.Popen(command, cwd=REPO, stdout=out, stderr=err,
                                   start_new_session=True)
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                returncode = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                returncode = process.wait()
    record = {
        "command": command, "cwd": str(REPO), "exit_code": returncode,
        "timeout": timed_out, "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    save_json(directory / f"{name}.command.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=180,
                        help="Hard timeout in seconds for each parse/proof command")
    parser.add_argument("--tamarin", default="tamarin-prover")
    args = parser.parse_args()
    if os.name == "nt":
        parser.error("Run this script through WSL, as shown in README.zh-CN.md")
    if args.timeout < 1:
        parser.error("--timeout must be positive")

    tamarin = shutil.which(args.tamarin)
    if not tamarin:
        parser.error(f"Tamarin not found: {args.tamarin}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    evidence = HERE / "evidence" / f"run-{stamp}"
    evidence.mkdir(parents=True, exist_ok=False)
    inputs = evidence / "inputs"
    inputs.mkdir()
    for path in [MODEL, Path(__file__).resolve()]:
        shutil.copy2(path, inputs / path.name)
    source_hashes = {}
    for relative in SOURCE_PATHS:
        original = REPO / relative
        target = inputs / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
        source_hashes[relative] = digest(original)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO,
                                     text=True).strip()
    status = subprocess.check_output(["git", "status", "--short"], cwd=REPO,
                                     text=True)
    (evidence / "git-status-before.txt").write_text(status, encoding="utf-8")
    version = subprocess.check_output([tamarin, "--version", "+RTS", "-N2", "-RTS"],
                                      stderr=subprocess.STDOUT, text=True)
    (evidence / "tamarin-version.txt").write_text(version, encoding="utf-8")
    maude = shutil.which("maude")
    if maude:
        version_maude = subprocess.check_output([maude, "--version"], text=True,
                                                stderr=subprocess.STDOUT)
        (evidence / "maude-version.txt").write_text(version_maude, encoding="utf-8")
    manifest = {
        "created_utc": stamp, "repository_head": commit,
        "model_scope": "A, B, C; two OTKs; one issuance credit per sender; ideal mTLS",
        "model_sha256": digest(inputs / MODEL.name),
        "runner_sha256": digest(inputs / Path(__file__).name),
        "source_sha256": source_hashes,
        "tamarin": {"path": str(Path(tamarin).resolve()),
                    "sha256": digest(Path(tamarin).resolve())},
        "maude": None if not maude else {
            "path": str(Path(maude).resolve()), "sha256": digest(Path(maude).resolve())},
        "source_changed_during_run": None,
    }
    save_json(evidence / "manifest.json", manifest)
    print(f"Evidence: {evidence}", flush=True)
    all_results = {}
    problems = []
    summary_pattern = re.compile(
        r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+\((all-traces|exists-trace)\):\s*"
        r"(verified|falsified|analysis incomplete)\b", re.MULTILINE)

    for case, flags in CASES.items():
        directory = evidence / case
        directory.mkdir()
        base = [tamarin, *flags, "--quit-on-warning"]
        rts = ["+RTS", "-N2", "-RTS"]
        print(f"[{case}] parse", flush=True)
        parsed = run([*base, "--parse-only", str(inputs / MODEL.name), *rts],
                     directory, "parse", args.timeout)
        if parsed["exit_code"] != 0 or parsed["timeout"]:
            problems.append(f"{case}: parse failed; inspect native output")
            all_results[case] = {"parse": parsed, "results": {}}
            continue
        print(f"[{case}] prove 10 lemmas", flush=True)
        proof = run([*base, "--prove", f"--output={directory / 'proof.spthy'}",
                     f"--output-json={directory / 'traces.json'}",
                     f"--output-dot={directory / 'traces.dot'}",
                     str(inputs / MODEL.name), *rts], directory, "verify", args.timeout)
        output = (directory / "verify.stdout.txt").read_text(encoding="utf-8", errors="replace")
        result_rows = summary_pattern.findall(output)
        results = {}
        for lemma, kind, verdict in result_rows:
            if lemma not in LEMMA_TYPES:
                problems.append(f"{case}: unexpected lemma {lemma}")
                continue
            row = {"type": kind, "actual": verdict,
                   "expected": expected(case, lemma)}
            row["matches_expected"] = (kind == LEMMA_TYPES[lemma]
                                       and verdict == row["expected"])
            results[lemma] = row
            if not row["matches_expected"]:
                problems.append(f"{case}/{lemma}: unexpected result")
        missing = set(LEMMA_TYPES) - set(results)
        if missing:
            problems.append(f"{case}: missing results: {sorted(missing)}")
        if len(result_rows) != len(results):
            problems.append(f"{case}: duplicate/unexpected result rows")
        if proof["exit_code"] != 0 or proof["timeout"]:
            problems.append(f"{case}: proof command failed or timed out")
        all_results[case] = {"parse": parsed, "proof": proof, "results": results}
        save_json(directory / "results.json", results)
        print(f"[{case}] {len(results)} results, "
              f"{sum(row['matches_expected'] for row in results.values())} expected", flush=True)

    manifest["source_changed_during_run"] = [
        path for path, before in source_hashes.items() if digest(REPO / path) != before]
    if manifest["source_changed_during_run"]:
        problems.append("SAGA source changed during the run")
    if digest(MODEL) != manifest["model_sha256"]:
        problems.append("Live model differs from the snapshot proved")
    if digest(Path(__file__)) != manifest["runner_sha256"]:
        problems.append("Runner changed during the run")
    manifest["artifacts"] = {
        str(path.relative_to(evidence)): digest(path)
        for path in sorted(evidence.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    save_json(evidence / "manifest.json", manifest)
    summary = {"cases": all_results, "problems": problems,
               "all_expected": not problems,
               "note": "Expected falsifications are results, not proof-command failures."}
    save_json(evidence / "summary.json", summary)
    # Include the final summary itself in the archive's artifact hashes.
    manifest["artifacts"]["summary.json"] = digest(evidence / "summary.json")
    save_json(evidence / "manifest.json", manifest)
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    print("PASS" if not problems else "INCOMPLETE / UNEXPECTED RESULT", flush=True)
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
