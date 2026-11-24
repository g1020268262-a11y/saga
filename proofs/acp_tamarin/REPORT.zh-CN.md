# SAGA 接触策略 Tamarin 原生验证与模型审查

## 结论与证据入口

2026-11-24 在原 OTK 分析使用的 WSL `TamarinVerify` 中，使用 Tamarin 1.12.0、Maude 3.5.1 完成四个配置的原生解析与全部 64 项引理分析。两可执行文件的 SHA-256 与旧 OTK 归档 `run-20261025T033815645931Z/manifest.json` 完全相同。正式归档为 [`evidence/20261124T111257499246Z`](evidence/20261124T111257499246Z/summary.json)。四次解析、四次证明命令均返回 0，没有超时、未完成结果或良构性警告。`native_complete=true` 表示每个原生结果均与单独保存的验收预期一致，不表示每项安全性质均成立。

D/A 的原生反例显示：参考规则选择保持拒绝，但 Provider 和接收方均因未更新最佳分值而得到允许预算，进而发放 OTK、消费同一 OTK、签发 ACT、完成客户端解密并接受首次应用请求。原有令牌签发对应关系和解密对应关系仍然成立，策略许可对应关系不成立。

原生证明与联合轨迹保存在每个配置目录的 `proof.spthy`、`traces.json` 和 `traces.dot` 中。单独提取的反例见 [`review/da-attack.native.json`](evidence/20261124T111257499246Z/review/da-attack.native.json)，18 步核对见 [`review/DA_TRACE.zh-CN.md`](evidence/20261124T111257499246Z/review/DA_TRACE.zh-CN.md)。这些文件来自原生 JSON，不来自 Python 有限路径示意。

## 建模逻辑及源码对应

输入由 `cases.json` 固定为 AID `alice@example.com:agent` 及有序规则。生成器仅将受支持语法中的匹配规则、数值分值比较和预算分类编码为事实，不把最终允许或拒绝结果放入协议规则。`spec` 和 `observed` 字段仅出现在引理与验收预期中。测试特意改变这些字段，确认所有协议规则保持逐字一致。

| 对象 | 实现/旧工件依据 | 新模型表示与审查判断 |
|---|---|---|
| 规则匹配与分值 | `saga/common/contact_policy.py`：`aid_specificity`、`match`；`proofs/decision_bridge/bridge.py`：闭合语法求值 | Python 只计算匹配与分值；Tamarin 的每个扫描位置自行选择更新或跳过。固定 UID 通配规则分值 70，`*` 分值 0。 |
| 规则优先级缺陷 | `match` 初始化 `best_pattern=None`，仅更新 `budget` | 规范分支同时更新最佳分值与预算；实现分支保留 `best`，只更新预算。两端分别执行实现分支。 |
| Provider 许可和发放 | `saga/provider/provider.py` 的 `/access`：登记身份/证书查找、`match`、负数及零拒绝、首次计账和 OTK 移除 | `Registered` 与私有事实抽象认证；正预算通过 `Debit` 发放一枚线性 OTK，并记录预算 10 到余额 9。仅表示首次申请，不模拟重复领取或 MongoDB 并发。 |
| 接收方本地许可 | `saga/agent.py` 的 `match(self.contact_rulebook,i_aid)<0` | 接收方负预算拒绝、非负预算允许。与 Provider 的零预算处理分别编码；本次四个场景没有零预算执行。 |
| OTK 消费与 ACT | `agent.py` 的 `otks_dict` 查找/删除、`sotk.exchange(i_pac)`、HKDF、令牌生成与保存 | 接收方消耗独立线性 OTK，使用 DH、带原有域标签的哈希 KDF、理想对称加密，保存绑定当前 PAC 的令牌。 |
| 客户端解密及请求 | `agent.py` 的客户端令牌处理；原 OTK Tamarin 模型的解密规则 | 只有匹配 DH 密钥及 PAC 的密文才能生成 `ReadyForChat`；接收方匹配活动令牌与 PAC 后触发 `ChatAccept`。 |

登记和认证 TLS 是模型初始条件及端点标记的私有事实，不是一次新的 TLS/证书验证。模型只有一个发送方、一枚 OTK、一次初始化、一次应用请求。新鲜 `sid` 是模型执行关联标识，不是声称生产协议新增了该字段。参考求值先行是分析仪器化的顺序安排；其预算不作为 Provider 的许可门槛。

## 原生执行中的问题与修改

1. **证据换行编码。** 原运行器将 CRLF 工作区字节直接与 LF Git blob 比较，因此在调用 Tamarin 前停止。现先从固定提交读取 Git blob 并核对 `cases.json` 中的 blob ID，再只接受原始字节、统一 LF 或统一 CRLF 三种明确编码；原始 SHA-256 和匹配编码分别记录。任何内容变化仍失败。历史证据未重写。
2. **良构性警告。** 首次原生解析通过，但证明时 `--quit-on-warning` 因 `provider` 与 `Provider` 的大小写混淆告警退出。仅将求值阶段常量改为 `provider_eval`，没有关闭告警。
3. **递归搜索问题。** 通用 `Scan` 关系使反向搜索展开大量候选前缀。独立 BFS 可达性探测在 45 秒超时，未作为证明结果。加入固定后缀守卫后 D/A 的 16 项分析完成，但继续配置的搜索被中止并保留日志。最终改为位置状态 `Scan0`、`Scan1`、`Scan2`；自动验证全部完成。

位置编码的依据是：对于长度为 n 的固定匹配规则表，`Scan_i(sid,stage,best,current)` 对应旧模型 `Scan(sid,stage,suffix_i,best,current)`。初始状态相同；第 i 步仍使用同一分值比较事实，规范选择同时更新两项，实现选择只更新预算，跳过保持两项；扫描末端仍执行原完成规则。该映射逐步保持状态、事件和启用条件，仅消除通用后缀变量，未剔除固定输入的任何合法执行。它不把运行到某个预算写成限制或假设。

原始 16 项引理从 `evaluation_reachable` 到文件末尾逐字保留，测试核验通过；没有删除性质、弱化公式、加入预设结论的 restriction 或使用未证明引理。`UniqueSetup` 是原模板已有的单次初始化限制。两核 RTS 参数与旧 OTK 运行方式一致。运行器另外记录命令、耗时、版本、可执行文件哈希，并在超时时终止整个子进程组。

早期失败、探测及中止运行保留在 `audit/` 和前三个 `evidence/` 目录；它们均不是最终成功结果。总清单 `EVIDENCE_MANIFEST.json` 绑定所有交付文件，正式归档自带原生运行时生成的 `manifest.json`。

## 四配置全部结果

V = 原生 `verified`；F = 原生 `falsified`。对 exists-trace 引理，F 表示未发现满足查询的可达轨迹；对 all-traces 引理，F 表示存在反例。两者不能混读。

| 引理 | 类型 | D/A | reverse | A/A | D/D |
|---|---|---|---|---|---|
| evaluation_reachable | exists | V | V | V | V |
| spec_matches_reference | all | V | V | V | V |
| provider_matches_observation | all | V | V | V | V |
| receiver_matches_observation | all | V | V | V | V |
| policy_budget_agreement | all | F | V | V | V |
| provider_issue_requires_policy_allow | all | F | V | V | V |
| token_issue_requires_policy_allow | all | F | V | V | V |
| chat_requires_policy_allow | all | F | V | V | V |
| chat_requires_token_issue | all | V | V | V | V |
| chat_requires_decryption | all | V | V | V | V |
| provider_rejection_reachable | exists | F | V | F | V |
| receiver_evaluation_reachable | exists | V | F | V | F |
| provider_release_reachable | exists | V | F | V | F |
| token_issue_reachable | exists | V | F | V | F |
| chat_accept_reachable | exists | V | F | V | F |
| denied_chat_reachable | exists | V | F | F | F |

交换规则顺序时，规范预算仍为 -1，但实际匹配函数最后处理具体拒绝规则，预算也为 -1；Provider 拒绝，不进入接收方。D/D 同样在 Provider 停止。两配置的 `receiver_matches_observation` 是接收方事件不存在时的真空成立，不能表述为实际观察到了接收方拒绝。A/A 的令牌建立和请求接受可达，同时拒绝后成功查询不成立，提供正常通信对照。

## D/A 原生反例的因果检查

原生反例有 18 个协议规则节点，事实依赖给出如下完整顺序。

1. 初始化身份、公钥、两端 OTK 状态和固定规则比较事实。
2. 规范扫描选择分值 70、预算 -1 的具体规则；随后跳过分值 0 的通配规则，记录 `SpecDecision(...,bneg1,deny)`。
3. Provider 从初始最佳分值 -1 开始，先选择具体拒绝规则，但最佳分值仍为 -1；通配规则随后也满足 0 > -1，将预算覆盖为 10。
4. Provider 完成扫描，消耗一枚待发放 OTK，记录 `ProviderIssue` 以及 `ProviderDebit(...,b10,b9)`。该 OTK 经私有事实交给发送方。
5. 发送方使用自己的登记身份与 PAC 申请 ACT。接收方重新扫描同一有序规则，也先选择拒绝预算、再被通配规则覆盖，记录接收方预算 10。
6. 接收方消费与 Provider 发放事件中同一枚 OTK，以自身 OTK 私钥和发送方 PAC 派生密钥，签发并保存绑定 PAC 的 ACT。
7. 客户端以自身私钥和 OTK 公钥匹配同一 DH 密钥，触发 `TokenReceive`；随后发送应用消息。
8. 接收方以同一执行、身份、PAC 和活动 ACT 接受消息，触发 `ChatAccept`。

核对程序验证了两次实现侧覆盖、规范拒绝、10→9 扣减、发放与消费 OTK 一致，以及签发、解密和接受的执行标识/身份/密文一致。它只检查已经由 Tamarin 导出的原生图，不枚举或生成攻击路径。

## 与原有 ProVerif、匹配函数及实现实验的交叉审查

旧模型 `proofs/proverif/agent_communication_authz_chat_turepass.pv` 通过 `ScenarioSpecDeny`、`ScenarioImplAllow` 固定场景，其接收方读取实现侧许可表。归档 `proofs/evidence/authz-bridge-turepass-20260922T111657792091Z/verification-summary.txt` 记录 `ChatAccept ==> TokenIssue` 为 true、`not event(ChatAccept(...))` 为 false。新模型把规则遍历放入 Tamarin；`chat_requires_token_issue` 保持原对应查询的意图，`chat_accept_reachable` 是 exists-trace，成功时应为 verified，与 ProVerif 否定可达性查询的 false 极性相反。新增策略对应引理直接检查拒绝后的执行；两模型的协议过程和认证抽象不同，未宣称二者形式等价。

`audit_source.py` 读取当前匹配函数的原始 AST 定义，只排除包导入及日志依赖，调用真实 `fnmatch` 和未改动函数体，四组返回值分别为 10、-1、10、-1，与固定历史观察一致。该结果单独标记为方法级执行，不计入 Tamarin 的 64 项结果。

历史消费者实验 `proofs/consumer_validation/evidence/20260926T070021921746Z-d64c8064` 的 A/A、D/D、D/A 断言均通过。D/A 与 A/A 的 Provider 返回 200、计账余额为 9，并签发、存储且解密 ACT；D/D 返回 403，后续接收方不执行。实验在 `receive_conversation` 前截断，因此只支持到 ACT 建立，不是一次应用消息接受或后端调用实验。新模型的 `ChatAccept` 是符号轨迹对这一后续阶段的分析，不能改写历史实验边界。reverse 的依据是实际匹配函数观察及新原生拒绝轨迹，没有声称新增了 reverse 消费者实验。

审查结论是：在固定输入、认证通道及理想密码学前提下，新模型把既有场景决策推进为显式的规则执行分析，并重现了与旧模型一致的授权后果。它不证明完整 `fnmatch`、任意动态策略、无限参与方或 Python 到 Tamarin 的自动精化，也不组合 OTK 转交及 ACT 并发问题。

## 复核命令和改动边界

从仓库根目录 PowerShell 执行：

```powershell
wsl.exe -d TamarinVerify --exec sh -lc 'cd /mnt/d/Users/10202/Desktop/saga; python3 -B proofs/acp_tamarin/run_model.py --repo-root . --timeout 180'
wsl.exe -d TamarinVerify --exec sh -lc 'cd /mnt/d/Users/10202/Desktop/saga; python3 -B proofs/acp_tamarin/inspect_native_trace.py proofs/acp_tamarin/evidence/20261124T111257499246Z'
wsl.exe -d TamarinVerify --exec sh -lc 'cd /mnt/d/Users/10202/Desktop/saga; python3 -B proofs/acp_tamarin/audit_source.py'
```

生成器及证据校验另有 7 项 Python 单元测试，均通过；它们是辅助检查，不作为符号证明。`audit/protected-files-before.json` 保存本轮前已有文件的哈希；提交前逐项复核其未变。仅新增/修改 `proofs/acp_tamarin/`，不运行旧验证器，不修改原实现、旧 ProVerif、OTK Tamarin、TLA+、历史证据或论文。既有论文工作区改动和英文目录保留在提交之外。
