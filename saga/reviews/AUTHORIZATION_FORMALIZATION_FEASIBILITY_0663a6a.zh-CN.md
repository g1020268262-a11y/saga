# SAGA 授权执行形式化路线：代码能力审查与修改方案

审查日期：2026-09-23。实际 HEAD：`0663a6a92c82a9b749e6499fcc8385884957fcbc`。本轮开始时工作树干净。

## 结论

**当前代码拥有有限授权语义的可执行基础，但尚未实现完整的 authorization-workflow formalization。** 现状准确描述是：有限规范求值 + 历史实现观察绑定 + 固定场景生成 + 符号协议后果分析。

因此，不能直接把当前工作改称面向 Agent Communication Systems 的一般授权形式化框架。可以以已有代码为基础升级成“范围明确的授权执行模型与 SAGA 实例分析”；这需要新建授权状态/事件接口、模型转换关系与相应性质，不能只改标题或给现有事实增加几个事件名称。

在用户给定 bridge 二选一中：**以“雏形”的严格限定理解，接近 B；A 中“人工结果转移”不准确。** 但其后端仍是场景适配器，不是策略到授权工作流的形式化编译器。ProVerif 模型的分类则明确是 **类型 A：外部决策事实驱动协议状态**。

## 审查范围与本轮验证

- 阅读 `paper/main.tex`、十节正文，检查辅助叙事、修订说明和参考文献配置；正式入口使用 `paper/references.bib`。
- 检查 decision_bridge 六个 Python 文件、README、输入/输出、测试和历史控制观察。
- 检查 matcher、Provider `/access`、Receiver 预检查、OTK 消费、token 创建/验证和消息后端边界。
- 检查 ProVerif 基线、诊断、共享 gate、独立 gate、turepass 与 bridge 派生模型，并比较模型族差异；历史 old/Verifpal 文件没有补充策略求值能力。
- 根目录不存在独立的 `evidence/`。实际证据位于 `proofs/evidence/` 与 `proofs/decision_bridge/{evidence,observations}/`。
- 重新运行现有 bridge 测试：25/25 通过。
- 内存中重算 decision pair，与 B111 归档相同；重建完整模型，与 B111 归档逐字节相同。
- 本轮直接调用当前真实 matcher：规则合法；正序返回 10，反序返回 -1。
- 六个正式 archive 的 manifest 所列文件哈希共 51 项全部相符；B111 的六个 bridge 脚本输入哈希相符。核对各 archive 原始 stdout 的 RESULT 行及关键 witness。
- 本轮未重新运行 ProVerif，未部署或运行 Provider/双 Agent，未修改论文、实现、模型或历史证据。符号验证结果在本文中均指已归档结果；本轮新增的只有本审查文件。

## 1. 当前 bridge 的真实能力

### 1.1 输入

`run_bridge.py:10–14` 的默认输入来自 Stage 1 的真实 matcher 观察，组装为两部分：

1. `context`：有序 rules（id、position、pattern、budget）、initiator、target、receiver、policy_id/version/hash、source path/hash/commit。
2. `observation`：归档路径、文件哈希、格式、实际返回值字段选择器。

关键限制在 `bridge.py:99–104`：`target` 是被匹配的 Initiator AID，而不是 Receiver；`receiver` 固定为 `aid_A`，并明确标注 `symbolic policy owner; not recorded by matcher`。当前 schema 没有真实请求、动作、Receiver 所有权观察、OTK 或 token 关联。

### 1.2 SpecDecision 如何产生

`bridge.py:48–92` 的 `evaluate()` 独立解析和求值规则。它不导入生产 matcher、不调用 fnmatch，也不把 archive 中的 expected 字段作为答案。

支持的模式是 `*`、小写 ASCII literal AID、literal UID 后接 `:*`。求值步骤为：验证输入 → 计算匹配与 specificity → 选择唯一最高分 → 取 budget → 分类为 Negative/Zero/Positive → 以 budget > 0 表示 Allow。

无匹配返回 0/Deny；最高分并列或语法超出范围返回 Unsupported；非法字段返回 Invalid。后二者不是 Deny。有限求值器对具体规则确实进行了计算，而非将“specific deny”作为固定标签。

当前记录中，它算出 winning rule r0、specificity 70、budget -1、Deny。JSON 中字段名是 `spec`；ProVerif 中没有名为 SpecDecision 的求值事件。

### 1.3 ImplObservedDecision 如何产生

`bridge.py:138–158` 加载实际观察字段，核对有序规则、AID、归档哈希及历史源码绑定，再使用 `budget_decision()` 解释实际返回预算。

真实调用来源有两类：

- Stage 1 `policy-matcher-sanity.py` 导入 `saga.common.contact_policy.match`，归档正序 10、反序 -1。
- `collect_controls.py:10–24` 直接调用真实 matcher，保存正常 Allow/Deny 的新观察。

`run_bridge.py` 本身只重放记录，不重新执行 matcher。因此准确答案是“来自真实 matcher 的已归档函数调用观察”，不是“来自当前 Provider/Receiver 执行”。哈希绑定说明材料一致，不构成第三方执行认证。

### 1.4 输出与能力边界

`build()` 输出上下文、evaluation_fingerprint、spec 结果、impl_observed 结果和 divergence。

但 `generate()` 在 `bridge.py:176–190` 只处理 Deny/Allow。通过重算和核验后，它输出固定语句：

```text
insert ScenarioSpecDeny(BuggyPolicy, aid_B);
insert ScenarioImplAllow(BuggyPolicy, aid_B);
```

其他组合不生成后果模型。`generate_model.py:44–59` 把这两句放入哈希固定模板，保留协议、状态和查询。当前具体规则、specificity、预算、policy version 和 fingerprint 不进入 ProVerif 的求值/状态语义；fingerprint 仅在来源说明中出现。

因此，当前有如下完整链：

```text
Concrete Policy → Independent Evaluation → Spec Decision
Concrete Policy + Matcher Execution Archive → Observed Impl Decision
Checked Pair → Fixed Scenario Facts → Protocol Consequence Model
```

但没有如下完整链：

```text
Runtime Request → Owned Policy → Evaluator Transition
→ Context-Bound Decision → Actual Enforcement → Acceptance
```

### 1.5 A/B 判断

称其为纯人工结果转移会低估现有代码：决策确实被独立计算和机械传递。称其为完整授权语义框架会高估现有代码：当前仅有一个有限求值前端、一个函数观察适配器和一个 D/A 后果模板。

**可称“有限授权语义与证据适配的原型基础”；不宜称“授权工作流形式化框架已经实现”。**

## 2. 当前 ProVerif 模型属于哪一类

| 模型族 | 授权输入的来源 | 分类 |
|---|---|---|
| registration / 原 communication | 没有策略求值层 | 尚未建模该授权问题 |
| authz diagnostic | 初始化 PolicyDeny；PolicyAllow 没有发生 | A：覆盖诊断 |
| chat_allow / chat_deny | 初始化 PolicyAllow、MatcherAllow 和 Authorized，或对应拒绝事件 | A：共享 gate 控制 |
| 三个 p_*_r_* 模型 | 生成脚本传入 Provider/Receiver 布尔参数 | A：独立 gate 控制 |
| turepass | 初始化 ScenarioSpecDeny / ScenarioImplAllow | A：预置偏差后果 |
| bridge B111 | 外部计算并校验决策后初始化同样事实 | A：证据约束的偏差后果 |

关键实现证据：

- `turepass.pv:262–263` 初始化两个 scenario facts。
- `:234` 读取 SpecDeny；`:238` 读取 ImplAllow 后释放材料。
- `:120–123` Receiver 读取 ProviderReleased 与同一个 ImplAllow。
- `:127–143` 生成 token、插入 ActiveToken，再接受消息。
- `:246–251` 仅有接受到签发的 correspondence，以及接受可达性查询。

存在 protocol workflow，不等于 authorization workflow 已完整形式化。这里没有 Policy AST、选取 policy 的规则、Evaluator 进程、带请求上下文的 Decision，也没有判断 matcher 行为是否符合规范的 ProVerif 查询。

历史共享 gate 模型虽有 `ChatAccept ⇒ PolicyAllow/MatcherAllow`，这两个事件同样来自初始化，不能据名称认定求值已建模。独立 gate 的 `ProviderReleased` 是专门增加的 handoff 抽象；Receiver 实现没有读取同名授权表。

特别需要在新路线处理：

1. 当前 Provider 在 SpecDeny 条件下才继续后果流程。规范 oracle 正在影响运行控制流；统一 allow/deny 模型必须将规范观察与实现驱动分离。
2. `SOTK1_A` 是全局固定密钥，模型复制 Receiver，且没有删除 OTK 的状态转移。B111 witness 的两个 Receiver 副本用同一 OTK 生成 token。实际实现 `agent.py:1069–1076` 会在锁内删除使用过的 OTK。这不是现实 OTK 重用攻击证据，是当前抽象与实现的差异。
3. PeerB 是规定流程，不能直接等同于任意主动 Initiator。若新论文继续使用该攻击者模型，须明确攻击者持有自己的凭证、能控制哪些请求和消息，而不获得诚实 Receiver/CA 密钥。

## 3. 转向 authorization formalization 具体需要补什么

### 3.1 先确定有限范围

建议只覆盖：静态策略、当前闭合模式语法、单次 fresh contact、一个新 token 和消息接受；允许多个有限请求上下文用于绑定检查。动作先限定为 Contact，不能从 contact policy 推导任意工具命令权限。

将三层问题分开定义：

- Decision conformance：求值是否符合规范？
- Enforcement correspondence：消费者是否用对了该请求的决定？
- End-to-end authorization：被接受的通信是否存在相应规范许可？

零预算是很好的边界例：Provider > 0，Receiver >= 0。局部谓词不同并不自动意味着最终通信不安全；前置拒绝可能已经阻断流程。新理论应表达各层义务及组合条件，而非简单要求所有 gate 返回同一个布尔值。

### 3.2 数据结构

在新 schema/version 中新增；不要改写 v1.1.1 归档。

| 结构 | 最小字段与用途 | 可复用内容 |
|---|---|---|
| PolicySnapshot / PolicyIR | policy id、version、owner、receiver、规则 AST、semantics version；区分 Any/UID/ExactAID | 现有 rules、位置、哈希与语法验证 |
| AuthzRequest | request id、subject I、receiver R、operation=Contact、policy reference、身份验证状态 | 现有 initiator；将易混淆的 target 明确改为 matched_subject |
| EvaluationRecord | request、consumer、policy reference、winning rule、rank、raw budget、status、求值语义/实现版本 | `evaluate()` 结果与 `load_observation()` |
| EnforcementDecision | consumer、evaluation reference、gate effect；明确 Provider >0 / Receiver >=0 | 现有三类 budget 分类；不能只复用一个统一 Allow |
| CredentialBinding | receiver、subject/PAC、OTK id、token id、授权来源上下文 | ActiveToken 的概念可复用；参数必须扩展 |
| OTKState | available / allocated / consumed 的有限状态，至少保证 Receiver 一次性消费 | 原实现消费位置；当前 PV 没有这层 |
| ModelInstance | 有限 policies/requests、角色映射、求值模式、gate 布局、支持域及观察引用 | manifest、输入哈希、错误分类和归档逻辑 |

request id、policy hash、evaluation id 在实现中可能只是审计元数据。模型可用它们标注因果来源，但不能把这些字段假装成现有协议会检查的密码学绑定。

### 3.3 新 bridge 后端

建议新增 `authorization_ir.py`、`compile_workflow.py` 和独立共同模板；文件名只是建议。本轮不创建这些实现。

前端保留独立有限语义。后端至少需要：

1. 接受有限 PolicyIR 和 Request 域，编译策略/请求选择和求值关系。
2. 在模型中收到请求、选取适用策略之后，才能得到 SpecDecision 与消费决定。
3. 支持 Allow/Allow、Deny/Deny、Deny/Allow；另一个方向可作为过度拒绝控制。Unsupported/Invalid 拒绝分析，不混入 Deny。
4. 为 Provider/Receiver 分别实例化求值与 gate 解释。
5. 生成统一的 Enforcement → OTK/Token → Message 结构，而非每个场景选不同协议模板。

最低成本方案不需要在 ProVerif 中重写 Python/fnmatch。可以将有限域中所有支持的 `(policy, subject)` 求值结果编译为确定性 reduction 或完整有限关系，由模型内 Evaluator 进程按实际 Request/Policy 查用。**但必须说明它是有限求值关系的编译，并证明/穷尽检查其对应关系。** 只给旧事实改名为 EvalResult，仍属于类型 A。

对 SAGA buggy matcher，可以显式建立支持域内的“最后一个匹配项”行为抽象；Fixed 为“唯一最高分匹配项”。该抽象需要依据实际循环与支持域论证，并用真实生产 matcher/最小补丁差分验证。不要将自含的 `test_matcher_bug.py` 克隆当作生产补丁验证。

实现观察模式与语义模式必须分开：没有执行过的输入不能标成 ImplObserved；抽象求值不能自动变成 Python 源码证明。

### 3.4 至少需要的语义义务

如果使用 formalization bridge 作为贡献，以下不能全部留给未来：

- 有限域内求值确定性与定义域：哪些请求有唯一结果，哪些拒绝分析？
- 求值保持：编译得到的 spec decision 与有限规范语义一致。
- 上下文保持：不会把 I1/R1/P1 的决定交给 I2/R2/P2。
- 执行保持的有限说明：哪些 IR transition 对应哪些模型 transition；特别是没有引入额外授权 gate。

这些是**有限语义到模型的局部义务**，不是整个 Python 服务的 refinement。若只采用穷尽检查，应将结论限定在列出的有限输入实例；若主张对支持语言成立，就需相应一般论证。

可增加一个明确的组合命题：在固定策略、正确的决定来源与凭证关联下，如果每条接受路径都经过至少一个规范可靠的 gate 且保持同一授权上下文，则接受具有规范许可。它应作为待证明的充分条件，不能先当作已得到的新定理；其条件和反例分析比“认证不等于授权”更适合成为研究主线。

### 3.5 事件与查询

建议新增或扩展：

```text
Request(ctx)
PolicySelected(ctx)
SpecDecision(ctx, budget_class, effect)
ImplDecision(ctx, consumer, budget_class, effect)
Enforce(ctx, consumer, effect)
IdentityVerified(ctx)
ProviderRelease(ctx, otk)
OTKConsumed(ctx, otk)
TokenIssue(ctx, otk, token)
ChatAccept(ctx, token, message)
```

`ctx` 绑定 subject、receiver、Contact 操作、policy/version 与已验证 PAC；各消费者可有各自的 evaluation id。事件必须由实际模型转移触发，不能都在初始化 emit。

以下是应实现的 query 含义；参数展开和具体 ProVerif 语法应在新模型中检查，不是已验证脚本：

| 性质 | 查询目标 | 用途 |
|---|---|---|
| Evaluation origin | ImplDecision(c,k,b,d) ⇒ Request(c) 且 PolicySelected(c) | 避免没有适用请求/策略的决定 |
| Consumer correctness | Enforce(c,k,Allow) ⇒ ImplDecision(c,k,b,Allow) | 检查决定消费的上下文与消费者 |
| Provider soundness | ProviderRelease(c,o) ⇒ SpecDecision(c,Positive,Allow) | 区分错误 release 与最终接受 |
| Issuance soundness | TokenIssue(c,o,t) ⇒ SpecDecision(c,Positive,Allow) | 检查授权依据而非仅 token 来源 |
| Acceptance soundness | ChatAccept(c,t,m) ⇒ SpecDecision(c,Positive,Allow) | 新路线的主要安全目标 |
| Credential provenance | ChatAccept(c,t,m) ⇒ TokenIssue(c,o,t) | 扩展现有 correspondence 的状态关联 |
| OTK provenance | TokenIssue(c,o,t) ⇒ OTKConsumed(c,o) | 检查新签发使用的 OTK；唯一性另由线性状态保证 |
| Non-vacuity / consequence | release、issue、accept 独立 reachability；允许场景能执行 | 排除通过禁用全部行为得到安全 |

受控模型中可增加绑定错误 mutant，用于确认上下文查询确实能抓到错用决定；它是测试模型的诊断，不是新增 SAGA 漏洞。至少使用两个不同授权上下文，避免所有身份都固定为唯一常量使绑定性质变得无辨别力。

不要要求一 token 只对应一条 ChatAccept；合法多消息使用不应被错误的 injectivity 禁止。OTKConsumed 事件的存在本身也不证明 OTK 不会被重复消费，必须建立真正一次性状态。

ProVerif correspondence 用于表达既往事件关系，详细参数和顺序含义应遵守官方语义：[ProVerif manual](https://bblanche.gitlabpages.inria.fr/proverif/manual.pdf)。

### 3.6 论文结构与复用

建议结构：Introduction；System/Threat Model；Authorization Semantics and Enforcement Model；Finite Formalization Bridge；Security Properties and Analysis；SAGA Instantiation and Violation；Repair and Validation；Related Work；Limitations/Conclusion。

必须重写 Introduction、当前第 3 节、Formalization、Evaluation；第 4 节根因分析作为实例保留；第 5 节旧后果叙事变为 SAGA instantiation 中的证据。主线先给模型和性质，再说明 SAGA 如何违背；不是把旧段落简单重排。

可复用：有限 grammar/rank/budget 求值、观察加载与历史源码绑定、哈希和输入校验、append-only archive 习惯、matcher 实例、密码协议角色骨架、消息接受事件、现有 gate 位置。不可原样复用为新保证：D/A-only 固定生成器、手动 Receiver 映射、持久共享 OTK、未验证的 ProviderReleased handoff、只有 token 来源的查询。

## 4. 重新评价上一轮增强方案

上一轮以“提升真实安全案例”为目标，排序合理；转向形式化论文后，不能直接沿用全部 P0/P1 标签。

| 项目 | 本轮判断 | 原因 |
|---|---|---|
| Consumer replay | 实证增强强烈建议；不是纯形式化论文的逻辑前提 | 不执行服务也能证明模型定理。但若声称实际 SAGA 接受越权消息、生产修复有效或消费者已验证，它就必须完成。回放本身也不能证明 bridge 语义保持。 |
| OTK lifecycle | 必须处理与所选范围相关的最小生命周期 | 当前有明确模型/实现差异。可以限定单次 fresh contact，无需同时建模 expiry、revocation、全部 quota/concurrency。 |
| Buggy/fixed comparison | 两条路线都应做；repair validation 主张下必须做 | 当前 fixed_match 是简化克隆。新模型要比较抽象语义，实证修复要比较真实源码最小补丁；两者不可替代。 |
| Control experiments | 必须 | 支持 allow/deny 非空性和错误归因；统一模板下至少四个主单元，加一个分离 gate 对照。 |
| Evaluator property | 不能整体归入“可以不做” | 顺序不变性这个特定引理可以不做；有限语义、定义域和编译保持义务在 Route B 下不能全部省略。无需完整 Python 正确性证明。 |
| Second system | 可以不做 | 以明确适用条件与 SAGA 单实例支撑，标题及结论保留 case-study 边界；不宣称跨系统验证。 |
| Benchmark | 大规模 benchmark 可以不做 | 仍需小型语义/绑定/控制矩阵；不能把“不做 benchmark”理解成没有系统验证。 |
| Full refinement | 可以不做 | 研究对象是范围明确的授权执行模型及局部语义转换；须保留实现对应限制。 |

若本地完整部署成本高，可先调用真实 consumer 函数做窄集成检查以辅助接口映射。但 mock HTTP、数据库或证书状态的测试不能升级为真实端到端 replay，应分别命名。

## 5. Route A / Route B 与 2027 投稿方向

### Route A

Matcher inconsistency → checked bridge → ProVerif consequence。已有主要组件，增加实际执行和修复验证后可以形成完整的安全案例。主要研究问题仍围绕具体偏差及其后果。

### Route B

Authorization model → finite formalization bridge → security properties → SAGA instantiation → matcher violation → repair validation。现有 evaluator 可作前端，但模型、关系和主性质需要新工作。其贡献应是如何区分决定正确性、消费正确性与跨阶段授权，而不是声称发明授权与认证的区别。

| 会议 | Route A | Route B | 建议 |
|---|---|---|---|
| AsiaCCS 2027 | 有实质运行时影响时可走安全分析路线；当前仅函数观察+后果模型偏弱 | 需要方法结果与清楚的 SAGA 安全收益共同支撑 | B + 有限真实验证更完整；纯增加形式术语不优于 A |
| SACMAT 2027 | 授权案例匹配，但需要超过具体 matcher 根因的洞见 | 直接对应 policy analysis、enforcement、verification/testing | 三者中最适合作为范围受限 Route B 的优先目标 |
| CSF 2027 | 当前贡献形态不合适 | 方向上更合适，但需真正基础性贡献；简单 evaluator 引理或多加几个查询不足 | 不作为最低成本路线的首选 |

上述判断依据官方范围，而非会名排序：[AsiaCCS 2027 CFP](https://asiaccs2027.cityu.edu.mo/call-for-papers/index.html)强调现实安全问题并设软件安全/形式化方向；[SACMAT 2027 CFP](https://www.sacmat.org/2027/call-for-papers.php)明确列出策略分析、执行、验证与测试；[CSF 2027 CFP](https://www.ieee-security.org/TC/CSF2027/cfp.html)明确要求基础性安全研究。

截至本次查询，后续窗口包括 AsiaCCS Cycle 2：2026-12-11；SACMAT Cycle 1：2026-10-30、Cycle 2：2027-02-12；CSF Fall：2026-10-15、Winter：2027-01-28。不要以临近窗口为理由把未完成语义关系写成既有贡献。日期来源为上述官方网站及 [AsiaCCS 首页](https://asiaccs2027.cityu.edu.mo/)。

## Option 1：保持当前论文定位

### 修改内容

1. 保留 recorded mismatch → checked scenario transfer → conditional consequence 主线。
2. 修正/收缩 OTK 与 handoff 模型，统一 token 及控制结构。
3. 增加真实 matcher 最小补丁、Allow/Deny 对照；若主打影响，补消费者 replay。
4. 以实际到达边界更新论文和 claim–evidence matrix，压缩 Stage 历史叙述。

### 工作量

- 仅做模型/文稿边界整理：约 3–5 人日，但贡献类型基本不变。
- 包含窄 replay、真实补丁、统一控制和重新写作：约 10–15 人日（2–3 周），环境阻塞另计。

适合已有短期截止日期、希望先完成可信安全案例的情形。保留现标题或明确 SAGA case-study 标题，不升级为一般 framework。

## Option 2：升级为范围明确的 authorization formalization paper

### 修改内容

1. 定义有限授权语义和状态转移模型，区分 decision、consumer effect 与 acceptance。
2. 新建 Policy/Request/Evaluation/CredentialBinding IR，保留真实观察与抽象语义两种证据来源。
3. 将 D/A-only scenario adapter 扩展为有限工作流后端，给出求值与上下文保持义务。
4. 建立上下文关联、授权 soundness、OTK 状态和非空性查询；用多上下文和控制实例验证。
5. 以 SAGA 实例检验模型，包括真实 matcher 的 buggy/fixed 及消费者对照；优先完成一个窄 replay。
6. 重写理论—实例—修复的论文主线，并限制适用范围。

### 工作量

约 20–30 人日（4–6 周），是从当前基线出发的总量，不是在 Option 1 之外再相加。若符号状态建模或部署遇到持续问题，应留出更长缓冲。该估算不包含第二系统、完整 refinement 或具有 CSF 竞争力的新一般性理论。

可考虑的范围准确标题是 **Formal Analysis of Authorization Enforcement: A SAGA Case Study**。用户提出的复数 Systems 标题并非逻辑上必须要求两个系统，但需要明确的系统类、适用条件及可实例化模型；当前固定角色/场景后端尚未达到这一点。

## 推荐

**面向用户列出的 2027 研究论文目标，推荐 Option 2 的受限版本，优先按 SACMAT 方向组织；当前代码不能直接声称已经完成该升级。**

理由：现有独立 evaluator 和证据绑定值得复用，而当前主要缺口在“决定如何成为有上下文、有状态、有安全义务的执行过程”。补这一层，比继续重复 matcher 缺陷或堆积固定场景更能改变论文的研究中心。

设置一个五个工作日的路线检查点：只先写出有限语义、IR、一个 allow/deny 双路径模型和两条关键性质，明确 bridge 的保持关系。若这时仍只能把预设 allow/deny 包装成新的事件，而无法说明请求、策略和决定的产生/消费关系，就回到 Option 1，不继续扩大标题。

推进顺序应为：**有限语义与研究命题 → 最小工作流模型 → 上下文/状态性质 → SAGA 观察与真实补丁 → 窄消费者验证 → 改写正文。** Consumer replay 作为实例证据与模型开发交叉检查开展，而不再被误认为升级形式化定位的唯一门槛。
