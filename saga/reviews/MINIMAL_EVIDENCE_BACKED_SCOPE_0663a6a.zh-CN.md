# SAGA：保持 bridge 设计的最小投稿增强

基线：`0663a6a92c82a9b749e6499fcc8385884957fcbc`；审查日期：2026-09-23。

本轮重新核对 bridge、生成器、运行结果解析器、模型事件/状态、正文贡献和归档输入输出。没有修改实现、模型或论文，也没有重新运行测试、ProVerif 或服务。此前同版本测试结果不冒充本轮新执行。

## 结论

可以把论文中心收敛为 **Evidence-backed Authorization Decision Analysis for Agent Communication Systems**，建议加副标题 **A SAGA Case Study**。

当前已有独立规范求值、真实实现观察、决定比较、场景重构和完整模型生成。最小缺口是：已有决定上下文主要停留在 JSON 和模型注释中，没有成为后果事件可以关联的参数；后端目前只接受 D/A，缺少同模板中的正常控制。

不需要新授权理论体系、不需要完整 IR、不需要让 ProVerif 求值 matcher。新增代码应限于既有 bridge 的上下文导出、一个版本化模型模板、对应查询/测试和结果解析。

## 1. Current Bridge Capability

| 能力 | 当前代码依据 | 结论 |
|---|---|---|
| Specification-side decision | `bridge.py:48–92` 的 evaluate：独立匹配、评分、选唯一最高分、解释预算 | 已完成，支持有限语法，不读取 archive expected 字段作为答案 |
| Observed implementation decision | `bridge.py:138–158`，读取实际返回值，绑定规则、AID、文件和历史源码 | 已完成；是历史函数执行观察，不是 Provider/Receiver 执行观察 |
| Decision comparison | `bridge.py:161–173` 的 build，构造 spec/impl_observed/divergence | 已完成，两个决定属于同一被检查的输入上下文 |
| Scenario reconstruction | `bridge.py:176–190` 重算决定对，再输出场景语句 | 已完成，但只为 D/A 输出两条固定事实 |
| ProVerif model generation | `generate_model.py:44–70` 重构模板场景区域并校验其余字节 | 已完成，有独立归档运行；不是只有片段或计划 |

足以保留为贡献的组合是：**独立求值 + 来源约束的真实观察 + 检查后的场景生成 + 范围明确的符号后果分析**。matcher 缺陷作为这一分析链的具体实例。

不足主要有两类，不能混淆：

- 表达组织问题：现有 Introduction 已经描述上述能力，但研究问题仍按历史 Stage 和 matcher 发现展开；没有让决定来源、决定比较与消费后果成为一条主线。不能说论文完全没写 bridge。
- 实际能力缺口：具体上下文没有进入模型事件参数；完整生成器只接受 D/A；没有同模板的 A/A、D/D 运行结果。后者需要小幅实现和新验证，不是文字修改。

模型仍回答“在这些已注入决定及协议假设下，哪些后果成立”，不回答任意政策或真实服务的普遍正确性。

## 2. Minimal Missing Layer

### 2.1 先澄清“同一个 authorization event”

现有证据支持的是 **same recorded evaluation context**：同一匹配身份、有序规则和历史 matcher 来源。spec 是对该输入独立求值的结果，impl 是相应归档调用的结果。

它不支持“同一个真实网络请求”：历史观察没有真实 Receiver、策略所有权或 request ID。新增一个 UUID 不能补出这些事实。

因此推荐保留论文口径为“同一记录求值的决定对”，并给它一个贯穿模型的 **analysis context**。如果未来一定要声称同一真实授权请求，至少需要在真实消费者的一次 matcher 调用处收集请求身份、Receiver、策略快照和返回值；本方案不把这项新增运行时收集设为前提。

### 2.2 最小字段选择

| 候选信息 | 是否必要 | 最小处理 |
|---|---|---|
| Request context | 需要分析上下文；不需要伪造实际 request | 直接复用现有 evaluation_fingerprint 和 bridge-result 文件哈希 |
| Identity binding | 必须 | 保留观察中的 AID → aid_B 映射；说明这是角色映射，不是新身份认证证据 |
| Policy snapshot | 必须 | 复用有序 rules 和 policy_hash；把对应符号 policy 常量写入生成映射 |
| Policy version | 现有标签可保留；不需新版本系统 | 当前 version="1" 是分析标签；策略快照由哈希确定，不宣称观察了部署版本 |
| Enforcement target | 必须明确，但可维持抽象 | 复用 symbolic receiver=aid_A；注明非实测 owner/receiver；stage 为 Provider/Receiver |
| Decision provenance | 必须，现有基本具备 | 保留 spec 求值版本、impl observation 路径/哈希/字段、历史源码版本；模型中区分两种来源 |
| Operation | 固定 Contact 即可 | 一项范围说明或常量；不引入动作语言 |
| Runtime session ID、时间戳、动态策略状态 | 不需要 | 本次不作具体会话或动态授权主张 |

`evaluation_fingerprint` 标识求值上下文，不保证唯一一次运行。最省事的完整决定对标识是生成器已有的 `bridge_result_sha256`，它覆盖上下文、决定及观察引用。可生成符号 `ctx_<hash>`，并在 manifest 中保留常量与原始结果的对应关系。

该标识在决定对序列化后计算，映射写入 manifest/模型头部，不把结果自身的哈希写回参与该哈希计算的 JSON，避免自引用。

这不是新数据层：复用当前 result/context，增加一小段导出映射和必要的语义说明即可。将 existing receiver_binding 的“抽象”含义保留下来，不因新增哈希而升级为已观察绑定。

还有一个必须写清的解释：`budget_decision()` 采用 Provider 的 `>0` 约定。Receiver 预检查是 `>=0`。最小模型控制选预算 -1 和正数，避免把零预算压缩成两端相同的决定；evaluator 对零的支持仍可保留。零预算的消费者后果不纳入这次新模型结果。

## 3. ProVerif Minimal Enhancement

### 3.1 保持决定外部注入

仍由 bridge 计算 SpecDecision、读取 ImplObservedDecision；ProVerif 不选择规则、不计算 specificity、不调用 Python。

新建一个版本化的 context-bound 后果模板，不改写历史 turepass 或 archive。桥接事实增加 context、subject、receiver、policy 参数。

建议只新增两种事件，并给已有事件增加 context：

```text
DecisionBound(ctx, origin, receiver, subject, policy, decision)
DecisionUsed(ctx, stage, receiver, subject, policy, decision)

ProviderRelease(ctx, receiver, subject)
TokenIssue(ctx, receiver, subject, token)
ChatAccept(ctx, receiver, subject, token, message)
```

origin 区分 SpecEvaluation 与 ImplObservation；stage 区分 Provider 与 Receiver。DecisionBound 表示“桥接输入在模型中绑定”，不是“ProVerif 执行了 matcher”。DecisionUsed 在消费者真正通过相应 guard 后发生，表示模型中的消费。

ctx 随决定引用、handoff 和 token 来源传递；接受时从被实际查中的 ActiveToken 记录取得 ctx，不能凭空填一个全局标签。ctx 是分析注释，不得变成线协议中不存在的新认证字段或额外拒绝条件。仍允许声明当前 ProviderReleased 是 handoff 抽象。

### 3.2 最有用的三类查询

以下是性质示意，新增参数和语法需在实现时运行检查：

1. **接受与签发具有相同决定上下文**

   `ChatAccept(c,R,I,t,m) ⇒ TokenIssue(c,R,I,t)`。

   这是对现有查询的直接扩展，不宣称同一实际服务会话或唯一签发。

2. **模型中的 gate 使用有来源的同上下文决定**

   `DecisionUsed(c,k,R,I,p,Allow) ⇒ DecisionBound(c,ImplObservation,R,I,p,Allow)`。

   再分别检查 release/issue 对应相应 DecisionUsed。其价值是验证模型输入消费与归因；部分保证来自模型结构，不把它包装成求值正确性定理。

3. **区分 token 来源与规范许可**

   `ChatAccept(c,R,I,t,m) ⇒ DecisionBound(c,SpecEvaluation,R,I,p,Allow)`，其中 p 必须通过 ctx 关联到同一策略，不能允许匹配任意 policy。

   预期 D/A 场景下授权对应关系失败，而接受到签发关系仍成立。保持 ChatAccept 独立可达性，用 A/A 和 D/D 对照解释真值与空真。

若为简化查询语法，把 policy 放入 ctx 的结构项或显式加入接受事件都可以；二者择一，不建设通用上下文编码器。可选再增加 release、issue 的独立可达性，但应与新结果解析器一致。

### 3.3 只增加两个完整模型控制

继续使用现有已归档输入：

| 控制 | 输入来源 | 预期结果，须新运行确认 |
|---|---|---|
| D/A | 原 specific-deny / wildcard-allow 观察 | Accept 可达；来源对应成立；规范授权对应失败 |
| D/D | 同一规则反序后的真实观察，或现有 deny observation | Accept 不可达；对应关系需标明空真 |
| A/A | 现有 allow observation | Accept 可达；来源及规范授权对应成立 |

使用同一个新模板和相同查询。spec 仅用于标注和查询，不用 SpecDeny 决定 Provider 是否继续；实际路径由注入的 impl 决定控制。否则当前 turepass 的 SpecDeny guard 会把正常 allow 场景挡掉。

这只是将已有有限决定组合带入同一后果模板，不扩展策略求值设计。D/D 不是 production fixed matcher 的修复证据。

### 3.4 不扩张的边界

本次不增加 OTK 生命周期研究、会话隔离定理或真实消费者执行主张。已有 OTK/复制进程抽象及 witness 的实例关联限制应继续公开说明，ctx 不叫 session ID。如果今后要把 witness 当作真实新联系重放依据，才必须另行处理这些状态差异。

单一 ctx 下的对应关系也不能证明跨请求防混淆；最小必做的是生成器对 context 被调换的拒绝测试。两个 ctx 的诊断模型可以选做，但不能把未做的多上下文性质写成贡献。

## 4. Paper Contribution Rewrite

### Current contribution

我们通过直接 matcher 调用确认 SAGA 中的顺序相关授权决定偏差；使用独立有限规范求值与来源绑定的实现观察重构偏差场景，并分析该场景中的消息接受和 token 签发关系。

### Enhanced contribution（完成新增验证后方可使用）

1. 我们对记录的授权求值构造可审查的决定对：规范决定由有限规则语义独立计算，实现决定来自绑定到相同输入和历史源码的实际观察。
2. 我们将决定对及其分析上下文机械传递到符号后果模型，并检查模型中的决定消费、token 签发和消息接受之间的上下文关联。
3. 我们以 SAGA 为案例，通过偏差与一致决定的同模板控制，区分决定来源、凭证来源和规范许可：模型中的消息接受可以具有合法签发来源，同时缺少对应规范许可。

这些贡献强调已经或将由检查支持的分析过程，不声称任意策略、多个系统或真实部署均满足相应性质。Agent Communication Systems 是问题领域，SAGA 是唯一实证实例。

## 5. Required Engineering Work

### 必须修改或新增

| 文件 | 最小任务 |
|---|---|
| `proofs/decision_bridge/bridge.py` | 复用 evaluate/load_observation/build；扩展新版本场景导出，将 pair/context 映射到符号常量；支持 D/A、A/A、D/D；明确预算解释域 |
| `proofs/decision_bridge/generate_model.py` | 对新模板保留哈希固定、场景区域重构与结构白名单；生成带 context 的绑定；保留旧版本重建入口或明确固定历史代码提交 |
| `proofs/decision_bridge/run_bridge.py` | 导出新增绑定元数据，更新摘要；不改为自动调用真实消费者 |
| `proofs/decision_bridge/run_verification.py` | 支持新输入/三个场景；当前 summarize 硬编码恰好两条查询，需要更新；区分分析运行完成与某条安全性质被反例否定 |
| `proofs/decision_bridge/test_bridge.py` | 保留旧版测试；新增 context 调换、来源混淆、三种组合生成、结果解析测试；旧版拒绝非 D/A 的测试不能直接删除历史含义 |
| 新模型 `proofs/proverif/agent_communication_authz_chat_context.pv`（建议名） | 从现有模型小幅扩展 context、事件及查询；采用统一控制结构；不用 ProVerif 求值策略 |
| 新 evidence archive | 保存新模型、输入、决定对、映射、查询原始结果及 manifest；不覆盖历史 archive |
| `proofs/decision_bridge/README.md`、`proofs/CLAIM_EVIDENCE_MATRIX.md` | 更新精确能力、版本关系和新旧查询范围 |

不需要修改 `saga/common/contact_policy.py`、Provider 或 Agent 来完成上述目标。

运行器不应把“预期发现授权对应关系失败”记成工具执行失败，也不应把任何反例都硬判为成功。应分别记录工具完成状态、查询 true/false/unknown、以及控制结果是否符合预期；unknown 和缺失结果不能冒充通过。

### 必须调整的正文

- `paper/main.tex`：标题、摘要。
- 第 1 节：三项贡献与问题中心。
- 第 3 节：定义 recorded evaluation context，区分真实 request/session。
- 第 5、6 节：补新事件、决定注入与上下文传播；区分历史模型与新结果。
- 第 7 节：加入统一 D/A、D/D、A/A 表，报告授权与凭证来源查询及非空性。
- 第 8、10 节：按最终范围更新限制与结论。
- 第 9 节：小幅调整定位，避免把已有规范/实现比较说成首次提出。

第 2 节背景和第 4 节 matcher 根因基本可保留。无需重排整篇论文为理论体系。

### 可选测试或实验

- 两个 ctx 的小型模型诊断，检查错误归因能否被发现。
- 几个额外的规则置换或无匹配测试；现有 evaluator 测试可继续复用。
- 真实 matcher 的最小补丁比较，作为额外实现验证，不是本次定位的必要条件。
- 窄 consumer replay；只有做了才增加实际消费者主张。

新增 context 与结果解析测试属于必做；可选的是额外覆盖，不是完全不测试。

## 6. Reviewer Impact

| 攻击点 | 最小增强后的回应 | 仍存在的边界 |
|---|---|---|
| bridge 只是人工映射？ | 对“决定值人工填写”的指控，现有代码已能回应；新增 context 将机械传递和消费归因展示得更明确 | 模板与符号角色仍由研究者设计，不声称自动提取协议 |
| ProVerif 只是人为构造结果？ | 三组同模板控制、不以 spec 决定运行分支、独立可达性与两类对应关系，使分析更可审查 | 偏差仍是有证据的输入，ProVerif 不独立发现 matcher 偏差；结构性来源查询的通过也不是新求值定理 |
| 是否只是 bug report？ | 论文对象扩展为从决定证据到后果归因的分析，并区分不同安全边界 | 实证仍是单一 matcher 机制；不能仅靠改名保证研究增量充足 |
| authorization insight 不足？ | 可以提炼“来源可追踪、凭证有效、规范许可”三者的区别及 gate 消费边界 | 这些区别本身不是首次发现；具体价值来自 SAGA 的可复核证据和控制结果 |

新增参数和几条查询提升的是证据完整性、归因清晰度与结果可信度，不会自动产生普遍理论或跨系统新颖性。模型与真实服务之间的边界仍需保留。

## Recommended Final Scope

保持当前版本的核心设计，只完成三项：

1. **上下文贯通：**复用现有决定对、evaluation fingerprint、policy hash 和来源信息，将一个明确标注为分析用途的 context 传入模型。不给历史函数观察补造真实请求身份。
2. **小规模模型增强与控制：**一个新模板、决定绑定/消费事件、带 context 的签发/接受对应关系，以及 D/A、D/D、A/A 三组新验证。保留现有状态抽象边界。
3. **围绕证据链调整论文：**以决定来源、比较、消费和后果为贡献；matcher 为 SAGA 实例；更新结果矩阵及贡献措辞，不扩大到真实部署或一般系统保证。

预计约 5–8 个有效工作日，取决于新查询求解和文稿修改；这是工作量估计，不是已验证工期。若上下文注释意外改变可达性，应先检查是否新增了实现没有的 guard，而非继续扩大模型来解释变化。
