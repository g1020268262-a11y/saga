# SAGA 接触策略 Tamarin 模型（已完成原生验证）

基于 `g1020268262-a11y/saga`，`my-modification` 分支提交 `cf15d0ae79d2a2a47d74fa66e75ccfc98bcda9c6`。

## 本次交付状态

2026-11-24 已在原 OTK 分析使用的 WSL `TamarinVerify` 中，使用 Tamarin 1.12.0 / Maude 3.5.1 完成四配置共 64 项引理的原生分析。正式结果为 `evidence/20261124T111257499246Z/summary.json`，`native_complete=true`，无超时、未完成项或良构性警告。原实现、其他模型、旧证据及论文未改动。

中文报告见 [REPORT.zh-CN.md](REPORT.zh-CN.md)；D/A 原生反例逐步核对见 [DA_TRACE.zh-CN.md](evidence/20261124T111257499246Z/review/DA_TRACE.zh-CN.md)。原生证明、JSON/DOT 轨迹及命令日志位于各配置目录。`finite_replay.json` 仍只是 Python 有限执行示意，**不属于 Tamarin 证明或反例**。`expected_native_results.json` 是验收预期，实测结果单独保存。

## 模型设计

与旧 ProVerif 场景模型不同，Tamarin 实际遍历已匹配的有序规则列表。规则是否匹配及字符评分由生成程序按照仓库 `bridge.py` 的受支持规则计算；列表中不直接注入允许或拒绝结果。最终以 `Scan0`、`Scan1`、`Scan2` 表示固定列表的位置，避免通用递归关系的反向搜索膨胀。每一位置的 `Spec_Select_Better_i` 同时更新最佳规则分值和预算；`Impl_Select_Better_i` 只更新预算，保留旧最佳分值，对应 `contact_policy.py` 的真实缺陷。Provider 与接收方分别执行实现侧求值，使用相同规则和发送方身份。Provider 预算大于零时发放一枚可用 OTK，并记录扣减；接收方本地策略检查拒绝负数。零预算两端判断不同，当前四组输入不包括零预算的实测控制。

注册与认证 TLS 以端点绑定私有事实表示，使用现有 OTK Tamarin 模型相同的 DH、哈希及对称加密建模方法。OTK 发放与消费分别使用线性事实，ACT 使用当前发送方 PAC 加密并绑定身份。客户端必须解密才能提交应用请求，接收方匹配 ACT 和 PAC 后触发 `ChatAccept`。每个模型仅包含固定规则集、一个发送方、一枚 OTK 和一次应用请求；通过新鲜 sid 关联同一次执行中的策略、发放、签发和接受事件。这是原策略影响模型的定点替换，非对全协议、完整 fnmatch 或 Python 的等价性证明。

四个配置均来自已有实际 matcher 观察：D/A（具体拒绝、通配允许）、reverse（反向排列）、A/A（单条允许）、D/D（单条拒绝）。源文件和证据 Git blob 固定在 cases.json。正式执行在 SAGA 仓库中使用现有 bridge.build 重新核对原始证据字节、历史源代码、输入顺序及决策；离线预览只使用本次转录的观察值。预期值只用于验证引理及结果验收，不直接决定 Tamarin 协议规则是否可执行。

## 与旧 ProVerif 的对应

- `chat_requires_token_issue` 对应原 ChatAccept ==> TokenIssue 查询。
- `chat_accept_reachable` 是原 ChatAccept 可达性查询的 exists-trace 形式（结果极性不同）。
- `chat_requires_policy_allow` 直接检查任何被接受请求是否有同次执行的预期允许事件。
- `denied_chat_reachable` 直接检查预期拒绝且请求被接受的路径。
- 另检查预算一致性、Provider 发放、ACT 签发、客户端解密、拒绝和正常执行可达性。共 16 项引理/每配置。

## 在原项目的 WSL 环境正式执行

本目录已安装在 `proofs/acp_tamarin/`，从 SAGA 根目录运行：

```bash
python3 -B proofs/acp_tamarin/run_model.py --repo-root .
```

Windows PowerShell 使用已核实的 WSL 环境：

```powershell
wsl.exe -d TamarinVerify --exec sh -lc 'cd /mnt/d/Users/10202/Desktop/saga; python3 -B proofs/acp_tamarin/run_model.py --repo-root . --timeout 180'
```

已有 Tamarin/Maude 时脚本会进行历史证据核验、生成模型、`--parse-only`、`--prove`，保存 stdout/stderr、proof.spthy、traces.json、traces.dot、版本及哈希、预期和实际结果对照。默认每次创建新归档 `proofs/acp_tamarin/evidence/<UTC>/`。超时、解析错误、警告、缺失或不符合预期的结论不能算作完成。若本地源文件或历史证据与本次审查版本不同，脚本停止而不是忽略差异。

也可以单独检查一个生成的模型（不执行仓库证据核验）：

```bash
tamarin-prover --quit-on-warning --parse-only proofs/acp_tamarin/evidence/20261124T111257499246Z/models/da.spthy +RTS -N2 -RTS
tamarin-prover --quit-on-warning --prove --output=da-proof.spthy --output-json=da-traces.json --output-dot=da-traces.dot proofs/acp_tamarin/evidence/20261124T111257499246Z/models/da.spthy +RTS -N2 -RTS
```

离线检查仅用于开发，不作为论文形式化结果：

```bash
python3 -B -m unittest -v test_models
python3 -B run_model.py --preview-only --offline-preview
```

## 预览执行结果

| 配置 | 预期预算 | Provider 预算 | 接收方预算 | Python 路径终点 |
|---|---:|---:|---:|---|
| D/A | -1 | 10 | 10 | ChatAccept |
| reverse | -1 | -1 | 未到达 | ProviderReject |
| A/A | 10 | 10 | 10 | ChatAccept |
| D/D | -1 | -1 | 未到达 | ProviderReject |

D/A 路径中，分值 70 的拒绝规则先被选择；由于最佳分值仍为 -1，分值 0 的通配规则覆盖预算为 10。Provider 与接收方各重复一次实现侧求值，随后出现 OTK 发放、ACT 签发、解密和应用请求接受。原始实现实验已记录错误允许至 ACT 签发和存储；这里的 Python 执行示意不是一次新的参考实现实验，也不是原生 Tamarin 轨迹。

正式原生结果已确认 D/A 的 `policy_budget_agreement` 和 `chat_requires_policy_allow` 为 falsified，`denied_chat_reachable`、`chat_accept_reachable` 及 `chat_requires_token_issue` 为 verified；正常允许可达，拒绝及反向排列不能完成通信。完整 16×4 结果表及各配置的真空成立说明见中文报告。本轮不修改论文，现有 ProVerif 归档继续保留。

早期良构性失败、递归搜索探测及中止运行均保留。`tests.log`、`toolchain_check.json` 是接收模块时已有的开发环境记录，不代表当前 WSL 工具链状态；当前辅助测试记录为 `audit/unit-tests.log`（7 项）。换行编码修正、阶段常量改名和扫描位置编码的依据见报告。全部交付文件的哈希见 `EVIDENCE_MANIFEST.json`；原生运行时的归档清单保留原样。
