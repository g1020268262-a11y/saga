# SAGA Claim-Evidence Matrix

## Overview

整理日期：2026-09-19。核对时仓库提交：`ae0025c11b2c3bc00d946bc5c90b455aeb706e9c`。

**Authorization correctness is not guaranteed by cryptographic authentication alone.**

本研究关注 **policy semantics + policy implementation + protocol consequence**：用户策略的预期含义是否被 matcher 正确实现，以及授权决定的偏差能否影响凭证签发和 Agent 通信授权。现有成果包括已确认的 matcher 实现级授权绕过、授权证明覆盖缺口、抽象授权分歧的通信后果模型，以及授权门控位置控制实验。它们不构成对 SAGA 密码学原语的破解结论。

本文件组织已有材料，不产生新实验或新安全结论。当前研究状态以 [AUDIT_STATUS.md](AUDIT_STATUS.md) 为准；历史阶段报告中的时间性表述仅描述当时的阶段。特别是，**matcher 实现级缺陷已经复现并确认**，待完成的是它与形式模型之间的严格语义映射，而不是重新确认该缺陷。

| Claim | 已完成工作 | 核心证据 | 当前支持的结论 | 不能自动扩展到的结论 |
|---|---|---|---|---|
| 1 | Authorization proof coverage gap | Stage 1 模型、查询摘要、重建轨迹 | 原认证与 token 保密结果不建立所需的授权可靠性 | 密码协议被破解，或实现层消息越权已复现 |
| 2 | Matcher implementation-level vulnerability | `test_matcher_bug.py`；原实现直接调用的 `policy-matcher-sanity.json` | 预期 DENY、实现 ALLOW；规则顺序影响授权决定 | Provider、token 和消息处理完整运行链已复现 |
| 3 | Authorization consequence modeling | `agent_communication_authz_chat_turepass.pv`、`turetrace` | 在预置规范拒绝／实现允许场景下，保存轨迹到达 `ChatAccept` | 已经建立具体 Python 执行到形式事件的精化关系 |
| 4 | Authorization gate placement experiments | 三个独立门控模型及其查询摘要 | Provider 与 Receiver 门控在不同阶段阻断后续事件 | 对生产实现门控机制或实际部署安全性的完整证明 |

**事件口径。** 本系列模型中，`PeerA = R` 是 token 签发方和聊天接收方，`PeerB = I` 是 token 接收方和聊天发送方。`Accept` 表示 B 收到并验证 token；`ChatAccept` 才表示 A 接受模型中的一条聊天消息。论文的 `ProviderGrant`、`TokenIssued`、`MessageAccepted` 与模型的 `ProviderRelease`、`TokenIssue`、`ChatAccept` 可作概念对照，但该对照本身不是实现到模型的语义映射证明。`turepass` 中的 `SpecIntendedDeny(B,A)` 参数顺序与 `TokenIssue(A,B,t)` 相反，使用时不能交换授权方向。

**证据来源核对。** 本轮只读核对了以下归档；所列模型的当前文件哈希与相应 manifest 的输入哈希一致，三个 manifest 所列的 12、6、8 个证据文件也分别匹配其记录。原 matcher 当前 SHA-256 与 sanity JSON 的记录一致。哈希核对是材料一致性检查，不是重跑实验。

| 归档 | 运行时基线 | 可核对材料 |
|---|---|---|
| [Stage 1](evidence/authz-stage1-20260916T123834944479Z/manifest.json) | `7372111bea150e32cee390a616849316d2780bfc` | 命令、ProVerif 2.05、输入哈希、原始输出、结果与检查记录 |
| [历史共享门控](evidence/authz-chat-guarded-20260917T080131985337Z/manifest.json) | `78e06379ec01f49d7b07067402ee60585dfe36c4` | 两个控制模型及其结果、输入与输出哈希 |
| [独立门控](evidence/authz-chat-gates-20260918T023621017067Z/manifest.json) | `2685d956b2f98fb1c4634dd6ec817fe4d9c448b8` | 三个控制模型及其结果、输入与输出哈希 |
| [`turetrace`](evidence/turetrace) | 本次快照中可读取；没有对应的独立运行 manifest | 已保存轨迹及 `ChatAccept` 可达性结果；不能用本次仓库快照补造其原始运行元数据 |

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

该 source hash 与本次核对的原 matcher 文件一致。这里引用的是既有输出，本轮没有执行这两个测试脚本。

## Security impact

**Order-dependent authorization bypass confirmed — at the matcher implementation/function level.**

本应由更具体规则决定的拒绝，被后出现的通配允许覆盖。`best_pattern` 保持 `None`，比较基准始终是其 specificity 值 `-1`；对正常处理的合法匹配规则，后续预算会继续覆盖前值。改变规则列表顺序可以改变实际授权决定，而预期最具体规则语义不变。

“Authorization bypass”在本 Claim 中指已确认的策略决策绕过：**Specification decision = DENY；Implementation decision = ALLOW**。它不以密码学攻击为前提，也不意味着测试已经穿过 Provider 和 Agent 的所有运行时检查。

## Scope

这是 **implementation-level vulnerability**。真实 matcher 的函数级偏差有直接调用证据，不应再退回仅为推测的状态。具体运行服务中的 `ProviderGrant`、`TokenIssued`、`MessageAccepted` 不在该 JSON 的实验范围内。规范依据是 matcher 的文档和 specificity 规则；不能仅凭示例脚本中的注释把它升级为对原论文全部策略语义的验证。

# Claim 3

## Claim

**Authorization decision divergence can propagate into agent communication authorization.**

该主张由明确假设授权分歧的形式后果模型支持：已保存的符号轨迹到达消息接受边界。它与 Claim 2 的具体实现证据相关，但二者之间的严格映射仍需完成。

## Evidence

| 文件 | 当前可核对内容 |
|---|---|
| [agent_communication_authz_chat_turepass.pv](proverif/agent_communication_authz_chat_turepass.pv) | 预置规范拒绝／实现允许场景；包含材料发布、token 签发和聊天消息接受 |
| [turetrace](evidence/turetrace) | 已保存的重建轨迹，包含 `SpecIntendedDeny`、`ProviderRelease`、`TokenIssue` 和 `ChatAccept` |
| [AUDIT_STATUS.md](AUDIT_STATUS.md) | 将该模型定位为 authorization consequence model，并将 Stage 4 整体标记为部分完成，待补语义映射与结构化证据归档 |

为避免把分析名称误写成已有模型事件，采用以下对照：

| 分析层含义 | 当前模型中的实际表示 | 证据语义 |
|---|---|---|
| `SpecDecision: DENY` | `ScenarioSpecDeny(BuggyPolicy,aid_B)` 表项；`SpecIntendedDeny(aid_B,aid_A)` 事件 | 规范侧拒绝是预置场景，不是模型计算具体 rulebook 的结果 |
| `ImplDecision: ALLOW` | `ScenarioImplAllow(BuggyPolicy,aid_B)` 表项 | 实现侧允许是 matcher 偏差的抽象，供 Provider 和 Receiver 读取 |
| Provider material release | `ProviderRelease(aid_A,aid_B)` | 模型中的访问材料发布 |
| Token issuance | `TokenIssue(aid_A,aid_B,tok)` | A 为 B 签发的 wire token；聊天模型这里使用加密 token 表示 |
| Message acceptance | `ChatAccept(aid_A,aid_B,tok,msg)` | A 通过该模型的 token／发送方绑定检查后接受一条消息 |

`SpecDecision` 和 `ImplDecision` 是上表的分析标签，不是当前文件中声明的事件名；`ScenarioSpecDeny` 和 `ScenarioImplAllow` 是 **table facts**，也不能误写为模型内计算得到的 policy events。

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
- 当前模型声明了 `ChatAccept ==> TokenIssue` 查询，但 `turetrace` 只保存消息接受可达性结果，未保存该 correspondence 的最终结果。轨迹中观察到先前签发，不等于已经归档其所有执行上的证明。
- 不能把 Claim 1 的认证与保密结果直接继承为此模型的新验证结果；`turepass` 没有查询原模型的完整性质集合。
- 该保存文件缺少独立的运行命令、版本、完整 stdout/stderr 和输入哈希 manifest。文件存在及轨迹内容可核对；严格的运行来源归档仍需补全，不能由本次材料整理补造。

因此，**授权分歧后果建模及到达 `ChatAccept` 的保存轨迹已经存在**；Stage 4 作为完整研究阶段仍有语义映射和证据归档工作。这与 matcher 缺陷已确认的结论一致。

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

两段已完成证据必须清楚连接而不能合并冒充：**具体 matcher 的 DENY/ALLOW 分歧已确认；在该分歧抽象下的通信后果已建模并有保存轨迹。二者之间可审计的实现到形式映射仍是剩余工作。**

## Current Limitations and Next Step

**Current completed:**

- Matcher bug reproduction：规则顺序导致的实现级授权绕过已有直接调用证据。
- Authorization proof-coverage diagnostic：保留原认证／保密结果的同时，新增授权对应关系失败。
- Authorization divergence modeling：固定规范拒绝／实现允许场景和到达 `ChatAccept` 的保存轨迹已有。
- Authorization gate placement controls：历史共享 gate 和三个独立 gate 场景已有归档结果。

**Remaining:**

- **Explicit semantic mapping from concrete matcher execution to formal events.** 将具体规则、评分、预算解释、参与方方向与场景表项／事件逐项对应；当前通用 `BuggyPolicy` 和固定表项不提供这一映射。
- 完成后果模型的结构化证据归档，区分模型中声明的查询、保存轨迹中的事实与已保存的最终验证结果；保留原始运行来源，不能补造历史执行信息。
- **Optional service-level end-to-end reproduction.** 如后续选择扩展实现证据，再评价运行中服务的各授权边界；本文件没有执行或新增此类实验。

**End-to-end implementation-to-formal mapping remains.** 这准确描述当前剩余边界，同时保留 matcher implementation-level vulnerability 已确认的结论。
