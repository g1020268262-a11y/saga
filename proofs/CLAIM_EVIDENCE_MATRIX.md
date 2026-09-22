# SAGA Claim-Evidence Matrix

## Overview

整理日期：2026-09-19。核对时仓库提交：`ae0025c11b2c3bc00d946bc5c90b455aeb706e9c`。

证据同步：2026-09-20，补充既有独立运行归档 `authz-turepass-20260919T090826295518Z`。本次仅同步研究状态，保留历史 `turetrace` 及其来源限制，不重跑实验。

证据同步：2026-09-22，基于 `6192c74e322692268b78c6f364eafb644da182e0`，纳入已完成的 bridge v1.1.1 及 `authz-bridge-turepass-20260922T111657792091Z`。本轮仅更新本矩阵并只读核对归档，不运行 matcher、bridge、测试或 ProVerif，不修改论文。下文将历史诊断、历史后果模型和当前 bridge-derived 后果证据分别标识。

**Authorization correctness is not guaranteed by cryptographic authentication alone.**

本研究关注 **policy semantics + policy implementation + protocol consequence**：用户策略的预期含义是否被 matcher 正确实现，以及授权决定的偏差能否影响凭证签发和 Agent 通信授权。现有成果包括已确认的 matcher 实现级授权绕过、授权证明覆盖缺口、抽象授权分歧的通信后果模型，以及授权门控位置控制实验。它们不构成对 SAGA 密码学原语的破解结论。

本文件组织已有材料，不产生新实验或扩大安全结论。[AUDIT_STATUS.md](AUDIT_STATUS.md) 保留历史阶段状态；当前 bridge 完成情况以下述版本化归档为依据，不能让早期“待完成”表述覆盖后来的结果。**历史 matcher 实现级偏差已有直接调用证据；记录场景的决策计算、来源绑定及模型场景重构已完成，通用实现到模型的 refinement 仍未建立。**

| Claim | 已完成工作 | 核心证据 | 当前支持的结论 | 不能自动扩展到的结论 |
|---|---|---|---|---|
| 1 | Authorization proof coverage gap | Stage 1 模型、查询摘要、重建轨迹 | 原认证与 token 保密结果不建立所需的授权可靠性 | 密码协议被破解，或实现层消息越权已复现 |
| 2 | Matcher implementation-level vulnerability | `test_matcher_bug.py`；原实现直接调用的 `policy-matcher-sanity.json` | 预期 DENY、实现 ALLOW；规则顺序影响授权决定 | Provider、token 和消息处理完整运行链已复现 |
| 3 | Historical and bridge-derived consequence modeling | 历史 `turetrace`、`authz-turepass-20260919T090826295518Z`；当前 `authz-bridge-turepass-20260922T111657792091Z` | 历史预置场景与当前 bridge 重构场景的各自归档支持 `ChatAccept` 可达及接受到签发的 correspondence；新归档不反向升级旧来源 | 独立 `TokenIssue` 可达性查询、ProVerif 执行 Python matcher、实现精化或服务执行证明 |
| 4 | Authorization gate placement experiments | 三个独立门控模型及其查询摘要 | Provider 与 Receiver 门控在不同阶段阻断后续事件 | 对生产实现门控机制或实际部署安全性的完整证明 |
| Mapping A--F（Claims 2--3 的当前连接） | Independent decision derivation, provenance binding, scenario reconstruction and fresh verification | bridge v1.1.1 代码、decision pair、派生模型、新运行 manifest 与保存的 25-test 日志 | 记录场景的 decision values 经独立有限求值与来源绑定机械传递至执行模型的场景区域 | 角色抽象的正确性证明、任意策略正确性、实现 refinement、同一具体服务会话 |

**事件口径。** 本系列模型中，`PeerA = R` 是 token 签发方和聊天接收方，`PeerB = I` 是 token 接收方和聊天发送方。`Accept` 表示 B 收到并验证 token；`ChatAccept` 才表示 A 接受模型中的一条聊天消息。论文的 `ProviderGrant`、`TokenIssued`、`MessageAccepted` 与模型的 `ProviderRelease`、`TokenIssue`、`ChatAccept` 可作概念对照，但该对照本身不是实现到模型的语义映射证明。`turepass` 中的 `SpecIntendedDeny(B,A)` 参数顺序与 `TokenIssue(A,B,t)` 相反，使用时不能交换授权方向。

**历史证据来源核对（2026-09-19/20）。** 当时只读核对了以下归档；所列模型文件哈希与相应 manifest 的输入哈希一致，三个早期 manifest 所列的 12、6、8 个证据文件分别匹配记录。原 matcher 当时的 SHA-256 与 sanity JSON 一致。这些是历史核对记录，不是对当前上游实现状态的结论。2026-09-22 的 bridge provenance 核对见 Mapping A--F；历史 replay 不以当前源码相同为必要条件。

| 归档 | 运行时基线 | 可核对材料 |
|---|---|---|
| [Stage 1](evidence/authz-stage1-20260916T123834944479Z/manifest.json) | `7372111bea150e32cee390a616849316d2780bfc` | 命令、ProVerif 2.05、输入哈希、原始输出、结果与检查记录 |
| [历史共享门控](evidence/authz-chat-guarded-20260917T080131985337Z/manifest.json) | `78e06379ec01f49d7b07067402ee60585dfe36c4` | 两个控制模型及其结果、输入与输出哈希 |
| [独立门控](evidence/authz-chat-gates-20260918T023621017067Z/manifest.json) | `2685d956b2f98fb1c4634dd6ec817fe4d9c448b8` | 三个控制模型及其结果、输入与输出哈希 |
| [`turetrace`](evidence/turetrace) | 本次快照中可读取；没有对应的独立运行 manifest | 已保存轨迹及 `ChatAccept` 可达性结果；不能用本次仓库快照补造其原始运行元数据 |
| [authz-turepass-20260919T090826295518Z](evidence/authz-turepass-20260919T090826295518Z/manifest.json) | `f8bf8273bc41c82c2fb117f1be395877a55c6e13` | 独立运行的命令、ProVerif 2.05、输入哈希、stdout/stderr、查询摘要与退出码；不是历史 `turetrace` 的追溯来源证明 |
| [bridge v1 development runs](decision_bridge/evidence/) | 各自 manifest 记录的开发状态 | 保留 fragment-only 产物，不改写为已执行完整模型 |
| [bridge v1.1](evidence/authz-bridge-turepass-20260922T071843950813Z/manifest.json) | `2db47d8f3460aa9f6652a83714afe98bc1eadaa4` | 校验已有场景接口并执行派生完整模型；不是 v1.1.1 的场景重构实现 |
| [bridge v1.1.1](evidence/authz-bridge-turepass-20260922T111657792091Z/manifest.json) | `830ba37faae41788b10f3a9cf7bfc68426d52d26`（干净运行代码提交） | 重构场景区域后的新 ProVerif 2.05 执行，两个既有查询及 25 项测试；归档提交为 `6192c74e322692268b78c6f364eafb644da182e0` |

# Claim 1

## Claim

**Authentication and confidentiality guarantees do not imply authorization soundness.**

在本研究语境中，该主张指原通信模型的认证和 token 保密查询不覆盖用户策略与授权行为之间的一致性；不是对所有协议或所有授权定义给出无条件的不可能性定理。

## Evidence

| 文件／模型 | 已保存结果及用途 |
|---|---|
| [AUTHORIZATION_DIAGNOSTIC.zh-CN.md](AUTHORIZATION_DIAGNOSTIC.zh-CN.md) | Stage 1 的模型边界、事件定义和运行说明 |
| [agent_communication.pv](proverif/agent_communication.pv) | 原通信模型；认证与 token 保密查询的基线 |
| [agent_communication_authz.pv](proverif/agent_communication_authz.pv) | 保留基线协议，加入策略事件和 token 接收阶段授权 correspondence |
| [verification-summary.txt](evidence/authz-stage1-20260916T123834944479Z/verification-summary.txt) | 原通信模型三条认证及 token 保密结果为 `true`；扩展保留全部 11 条基线结果，新增授权 correspondence 为 `false` |
| [authorization-trace.txt](evidence/authz-stage1-20260916T123834944479Z/authorization-trace.txt) | 保存了 `PolicyDeny`、`TokenIssue`、`Accept` 和成功重建轨迹的记录 |
| [原始扩展输出](evidence/authz-stage1-20260916T123834944479Z/agent_communication_authz.stdout.txt)、[manifest](evidence/authz-stage1-20260916T123834944479Z/manifest.json) | 结果来源、版本、输入哈希与执行记录 |

关键已保存结果为：

| 查询含义 | 结果 |
|---|---|
| `EndAgentAuthB ==> EndAgentAuthA` | `true` |
| `EndAuthA ==> EndProviderAuthA` | `true` |
| `EndAuthB ==> EndProviderAuthB` | `true` |
| `not attacker_p6(token[])` | `true` |
| `Accept(issuer,recipient,tok) ==> PolicyAllow(issuer,recipient)` | `false` |

## What is proven

在保留原通信行为的诊断扩展中，既有认证和保密结果仍成立，但新增的 token 接收授权对应关系失败。这证明现有性质集合没有建立该授权义务，支持 **verification coverage gap** 的结论。

诊断的机制必须与结论一起说明：`PolicyDeny` 是预置事件，不是阻断执行的 guard；`PolicyAllow` 仅声明而不发生。因此原协议到达 `Accept` 即可违反新增查询。该实验指出缺少被模型约束的授权依据，而非证明密码学验证失效。

## What is not proven

- Stage 1 没有执行或形式化真实 matcher，因此不是 Claim 2 的实现级证明。
- `Accept` 只表示 token 接收与验证，不表示接收方接受业务消息。
- 模型内参与方收到 token 不等于外部符号攻击者获得 token；它与 token 保密结果并不矛盾。
- 本阶段不证明运行中服务的端到端越权，也不证明密码学原语或原认证查询被攻破。

# Claim 2

## Claim

**The contact policy matcher can produce implementation decisions inconsistent with intended policy semantics.**

## Evidence

| 文件 | 证据角色及结果 |
|---|---|
| [test_matcher_bug.py](test_matcher_bug.py) | 自含的缺陷／对照 matcher 示例，使用 Mallory 场景；对应 [AUDIT_STATUS.md](AUDIT_STATUS.md) 已确认的复现结论 |
| [policy-matcher-sanity.py](evidence/authz-stage1-20260916T123834944479Z/policy-matcher-sanity.py) | 直接导入原项目 `aid_specificity`、`check_rulebook`、`match` 的已归档测试脚本 |
| [policy-matcher-sanity.json](evidence/authz-stage1-20260916T123834944479Z/policy-matcher-sanity.json) | 原实现直接调用的保存结果：expected `-1`，actual `10`；反转规则顺序返回 `-1` |
| [saga/common/contact_policy.py](../saga/common/contact_policy.py) | `match()` 文档规定最具体规则优先；循环更新预算但不更新 `best_pattern` |

当前状态记录中的具体反例为：

| 顺序 | Rule pattern | Budget |
|---|---|---|
| 1 | `mallory@example.com:*` | `-1` |
| 2 | `*` | `10` |

对于匹配具体规则的 Mallory AID：

```text
Expected: DENY  (budget = -1; specific deny wins)
Actual:   ALLOW (budget = 10; later wildcard allow overrides)

Implementation decision != Specification decision
```

**两份 matcher 材料的来源不能混写。** `test_matcher_bug.py` 定义了自己的 `buggy_match()` 和 `fixed_match()`，并使用简化 specificity 评分；它没有直接导入生产 matcher。因此，它是自含的逻辑复现与对照材料，不能单独标为“原实现直接调用日志”，也不构成一般性修复正确性证明。

原实现直接调用的保存证据是 sanity JSON。该记录采用 `alice@example.com:agent` 和 `alice@example.com:*`，而不是 Mallory 字符串；其规则结构与上述反例相同。记录显示：

| 保存字段 | 值 |
|---|---|
| `rulebook_valid` | `true` |
| `specificities` | `[70, 0]` |
| `expected_under_documented_most_specific_semantics` | `-1` |
| `actual_specific_deny_then_wildcard_allow` | `10` |
| `actual_wildcard_allow_then_specific_deny` | `-1` |
| `source` | `saga/common/contact_policy.py` |
| `source_sha256` | `2e37f59651acc31ed9fad8436462faabcb49c52ab3032eccd1529cd72870aa97` |

该 source hash 绑定指定历史源码提交 `7372111bea150e32cee390a616849316d2780bfc` 的工作区字节。当前 bridge 通过历史 Git blob 的明确换行编码核对它，不要求当前 checkout 相同。这里引用既有输出，本轮没有执行这两个测试脚本；bridge 读取该观察也不构成一次新的 production matcher execution。

## Security impact

**Order-dependent authorization bypass confirmed — at the matcher implementation/function level.**

本应由更具体规则决定的拒绝，被后出现的通配允许覆盖。`best_pattern` 保持 `None`，比较基准始终是其 specificity 值 `-1`；对正常处理的合法匹配规则，后续预算会继续覆盖前值。改变规则列表顺序可以改变实际授权决定，而预期最具体规则语义不变。

“Authorization bypass”在本 Claim 中指已确认的策略决策绕过：**Specification decision = DENY；Implementation decision = ALLOW**。它不以密码学攻击为前提，也不意味着测试已经穿过 Provider 和 Agent 的所有运行时检查。

## Scope

这是 **implementation-level vulnerability**。真实 matcher 的函数级偏差有直接调用证据，不应再退回仅为推测的状态。具体运行服务中的 `ProviderGrant`、`TokenIssued`、`MessageAccepted` 不在该 JSON 的实验范围内。规范依据是 matcher 的文档和 specificity 规则；不能仅凭示例脚本中的注释把它升级为对原论文全部策略语义的验证。

# Claim 3

## Claim

**Authorization decision divergence can propagate into agent communication authorization.**

历史后果模型由预置授权分歧驱动；当前 bridge v1.1.1 另有从已绑定决定对重构场景并执行模型的归档，两类证据分别支持各自的符号后果。记录场景的机械化证据传递已完成，但具体策略求值到符号协议角色的对应仍是分析抽象，未完成 refinement。

## Evidence

| 文件 | 当前可核对内容 |
|---|---|
| [agent_communication_authz_chat_turepass.pv](proverif/agent_communication_authz_chat_turepass.pv) | 预置规范拒绝／实现允许场景；包含材料发布、token 签发和聊天消息接受 |
| [turetrace](evidence/turetrace) | 已保存的重建轨迹，包含 `SpecIntendedDeny`、`ProviderRelease`、`TokenIssue` 和 `ChatAccept` |
| [AUDIT_STATUS.md](AUDIT_STATUS.md) | 历史 authorization consequence model 定位；后续独立归档及 bridge 完成情况见本矩阵，不把历史待办等同于当前状态 |
| [独立运行 manifest](evidence/authz-turepass-20260919T090826295518Z/manifest.json) | 记录未修改模型的独立执行、ProVerif 2.05、输入哈希与退出码 `0` |
| [独立运行 stdout](evidence/authz-turepass-20260919T090826295518Z/agent_communication_authz_chat_turepass.stdout.txt)、[stderr](evidence/authz-turepass-20260919T090826295518Z/agent_communication_authz_chat_turepass.stderr.txt) | 完整查询结果和符号可达性 witness；stderr 为空 |
| [独立运行 verification summary](evidence/authz-turepass-20260919T090826295518Z/verification-summary.txt)、[版本记录](evidence/authz-turepass-20260919T090826295518Z/proverif-version.txt) | 区分已声明查询、最终结果与 witness 中的事件观察 |

### Established by the independent evidence package

以下结果来自 `authz-turepass-20260919T090826295518Z` 的原始输出，不是对历史 `turetrace` 补写结果：

| 查询／性质 | 已归档结果 | 支持的结论 |
|---|---|---|
| `ChatAccept` reachability | `RESULT not event(ChatAccept(receiver,sender_1,tok,msg)) is false.`，并重建 witness | 在明确授权分歧假设和模型抽象下，消息接受可达 |
| `ChatAccept ==> TokenIssue` | `RESULT event(ChatAccept(receiver,sender_1,tok,msg)) ==> event(TokenIssue(receiver,sender_1,tok)) is true.` | 接受事件对应此前相同接收方、发送方及 token 的签发事件；不等于策略允许 |

**Boundary:**

- **No independent TokenIssue reachability query.** witness 中观察到 `TokenIssue`，但模型没有独立的 `TokenIssue` 可达性查询，不能报告不存在的查询结果。
- **No matcher execution inside ProVerif.** 模型预置授权分歧，不执行 Python matcher 或具体 rulebook 求值。
- **No implementation refinement proof.** 独立运行归档补齐的是形式后果模型的运行来源，不是实现到形式模型的语义精化证明。

为避免把分析名称误写成已有模型事件，采用以下对照：

| 分析层含义 | 历史 turepass 模型中的实际表示 | 历史证据语义 |
|---|---|---|
| `SpecDecision: DENY` | `ScenarioSpecDeny(BuggyPolicy,aid_B)` 表项；`SpecIntendedDeny(aid_B,aid_A)` 事件 | 规范侧拒绝是预置场景，不是模型计算具体 rulebook 的结果 |
| `ImplDecision: ALLOW` | `ScenarioImplAllow(BuggyPolicy,aid_B)` 表项 | 实现侧允许是 matcher 偏差的抽象，供 Provider 和 Receiver 读取 |
| Provider material release | `ProviderRelease(aid_A,aid_B)` | 模型中的访问材料发布 |
| Token issuance | `TokenIssue(aid_A,aid_B,tok)` | A 为 B 签发的 wire token；聊天模型这里使用加密 token 表示 |
| Message acceptance | `ChatAccept(aid_A,aid_B,tok,msg)` | A 通过该模型的 token／发送方绑定检查后接受一条消息 |

`SpecDecision` 和 `ImplDecision` 是上表的分析标签，不是当前文件中声明的事件名；`ScenarioSpecDeny` 和 `ScenarioImplAllow` 是 **table facts**，也不能误写为模型内计算得到的 policy events。

### Historical Implementation-to-Model Mapping（叙事补充，2026-09-20）

本小节保留当时的人工解释与论文状态，不作为当前 bridge 能力描述。本轮未修改论文；当前决定值传递机制见下文 Mapping A--F。

新增说明见 [第六章](../paper/sections/06_formalization.tex) 的 `Implementation-to-Model Mapping` 小节、对照表和示意图。它连接 Claims 2--3 的证据解释，不增加独立安全贡献、实验或查询。

| Claim | Evidence | Boundary |
|---|---|---|
| Matcher observation can be abstracted into formal authorization divergence | [真实调用脚本](evidence/authz-stage1-20260916T123834944479Z/policy-matcher-sanity.py)、[JSON](evidence/authz-stage1-20260916T123834944479Z/policy-matcher-sanity.json)、第六章映射说明，以及 `turepass` 的表项初始化 | Manual abstraction for the recorded case; no automatic translation, mapping validation, or refinement proof |

具体映射以真实调用归档为依据：`alice@example.com:agent` 对应 specific-deny/general-allow 规则，specificity 为 `70` 和 `0`，规范预期 budget 为 `-1`，实际返回 `10`；反转顺序返回 `-1`。[test_matcher_bug.py](test_matcher_bug.py) 是采用 Mallory 身份和简化 specificity 的独立示例，不是该真实调用的执行脚本。

第六章按第三章的正 budget 许可约定，将该记录解释为 `(D_spec(P_R,I), D_impl(P_R,I)) = (Deny, Allow)`。人工抽象将发起方表示为 `aid_B`，接收方固定为 `aid_A`，用 `BuggyPolicy` 命名场景，并以 `ScenarioSpecDeny(BuggyPolicy,aid_B)` 和 `ScenarioImplAllow(BuggyPolicy,aid_B)` 表示决定对。该场景标识不是具体 rulebook 编码；模型不保存规则模式、顺序、specificity 计算或 budget 数值。

授权分歧由两个表项共同表示，模型没有 `SpecDivergence` 事件。`ChatAccept` 属于形式后果证据，不是 matcher JSON 的观察。Provider 与 Receiver 读取同一个实现侧允许表项仍是模型假设；函数级记录没有验证这些消费者或 `ProviderReleased` handoff。新增文字和图使人工映射显式化，**没有完成自动或手工精化证明，也没有消除现有语义映射限制**。历史 `turetrace` 和独立 `authz-turepass-20260919T090826295518Z` 归档及其查询范围均保持不变。

保存轨迹支持的抽象事件关系为：

```text
SpecDecision: DENY       +       ImplDecision: ALLOW
        (fixed scenario assumptions)
                         ↓
                  ProviderRelease
                         ↓
                     TokenIssue
                         ↓
                      ChatAccept
```

可定位证据：`turetrace` 第 14、16 行记录场景表项；第 122 行记录规范拒绝事件；第 128 行记录 Provider 发布；第 168 行记录被后续接受的 token 的签发；第 208 行记录 `ChatAccept`。这些是证据文件行号；轨迹中的 `{...}` 是 ProVerif 进程位置编号。文件结尾保存：

```text
A trace has been found.
RESULT not event(ChatAccept(receiver,sender_1,tok,msg)) is false.
```

这里的 `false` 表示“消息接受不可达”不成立，即消息接受可达。它不是认证 correspondence 失败结果。

## Scope

**Formal consequence model. Not full running-service exploit.**

`ScenarioImplAllow` 是 matcher bug 的形式化抽象，并未调用 Python `match()`，也未计算模式匹配、specificity 或规则顺序。已保存轨迹证明的是：在该固定分歧场景及模型假设下，规范拒绝可与 token 签发、消息接受共同出现。它不是整个运行中实现的自动执行轨迹。

下列边界必须随 Claim 保留：

- `tls_chat` 是私有信道，用来抽象经过认证且保密的传输，不是 TLS 实现证明。
- `ProviderReleased` 是连接 Provider 放行与接收方处理的控制流程抽象，尚未建立其与生产实现的完整对应。
- 模型中新生成 token 不等于已经证明会话隔离或 injective agreement。保存轨迹包含多份复制进程，不能改写为已证明的严格单会话执行。
- 历史 `turetrace` 只保存消息接受可达性结果，未保存 `ChatAccept ==> TokenIssue` 的最终结果；单独观察轨迹不能证明 correspondence。独立归档 `authz-turepass-20260919T090826295518Z` 已保存该查询为 `true` 的结果，其范围限于该模型。
- 不能把 Claim 1 的认证与保密结果直接继承为此模型的新验证结果；`turepass` 没有查询原模型的完整性质集合。
- 历史 `turetrace` 仍缺少对应的独立运行命令、版本、完整 stdout/stderr 和输入哈希 manifest。新增归档提供另一独立运行的完整来源，不能反向作为历史文件的运行元数据。

因此，历史后果模型的可达性和 correspondence 有独立来源；当前记录场景的 bridge 传递进一步由以下归档支持。剩余角色对应和实现 refinement 义务不应与已经完成的有限证据传递混写。

### Current Implementation-to-Model Evidence Transfer: Mapping A--F（2026-09-22）

下表中的 **B111** 指 [authz-bridge-turepass-20260922T111657792091Z](evidence/authz-bridge-turepass-20260922T111657792091Z/)。这是已归档运行的整理，不是本轮重新执行。

| Claim | Evidence | Established for the recorded case | Boundary |
|---|---|---|---|
| A — Historical production observation | [Stage 1 sanity JSON](evidence/authz-stage1-20260916T123834944479Z/policy-matcher-sanity.json)、其调用脚本及历史源码提交 | 对 Alice 的指定 ordered rulebook，实际返回 budget `10`；反序观察为 `-1` | 生产执行证据仍来自原归档；bridge 不是新的 production execution，不包含服务流程 |
| B — Independent finite specification evaluation | [bridge.py](decision_bridge/bridge.py) 的 `evaluate()`；[B111 decision pair](evidence/authz-bridge-turepass-20260922T111657792091Z/bridge-result.json)；[测试代码](decision_bridge/test_bridge.py)和保存日志 | 独立匹配和 specificity 计算，选择唯一最高分 `r0`（70），budget `-1`，`SpecDecision = Deny`；不 import production `match()`，不使用归档 expected/specificities 作为规范答案 | 有限输入域内的可执行 evaluator 及测试，不是 evaluator 的形式正确性证明、完整 fnmatch 或 arbitrary policy correctness |
| C — Same-evaluation decision pair | `load_observation()`、`verify_historical_source()`、`build()`；B111 decision pair 和 manifest | 绑定相同有序规则、target identity、policy hash、源码 revision 和 observation provenance；`Spec = Deny`、`ImplObserved = Allow`、`divergence = true` | `target` 是被匹配的 initiator；`aid_A`、`BuggyPolicy` 及 policy label 是 symbolic/scenario-local，不是历史观察记录的 deployed receiver 或 policy owner；不是同一具体服务会话 |
| D — Bridge-derived scenario reconstruction | [generate_model.py](decision_bridge/generate_model.py)、`generated_scenario_block_sha256`、[派生模型](evidence/authz-bridge-turepass-20260922T111657792091Z/agent_communication_authz_chat_bridge.pv)、保存测试 | 重新校验决定对，通过 `prefix + generated_block + suffix` 重构执行模型场景；v1.1 仅校验已有接口，v1.1.1 从已检查决定对重构区域 | 自动化场景适配与检查不是 implementation-to-model refinement；ProVerif 内仍不计算 Python matcher |
| E — Fresh derived-model verification | [run-start](evidence/authz-bridge-turepass-20260922T111657792091Z/run-start.json)、[manifest](evidence/authz-bridge-turepass-20260922T111657792091Z/manifest.json)、[stdout](evidence/authz-bridge-turepass-20260922T111657792091Z/proverif-stdout.txt)、[summary](evidence/authz-bridge-turepass-20260922T111657792091Z/verification-summary.txt) | 新 ProVerif 2.05 执行，退出码 `0`；`ChatAccept` reachable = `true`；`ChatAccept ==> TokenIssue` = `true` | standalone `TokenIssue` reachability query = **absent**；不是 production service exploit，不能将 witness 内签发事件报告为独立查询 |
| F — Frozen transformation integrity | template SHA、`validate_structure()`、mutation tests、[保存的 25-test 日志](evidence/authz-bridge-turepass-20260922T111657792091Z/tests-stderr.txt) | 除 provenance header、重构 scenario region 和三处批准的 comment normalization，冻结协议内容和 queries；归档 tests exit `0`、`tracked_files_unchanged = true` | artifact-level transformation integrity，不是任意两个模型的语义等价定理或 Python refinement |

**有限语义。** 支持 `*`、小写 ASCII literal AID 和 literal UID 后接 `:*`；按数值 specificity 的唯一最高匹配选择预算。预算分为 Negative/Zero/Positive，仅 Positive 表示许可，无匹配取 Zero。并列最高分或域外 pattern 为 Unsupported，畸形输入为 Invalid，不悄悄解释成 Deny。这不覆盖完整 Python/fnmatch、动态策略、配额或 token 生命周期，也不改变 receiver 零预算 precheck 的已有边界。

**当前决定值传递与剩余角色抽象。** Decision values for the recorded case are now mechanically transferred through an independently evaluated, provenance-bound bridge into the generated scenario region. The bridge removes the hand-entered decision labels for the recorded case by independently deriving the specification-side decision and binding the implementation-side decision to an archived matcher execution. It then reconstructs the authorization-divergence scenario region of the executed ProVerif model.

This is a machine-checked evidence transfer for the recorded evaluation, not a general refinement proof between the Python implementation and the symbolic protocol model. 此处 machine-checked 指脚本进行求值、绑定、重算和结构检查，不指对这些脚本本身完成定理证明。

The mapping from the concrete policy evaluation to symbolic protocol roles (`aid_B`, `aid_A`, `BuggyPolicy`) remains an analysis abstraction and is not a proved implementation-to-model refinement. Provider/Receiver 共享该决定与 `ProviderReleased` handoff 仍是协议模型抽象。`ScenarioSpecDeny` / `ScenarioImplAllow` 仍为 table facts；不是新增的 matcher execution events。

**来源核对（只读）。** B111 manifest 的 11 项 artifact 哈希与当前文件及下述 evidence commit 中的 Git blob 一致；所列脚本哈希、原始 observation、source model、实际生成场景字节均已核对。policy hash 和 evaluation fingerprint 按记录的 canonical JSON 格式复核。历史源码通过指定 Git blob 和统一 CRLF 编码匹配归档工作区字节哈希，二者原始哈希并不相等。当前源码匹配仅为记录信息，不是 replay 的前提。

| Provenance item | Verified value / source |
|---|---|
| Bridge code / clean run commit | `830ba37faae41788b10f3a9cf7bfc68426d52d26` — manifest `git_commit`，`git_status = clean` 指创建新归档前 |
| Evidence commit | `6192c74e322692268b78c6f364eafb644da182e0` — 由 Git 历史及归档文件字节核对；不是 manifest 的运行提交字段 |
| Historical matcher source commit | `7372111bea150e32cee390a616849316d2780bfc` |
| Observation SHA-256 | `b1148bdb2e2b450ca318b28266deb2dcd30d74af1ccec405ff855bf43c7fc56d` |
| Policy hash | `23cfaf931100d7e47702e962a38b99bd8c837e0b15624438658b9b8f4ca5138c` |
| Evaluation fingerprint | `40888f0bb40808888091783a8f63adb9fb9a6615a04a13efdd9d31c4a8d010a5` |
| Bridge-result SHA-256 | `24b7591099425a109bb83b69cf0bf797166014dda9493d1a1c8db621352d3f3f` |
| Source model / template SHA-256 | `e6ffbd5acebd3aa1f05ea7942c4f7eb23d4469357c7a01fea082de2b2e8ab121` |
| Generated scenario block SHA-256 | `69d5b0d1752ec59c90e9ed455126222430b12b12d67c23bf407e42fea5b56f42` |
| Generated model SHA-256 | `20113b40cc0974a5de514a72b4630aa149bc6f2b79cdca5574d6de7c795b1329` |

两条实际 `RESULT` 与 summary/manifest 一致：不可达断言为 `false` 表示 `ChatAccept` 可达，对应性为 `true`。旧 turepass 与 B111 的 stdout 哈希相同；冻结语义下的输出一致本身既不能证明也不能否定新执行，新执行的来源应结合独立 run-start、命令、代码提交、派生输入哈希、退出码与 manifest，而非仅凭 stdout 内容区分。哈希绑定不是归档真实性签名，也不是独立第三方执行认证。

**仍不支持：** Python matcher refinement、full implementation formal verification、complete Python semantics、complete fnmatch semantics、all-policy correctness、deployed service exploitation、concrete deployed receiver ownership、arbitrary adversarial session guarantees、full session isolation、current upstream vulnerability status，以及 turepass/bridge run 中独立 `TokenIssue` reachability query 的结论。Stage 1 的认证与保密查询也不因该 bridge 自动转移为所有后续模型的已验证性质。

# Claim 4

## Claim

**Authorization enforcement placement affects security outcomes.**

## Evidence

当前独立门控实验的说明见 [AUTHORIZATION_CHAT_GATES.zh-CN.md](AUTHORIZATION_CHAT_GATES.zh-CN.md)，结果见 [verification-summary.txt](evidence/authz-chat-gates-20260918T023621017067Z/verification-summary.txt)，运行来源见 [manifest.json](evidence/authz-chat-gates-20260918T023621017067Z/manifest.json)。

| 模型／场景 | `ProviderRelease` 可达 | `TokenIssue` 可达 | `ChatAccept` 可达 | 定位到的行为 |
|---|---|---|---|---|
| [agent_communication_authz_chat_p_allow_r_allow.pv](proverif/agent_communication_authz_chat_p_allow_r_allow.pv) | 是 | 是 | 是 | 双允许控制路径可执行到消息接受 |
| [agent_communication_authz_chat_p_allow_r_deny.pv](proverif/agent_communication_authz_chat_p_allow_r_deny.pv) | 是 | 否 | 否 | Provider 已发布材料，Receiver gate 在签发前阻断 |
| [agent_communication_authz_chat_p_deny_r_allow.pv](proverif/agent_communication_authz_chat_p_deny_r_allow.pv) | 否 | 否 | 否 | Provider gate 阻断材料发布及后续事件 |

双允许场景的 `ChatAccept ==> TokenIssue` 和 `ChatAccept ==> ChatSend` 均为 `true`，同时 `ChatAccept` 可达，因而不是空真。两个单侧拒绝场景的对应关系也为 `true`，但 `ChatAccept` 不可达；这些真值是空真的，不能单独作为更强消息认证结论。

这些结果表明：接收方阻断可以阻止模型中的 token 签发和消息接受，却不能撤销已经发生的 Provider 发布。Provider 阻断则在更早边界停止后续流程。结论依赖独立门控以及 `ProviderReleased` 传递抽象，不能直接称为生产协议中已证明存在的机制。

**历史共享门控对照也已完成，应保留但不能与独立门控混用。** 说明见 [AUTHORIZATION_CHAT_GUARDED.zh-CN.md](AUTHORIZATION_CHAT_GUARDED.zh-CN.md)，结果见 [历史摘要](evidence/authz-chat-guarded-20260917T080131985337Z/verification-summary.txt)，来源见 [历史 manifest](evidence/authz-chat-guarded-20260917T080131985337Z/manifest.json)。

| 历史模型 | 结果 | 对当前研究的作用 |
|---|---|---|
| [agent_communication_authz_chat_allow.pv](proverif/agent_communication_authz_chat_allow.pv) | `ChatAccept` 可达；与 `PolicyAllow`、`MatcherAllow`、`TokenIssue`、`ChatSend` 的对应关系为 `true` | 检查消息事件与凭证绑定的允许控制路径 |
| [agent_communication_authz_chat_deny.pv](proverif/agent_communication_authz_chat_deny.pv) | `ChatAccept` 不可达；上述对应关系为空真 | 检查共享授权状态缺失时的拒绝控制路径 |

两者共用 `Authorized(A,B)`，不能分别定位两道 gate 的作用；历史 `MatcherAllow` 名称表示预置场景事件，不代表执行了真实 matcher。三个独立门控模型正是对这一控制实验边界的细化。

所有这些控制模型均不计算具体 contact policy 的 most-specific 语义，也不覆盖 token 到期、配额递减、撤销、实际 TLS 或业务处理副作用。它们支持门控位置和阻断边界的比较，不是生产实现已修复或全局安全的结论。

# Overall Research Argument

```text
Policy specification
        ↓
Matcher implementation
        ↓
Authorization decision
        ↓
Agent communication capability
```

研究论证由四类互补证据组成：Claim 1 确定原认证与保密证明没有建立所需授权义务；Claim 2 确认具体 matcher 会偏离预期策略；Claim 3 展示授权分歧在明确抽象前提下可传播到消息接受；Claim 4 比较不同门控位置对材料发布、凭证签发和消息接受的影响。

当前贡献因此不只是孤立代码错误，而是对 **authorization enforcement inconsistency in agentic systems** 的分层分析：密码学有效性、策略决定正确性和跨阶段授权执行需要分别论证。但这仍是 SAGA 个案及相应模型的证据，不应扩展为所有 agentic systems 都存在同类漏洞。

当前主证据链已经连接记录场景的决定值传递，但各层证据不能合并冒充服务执行：

```text
Implementation evidence: archived production matcher observation
        ↓ historical source provenance binding
Same concrete policy input
        ├─ independent finite specification evaluator → SpecDecision = Deny
        └─ bound implementation observation → ImplObservedDecision = Allow
        ↓ checked same-evaluation decision pair
Formal adapter: bridge-generated scenario region
        ↓ reconstructed full model (frozen protocol semantics and queries)
Formal consequence: fresh archived ProVerif 2.05 execution
        ↓
ChatAccept reachable; ChatAccept ==> TokenIssue
```

**记录场景的可审计、机械化证据传递已完成；具体求值到符号角色的抽象、生产消费者对应及通用 refinement 仍未证明。** 原有 Stage 1 diagnostic、gate experiments、历史 turepass 及 bridge v1/v1.1 证据保持各自含义，不反向声称早期模型已包含自动 semantics。

## Current Limitations and Next Step

**Current completed:**

- Matcher bug reproduction：规则顺序导致的实现级授权绕过已有直接调用证据。
- Authorization proof-coverage diagnostic：保留原认证／保密结果的同时，新增授权对应关系失败。
- Authorization divergence modeling：固定规范拒绝／实现允许场景和到达 `ChatAccept` 的保存轨迹已有。
- Formal consequence provenance：`authz-turepass-20260919T090826295518Z` 已归档 `ChatAccept` 可达性和 `ChatAccept ==> TokenIssue` 结果、完整输出、版本及 manifest；历史 `turetrace` 单独保留。
- Authorization gate placement controls：历史共享 gate 和三个独立 gate 场景已有归档结果。
- Decision bridge v1.1.1：独立有限 spec 求值、历史观察来源绑定、同一求值 context 的决定对、场景区域重构和结构检查已有实现与保存的 25 项测试结果。
- Bridge-derived consequence evidence：B111 独立归档支持两个既有查询，记录干净代码提交、生成模型和各层哈希；本轮只读核对，没有重新执行。

**Remaining:**

- **General refinement and deployment-role correspondence.** 记录场景的规则、评分、预算决定及场景输入传递已由 bridge 处理；剩余的是 evaluator/adapter 的形式正确性、具体求值到符号协议角色及生产执行的严格对应，不能把这两种完成程度混写。
- **Optional service-level end-to-end reproduction.** 如后续选择扩展实现证据，再评价运行中服务的各授权边界；本文件没有执行或新增此类实验。

**End-to-end implementation-to-formal refinement remains unproved.** 这不否定已经完成的 recorded-evaluation evidence transfer，也不改变历史 matcher observation 已确认的结论。
