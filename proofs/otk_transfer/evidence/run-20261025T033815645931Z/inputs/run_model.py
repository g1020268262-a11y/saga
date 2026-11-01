"""Run the focused SAGA OTK-transfer model and retain native Tamarin evidence.

Use Python 3 inside the WSL distribution containing Tamarin/Maude; see README.
Only this directory's new evidence directory is written. No SAGA code is run.
"""

from __future__ import annotations

import argparse
from collections import Counter
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


def extract_witness(directory: Path) -> None:
    """Project the solver's native witness; never invent a replacement trace."""
    source = directory / "traces.json"
    native = json.loads(source.read_text(encoding="utf-8"))
    lemma = "transfer_after_C_exhaustion_completes"
    matches = [g for g in native["graphs"] if f"_{lemma}-" in g["jgLabel"]]
    if len(matches) != 1:
        raise ValueError(f"Expected one native witness for {lemma}, found {len(matches)}")
    graph = matches[0]
    nodes = {node["jgnId"]: node for node in graph["jgNodes"]
             if node["jgnType"] == "isProtocolRule"}
    edges = {(edge["jgeSource"].split(":")[0], edge["jgeTarget"].split(":")[0])
             for edge in graph["jgEdges"]}
    edges = {(a, b) for a, b in edges if a in nodes and b in nodes and a != b}
    remaining = set(nodes)
    ordered = []
    while remaining:
        ready = sorted(n for n in remaining
                       if not any(a in remaining and b == n for a, b in edges))
        if not ready:
            raise ValueError("Native witness graph contains an unexpected dependency cycle")
        ordered.extend(ready)
        remaining.difference_update(ready)
    rows = []
    actions = []
    for node_id in ordered:
        node = nodes[node_id]
        acts = node["jgnMetadata"]["jgnActs"]
        actions.extend(acts)
        rows.append({"node": node_id, "rule": node["jgnLabel"],
                     "actions": [a["jgnFactShow"] for a in acts]})

    def atom(term: dict) -> str:
        return term.get("jgnConst", term.get("jgnShow", json.dumps(term, sort_keys=True)))

    issues = [a for a in actions if a["jgnFactName"] == "ProviderIssue"]
    accepted = [a for a in actions if a["jgnFactName"] == "RequestAccepted"]
    forwards = [a for a in actions if a["jgnFactName"] == "ForwardOTK"]
    decrypts = [a for a in actions if a["jgnFactName"] == "ClientDecryptedToken"]
    rejected = [a for a in actions if a["jgnFactName"] == "ProviderRejectExhausted"]
    issue_counts = Counter(atom(a["jgnFactTerms"][1]) for a in issues)
    c_accepted = [a for a in accepted if atom(a["jgnFactTerms"][1]) == "'C'"]
    c_keys = {atom(a["jgnFactTerms"][2]) for a in c_accepted}
    keys_by_sender = {atom(a["jgnFactTerms"][1]): atom(a["jgnFactTerms"][2]) for a in issues}
    checks = {
        "one_provider_issue_to_B_and_one_to_C": issue_counts == {"'B'": 1, "'C'": 1},
        "C_accepted_with_two_distinct_OTKs": len(c_accepted) == 2 and len(c_keys) == 2,
        "accepted_keys_are_exactly_the_two_issued_keys": c_keys == set(keys_by_sender.values()),
        "one_explicit_B_to_C_forward_of_Bs_issued_key": len(forwards) == 1
            and atom(forwards[0]["jgnFactTerms"][1]) == "'B'"
            and atom(forwards[0]["jgnFactTerms"][2]) == "'C'"
            and atom(forwards[0]["jgnFactTerms"][3]) == keys_by_sender.get("'B'"),
        "C_decrypted_both_tokens": len(decrypts) == 2
            and all(atom(a["jgnFactTerms"][1]) == "'C'" for a in decrypts),
        "Provider_explicitly_rejected_C_for_exhaustion": any(
            atom(a["jgnFactTerms"][1]) == "'C'" for a in rejected),
        "both_acceptances_bound_to_same_C_PAC": len({
            atom(a["jgnFactTerms"][4]) for a in c_accepted}) == 1,
    }
    if not all(checks.values()):
        raise ValueError(f"Native trace interpretation checks failed: {checks}")
    projection = {
        "source": "traces.json", "source_sha256": digest(source),
        "lemma": lemma, "graph_label": graph["jgLabel"], "checks": checks,
        "keys_by_provider_recipient": keys_by_sender,
        "provider_issue_counts": dict(issue_counts),
        "C_distinct_used_OTKs": sorted(c_keys),
        "nodes_one_topological_order": rows,
        "native_edges": graph["jgEdges"],
        "ordering_note": "One topological ordering, not a unique total schedule.",
    }
    save_json(directory / "witness.json", projection)
    lines = ["# C 耗尽领取配额后使用转交 OTK：原生轨迹投影", "",
             f"来源：Tamarin `{lemma}` 的 `exists-trace` 见证。", "",
             "本文件从原始 `traces.json` 提取事件，没有手工编造执行步骤。"
             "下表是一种满足原图依赖的拓扑顺序，不表示唯一的全局执行顺序。", "",
             "机器核对：Provider 向 B、C 各发放一个；C 使用两个不同 OTK；"
             "B 明确转交自己的那个 OTK；C 解密两个 token；"
             "Provider 已因 C 配额耗尽拒绝其领取请求。", "",
             "见证公式额外要求：C 的第一次受理 < 配额耗尽拒绝 < B 转交 < C 收到转交 < 第二次受理。", "",
             "| 节点 | 规则 | 原始观察事件 |", "|---|---|---|"]
    for row in rows:
        events = "<br>".join(f"`{a}`" for a in row["actions"]) or "初始化／内部状态步骤"
        lines.append(f"| `{row['node']}` | `{row['rule']}` | {events} |")
    lines += ["", "解释边界：这是固定两发送方、每方领取配额为 1、两个 OTK、"
              "理想 mTLS 与选定转交行为下的模型见证；没有运行原生 SAGA 网络服务。", ""]
    (directory / "witness.zh-CN.md").write_text("\n".join(lines), encoding="utf-8")


def write_report(evidence: Path, all_results: dict, problems: list[str]) -> None:
    labels = {
        "normal_B_completes": "B 正常完成一次请求（可达性）",
        "normal_C_completes": "C 正常完成一次请求（可达性）",
        "transfer_after_C_exhaustion_completes": "C 耗尽后通过转交完成第二次请求（可达性）",
        "provider_per_sender_issuance_limit": "Provider 对每个发送方最多发放一次",
        "provider_issues_each_OTK_once": "同一个 OTK 最多由 Provider 发放一次",
        "receiver_consumes_each_OTK_once": "同一个 OTK 最多在 A 处消费一次",
        "accepted_request_has_matching_token_and_decryption": "受理前有匹配的 token 签发与解密",
        "long_term_keys_not_disclosed": "长期访问控制私钥没有被网络攻击者获知",
        "successful_use_requires_issue_to_same_sender": "成功使用要求此前发给同一发送方（候选性质）",
        "sender_uses_at_most_one_distinct_OTK": "每方最多使用一个不同 OTK（候选使用上限）",
    }
    lines = ["# OTK 主动转交：本次 Tamarin 结果", "",
             f"证据目录：`{evidence.name}`。", "",
             "主模型中，Provider 的领取次数限制成立；C 仍能使用 B 主动转交的 OTK。"
             "转交轨迹包含 C 先完成一次请求、Provider 因 C 配额耗尽拒绝再次领取、"
             "随后 C 收到 B 的 OTK 并用自己的身份和私钥完成第二次请求。", "",
             "| 检查 | 主动转交 | 禁止转交 | 两端明确拒绝 C |",
             "|---|---|---|---|"]
    for lemma, label in labels.items():
        verdicts = []
        for case in CASES:
            actual = all_results[case]["results"].get(lemma, {}).get("actual", "缺失")
            if LEMMA_TYPES[lemma] == "exists-trace":
                meaning = {"verified": "可达", "falsified": "不可达"}.get(actual, actual)
            else:
                meaning = {"verified": "成立", "falsified": "存在反例"}.get(actual, actual)
            verdicts.append(meaning)
        lines.append(f"| {label} | {' | '.join(verdicts)} |")
    lines += ["", "## 结果应如何解释", "",
              "OTK 的一次性消费、token 对实际发送方 PAC 的绑定以及 Provider 的发放计数，"
              "可以同时成立，但不自动建立领取者与使用者的一致性。"
              "本结果没有证明 Provider 多发了 OTK；它区分了发放上限与跨身份实际使用上限。", "",
              "两个候选性质是本次明确提出的检查目标；不据此声称原论文已经承诺或证明"
              "在主动转交／协作发送方条件下，这两个更强目标成立。", "",
              "这是固定配置的符号模型分析，没有原生网络重放，没有完整注册、"
              "策略更新、撤销、任意预算、token 多次使用或线程竞态验证。", "",
              "对照的判读规则：只有结果表确认 B、C 正常路径可达，才排除了对应的空成立问题。"
              "明确拒绝 C 的配置预期使 C 不可达；若得到该结果，针对 C 的安全性仍不能"
              "单独作为非空证明。表内“缺失”表示本次未取得该项结论。", "",
              "## 证据", "",
              "- [原生转交轨迹投影](forwarding/witness.zh-CN.md)",
              "- [轨迹投影与原始 JSON 的哈希绑定](forwarding/witness.json)",
              "- [全部查询的机器结果](summary.json)",
              "- [模型、脚本、源码和工具的哈希清单](manifest.json)",
              "- 各对照目录保存解析／证明命令、退出码、stdout、stderr、证明文件和 JSON/DOT 轨迹。", "",
              f"本次结果核对：{'30/30 与预期一致' if not problems else '存在失败或未完成项，详见 summary.json'}。", ""]
    (evidence / "REPORT.zh-CN.md").write_text("\n".join(lines), encoding="utf-8")


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
        base = [tamarin, *flags, "--quit-on-warning", "--derivcheck-timeout=30"]
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

    try:
        extract_witness(evidence / "forwarding")
    except (OSError, ValueError, KeyError) as error:
        problems.append(f"Native witness projection failed: {error}")
    manifest["source_changed_during_run"] = [
        path for path, before in source_hashes.items() if digest(REPO / path) != before]
    if manifest["source_changed_during_run"]:
        problems.append("SAGA source changed during the run")
    if digest(MODEL) != manifest["model_sha256"]:
        problems.append("Live model differs from the snapshot proved")
    if digest(Path(__file__)) != manifest["runner_sha256"]:
        problems.append("Runner changed during the run")
    write_report(evidence, all_results, problems)
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
