"""Add provider/OTK correspondences to an unchanged upstream model and run ProVerif."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time


ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "proofs/proverif/agent_communication.pv"
MODEL = ROOT / "proofs/proverif/agent_communication_provider_otk.pv"
UPSTREAM = "7372111bea150e32cee390a616849316d2780bfc"
BASELINE_SHA256 = "3faf15a801658dc70ceacf1752557cec62ad965854304ad703dce8bdee008302"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extension() -> bytes:
    """Only add observer events and queries; erasure restores the original bytes."""
    original = BASELINE.read_bytes()
    if digest(BASELINE) != BASELINE_SHA256:
        raise ValueError("Baseline hash changed; review the source mapping first.")
    if git("hash-object", "--", str(BASELINE.relative_to(ROOT))) != git(
        "rev-parse", f"{UPSTREAM}:proofs/proverif/agent_communication.pv"
    ):
        raise ValueError("Baseline differs from the pinned upstream model.")
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    additions = [
        ("event EndAgentAuthB(bitstring, bitstring, key).", """
(* Observation only: registration confirmation is NOT a contact-policy check.
   Full tuples are (receiver, initiator, initiator_metadata, PAC_B, OTK_A).
   ReceiverAcceptsInitiator is A issuing a token, not a TLS/key-confirmation
   event. InitiatorCompletesConnection is B verifying the returned token.
   ProviderIssuesOTK records the decision immediately before the original
   public-channel output. It does not assert confidential delivery to B. *)
event ProviderConfirmsInitiator(bitstring, bitstring, pkey).
event ProviderIssuesOTK(bitstring, bitstring, bitstring, pkey, pkey).
event ReceiverAcceptsInitiator(bitstring, bitstring, bitstring, pkey, pkey).
event InitiatorCompletesConnection(bitstring, bitstring, bitstring, pkey, pkey).
""", "after"),
        ("  event EndAgentAuthA(token, ED_A, DH_A);", """
  event ReceiverAcceptsInitiator(aid_A, aid_B, ED_B, PAC_B, OTK1_A);
""", "after"),
        ("  event EndAgentAuthB(token, ED_A, DH_B);", """
  event InitiatorCompletesConnection(aid_A, aid_B, ED_B, PAC_B, OTK1_A);
""", "after"),
        ("  event EndProviderAuthB(ED_B, aid_B, OTK1_B);", """
  event ProviderConfirmsInitiator(aid_B, ED_B, PAC_B);
""", "after"),
        ("  out(prov_b, (Cert_A, Cert_B, aid_A, OTK1_A_sig, OTK1_A, sigma_A_sig, PAC_A, ED_A));", """
  event ProviderIssuesOTK(aid_A, aid_B, ED_B, PAC_B, OTK1_A);
""", "before"),
        ("query attacker(token). ", """
(* Main goal at A's local token-issuance point. No new execution guard. *)
query receiver: bitstring, initiator: bitstring, ed: bitstring, pac: pkey, otk: pkey;
  event(ReceiverAcceptsInitiator(receiver, initiator, ed, pac, otk))
  ==> event(ProviderConfirmsInitiator(initiator, ed, pac))
      && event(ProviderIssuesOTK(receiver, initiator, ed, pac, otk)).

(* Separate the registration-authentication component from OTK issuance. *)
query receiver: bitstring, initiator: bitstring, ed: bitstring, pac: pkey, otk: pkey;
  event(ReceiverAcceptsInitiator(receiver, initiator, ed, pac, otk))
  ==> event(ProviderConfirmsInitiator(initiator, ed, pac)).

(* Also check the stronger completion point where B verifies A's token. *)
query receiver: bitstring, initiator: bitstring, ed: bitstring, pac: pkey, otk: pkey;
  event(InitiatorCompletesConnection(receiver, initiator, ed, pac, otk))
  ==> event(ProviderConfirmsInitiator(initiator, ed, pac))
      && event(ProviderIssuesOTK(receiver, initiator, ed, pac, otk)).

(* Non-vacuity: false "not event" results mean these endpoints are reachable. *)
query receiver: bitstring, initiator: bitstring, ed: bitstring, pac: pkey, otk: pkey;
  event(ReceiverAcceptsInitiator(receiver, initiator, ed, pac, otk)).
query receiver: bitstring, initiator: bitstring, ed: bitstring, pac: pkey, otk: pkey;
  event(InitiatorCompletesConnection(receiver, initiator, ed, pac, otk)).
""", "after"),
    ]
    data = original
    for anchor, body, position in additions:
        anchor_bytes = anchor.encode() + newline
        if data.count(anchor_bytes) != 1:
            raise ValueError(f"Missing or ambiguous insertion anchor: {anchor}")
        block = (newline + b"(* PROVIDER-OTK-BEGIN *)" + newline
                 + body.strip("\n").encode().replace(b"\n", newline) + newline
                 + b"(* PROVIDER-OTK-END *)" + newline)
        replacement = block + anchor_bytes if position == "before" else anchor_bytes + block
        data = data.replace(anchor_bytes, replacement)
    erased = re.sub(rb"\r?\n\(\* PROVIDER-OTK-BEGIN \*\)\r?\n.*?\(\* PROVIDER-OTK-END \*\)\r?\n",
                    b"", data, flags=re.S)
    if erased != original:
        raise ValueError("Removing observer blocks did not restore the exact baseline.")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proverif", default="proverif")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    expected = extension()
    if MODEL.exists() and MODEL.read_bytes() != expected:
        parser.error("Existing extension differs; refusing to overwrite it.")
    if not MODEL.exists():
        MODEL.write_bytes(expected)
    print("Observer erasure restores the upstream model byte for byte.", flush=True)
    if args.build_only:
        return 0

    executable = shutil.which(args.proverif)
    if not executable:
        parser.error(f"ProVerif executable not found: {args.proverif}")
    executable = str(Path(executable).resolve())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (args.output or ROOT / "proofs/evidence" / f"provider-otk-{stamp}").resolve()
    output.mkdir(parents=True, exist_ok=False)
    inputs = output / "inputs"
    inputs.mkdir()
    for source in (BASELINE, MODEL, Path(__file__).resolve()):
        shutil.copy2(source, inputs / source.name)
    version = subprocess.run([executable, "-help"], capture_output=True)
    (output / "proverif-version.txt").write_bytes(version.stdout + version.stderr)
    manifest = {
        "started_utc": datetime.now(timezone.utc).isoformat(), "upstream_commit": UPSTREAM,
        "worktree_head": git("rev-parse", "HEAD"),
        "baseline_sha256": digest(BASELINE), "extension_sha256": digest(MODEL),
        "observer_erasure_equals_baseline": True,
        "protocol_control_flow_changed": False, "native_replay_performed": False,
        "proverif_executable": executable, "proverif_sha256": digest(Path(executable)),
        "proverif_version": (version.stdout + version.stderr).decode(errors="replace").splitlines()[0],
        "input_sha256": {p.name: digest(p) for p in inputs.iterdir()}, "runs": [],
        "completed": False,
    }
    save_json(output / "manifest.json", manifest)
    print(f"Evidence directory: {output}", flush=True)
    completed = False
    try:
        for name, flags in (("parse", ["-parse-only"]), ("verify", [])):
            command = [executable, *flags, str(inputs / MODEL.name)]
            record = {"name": name, "command": command, "started_utc": datetime.now(timezone.utc).isoformat()}
            manifest["runs"].append(record)
            save_json(output / "manifest.json", manifest)
            started = time.monotonic()
            with (output / f"{name}.stdout.txt").open("wb") as stdout, (output / f"{name}.stderr.txt").open("wb") as stderr:
                try:
                    result = subprocess.run(command, cwd=inputs, stdout=stdout, stderr=stderr,
                                            timeout=args.timeout, check=False)
                    record.update({"exit_code": result.returncode, "timed_out": False})
                except subprocess.TimeoutExpired:
                    record.update({"exit_code": None, "timed_out": True})
            record["elapsed_seconds"] = round(time.monotonic() - started, 3)
            log = (output / f"{name}.stdout.txt").read_text(encoding="utf-8", errors="replace")
            record["results"] = re.findall(r"^RESULT .+$", log, re.M)
            record["stdout_sha256"] = digest(output / f"{name}.stdout.txt")
            record["stderr_sha256"] = digest(output / f"{name}.stderr.txt")
            save_json(output / "manifest.json", manifest)
            if record["exit_code"] != 0:
                raise RuntimeError(f"{name} failed; see archived stdout/stderr.")
            if name == "verify":
                completed = len(record["results"]) == 16
                summary = {"results": record["results"], "result_count": len(record["results"]),
                           "tool_completed": completed,
                           "baseline_unchanged": digest(BASELINE) == manifest["baseline_sha256"],
                           "extension_unchanged": digest(MODEL) == manifest["extension_sha256"]}
                save_json(output / "summary.json", summary)
                (output / "verification-summary.txt").write_text("\n".join(record["results"]) + "\n", encoding="utf-8")
                print("\n".join(record["results"]), flush=True)
                if not completed or not summary["baseline_unchanged"] or not summary["extension_unchanged"]:
                    raise RuntimeError("Result count or model-integrity check failed.")
                manifest["completed"] = True
        return 0
    finally:
        manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["evidence_sha256"] = {p.name: digest(p) for p in output.iterdir()
                                       if p.is_file() and p.name != "manifest.json"}
        save_json(output / "manifest.json", manifest)
        print(f"Manifest: {output / 'manifest.json'}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
