# 中文阅读副本

> 本文件是英文投稿稿件的中文阅读副本，仅供作者核对和理解。
> 英文稿为正式投稿版本和唯一权威版本。
> 如中英文表述存在歧义，以英文稿为准。

# SAGA 中一处授权决策不一致的形式化与实证分析

## 摘要

我们分析 SAGA 中的一处授权决策不一致（authorization decision inconsistency）。一项形式化覆盖诊断（coverage diagnostic）首先表明，已有的认证和 token 保密性性质并未建立所需的授权对应关系（correspondence）。随后，实现分析识别出一个依赖规则顺序的 matcher 缺陷，其决策沿生产 consumer（消费方逻辑）传播至 token 签发和 token 存储。在固定分歧场景（fixed divergence）下，ProVerif 报告 `ChatAccept` 可达；与此分开，ProVerif 验证了一个要求先前发生 `TokenIssue` 的非单射对应关系（non-injective correspondence）。

**关键词：** 授权（authorization）、访问控制、形式化验证、AI agent、ProVerif

## 1. 引言

基于 LLM 的自主 agent 正日益借助外部工具和服务开展工作 [1, 2]。SAGA [3] 使用联系策略和访问控制 token 来授权已注册 agent 之间的通信。仅有认证并不能建立授权 [4]；在 SAGA 中，接收方的联系策略决定是否许可 [3]。

对 SAGA 参考通信模型进行的授权覆盖诊断保留了已有的认证和 token 保密性结果，但报告新增的授权对应关系为假。这暴露出一个缺失的证明义务：已验证的性质并未建立策略授权。该诊断既不执行 Python matcher，也不识别其缺陷；它促使我们检查策略求值和执行机制。该检查识别出生产 matcher 中一个依赖规则顺序的不一致。

该缺陷并不局限于错误的整数返回结果。在受控执行中，规范拒绝转化为实现许可，该许可通过生产 Provider 和接收方 consumer，并到达 token 签发和存储。在一个独立的后果模型中，相应的固定分歧场景允许 `ChatAccept` 发生，同时其要求先前发生 `TokenIssue` 的对应关系仍为真。这些证据层共同刻画了一条授权绕过路径（authorization-bypass path）。实证路径止于 token 签发和存储；只有符号模型到达消息接受。

我们的贡献包括：（1）诊断 SAGA 参考模型中的授权证明覆盖缺口（authorization proof-coverage gap）；（2）识别依赖规则顺序的生产 matcher 不一致，并验证其通过生产 consumer 传播至 token 签发和存储；以及（3）表明在相同的固定 Spec-Deny/Impl-Allow 分歧场景下，符号事件 `ChatAccept` 可达，而要求先前发生 `TokenIssue` 的对应关系仍为真。

### 相关工作

既有工作研究了分布式授权语言与策略语义 [5, 6]，以及策略验证和变更影响分析 [7]。SPKI [4] 和 Macaroons [8] 为基于凭证和基于能力的授权提供了相关抽象。符号协议分析器 ProVerif 和 Tamarin 支持协议层面的安全验证 [9, 10]；SAGA 使用 ProVerif 分析其通信协议 [3]。近期研究也关注自主 LLM agent 的安全评估 [2]。与这些工作不同，我们考察 SAGA 所规定的规则选择语义与其实现之间的一处具体偏差，并追踪该偏差对下游 consumer 的影响，从而补充 SAGA 在其模型假设下提供的协议层保证。

## 2. 授权决策不一致

### 工作流与策略语义

发起方通过 SAGA 的 Provider 请求建立联系。接收方的有序策略将身份模式映射为整数预算。Provider 和接收方分别使用生产 matcher 对发起方进行求值。Provider 以求值结果为门控条件决定是否释放一次性密钥（OTK）；接收方则在签发 token 之前重新检查其策略。

对于固定策略和有效身份，SAGA 第 IV-D.1 节 [3] 规定，应选择最具体的匹配规则；实现使用 `aid_specificity()` 为模式评分。正预算许可请求，负预算拒绝请求。我们不考虑具体程度相同的冲突、求值期间的策略变化或零预算。

### 根因与观测

被测试的生产 matcher 是 `saga/common/contact_policy.py` 中的 `match()`。随附 artifact 记录了固定的上游源代码来源，并将归档的 matcher 观测与该源代码绑定。[^repo] 其 `best_pattern` 初始值为 `None`，对应的具体程度为 $-1$。具体程度更高的匹配规则会更新预算，却不会更新 `best_pattern`。因此，后续匹配规则仍与 $-1$ 比较，使得即使具体程度更低的通配符规则也能够覆盖预算。在记录的案例中，`aid_specificity()` 对 `alice@example.com:*` 的评分为 $70$，对 `*` 的评分为 $0$；二者的预算分别为 $-1$ 和 $10$。

[^repo]: 复现 artifact：`github.com/g1020268262-a11y/SAGA-Authorization-Analysis-Artifact`。

**表 1　两种规则顺序下的规范结果与生产 matcher 结果。**

| 规则顺序 | 规范预算 | Matcher 预算 |
|---|---:|---:|
| 先具体拒绝，后通配符允许 | $-1$ | $10$ |
| 先通配符允许，后具体拒绝 | $-1$ | $-1$ |

一个独立的有限规范求值器在表 1 的两种顺序下均选择具体拒绝。当具体拒绝规则位于通配符允许规则之前时，规范以预算 $-1$ 拒绝，但生产 matcher 返回 $10$ 并予以许可。相反顺序返回规范所规定的拒绝，由此证实该行为依赖规则顺序。在所测试案例中，这构成实现层面的授权绕过（authorization bypass）：规范拒绝，而生产 matcher 许可。这些 matcher 调用本身并不能建立下游 token 状态、消息接受或已部署攻击利用。

## 3. 形式化授权分析

### 覆盖诊断

我们的分析始于对 SAGA 参考通信模型的授权覆盖诊断。归档的 ProVerif 2.05 扩展保留了原有的认证和 token 保密性结果，而新增的、要求 `Accept` 之前发生 `PolicyAllow` 的对应关系为假。这里的 `Accept` 表示 token 的接收和验证，而不是之后的 `ChatAccept`。该诊断没有将其策略事件连接到执行门控；它暴露出一个缺失的授权证明义务，既不执行 matcher，也不识别 Python 缺陷。

### 后果模型

后续符号模型固定了已记录的分歧：规范拒绝，而观测到的实现许可。ProVerif 将这些事实作为假设；它不运行 Python 或生产 matcher，不发现该不一致，也不建立实现精化关系（implementation refinement）。

### 模型假设

发起方拥有有效的已注册身份，遵循规定的符号对等方进程，并且不能改变接收方的固定策略。因此，这些假设下的可达性（reachability）并非任意攻击者可达性声明。Provider 和证书颁发机构（CA）受到信任，密码学检查有效，私钥保持未泄露；一条私有符号信道对经过认证且保密的传输进行抽象。

在符号接收方中，`TokenIssue`$(R,I,t)$ 发生在一条 `ActiveToken` 记录存储接收方 $R$、发起方 $I$、加密 token $t$ 以及 $I$ 的公开访问控制密钥之后，但发生在发送 $t$ 之前。对于私有信道消息 $m$，`ChatAccept`$(R,I,t,m)$ 仅在以下检查之后发生：固定身份检查，以及一条同时匹配接收方 $R$、发起方 $I$、所提交 token $t$ 和与 $I$ 关联的发送方公钥的 `ActiveToken` 记录检查。

### 查询与结果

随附 artifact 归档了 ProVerif 2.05 的运行、生成的模型和原始输出。该运行报告在固定分歧场景下 `ChatAccept` 可达。与此分开，它报告以下非单射对应关系为真：

\[
 \mathsf{ChatAccept}(R,I,t,m)
 \Longrightarrow \mathsf{TokenIssue}(R,I,t)
\]

该对应关系要求：对于 `ChatAccept` 所使用的同一接收方 $R$、发起方 $I$ 和加密 token $t$，先前已经发生 `TokenIssue`。这建立的是 token 来源一致性，而不是对预期策略的遵从。在固定分歧场景下，该对应关系因此可以与规范拒绝同时成立。`ChatAccept` 见证轨迹包含 token 签发；不存在独立的 `TokenIssue` 可达性查询。

实证执行与符号执行仅在授权决策和 token 生命周期事件层面进行比较；本文未建立对象层面的精化关系。只有符号执行到达消息接受。

### 授权绕过路径

跨越这些证据层，相关结果刻画了一条授权绕过路径：成文策略拒绝发起方，生产 matcher 予以许可，该决策通过 Provider 和接收方处理传播至 token 签发和存储，而相应的固定符号分歧场景允许 `ChatAccept` 发生。实现端点与符号端点仍属于彼此分离的证据层。我们使用“授权绕过”描述这一策略执行失败，而不是声称存在任意攻击者攻击利用或已部署攻击利用。

## 4. Consumer 侧传播验证

### 目的

该实验验证授权绕过路径的实现部分。它沿着已记录的 Spec-Deny/Impl-Allow 案例，通过生产 Provider 和接收方 consumer 追踪至 token 签发和存储；它不执行应用消息接受。

### 环境

归档的 consumer 运行记录了 matcher、Provider、接收方以及 token 相关密码学代码的源文件哈希。这些相关源代码与分析中使用的固定上游基线一致。测试 harness 驱动生产 Provider 的 `/access` 路由和接收方处理程序，使执行从 matcher 求值一直到 `active_tokens` 存储。该 harness 提供已签名的注册材料、本地证书和内存传输，同时保留生产密码学检查。Matcher wrapper 调用原始 matcher，记录其结果，并将该结果原样返回；fixture 既不预设授权决策，也不预设由此产生的 token 状态。一个边界 stub 在原始 `receive_conversation` 执行之前拦截该调用。

### 案例与对照

Provider 和接收方使用相同的策略。分歧 D/A 案例将具体拒绝规则（$-1$）置于通配符允许规则（$10$）之前。对照案例为 A/A（两条规则都以 $10$ 允许）和 D/D（预算为 $10$ 的通配符允许规则位于预算为 $-1$ 的具体拒绝规则之前）。每个案例都以全新状态和一个 OTK 运行一次。首字母和第二个字母分别表示规范决策与观测到的实现决策，而不是 Provider 和接收方的结果。A/A 到达 token 发送和存储；D/D 返回 HTTP 403，不释放 OTK，也不改变状态，并且从未到达接收方，因此接收方拒绝仍未测试。

**表 2　分歧案例沿生产 consumer 路径的传播；未执行消息接受。**

| 证据点 | 分歧案例结果 |
|---|---|
| 规范 | 拒绝（$-1$） |
| Provider matcher | 允许（$10$） |
| Provider `/access` | HTTP 200；释放 OTK |
| 接收方 matcher | 允许（$10$） |
| 接收方 | 消耗 OTK |
| 端点 | token 已签发并存储 |

### 结果与证据

表 2 表明，两个 matcher 均返回 $10$，OTK 被释放并消耗，并且一个 token 被生成、发送并存储在 `active_tokens` 中。该端点不包括消息接受：没有发送应用消息，也未调用原始 `receive_conversation`。

## 5. 范围与结论

我们的分析从形式化授权覆盖诊断出发，推进到一个具体实现缺陷，再推进到其授权绕过后果。该诊断表明，已有的认证和 token 保密性结果并未建立所需的策略授权义务。实现检查随后识别出生产 matcher 对成文的最具体规则优先语义（most-specific semantics）的违反。在受控执行中，由此产生的决策到达 token 签发和存储；在相应的固定符号分歧场景下，即使要求先前发生 `TokenIssue` 的对应关系仍为真，`ChatAccept` 依然可达。因此，token 来源一致性可以与规范拒绝同时存在。

证据覆盖一个已记录的 SAGA 案例和所测试的策略。它并不建立任意策略正确性、Python--ProVerif 精化关系、任意攻击者攻击利用或已部署攻击利用。实证执行止于应用消息接受之前；该端点只属于符号模型。

## 参考文献

正文中的引用编号与英文投稿稿件一致；以下 bibliographic entries 保留英文。

1. L. Wang, C. Ma, X. Feng, Z. Zhang, H. Yang, J. Zhang, Z. Chen, J. Tang, X. Chen, Y. Lin, W.X. Zhao, Z. Wei, and J. Wen, “A survey on large language model based autonomous agents,” *Frontiers of Computer Science*, vol. 18, no. 6, p. 186345, 2024.
2. E. Debenedetti, J. Zhang, M. Balunović, L. Beurer-Kellner, M. Fischer, and F. Tramèr, “AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents,” *Advances in Neural Information Processing Systems 37 (NeurIPS 2024)*, pp. 82895–82920, 2024.
3. G. Syros, A. Suri, J. Ginesin, C. Nita-Rotaru, and A. Oprea, “SAGA: A security architecture for governing AI agentic systems,” *Network and Distributed System Security (NDSS) Symposium*, Internet Society, Feb. 2026.
4. C. Ellison, B. Frantz, B. Lampson, R. Rivest, B. Thomas, and T. Ylonen, “SPKI certificate theory,” RFC 2693, RFC Editor, Sept. 1999. Experimental.
5. M.Y. Becker and P. Sewell, “Cassandra: Distributed access control policies with tunable expressiveness,” *5th IEEE International Workshop on Policies for Distributed Systems and Networks (POLICY)*, 2004.
6. M.Y. Becker, C. Fournet, and A.D. Gordon, “Design and semantics of a decentralized authorization language,” *20th IEEE Computer Security Foundations Symposium (CSF)*, pp. 3–15, IEEE, 2007.
7. K. Fisler, S. Krishnamurthi, L.A. Meyerovich, and M.C. Tschantz, “Verification and change-impact analysis of access-control policies,” *27th International Conference on Software Engineering (ICSE)*, pp. 196–205, 2005.
8. A. Birgisson, J.G. Politz, Ú. Erlingsson, A. Taly, M. Vrable, and M. Lentczner, “Macaroons: Cookies with contextual caveats for decentralized authorization in the cloud,” *Network and Distributed System Security Symposium (NDSS)*, Internet Society, 2014.
9. B. Blanchet, “Modeling and verifying security protocols with the applied pi calculus and ProVerif,” *Foundations and Trends in Privacy and Security*, vol. 1, no. 1–2, pp. 1–135, 2016.
10. S. Meier, B. Schmidt, C. Cremers, and D. Basin, “The TAMARIN prover for the symbolic analysis of security protocols,” *Computer Aided Verification (CAV)*, Lecture Notes in Computer Science, vol. 8044, pp. 696–701, Springer, 2013.

---

**TRANSLATION CLAIM DRIFT: NONE**
