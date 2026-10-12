# 中文阅读副本

> 本文件是英文投稿稿件的中文阅读副本，仅供作者核对和理解。
> 英文稿为正式投稿版本和唯一权威版本。
> 如中英文表述存在歧义，以英文稿为准。

# SAGA 中一处授权决策不一致的形式化与实证分析

## 摘要

身份认证和 token 保密性并不能保证接收方授权。SAGA 中依赖规则顺序的 matcher 不一致导致规范拒绝而实现许可。授权诊断暴露出证明覆盖缺口。受控 consumer validation 到达 token 签发和存储；在固定符号分歧下，ProVerif 报告 `ChatAccept` 可达，同时要求先前发生 `TokenIssue` 的非单射对应关系成立。

**关键词：** 授权（authorization）、访问控制、形式化验证、AI agent、ProVerif

## 1. 引言

基于 LLM 的 agent 正日益使用外部工具和服务 [1, 2]。身份认证确认身份；接收方授权决定已识别身份的 agent 是否可以通信 [3]。SAGA [4] 结合了经过认证的身份、联系策略和访问控制 token。其既有认证和 token 保密性结果并未建立 token 签发遵循接收方预期策略这一结论。

授权覆盖诊断暴露出这一证明覆盖缺口。它促使我们进行代码检查和受控 matcher 测试，并揭示一处依赖规则顺序的决策不一致。我们考察其通过 consumer 的传播，以及固定符号场景下的后果。

我们的贡献包括：（1）SAGA 参考模型中的授权证明覆盖缺口；（2）依赖规则顺序的生产 matcher 不一致及其在受控条件下通过 consumer 传播至 token 签发和存储；（3）固定 specification-deny/implementation-allow 分歧下的形式化后果分析，表明符号事件 `ChatAccept` 可达，同时要求先前发生 `TokenIssue` 的对应关系为真。

### 相关工作

既有工作研究了授权语言与策略语义 [5, 6]，以及策略验证和变更影响分析 [7]。SPKI [3] 和 Macaroons [8] 提供基于凭证和基于能力的授权抽象。ProVerif 和 Tamarin 支持符号协议验证 [9, 10]。我们考察一处具体的策略求值错误及其 consumer 后果，在 SAGA 的模型假设下补充其协议保证。

## 2. 授权决策不一致

### 工作流与策略语义

SAGA 的 Provider 按接收方的有序策略处理联系请求；该策略将身份模式映射为整数预算。Provider 和接收方分别调用生产 matcher：Provider 以求值结果控制一次性密钥（OTK）的释放，接收方在 token 签发前重新检查授权。

SAGA 第 IV-D.1 节 [4] 规定选择最具体的匹配规则；`aid_specificity()` 为模式评分。正预算许可请求，负预算拒绝请求。我们考虑固定策略和有效身份，排除具体程度相同的冲突与零预算。

### 根因与观测

被测试的生产 matcher 是 `saga/common/contact_policy.py` 中的 `match()`。Artifact 将归档的 matcher 观测绑定到固定上游源代码的来源记录。[^repo] 其 `best_pattern` 初始值为 `None`，具体程度为 $-1$。更具体的匹配规则会更新预算，却不会更新 `best_pattern`。后续匹配仍与 $-1$ 比较，使得具体程度更低的通配符也能覆盖预算。在记录的案例中，`aid_specificity()` 对 `alice@example.com:*` 的评分为 $70$，对 `*` 的评分为 $0$；其预算分别为 $-1$ 和 $10$。

[^repo]: 复现 artifact：`github.com/g1020268262-a11y/SAGA-Authorization-Analysis-Artifact`。

**表 1　两种规则顺序下的规范预算与 matcher 预算。**

| 规则顺序 | 规范预算 | Matcher 预算 |
|---|---:|---:|
| 先具体拒绝，后通配符允许 | $-1$ | $10$ |
| 先通配符允许，后具体拒绝 | $-1$ | $-1$ |

独立的有限规范求值器在表 1 的两种顺序下均选择具体拒绝。先具体拒绝、后通配符允许时，规范预算为 $-1$，matcher 预算却为 $10$；颠倒顺序则恢复拒绝。这证实该案例存在依赖规则顺序的实现层面授权绕过。

## 3. 形式化授权分析

### 覆盖诊断

归档的 ProVerif 2.05 诊断扩展了 SAGA 的参考模型。它保留原有的认证和 token 保密性结果，但报告新增的、要求 `Accept` 之前发生 `PolicyAllow` 的对应关系为假。`Accept` 表示 token 接收和验证，与 `ChatAccept` 不同。`PolicyAllow` 未连接到策略执行；这构成授权证明覆盖缺口。该诊断既不执行 Python matcher，也不识别其缺陷。

### 模型与假设

Decision Bridge 将经过检查的 specification-deny/implementation-allow 决策对转移到固定符号场景。ProVerif 将这一决策对作为假设；它不执行 Python 或生产 matcher，也不发现该缺陷。Bridge 既不是通用的代码到模型翻译器，也不是 Python-to-ProVerif 精化证明。不同执行之间只通过授权决策和 token 生命周期事件进行比较。

发起方拥有有效的已注册身份，遵循规定的符号对等方进程，并且不能改变接收方的固定策略。因此，这一可达性并非任意攻击者可达性声明。Provider 和证书颁发机构（CA）受到信任，密码学检查有效，私钥未泄露。一条私有符号信道抽象了经过认证且保密的传输。

在符号接收方中，`TokenIssue`$(R,I,t)$ 发生在 `ActiveToken` 存储接收方 $R$、发起方 $I$、加密 token $t$ 和 $I$ 的公开访问控制密钥之后，且在传输之前。对于私有信道消息 $m$，`ChatAccept`$(R,I,t,m)$ 仅在检查固定身份以及一条匹配 $R$、$I$、$t$ 和 $I$ 的发送方公钥的 `ActiveToken` 记录之后发生。

### 授权条件与结果

Artifact 归档了 ProVerif 2.05 模型和原始输出。运行报告在固定分歧下 `ChatAccept` 可达；与此分开，它验证了以下非单射 token 来源对应关系：

\[
 \mathsf{ChatAccept}(R,I,t,m)
 \Longrightarrow \mathsf{TokenIssue}(R,I,t)
\]

其中，$R$ 是接收方和 token 签发方，$I$ 是发起方。先前的签发必须匹配 $R$、$I$ 和加密 token $t$。对于静态接收方策略，另一个不同的理想授权条件是：

\[
 \mathsf{TokenIssue}(R,I,t)
 \Longrightarrow \mathsf{Allow}_{\mathrm{spec}}(P_R,I),
\]

其中，$P_R$ 是 $R$ 的联系策略，$\mathsf{Allow}_{\mathrm{spec}}$ 表示按其预期语义得到的许可，而不是 matcher 的返回结果。第二个公式是期望条件，既不是已执行的 ProVerif 查询，也不是已证明的定理。

对于记录的先具体拒绝、后通配符允许案例，该对应关系与预期策略拒绝同时存在。因此，token 来源一致性并不蕴含符合策略的签发。`ChatAccept` 见证轨迹包含签发；不存在独立的 `TokenIssue` 可达性查询。

## 4. Consumer 侧传播验证

归档的源文件哈希将 matcher、Provider、接收方以及 token 相关密码学代码绑定到固定上游基线。Harness 使用已签名的注册材料、本地证书和内存传输，驱动生产 `/access` 路由及接收方处理程序，并保留生产密码学检查。两个 consumer 都调用原始 matcher；wrapper 记录其结果并将其原样返回。Fixture 既不预设授权决策，也不预设 token 状态。

### 案例与对照

两个 consumer 使用相同的策略。D/A 将具体拒绝（$-1$）置于通配符允许（$10$）之前；A/A 将两个预算均设为 $10$，D/D 则颠倒 D/A 的顺序。两个字母分别表示规范决策与观测到的实现决策。每个案例均以全新状态和一个 OTK 运行一次。A/A 到达 token 发送和存储；D/D 返回 HTTP 403，不释放 OTK、不改变状态，也从未到达接收方，因此接收方拒绝仍未测试。

**表 2　分歧 D/A 案例的生产 consumer 结果。**

| 证据点 | 分歧案例结果 |
|---|---|
| 规范 | 拒绝（$-1$） |
| Provider matcher | 允许（$10$） |
| Provider `/access` | HTTP 200；释放 OTK |
| 接收方 matcher | 允许（$10$） |
| 接收方 | 消耗 OTK |
| 端点 | token 已签发并存储 |

表 2 确认在规范拒绝的情况下仍发生 token 签发和存储：一个 token 被生成、发送并存储到 `active_tokens`。没有发送应用消息：边界 stub 在原始 `receive_conversation` 处理程序执行前拦截该调用。

## 5. 范围与结论

记录的 SAGA 不一致在受控执行中传播至 token 签发和存储。在相应的固定符号分歧下，`ChatAccept` 可达，而要求先前发生 `TokenIssue` 的对应关系成立。Token 来源一致性不能替代符合预期策略的接收方授权。

证据覆盖一个已记录的案例和所测试的策略。它既不建立任意策略正确性，也不建立任意攻击者攻击利用或已部署攻击利用。只有符号模型到达消息接受。

## 参考文献

正文中的引用编号与英文投稿稿件一致；以下 bibliographic entries 保留英文。

1. L. Wang, C. Ma, X. Feng, Z. Zhang, H. Yang, J. Zhang, Z. Chen, J. Tang, X. Chen, Y. Lin, W.X. Zhao, Z. Wei, and J. Wen, “A survey on large language model based autonomous agents,” *Frontiers of Computer Science*, vol. 18, no. 6, p. 186345, 2024.
2. E. Debenedetti, J. Zhang, M. Balunović, L. Beurer-Kellner, M. Fischer, and F. Tramèr, “AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents,” *Advances in Neural Information Processing Systems 37 (NeurIPS 2024)*, pp. 82895–82920, 2024.
3. C. Ellison, B. Frantz, B. Lampson, R. Rivest, B. Thomas, and T. Ylonen, “SPKI certificate theory,” RFC 2693, RFC Editor, Sept. 1999. Experimental.
4. G. Syros, A. Suri, J. Ginesin, C. Nita-Rotaru, and A. Oprea, “SAGA: A security architecture for governing AI agentic systems,” *Network and Distributed System Security (NDSS) Symposium*, Internet Society, Feb. 2026.
5. M.Y. Becker and P. Sewell, “Cassandra: Distributed access control policies with tunable expressiveness,” *5th IEEE International Workshop on Policies for Distributed Systems and Networks (POLICY)*, 2004.
6. M.Y. Becker, C. Fournet, and A.D. Gordon, “Design and semantics of a decentralized authorization language,” *20th IEEE Computer Security Foundations Symposium (CSF)*, pp. 3–15, IEEE, 2007.
7. K. Fisler, S. Krishnamurthi, L.A. Meyerovich, and M.C. Tschantz, “Verification and change-impact analysis of access-control policies,” *27th International Conference on Software Engineering (ICSE)*, pp. 196–205, 2005.
8. A. Birgisson, J.G. Politz, Ú. Erlingsson, A. Taly, M. Vrable, and M. Lentczner, “Macaroons: Cookies with contextual caveats for decentralized authorization in the cloud,” *Network and Distributed System Security Symposium (NDSS)*, Internet Society, 2014.
9. B. Blanchet, “Modeling and verifying security protocols with the applied pi calculus and ProVerif,” *Foundations and Trends in Privacy and Security*, vol. 1, no. 1–2, pp. 1–135, 2016.
10. S. Meier, B. Schmidt, C. Cremers, and D. Basin, “The TAMARIN prover for the symbolic analysis of security protocols,” *Computer Aided Verification (CAV)*, Lecture Notes in Computer Science, vol. 8044, pp. 696–701, Springer, 2013.

---

**TRANSLATION CLAIM DRIFT: NONE**
