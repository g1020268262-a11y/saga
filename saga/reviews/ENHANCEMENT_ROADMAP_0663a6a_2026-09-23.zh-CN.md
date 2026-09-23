# SAGA 投稿增强方案：以真实消费者执行支撑跨层授权分析

日期：2026-09-23。设计基线：`0663a6a92c82a9b749e6499fcc8385884957fcbc`。

输入：上一轮针对 `fe096ee9123052f422a1baf48e0d4fbdfb2294c5` 的匿名审稿报告，以及当前实现、论文、bridge v1.1.1 和证据目录。当前 HEAD 在论文第 4、5、9 节已有后续修订；本方案不把已修正的旧版本叙述问题再次列为主要工程任务。

本文件是研究与实验设计，不是已完成实验的结果。本轮未修改论文、运行时实现、模型或历史证据，未运行真实通信链或重新执行 ProVerif。下述结果均为待检验预测。

## 1. Research Contribution Redesign

**选择 D：混合形式——由案例驱动的跨层分析流程，加上经过真实消费者验证的 SAGA 安全案例。**

以实证为中心，以有限语义和符号分析解释机制。三周内最合理的研究增量是把“函数返回错误”推进为“明确授权上下文中的错误决策，被哪些消费者使用，如何传播至应用消息接受，以及在哪个真实执行点可以阻断”。

- A 漏洞分析路线需要足够深的实际影响；目前不能预支部署影响或普遍受害面。
- B 纯方法路线需要更强的方法独立性、适用边界与验证，单一 SAGA 实例不足以支撑通用框架。
- C 纯案例路线可以诚实成立，但不能充分利用已有 evaluator、bridge 和模型。
- D 可以用统一的观察接口和可控干预形成可复用分析步骤，同时把验证范围明确限制在 SAGA、有限策略子集和 fresh-contact 路径。

### 三个研究问题

1. **决策偏差：**在明确定义的有限策略语义下，哪些规则顺序使实现决策偏离规范？
2. **消费与传播：**Provider 与 Receiver 如何分别解释和消费同一个策略上下文中的 matcher 输出？偏差能否越过 OTK 释放、token 签发、消息接受边界？
3. **阻断与保真：**只修复指定消费者的 matcher，是否阻断被禁止的请求，并保留被允许的通信？范围明确的符号模型能否解释相同边界？

### 贡献的目标形态

1. 一套小范围、可复核的分析流程：独立规范求值、消费者事件关联、局部修复对照、符号性质检查。
2. 一个真实运行时案例：同一策略、身份和协议结构下，错误实现与局部修复产生不同的授权后果。
3. 一组边界明确的性质：有限 evaluator 的顺序不变性；fresh-contact 模型中的凭证来源、状态关联与规范授权性质。

“认证与保密不蕴含授权一致性”保留为研究动机。“bridge 带有来源哈希”保留为可信实验基础。二者都不应单独承担主要新颖性。

对比 Cedar 时，应承认独立规范与实现差分测试已有成熟先例。本文需突出额外检查的是**决策被消费者使用后的安全边界，以及选择性修复的传播差异**，并通过实验兑现这一点；不能声称首创跨层授权检查。[Cedar 官方规范与差分测试说明](https://github.com/cedar-policy/cedar-spec/blob/main/README.md)

## 2. Minimum Required Enhancements

工作量按一名熟悉仓库、能够部署本地服务的研究者估算；环境尚未实际部署验证。以下阶段共享脚手架，增量成本不应重复相加。核心路线约 12–15 人日；若环境或模型阻塞，应删除 P2、压缩 P1。

| 优先级 | 修改内容与可验收交付物 | 预计工作量 | 主要回应的攻击点 |
|---|---|---:|---|
| P0 | 真实 Provider 与双 Agent 的 fresh-contact 执行；合法凭证；记录 OTK、token、消息接受的完整链 | 3–4 人日 | “只有函数 bug”“后果全由模型预设” |
| P0 | 同一协议结构的 2×2 主对照、反序对照、Provider buggy / Receiver fixed 分离修复 | 1.5–2 人日，基于上述环境 | “修复只是关掉系统”“gate placement 仅是模型开关” |
| P0 | 建立消费者事件与模型事件映射；限定 fresh-contact；修正新模型中的 OTK 生命周期；统一控制模型模板 | 2–3 人日 | “符号 witness 与真实状态不一致”“跨场景不可比较” |
| P0 | 重写研究问题、贡献、Attack/Evaluation；更新 claim–evidence matrix；补充最接近的方法比较 | 2–3 人日 | “只有 bug report + ProVerif”“bridge 冒充 refinement” |
| P0 | 冻结依赖、运行配置、最小修复差异与结果包；进行一次干净环境重放 | 1 人日 | “结果无法复核”“实际运行了哪份 matcher 不清楚” |
| P1 | 支持域内 evaluator 顺序不变性的小证明；少量语义分类与变形测试 | 1–1.5 人日 | “reference evaluator 也是未经验证的自写 oracle” |
| P1 | Provider fixed / Receiver buggy 反向分离修复；零预算与无匹配边界检查 | 0.5–1 人日 | “阻断点不明确”“所有消费者被简化成一个布尔决策” |
| P1 | 独立复核事件投影和模型查询的非空性；必要时增加一个绑定破坏诊断 mutant | 0.5–1 人日 | “correspondence 由事件位置自动成立”“查询空真” |
| P2 | 第二种小型机制实例或第二系统，用于检查观察接口能否迁移 | 至少 3–5 人日，另立预算 | 方法通用性不足；三周内不作为交付承诺 |
| P2 | 现有条件成熟时再做机器检查的 evaluator 引理或轻量性能测量 | 1–3 人日起 | 增强形式可信度或工程完整性，不能替代运行时后果 |

P0 的形式模型工作是为了使保留在正文中的形式主张与实验一致。若时间不足，应收缩形式主张和模型范围，而不是保留有状态不一致的旧 witness 作为新实证的解释。

## 3. Consumer-Level Validation Plan

### 3.1 按实现确定执行顺序

当前 token 由 Receiver 生成，不能把 Provider 画成 token issuer。实际执行链应为：

```text
正常注册、安装 Receiver 所有者策略、准备合法 I/R 凭证
  → Initiator 请求 Provider /access
  → Provider 验证请求身份、执行 matcher
  → Provider 分配并释放 Receiver OTK
  → Initiator 与 Receiver 建立真实连接
  → Receiver 执行 matcher 预检查，完成身份、证书和签名检查
  → Receiver 取出并删除对应 OTK 私钥
  → Receiver 生成、存储并发送 token
  → Initiator 收到 token，携带 token 发送唯一测试消息
  → Receiver 验证 token，将消息交给 LocalAgent.run
```

代码入口：`experiments/hello_world.py` 已提供不使用 LLM 的双 Agent 通信。使用一个经现有 LocalAgent 接口接入的确定性接收后端：收到唯一测试 nonce 后记录内容，返回协议已有的任务结束标记。保留真实 Agent、Provider、数据库、证书、签名、OTK、token 与 socket 路径；不把授权返回值或 token 校验替换成 mock。

`saga/agent.py:631` 的实际后端调用及后端收到相同消息，是本实验的应用接受边界。token 已生成、socket 收到字节或普通“Received”日志均不能独立证明该边界。此结果支撑本地真实实现的消息投递，不等同于某个外部业务工具已被调用或部署系统被攻破。

使用专用、可丢弃的 MongoDB 实例与隔离凭证目录；仓库 README 明确要求 MongoDB 独占。固定成功部署后的依赖版本，不顺手升级整个项目。每次 fresh-contact 实验重建两端进程和状态，避免 `retrieve_valid_token` 缓存跳过 Provider 路径。

### 3.2 最小攻击者与运行假设

- I 是正常注册、持有自己合法证书与私钥的主动发起者；可以选择发送被策略禁止的联系请求与消息。
- Receiver 所有者安装固定策略；不授予攻击者修改 Receiver 策略、数据库或签发者密钥的能力。规则顺序是被测试的部署配置，不宣称攻击者必然能操纵该顺序。
- 保留原有证书与 Provider stamp 验证；不通过关闭 TLS、伪造信任根或手工注入 token 来制造成功。
- 第一阶段只研究一次新联系、固定策略、单条普通消息；不同时承担策略更新、token 撤销、并发配额或任意重连的结论。

### 3.3 事件与关联字段

所有事件附带 `case_id`、`run_id`、进程标识、本地递增序号、单调时钟、源码/配置版本。run_id 是实验元数据，不是密码学会话绑定。

| 边界 | 必须记录的事实 | 关联依据 |
|---|---|---|
| 注册与身份 | I/R AID、策略所有者、验证后的证书指纹、PAC 公钥指纹 | 实际注册和证书验证结果 |
| 策略上下文 | Provider DB 与 Receiver 本地各自读取的有序规则、策略哈希/版本 | 两份真实快照；预期相同也必须检查 |
| MatcherEval(P/R) | 消费者、实际输入 AID、原始预算、源码哈希、独立 spec 结果、消费者放行/拒绝 | Provider 和 Receiver 的两个独立求值事件 |
| ProviderRelease | 请求者、目标 Receiver、释放 OTK 公钥指纹、实际响应或失败码、相关配额状态 | DB 分配结果与 Initiator 收到的 OTK 相同 |
| ReceiverIdentityVerified | 经 stamp、证书与签名检查后确认的身份/PAC；关联先前声称的 AID | 实际连接与验证结果 |
| OTKConsumed | OTK 公钥指纹、消费前存在、消费后已删除 | Receiver 原有锁内的取出和删除位置 |
| TokenIssue/Send/Receive | Receiver、接收者 PAC、关联 OTK、加密 token 指纹；存储、发送、接收分别记录 | 同一个实际 wire token |
| TokenValidated | 呈交 token 指纹、对应 PAC、有效性结果、配额/有效期条件 | 真实 `token_is_valid` 与 active-token 状态 |
| MessageAccepted | Receiver、已验证 I、token 指纹、唯一消息 nonce/规范化摘要、实际后端收到的消息 | token 验证后真实后端调用与接收日志 |

特别注意：Receiver 在 `saga/agent.py:951` 先用 card 中声称的 AID 进行策略预检查，随后才做进一步身份验证。日志应区分 `claimed_i_aid` 与 `verified_i_aid`；拒绝分支可能没有后者，不能补造“已认证”的事件。

Provider 对负数与零都拒绝，Receiver 该预检查只拒绝负数。保留原始预算和每个消费者的解释。主实验用 `-1` 与 `10` 避开零边界；零预算作为 P1 独立检查，不悄悄改写原有接口语义。

token 指纹统一取解码后的实际加密 token 字节的 SHA-256，避免 Base64 文本规范化差异；OTK 指纹取规范化公钥字节。公开材料使用测试身份、公钥与指纹，不公开私钥或可用 token。现有详细日志可能含密钥材料，因此独立生成最小事件日志，并保留可复核的脱敏规则，不能把运行 stdout 直接当可发布附件。

### 3.4 防止 OTK 重用与假关联

1. 各实验单元均使用新注册状态、新 OTK、新 token 和新消息 nonce；重放的是完整工作流，不是重复发送上一轮消耗过的 OTK 报文。
2. 每次 token 签发必须对应同一次实际 OTK 消费；该 OTK 指纹在 Receiver 消费日志中只能出现一次。记录 Provider 释放、Initiator 收到与 Receiver 消费三端一致性。
3. 用真实 OTK/token/PAC 关联因果链；不能只靠“时间接近”或测试脚本分配的 session_id。
4. 使用静态策略窗口，核对 Provider 和 Receiver 快照；把动态策略更新明确留在范围外。
5. 观测钩子只记录已有分支结果，不增加放行条件、不创建本来不存在的 token、不将审计 policy_hash 加入线协议。
6. 为每一模型事件给出实现位置、触发条件、绑定字段和抽象掉的状态。日志检查器验证投影后的事件关联，不宣称自动提取了完整程序语义。

### 3.5 成功与失败的判据

- 正向成功：消息 nonce 确实进入 Receiver 后端；同一个实际 token 有签发、发送、接收、验证记录；OTK 单次消费；双方身份与策略上下文一致。
- 负向成功：发生明确的授权拒绝，客户端请求已结束、服务健康、日志完整，且下游边界未发生。单纯超时、缺日志、连接失败均记为 Inconclusive。
- Provider 拒绝时，Receiver 求值记为 NotReached。可以另有直接 matcher 单测，但不能把该单测冒充真实 Receiver 已执行。
- 每个核心单元至少进行 3 次全新状态重复，报告所有运行。该数字用于检查可重复性，不用于宣称真实漏洞发生率或统计普遍性。

## 4. Control Experiment Design

采用 2×2 主设计：matcher 版本 × 规范意图；再增加顺序与消费者位置干预。协议、消息流程、证书验证和 token 机制保持相同，密钥和随机量每次更新。

- `Pdeny = [I_uid:* → -1, * → 10]`。
- `Pallow = [I_uid:* → 10, * → 10]`。
- `reverse(Pdeny)` 仅改变顺序。
- Fixed 是对当前缺陷的最小补丁：选中更具体匹配时同时更新 `best_pattern`。不重写 matcher，不改预算解释，不声称解决任意模式或同分规则问题。

| 单元 | Provider / Receiver | 策略 | 待验证的实际结果 | 证明目的 |
|---|---|---|---|---|
| E1，P0 | Buggy / Buggy | Pdeny | spec deny；两个消费者实际错误放行；OTK 释放、token 签发、消息接受 | 真实偏差传播到应用边界 |
| E2，P0 | Fixed / Fixed | Pdeny | Provider spec deny / impl deny；Receiver NotReached | 最小修复阻断同一禁止请求 |
| E3，P0 | Buggy / Buggy | Pallow | spec allow / impl allow；消息接受 | 原版本正常允许路径可用 |
| E4，P0 | Fixed / Fixed | Pallow | spec allow / impl allow；消息接受 | 修复没有以拒绝所有请求制造“安全” |
| E5，P0 | Buggy / Buggy | reverse(Pdeny) | Provider deny；Receiver NotReached | 在不改代码时定位规则顺序的因果作用 |
| E6，P0 | Buggy / Fixed | Pdeny | Provider 释放 OTK；Receiver 预检查拒绝；不消费 Receiver OTK、不签发 token、不接受消息 | 真实接收端 gate 可截断传播；不是模型假设 |
| E7，P1 | Fixed / Buggy | Pdeny | Provider 拒绝；Receiver NotReached | 前置 gate 本身足以阻断本 fresh-contact 路径 |

E6 中 Provider 可能已经分配 OTK、消耗联系额度，而 Receiver 尚未消费 OTK。记录这一差别；不要将“没有消息接受”扩写成“没有任何状态副作用”。

四项用户要求分别由 E1 的 buggy、E2 的 fixed 与 D/D、E3/E4 的 A/A 覆盖。它们不是四个互斥概念，而是版本与策略意图两个维度。E6 比再加十个相似策略更有研究收益，因为它直接检验消费者位置。

每个进程启动时记录实际加载 matcher 的文件哈希；选择性修复要重启对应进程，不能仅在磁盘改文件后假定运行实例已更新。使用真正的版本差异，不用预设 allow/deny 返回值替代实现。

如实际结果与上述预测不同，先解释新的阻断条件或前置假设，再调整主张。不得绕过额外真实检查以强行得到 E1 成功。

## 5. Formal Model Improvement

### 5.1 首要工作：状态边界与统一模型

现有 turepass 模型使用全局固定 OTK 和复制进程；既有归档 witness 的 OTK/Receiver 实例关联不能直接代表实现中的单次消费。新模型应先限定一个 fresh-contact 执行：OTK 由持有它的 Receiver 实例取用一次，再进入 token 与消息处理阶段。若使用私有通道表示一次性状态，必须真正消费消息；ProVerif 持久 table 的 `get` 本身不是删除操作。

保持 bridge v1.1.1 与 S/D/G/B 历史归档不变。新建版本化的共同模型模板和新证据目录，支持 E1–E6 的实际决策输入。当前 `generate_model.py` 只接受 D/A，不适合作为全体控制的生成器；不要为了控制实验破坏其历史可重建性。

同一模板中只变更受证据约束的策略结果、消费者版本/行为参数；token 新鲜性、OTK 生命周期、身份验证、消息路径都保持一致。spec 事件作为观察性 oracle，不能以“必须 SpecDeny 才启动 Provider”的控制条件排除所有 allow 对照。

### 5.2 最有价值的 correspondence

令 `c` 表示固定上下文：I、R、策略版本/哈希、已验证 PAC 关联。`o` 是 OTK，`t` 是实际符号 token，`m` 是消息。以下是性质含义，不是可直接复制的 ProVerif 语法：

1. `ChatAccept(c,t,m) ⇒ previously TokenIssue(c,o,t)`。
   扩展既有 token 来源性质，将身份与上下文绑定起来。
2. `TokenIssue(c,o,t) ⇒ previously ProviderRelease(c,o) ∧ ReceiverPermit(c) ∧ IdentityVerified(c) ∧ OTKConsumed(c,o)`。
   只针对 fresh-contact 路径；每个前件必须能映射到真实执行分支。ReceiverPermit 指实现 gate 的通过，不等于规范授权。
3. `ChatAccept(c,t,m) ⇒ SpecAllow(c)`。
   这是直接表达授权目标的性质。预期 buggy Pdeny 下失败；fixed Pdeny 下接受不可达；Pallow 下接受可达且性质成立。

第三条必须配合 allow 接受可达性，否则 deny 场景中的成立可能仅为空真。不能像覆盖诊断一样永不发出 SpecAllow，再把所有授权性质失败当作实现攻击。

policy_hash 等可以作为分析用 ghost 注释，但不能成为实现没有检查的额外 guard。新模型如果靠额外身份检查或线协议字段消除了反例，就已经偏离这次实验对象。

同样，TokenIssue 与 ProviderRelease 的关系必须来自真实 OTK 分发假设和消息流，不能为了证明它而额外加入实现没有对应检查的 `get ProviderReleased` gate。若该关系只能由受控实验流程保证，就将其报告为该流程的事件一致性检查，不升级为任意攻击者下的安全定理。真实测试中的主动发起者与模型中的受控角色也要分别说明；不能将一次指定脚本的成功扩写成完整攻击者能力建模。

同一 token 可以合法承载多条消息，因此不要要求 ChatAccept 到 TokenIssue 的一对一 injective correspondence。需要唯一性时，把目标放在 OTK 消费与签发关系，并先明确其事件基数和 fresh-contact 范围。

### 5.3 小而有用的 evaluator 性质

建议证明：在当前闭合模式语法、合法预算、唯一最高 specificity 匹配或无匹配的域内，规则排列不会改变返回预算和 allow/deny：

`decision(eval(P,I)) = decision(eval(π(P),I))`，且返回 budget 相同。

排列后要同步调整位置字段；比较语义结果，不比较有意绑定原始顺序的 policy_hash、evaluation_fingerprint 或随位置编号的规则 ID。最高分并列仍维持 Unsupported，不为证明方便悄悄定义新政策。

论证可基于唯一最大元素的排列不变性，辅以扫描算法维持最大已见匹配的循环不变量。若只给算法数学证明，应明确没有机器验证 Python 源码。少量变形测试用于验证可执行 evaluator 与修复实现对这些性质的遵守，不能把测试称为定理。

测试按语义类别组织：无匹配、单匹配、specific allow 覆盖 wildcard deny、specific deny 覆盖 wildcard allow、无关规则插入、顺序置换；另列零预算、并列最高分、非法/不支持输入的分类。约 20–30 个有目的的实例已足够起步，不用随机堆积数千相似策略。

### 5.4 Bridge 应增加的保证

新增一个小型可执行检查器，验证：输入原始求值记录能重算 decision pair；角色、策略、OTK、token 关联一致；模板外结构未改变；未到达的消费者没有伪造观察；所有结论能定位到日志和模型查询。

它改善的是**输入与事件投影的可追溯性**，不是实现 refinement。ProVerif 分析模板描述的行为集合；真实执行见证及控制实验独立验证这条具体链。二者一致形成交叉证据，不能合并宣称“已验证 Python matcher / 完整服务正确”。

## 6. Paper Structure Revision

建议改为九节，按研究问题和证据类型组织，弱化历史 Stage 编号：

| 新章节 | 内容 | 现有章节处理 |
|---|---|---|
| 1 Introduction | 跨层问题、三个 RQ、经实验支持的三项贡献 | 重写 Introduction |
| 2 SAGA and Threat Model | 真实角色、token issuer、两类消费者、合法凭证攻击者、fresh-contact 范围 | 压缩 Background，整合威胁模型 |
| 3 Analysis Workflow and Decision Semantics | 有限语义、原始预算与消费者解释、事件接口、局部干预、保证边界 | 重写 Problem，抽取部分 Formalization |
| 4 SAGA Instantiation and Runtime Propagation | matcher 根因、最小策略、真实执行链、事件映射与成功 witness | 保留精简 Inconsistency；以实测内容替换当前 Attack 主线 |
| 5 Scoped Symbolic Analysis | OTK 状态、上下文绑定、共同模板、查询、抽象限制；小 evaluator 性质 | 重写 Formalization |
| 6 Evaluation | E1–E6 矩阵、E7/边界可选项、重复运行、实测与模型一致/不一致处、复现方式 | 重写 Evaluation |
| 7 Related Work | 授权语言/策略分析、规范与实现差分测试、协议验证、agent 安全的明确区别 | 针对 Cedar 等补强，不再大范围泛称他人忽略授权 |
| 8 Discussion and Limitations | 单系统、有限模式、静态策略、测试部署、非 refinement、可迁移部分 | 重写重点并压缩重复免责声明 |
| 9 Conclusion | 回答 RQ，概括已验证的消费者传播和阻断事实 | 按实际结果更新 |

Stage 1 作为“既有查询没有覆盖何种授权性质”的动机或附录。旧 gate 模型作为历史探索和对照背景。manifest、长哈希清单和模板重建细节放 artifact/附录；正文保留足以审查输入来源与转换范围的信息。

论文主结果表至少并列展示：spec budget、Provider 实测预算/结果、Receiver 实测预算/结果或 NotReached、OTK release/consume、TokenIssue、MessageAccepted、对应模型查询结果。避免用一个勾选格抹平这些不同边界。

## 7. Venue Impact

以下是完成指定增强后对研究形态的匹配判断，不是录用概率或当前征稿窗口。A/B/C 按独立增加该项理解；D 包含真实执行、对照、状态一致的模型及小语义性质。

| 增强方案 | 相关 workshop，如 STM | SACMAT / NordSec | CSF | CCS / USENIX Security |
|---|---|---|---|---|
| A：只增加统一 matcher/模型控制，仍无真实消费者链 | 有帮助，可形成完整短案例 | 有改善，但后果仍依赖抽象；不宜作为最佳投稿包 | 改善有限，没有新的基础性结果 | 改善很小 |
| B：增加真实 consumer replay | 明显增强实证完整性 | NordSec 的系统安全案例形态更可信；SACMAT 仍需清楚提炼授权分析增量 | 应用价值增加，不能代替形式贡献 | 影响证据前进，但单系统简单根因仍限制竞争力 |
| C：只增加有限 evaluator 语义性质 | 提升严谨性 | 提升 oracle 可信度；不能补上实际传播链 | 简单顺序不变性引理本身不足 | 增量很小 |
| D：三项全部完成 | 最完整、较匹配的短论文/专题案例候选 | 最值得投入的目标组合；SACMAT 强调授权方法与可复用洞见，NordSec 强调完整安全实证 | 仍需更实质的基础性洞见，不能仅因使用 ProVerif 就优先投 | 不建议把三周增强视为足够门槛；仍需更广影响或更深新机制 |

建议先按 **D 的核心部分**完成，形成可投 SACMAT/NordSec 方向的研究包；若 replay 或方法增量受限，收缩为匹配的 workshop 论文。不要为了某个顶会标签把三周计划扩展成通用框架或大型形式化项目。

这一判断与各方向官方范围相符：[SACMAT](https://www.sacmat.org/2026/index.php) 聚焦访问控制，[NordSec](https://www.nordsec.org/) 面向安全 IT 系统，[STM](https://www.ieee-security.org/Calendar/cfps/cfp-STM2026.html) 包括安全与信任管理。尤其 [CSF CFP](https://csf2026.ieee-security.org/cfp.html) 明确要求基础性安全研究，缺少这一层次可能不进入实质评审。引用这些页面用于研究定位，未据此推荐已过期投稿日期。

## 8. Do Not Recommend

| 不建议的增强 | 原因 | 替代 |
|---|---|---|
| 完整 Python→ProVerif refinement 或自动程序提取 | 成本可能超过整个案例，动态运行时、库、数据库与网络语义远超当前主张 | 可核对的事件映射、具体执行验证、有限 evaluator 性质 |
| 大规模多会话 ProVerif 模型 | 增加状态问题和求解负担，可能掩盖 OTK/配额抽象错误 | 单次 fresh-contact、小共同模板、明确状态边界 |
| 重写整个 matcher 或设计新 policy language | 引入新行为，破坏缺陷因果归因，也制造不必要维护范围 | 一处最小根因补丁，支持域内验证 |
| 大量随机 policy benchmark | 相似样例数量不能替代消费者传播与影响证据 | 按语义类别的小型矩阵与规则置换 |
| 接入 LLM、复杂工具链或 prompt-injection 攻击 | 引入不相关变量、成本与不稳定性，难以定位授权原因 | 确定性 LocalAgent 消息接收后端 |
| 为 bridge 构建通用编译器 | 通用性尚无任务需求，工程量不等于方法贡献 | 有限参数的统一模板和显式拒绝不支持输入 |
| 任意增加 correspondence 数量 | 很多查询由放置事件的位置直接成立；也可能要求错误的 injectivity | 三个有明确安全解释的性质及非空性对照 |
| 以哈希、manifest 数量或制图替代新增安全结果 | 提升复现便利但不回答传播和阻断问题 | 先拿到最小因果实验，再做一张事件链和一张结果矩阵 |
| 同时研究动态撤销、策略竞态、token 缓存、配额并发 | 每项都引入不同安全命题，三周难以做实 | 明确固定策略和 fresh-contact 范围，作为后续工作 |

## Recommended Roadmap

### Week 1：优先拿到真实消息接受与最小反事实

**Day 1–2：**隔离测试部署，正常注册两端，跑通 Pallow 的真实通信。接入确定性 LocalAgent，定义事件字段，记录已验证身份、策略、OTK、token 与消息 nonce。先证明环境能完成允许请求，再尝试偏差场景。

**Day 3–4：**运行 buggy Pdeny，确认原始 matcher 输出确被 Provider/Receiver 消费；建立 OTK 单次消费和 token 到消息接受的关联。完成最小 matcher 补丁，确保原始源码和 patched 源码都可识别、可重建。

**Day 5：**完成 E1–E4 的首轮，检查修复阻断禁止请求但保留允许请求；记录 E5 的顺序干预。每个正式单元补齐 3 次独立 fresh-state 运行。

**退出标准：**有一条可复核的真实禁止联系传播链，以及不靠关闭整个服务实现的修复对照。若到 Day 2 仍无法跑通允许路径，优先排查环境；若到 Week 1 仍无完整传播链，则按实际到达边界收缩论文，不能绕过检查强行生成攻击结果。

### Week 2：补齐消费者位置和形式解释

**Day 6：**完成 E6 分离修复；资源允许再做 E7。特别核对 OTK 已释放但 Receiver 未消费的状态。

**Day 7–8：**新建统一 fresh-contact 模型，解决 OTK 单次消费与上下文关联；建立实现—事件映射，运行三类性质及 allow 可达性控制。旧 bridge/归档保持冻结。

**Day 9：**给出有限 evaluator 顺序不变性论证与少量变形测试；预算不足时先保留精确定义和算法论证，不启动新的定理证明器学习项目。

**Day 10：**把运行日志投影、模型输入、模型查询与 E1–E6 逐行对照；对所有不一致作解释或收缩假设。模型求解调优若持续超过一天，先减少非核心会话和状态，不牺牲真实语义去换取通过。

**退出标准：**主结果矩阵没有将 NotReached 写成 Deny，没有跨会话 OTK 假关联，没有依赖不同协议模板的控制结果；形式结论严格限定于新模型。

### Week 3：把结果转化为投稿包

**Day 11–12：**按九节结构重写主线，优先 Introduction、Analysis Workflow、Runtime Propagation、Formalization、Evaluation。补齐 Cedar 等直接比较；以真实结果回答三个 RQ。

**Day 13：**独立从干净状态重放核心矩阵与模型；更新 claim–evidence matrix；检查每条实证、形式与范围主张的证据来源。失败的重放也进入问题清单，不能只保留成功日志。

**Day 14–15：**修复复现或论证缺口，压缩正文、整理匿名 artifact、选择最合适的下一投稿窗口。优先保住完整核心，不补第二系统、大模型或大 benchmark。

**最终交付物：**一套隔离实验入口、一个确定性消息后端、少量观测与关联检查、最小 matcher 补丁、一个共同符号模板、小型语义性质、统一结果矩阵，以及围绕这些结果重写的论文。三周的成功标准是形成可信、边界明确且可投稿的跨层案例分析，不是制造更多脚本或预支顶会录用。
