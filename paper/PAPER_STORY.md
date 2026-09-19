# Paper Story: Authorization Enforcement Gap in Agentic Systems

本文档用于设计论文研究故事、贡献与论证边界，不是论文正文。依据当前 [AUDIT_STATUS.md](AUDIT_STATUS.md) 与 [CLAIM_EVIDENCE_MATRIX.md](CLAIM_EVIDENCE_MATRIX.md) 整理；所有结果均来自已有材料，本次没有新增实验或改变安全结论。

# 1. Research Problem

Agentic systems 依赖身份认证、安全通信与授权策略：认证确定参与方身份，安全通信保护消息，授权策略决定哪些主体可以获得哪些通信能力。这些保证需要共同成立，但不能相互替代。

SAGA 现有认证与保密验证覆盖 identity correctness、authentication 与 confidentiality 等性质；这些性质本身没有建立用户策略到最终访问接受之间的一致性。论文应以本案例的实际证明范围为依据，不把这一观察扩展为对所有现有安全验证的判断。

核心区别是：密码层回答的 “who is communicating” 不等于策略层要求的 “who should be allowed to communicate”。即使主体身份真实、消息未被篡改，错误的策略决定仍可能赋予该主体不应获得的能力。

授权正确性至少依赖以下链条：

```text
Policy semantics
       +
Policy implementation
       +
Enforcement at protocol boundaries
```

**研究问题：当密码协议的认证与保密保证成立时，如何判断策略语义、策略求值实现与通信授权执行是否仍然一致？**

问题的重要性在于：用户通过策略表达访问边界，而系统通过凭证签发与消息接受落实边界。如果验证只覆盖身份与密码材料，策略求值的错误可能处于已有证明的覆盖范围之外。本文用 SAGA 个案分析这一缺口，不宣称其在所有 agentic systems 中普遍存在。

# 2. Key Observation

系统可以同时存在正确的密码学认证与错误的授权决定；通过身份认证的主体也可能是策略明确拒绝的主体。

```text
Authenticated Agent
        |
        v
Secure Channel
        |
        v
Wrong Authorization Decision
        |
        v
Unauthorized Capability
```

此图表达概念关系，不表示 SAGA 各协议消息的实际时间顺序，也不是完整服务执行记录。最后一步在当前研究中由带有明确前提的形式化后果模型支持。

**叙事重点：认证与授权分别承担不同的证明义务。** 当前发现不需要以破解密码算法、伪造身份或窃取私钥为前提；研究材料也没有证明这些攻击发生。

# 3. Root Cause

## Specification

Contact policy matcher 的预期语义是 most-specific matching rule wins：多个规则匹配时，应由最具体的匹配规则决定预算。对于当前反例中的规则关系：

```text
specific deny
    beats
general allow
```

因此，在具体拒绝规则与一般允许规则同时匹配时，规范决定为 DENY。

## Implementation

被审计的 [contact_policy.py](../saga/common/contact_policy.py) 在选中匹配规则后没有更新 `best_pattern`。对于当前有效模式，后续匹配规则可能继续覆盖已选预算，使结果依赖规则排列顺序。

```text
general allow
  overrides
specific deny

SpecDecision           = DENY
ImplementationDecision = ALLOW
```

证据需要区分来源，不能把示例脚本与实际实现执行记录混为一谈：

| 材料 | 支持的内容 | 叙事用途 |
|---|---|---|
| [test_matcher_bug.py](test_matcher_bug.py) | 自包含的错误／修正 matcher 对照，使用简化 specificity 计算与 Mallory 示例 | 解释缺陷机制；该脚本不是直接导入生产 matcher 的执行证据 |
| [policy-matcher-sanity.json](evidence/authz-stage1-20260916T123834944479Z/policy-matcher-sanity.json) | 对真实 matcher 的已保存调用结果；Alice 示例中预期预算为 -1，实际为 10；反向排列后为 -1 | 确认实际实现的规则顺序依赖与 DENY/ALLOW 分歧 |
| [Claim–Evidence Matrix：Claim 2](CLAIM_EVIDENCE_MATRIX.md#claim-2) | 汇总实现、记录与结论边界 | 保持论文措辞与证据范围一致 |

**已确认结论：implementation-level authorization vulnerability，即 matcher／函数层的 order-dependent authorization bypass。** 这一结论不需要等待完整服务复现才能成立；同时，它自身不等于运行中服务已经完成端到端绕过。

# 4. Attack Narrative

论文用下面的因果链组织影响分析，而不是提供新的攻击执行步骤：

```text
Policy Rule
    |
    v
Matcher Evaluation
    |
    v
Authorization Decision Divergence
    |
    |  Concrete-to-formal semantic mapping remains
    v
Abstract Spec-Deny / Impl-Allow Scenario
    |
    v
ProviderRelease
    |
    v
Token Issuance (TokenIssue)
    |
    v
Agent Communication Acceptance (ChatAccept)
```

**Matcher 是实现缺陷的入口；ProVerif 用于分析该类授权分歧的协议后果。** 上半段有真实 matcher 调用证据，下半段有形式化模型与保存轨迹；中间连接尚不是已经完成的实现精化证明。

在 [agent_communication_authz_chat_turepass.pv](proverif/agent_communication_authz_chat_turepass.pv) 中，`ScenarioSpecDeny` 与 `ScenarioImplAllow` 是固定场景表项，不是 Python matcher 的计算结果。`SpecDecision` 和 `ImplDecision` 是叙事标签，不是模型实际声明的事件名。

已有 [turetrace](evidence/turetrace) 记录了规范拒绝、Provider 发布、token 签发与 `ChatAccept`，并保存消息接受可达性结果。它支持的表述是：**在固定规范拒绝／实现允许场景及模型假设下，授权分歧可以传播到消息接受。**

独立 gate 对照进一步说明阻断位置的差别，结果来自 [AUTHORIZATION_CHAT_GATES.zh-CN.md](AUTHORIZATION_CHAT_GATES.zh-CN.md) 及其引用的已有运行记录：

| 场景与模型 | ProviderRelease | TokenIssue | ChatAccept | 论证作用 |
|---|---|---|---|---|
| [Provider allow / Receiver allow](proverif/agent_communication_authz_chat_p_allow_r_allow.pv) | 可达 | 可达 | 可达 | 允许路径能够完成 |
| [Provider allow / Receiver deny](proverif/agent_communication_authz_chat_p_allow_r_deny.pv) | 可达 | 不可达 | 不可达 | Receiver 在签发前阻断，但此前材料已发布 |
| [Provider deny / Receiver allow](proverif/agent_communication_authz_chat_p_deny_r_allow.pv) | 不可达 | 不可达 | 不可达 | Provider 在更早边界阻断 |

这些是明确控制流程抽象下的对照结果，不是生产系统修复效果的证明。历史 [shared-gate allow](proverif/agent_communication_authz_chat_allow.pv) 与 [shared-gate deny](proverif/agent_communication_authz_chat_deny.pv) 模型用于共享授权状态的控制对照，不能替代独立门控位置分析。

# 5. Formal Analysis Boundary

## Proven

这里的“已证明”分别指实现记录支持的事实与模型内验证结果，必须保留各自范围。

| 已完成事项 | 证据与结果 | 准确结论 |
|---|---|---|
| Matcher implementation mismatch | 真实 matcher 保存记录显示预期拒绝、实际允许，反向排列改变结果 | 实现级顺序依赖授权绕过已确认 |
| Authorization verification gap | [诊断文档](AUTHORIZATION_DIAGNOSTIC.zh-CN.md) 与 [Stage 1 模型](proverif/agent_communication_authz.pv)：原认证／保密查询结果保留，新增授权 correspondence 失败 | 原证明未建立所需授权性质 |
| Abstract divergence can reach ChatAccept | `turepass` 模型与 `turetrace` 的可达性记录 | 在指定分歧及模型假设下存在到达消息接受的执行 |
| Gate placement controls | 三个独立 gate 模型的已有结果 | 不同门控位置在模型中阻断不同阶段 |

Stage 1 中 `PolicyAllow` 没有被触发；因此，在 `Accept` 可达时，对它的授权对应关系失败是覆盖诊断，不能单独证明真实 matcher 的缺陷。此外，该模型的 `Accept` 是 token 接受事件，不是后续模型的 `ChatAccept`。

后果模型还受以下条件约束：`tls_chat` 为私有信道抽象；`ProviderReleased` 为 Provider 放行到接收方处理的因果传递抽象，尚无完整生产实现映射。新鲜 token 的使用本身也不等于已经证明会话隔离或 injective agreement。

`turetrace` 保存的是 `ChatAccept` 可达性结果，没有保存模型声明的 `ChatAccept ==> TokenIssue` 查询的最终结果。不得将轨迹中的先前签发改写为已归档的全执行 correspondence 证明，也不得把 Stage 1 的完整密码性质结果直接继承给 `turepass`。

## Not Proven Yet

当前没有声称以下结论；其中密码破解与私钥泄露也不是本研究预计必然发现的后续结果。

- **Cryptographic break：** 没有证明密码算法或协议密码性质被攻破。
- **Private key compromise：** 没有证明私钥被窃取或恢复。
- **Full production exploit：** 没有展示运行中服务从具体规则配置到最终受保护业务行为的完整执行证据。

因此不能使用 “SAGA cryptography is broken” 或 “full end-to-end implementation exploit reproduced” 描述现有成果。也不能反过来写成“漏洞尚未证明”：matcher 实现缺陷已经确认，剩余的是跨层映射与更完整的实现影响证据。

## Remaining Future Work

首要工作是建立可审计的严格语义映射：

```text
Concrete Rulebook
       |
       v
Matcher Execution
       |
       v
Formal Events
```

映射应说明具体规则、specificity、返回预算与允许／拒绝解释如何对应场景表项和事件，并统一参与方方向。当前模型的 `SpecIntendedDeny` 使用 sender-first 参数，而 `ProviderRelease` 等使用 receiver-first 参数；仅凭事件名称不能认定参数语义一致。

另需完善后果模型的证据来源归档；现有 `turetrace` 未附独立运行 manifest 与完整验证输出，不能补造历史来源或未保存的查询结果。服务级端到端复现是可选的后续扩展，本次没有开展。

**End-to-end implementation-to-formal mapping remains.**

# 6. Research Contributions

| 贡献 | 推荐论文表述 | 已有支撑与边界 |
|---|---|---|
| Contribution 1: Authorization enforcement gap in agentic systems | 以 SAGA 为案例，识别密码学验证与策略授权执行之间尚未覆盖的证明义务 | 原性质与新增授权诊断；不宣称所有系统均有该问题或已证明文献首创性 |
| Contribution 2: Order-dependent authorization bypass caused by policy evaluation inconsistency | 确认策略求值偏离最具体规则优先语义，导致规则顺序相关的实现级授权绕过 | 真实 matcher 的保存调用记录；范围是函数级，不包装成完整服务利用 |
| Contribution 3: Formal analysis of authorization divergence impact | 在明确场景抽象下分析授权分歧到通信接受的后果，并比较 Provider／Receiver gate 的阻断位置 | 后果轨迹与门控对照；尚非 Python 到模型的精化证明 |

“为什么不只是简单代码 bug”的回答应来自这些证据的组合：代码缺陷揭示策略语义与求值实现之间的偏离；证明覆盖诊断说明现有认证／保密保证未约束该偏离；后果与门控分析说明凭证签发、材料发布和通信接受需要分别定义授权义务。

这一研究贡献仍以 SAGA 个案为支撑。论文需要诚实承认根因包含具体编码错误，不把一个缺陷自动提升为普遍性定理，也不声称已经完成严格跨层证明。

# 7. Paper Positioning

推荐定位为 **Authorization enforcement vulnerability**，或 **Gap between cryptographic verification and authorization enforcement**。

工作标题可用：**Authorization Enforcement Gaps in Agentic Systems: A SAGA Case Study**。标题中的个案限定与当前证据范围一致。

避免使用 “Breaking SAGA” 或 “Cryptographic vulnerability”：它们会使读者误以为论文展示了密码协议破解。叙事应依次建立研究问题、实现分歧、抽象后果与边界，而非先用强攻击结论吸引读者再在限制段撤回。

研究主线为：**policy semantics → matcher implementation → authorization decision → agent communication capability**。现阶段可支持的定位是授权执行不一致的分层案例分析，尚不是完整实现安全性定理、部署影响普查或修复验证论文。

# 8. Reviewer Questions

**Q1: Is this a crypto attack?**

No. 当前没有密码破解证据。Stage 1 的已有记录保留了原认证与保密查询的成立结果，同时新增授权查询失败。因此可以说这些已查询性质保持成立，不能无条件声称所有密码性质在所有后续模型或生产部署中都已证明完好。

**Q2: Is this only a coding bug?**

根因确实包含具体编码错误，但研究论证还覆盖策略语义与执行实现之间缺失的验证边界，以及该分歧在抽象协议中的后果和不同 gate 的阻断位置。这些分析构成超出错误定位本身的贡献；严格实现到模型映射仍需补全。

**Q3: Does ProVerif model the Python matcher?**

No. 当前模型以固定场景表项抽象分歧，并未执行 Python matcher 或形式化计算规则排序与 specificity。具体 matcher 缺陷有独立实现证据；二者之间的 strict semantic mapping 是后续工作。

**Q4: Does the saved trace establish a full end-to-end exploit?**

No. 它建立的是给定模型与固定场景下的消息接受可达性。真实 matcher 的结果与抽象通信后果分别已有证据，但不能拼接称为一次完整运行中服务的攻击记录。

**Q5: Are the deny-gate results stronger authentication proofs?**

No. 拒绝场景中 `ChatAccept` 不可达，因此相关 correspondence 为真可能只是空真。它们主要定位阻断边界；双允许路径的可达性对照用于避免把不可执行流程当作安全保证。

**Q6: Is the divergence simply assumed by the model?**

Yes, 在后果模型中它是明确输入的场景假设，其现实依据来自独立的 matcher 证据。模型回答“该类分歧在这些协议抽象下能否传播到接受”，不独立证明“Python matcher 必然产生该分歧”。论文必须显式区分这两个问题。
