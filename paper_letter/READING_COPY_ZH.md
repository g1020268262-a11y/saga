# 中文阅读副本

> 本文件是英文投稿稿件的中文阅读副本，仅供作者核对和理解。
> 英文稿为正式投稿版本和唯一权威版本。
> 如中英文表述存在歧义，以英文稿为准。

# SAGA 中一处授权决策不一致的形式化与实证分析

## 摘要

身份认证并不保证通信符合接收方的联系策略。我们识别出 SAGA 中一处依赖规则顺序的 matcher 缺陷，将规定的拒绝转化为许可。受控 Provider/接收方执行确认其传播至 token 签发和存储。在与证据关联的符号场景中，ProVerif 报告 `ChatAccept` 在给定条件下可达，同时要求先前发生 `TokenIssue` 的对应关系成立，从而区分了 token 来源与策略遵从。

**关键词：** 授权（authorization）、访问控制、形式化验证、AI agent、ProVerif

## 1. 引言

基于 LLM 的 agent 正日益使用外部工具和服务 [1, 2]。身份认证确认身份，而接收方授权决定已识别身份的 agent 是否可以通信 [3]。仅凭身份认证和 token 保密性，不能确定通信符合接收方预期的联系策略。

SAGA [4] 使用联系策略和访问控制 token 管理已注册 agent 之间的通信。其策略 matcher 实现接收方的授权决策。我们研究的问题是：接收方预期策略与其实现之间的不一致，是否会允许本应被拒绝的 agent 通信，以及这一许可能够沿协议传播到哪个阶段？

我们识别出一处依赖规则顺序、违反 SAGA 最具体规则语义的 matcher 缺陷，导致规范拒绝而实现许可。授权覆盖诊断识别出缺失的证明义务，但并未发现该实现缺陷。对生产 Provider 和接收方代码路径的受控执行确认，许可传播至 token 签发和存储。在相应的、与证据关联的固定符号分歧下，ProVerif 报告 `ChatAccept` 可达，同时要求先前发生 `TokenIssue` 的对应关系成立。实际应用消息接受尚未得到证实。

我们的贡献包括：（1）识别并解释 SAGA 中一处具体的授权决策不一致；（2）使用 ProVerif 分析其在给定条件下的符号后果；（3）通过受控生产代码执行，验证其传播至 token 签发和存储。

### 相关工作

既有工作研究了授权语言与语义 [5, 6]，以及策略验证 [7]。SPKI [3] 和 Macaroons [8] 提供相关的授权抽象。ProVerif 和 Tamarin 支持符号协议分析 [9, 10]。我们的分析将一处具体的策略实现不一致，与其 consumer 后果和符号后果关联起来。

## 2. 授权决策不一致

### 预期授权语义

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

独立的有限规范求值器在表 1 的两种顺序下均选择拒绝。先具体拒绝、后通配符允许时，规定的 $-1$ 变为观测到的 $10$；颠倒顺序则恢复拒绝。该反例证实了记录策略中的实现级授权决策不一致，许可结果依赖规则顺序。

## 3. 形式化授权分析

### 授权性质与 ProVerif 查询

Token 来源一致性并不能确定通信符合接收方的预期策略。对于静态接收方策略，期望的授权条件为：

\[
 \mathsf{TokenIssue}(R,I,t)
 \Longrightarrow \mathsf{Allow}_{\mathrm{spec}}(P_R,I),
\]

其中，$R$ 是接收方和 token 签发方，$I$ 是发起方，$P_R$ 是接收方的联系策略。$\mathsf{Allow}_{\mathrm{spec}}$ 表示按预期策略语义得到的许可。该条件既不是已执行的 ProVerif 查询，也不是已证明的定理。

归档的 ProVerif 2.05 模型在固定的规范拒绝／实现许可分歧下评估两个查询。查询使用源模型的变量名；结果行缩写事件参数。

**Query 1：消息接受可达性。**

```proverif
query receiver: bitstring, sender: bitstring,
      tok: bitstring, msg: bitstring;
  event(ChatAccept(receiver,sender,tok,msg)).
```

```text
RESULT not event(ChatAccept(...)) is false.
```

否定事件结果为 false，确立了 `ChatAccept` 在固定符号场景中可达。

**Query 2：Token 来源对应关系。**

```proverif
query receiver: bitstring, sender: bitstring,
      tok: bitstring, msg: bitstring;
  event(ChatAccept(receiver,sender,tok,msg))
  ==> event(TokenIssue(receiver,sender,tok)).
```

```text
RESULT event(ChatAccept(...))
  ==> event(TokenIssue(...)) is true.
```

经验证的非单射对应关系要求先前发生同一接收方、发起方和加密 token 对应的 `TokenIssue`。两项结果共同表明：尽管预期策略拒绝，符号消息接受仍可达，同时 token 来源一致性仍成立。接受见证包含 token 签发；未执行独立的 `TokenIssue` 可达性查询。

SAGA 既有的认证和 token 保密性验证未建立这一授权义务。归档的覆盖诊断报告新增的授权对应关系为假，因为 `PolicyAllow` 未连接到策略执行。该诊断涉及的 `Accept` 表示 token 接收和验证，而不是 `ChatAccept`。它并不识别 Python matcher 缺陷。

### 场景与协议解释

一个有限的 bridge 将归档的 matcher 观测与独立求值的策略决策进行比较，检查源码证据，并将经过验证的 Deny/Allow 决策对实例化到固定 ProVerif 场景。这是场景重构，而不是 Python-to-ProVerif 精化。

符号发起方拥有有效的已注册身份，遵循规定的对等方进程，并且不能改变接收方的固定策略。Provider 和证书颁发机构（CA）受到信任，私钥未泄露，一条私有符号信道抽象了经过认证且保密的传输。

在模型中，`TokenIssue`$(R,I,t)$ 发生在相应的 `ActiveToken` 条目存储之后、token 发送之前。`ChatAccept`$(R,I,t,m)$ 发生在消息接收以及对发送方身份、已存储的接收方、发起方、token 和发送方密钥绑定的检查之后。

ProVerif 假定经过检查的授权分歧；它不执行 Python matcher。所得可达性以符号模型及其假设为条件，不构成任意攻击者或已部署攻击利用的声明。受控实现验证到达 token 签发和存储，但不执行应用消息接受。

## 4. Consumer 侧传播验证

该验证考察错误许可是否能通过生产 consumer 检查并到达 token 签发和存储。受控 harness 驱动 Provider 的 `/access` 路由和接收方握手，包括 OTK 释放和消耗。归档的源文件哈希将 matcher、consumer 和 token 相关密码学代码绑定到固定上游基线。

已签名的注册材料、本地证书和内存传输提供 fixture，同时生产密码学检查保持有效。两个 consumer 都调用原始 matcher；wrapper 记录其结果并将其原样返回。Fixture 既不预设授权决策，也不预设 token 状态。

### 对照设计

A/A、D/A 和 D/D 标签中的两个字母分别表示规范决策与观测到的 matcher 决策，而不是 Provider 和接收方的结果。在每个案例内，两个 consumer 使用同一策略。A/A 将两条规则的预算均设为 $10$，作为正常许可路径的对照。D/A 将具体拒绝（$-1$）置于通配符允许（$10$）之前，产生观测到的授权不一致。D/D 颠倒这一顺序，恢复拒绝并检验 Provider 侧阻断。每个案例均以全新状态和一个 OTK 运行一次；D/D 案例未到达接收方。

**表 2　分歧 D/A 案例的生产 consumer 结果。**

| 证据点 | 分歧案例结果 |
|---|---|
| 规范 | 拒绝（$-1$） |
| Provider matcher | 允许（$10$） |
| Provider `/access` | HTTP 200；释放 OTK |
| 接收方 matcher | 允许（$10$） |
| 接收方 | 消耗 OTK |
| 端点 | token 已签发并存储 |

A/A 到达 token 发送和存储。在 D/A 中，表 2 确认：尽管规范拒绝，两个生产 matcher 产生的许可仍到达 token 签发和 `active_tokens` 存储。一个 token 被生成、发送并存储。D/D 返回 HTTP 403，不释放 OTK、不改变状态，仅建立 Provider 侧阻断；接收方拒绝仍未测试。

这些观测建立的是受控 consumer 传播，而不是应用消息接受。没有发送应用消息：边界 stub 在原始 `receive_conversation` 处理程序执行前拦截该调用。

## 5. 范围与结论

对于记录的 SAGA 策略，依赖规则顺序的匹配会授权一个被预期最具体语义拒绝的 agent。由此产生的许可通过受控生产 consumer 到达 token 签发和存储；相应的固定符号模型允许 `ChatAccept` 发生，同时要求先前发生 `TokenIssue` 的对应关系成立。身份认证和 token 来源一致性不足以建立通信符合接收方预期授权策略这一结论。

这些发现限于记录的案例、所测试的策略、fixture 和符号假设。它们既不建立任意策略正确性，也不建立 Python-to-ProVerif 精化关系、任意攻击者攻击利用或已部署攻击利用。Consumer 执行止于 token 签发和存储；消息接受仅属于符号模型。

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
