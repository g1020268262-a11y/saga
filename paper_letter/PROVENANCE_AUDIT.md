# Production provenance and Letter revision audit

审计日期：2026-10-01。开始时分支为 `my-modification`，HEAD 为
`f34a4de06b69e425c99cc0ea3106acb841b4fdee`，工作区干净。
先完成只读 Phase A，再进行 Phase B 论文修改。本轮没有运行 matcher、consumer
或 ProVerif 实验；以下执行结果均来自既有归档。

## 1. Phase A: Production provenance

### 上游及历史受测版本

- SAGA v2 原文将实现指向 [gsiros/saga](https://github.com/gsiros/saga)。
- 本地 upstream remote 同样指向该地址。实时 `git ls-remote upstream HEAD refs/heads/main`
  返回 `7372111bea150e32cee390a616849316d2780bfc`；[上游提交页面](https://github.com/gsiros/saga/commit/7372111bea150e32cee390a616849316d2780bfc)
  也确认该提交存在，标题为 `Add Apache V2 License`。
- Study repository 为 [g1020268262-a11y/saga](https://github.com/g1020268262-a11y/saga)。
  Matcher 历史观测的 `base_commit` 就是上述上游提交，不是本轮 HEAD。
- Consumer 历史运行 HEAD 是 `8cc5dd7ae8b11acb209914d1631c0688ac68aec6`，
  并非 `7372111`。`7372111` 是它的祖先。该运行的工作区含论文修改及当时未跟踪的
  consumer harness，不能称为一次完整干净 checkout 的执行。
- 对下面四个相关生产文件逐一比较：上游 `7372111` 的 Git blob、consumer HEAD
  的 Git blob、当前源码（仅统一 CRLF/LF）完全相同。另对当前原始文件字节计算 SHA-256，
  与 consumer manifest 的执行前、后源码哈希分别一致。Harness、fixtures、runner
  当前字节也与当时记录一致。因此本轮检查的 harness 绑定到了该历史运行。
- `git log 7372111..HEAD --` 对这四个文件没有修改记录。未发现研究分支修改关键 matcher。
  该结论仅覆盖核验的基线、文件及历史路径，不声称所有 SAGA 版本或整个研究仓库未修改。

| 生产文件 | 历史执行前后及当前文件 SHA-256 |
|---|---|
| `saga/common/contact_policy.py` | `2e37f59651acc31ed9fad8436462faabcb49c52ab3032eccd1529cd72870aa97` |
| `saga/provider/provider.py` | `097fd8ed76756d61336689259f496144484f8fa72d7d040dd2df90eedc934c6e` |
| `saga/agent.py` | `94bebf70df4f76e55c0bb8a54c5f29b7fa688ead197ece18f8ac9dec8edae8d5` |
| `saga/common/crypto.py` | `dca1a5fa145afbf419b1a71af068e0b98a3ac533a929862d12e023f5c8436b7b` |

Git blob 使用 LF，Windows 执行文件使用 CRLF；例如 matcher 的 LF blob SHA-256 是
`c95b91e2d9bfa99d562423c4356e8e2532b202fe33e4d84da4b8059abe8e60b5`。
归档字节哈希与规范化后的源码内容比较是两个独立检查，未混用。

### Matcher 及 Table 1

实际定位：`saga/common/contact_policy.py:137` 的 `match()`。
`aid_specificity()` 从第 108 行开始：`None` 得 -1，全局 `*` 得 0。
第 148 行将 `best_pattern` 初始化为 `None`；第 153–154 行仅更新预算而未更新该变量。
后续匹配仍与 -1 比较，因此 wildcard 的 0 也能覆盖先前预算。

`proofs/evidence/authz-stage1-20260916T123834944479Z/` 中的
`policy-matcher-sanity.json`、`.py` 和 `manifest.json` 共同给出历史观测、执行方法、
源码版本及哈希。JSON 和脚本的归档哈希均核验通过，未执行该脚本。
记录身份是 `alice@example.com:agent`，模式是 `alice@example.com:*` 与 `*`。
前一模式的分数 70 来自 17 个 UID 字面字符各计 4，加上 nametag 通配符权重 2；
不是通用常数，也不是完整 exact AID。两种顺序记录返回 10 与 -1，Table 1 未改。

### Consumer 路径与 fixtures

检查文件：`proofs/consumer_validation/harness.py`、`fixtures.py`、`run_phase1.py`，
以及 `proofs/consumer_validation/evidence/20260926T070021921746Z-d64c8064/` 的
manifest、各 case 的 input/result/events。该成功归档的全部 16 个 artifact 哈希通过。
它记录 A/A、D/D、D/A 三个 case completed、expectations_met=true；不是本轮重新运行。

| 环节 | 实际执行或替换边界 |
|---|---|
| Provider `/access` | Flask `test_client` 调用真实路由；本地 MongoDB 执行真实查询、counter 更新及 OTK 弹出。没有 mock `/access` 响应。 |
| Provider/receiver matcher | `Recorder.matcher` 包装原 `policy.match`，调用后记录并原样返回。没有伪造预算。 |
| Receiver | 真实 `Agent.handle_i_agent_connection` 读取受控握手、调用 matcher，并执行所经过的证书/签名检查。 |
| OTK release/consumption | Provider 路由真实返回并移除 OTK；receiver 查找并删除本地 OTK，计算共享密钥。初始 OTK 由 fixture 配置。 |
| Token generation/storage/send | 真实 `Agent.generate_token` 及 crypto 逻辑生成 token；`agent.py:1103` 写 `active_tokens`，第 1111 行调用真实 `Agent.send`，由内存连接收集序列化输出。 |
| Registration | 不走注册服务；fixture 用真实签名材料直接填入 Provider user/agent 记录，并以这些材料构造 Agent。 |
| Certificate acquisition | 本地生成 CA，跳过 CA 下载构造；替换两处 `get_SAGA_CA` 及 `Agent.get_provider_cert`。生产签名/验证方法保留。不是验证真实 PKI 部署。 |
| TLS | Flask fixture 提供 `SSL_CLIENT_CERT`；`MemoryConnection` 提供 recv/sendall/getpeercert 等接口。没有真实 TLS 握手或网络传输验证。Agent 字节 framing 仍执行。 |
| Application boundary | `Agent.receive_conversation` 被 cutoff stub 替换。原 handler 到达调用点时执行 stub，记录已发送/存储状态及空 timing 后返回；原始方法从未调用、内部逻辑未执行。 |
| Local agent | `ForbiddenLocalAgent.run` 会计数并报错；既有结果显示未调用。不执行 LLM 或工具。 |

初始 `active_tokens` 为空。Harness 的 `case['impl_budget']` 只用于期望值检查，
不作为 matcher 返回值，也不决定是否进入 receiver：后者由真实 HTTP status 是否为 200 决定。
`MemoryConnection.sendall` 仅记录生产输出，cutoff 仅观察 token 是否已存在；两者均不写最终
token 状态。D/A 的归档事件依次记录两个 matcher 返回 10、HTTP 200、OTK release、
receiver send、boundary 时 sent/stored=true；随后验证解密内容与存储内容一致。
D/D 在 Provider 拒绝，没有执行 receiver rejection，结论保持该限制。

**审计结论：**支持“指定基线中相关生产源码未改，受控调用其授权及 token 路径”的描述。
不支持“整个实验环境未修改”“执行完整原始端到端协议”或“真实部署攻击”的描述。
未发现要求停止论文修改的关键冲突。

**证据边界：**上述是源码和自记录历史工件的一致性审计，不是独立重跑或外部执行证明；
未验证真实 registration、PKI/TLS 部署、应用消息接受、任意策略或所有后续版本。
也不把 2026 年上游基线等同于 SAGA v2 发表时的原始 release。

## 2. Phase A: Formal evidence

- 版本：归档记录及版本输出为 **ProVerif 2.05**。
- 核心源模型：`proofs/proverif/agent_communication_authz_chat_turepass.pv`，
  SHA-256 `e6ffbd5acebd3aa1f05ea7942c4f7eb23d4469357c7a01fea082de2b2e8ab121`。
- 历史运行 revision：`830ba37faae41788b10f3a9cf7bfc68426d52d26`。
- 实际受检生成模型：`proofs/evidence/authz-bridge-turepass-20260922T111657792091Z/agent_communication_authz_chat_bridge.pv`，
  SHA-256 `20113b40cc0974a5de514a72b4630aa149bc6f2b79cdca5574d6de7c795b1329`。
- 同目录 manifest 的全部 11 个 artifact 哈希通过；当前核心模型哈希与当时 source_model 哈希相符。
- 核心源码第 246–251 行只有两个 query；生成模型对应第 254–259 行：
  `event(ChatAccept(receiver,sender,tok,msg)) ==> event(TokenIssue(receiver,sender,tok))`，
  以及 `event(ChatAccept(receiver,sender,tok,msg))`。没有 standalone TokenIssue reachability query。
- 原始结果文件为同目录 `proverif-stdout.txt`，摘要在 `verification-summary.txt`：
  correspondence `is true`；`not event(ChatAccept(...)) is false`，即 ChatAccept 可达。
- 核心第 133–135 行在 `ActiveToken` 插入之后、发送 token 之前产生 TokenIssue。
  第 139–143 行从私有通道接收消息，检查 `sender = aid_B` 并匹配 receiver/sender/token/key
  的 ActiveToken 条目后产生 ChatAccept；参数 t 是加密 token。与正文事件解释一致。
- 第 262–263 行预置 `ScenarioSpecDeny` 和 `ScenarioImplAllow`。故 specification denial、
  symbolic acceptance 可达及来源 correspondence 为真在既有模型内共存。
  新增解释仅指出 token 来源关联不足以建立策略合规，没有增强 query、攻击者或模型 claim。
- 本轮未运行 ProVerif，也未对 Python–模型建立 refinement。

## 3. Phase B: 修改前后

| 位置 | 修改前 | 修改后 |
|---|---|---|
| Section 1 后果概述 | 重复摘要及 Section 3 的具体 formal 结果 | 简写受控 token 终点和独立条件模型，保留实证不达 message acceptance |
| Section 1 Related Work | 罗列策略语义/分析和 ProVerif | 用原有四条参考文献区分策略语言/验证、SAGA 自身协议分析与本文具体实现偏差/消费者后果；不推翻原模型假设下保证 |
| Section 2 provenance | `revision 7372111 of the study repository` | 说明该 SHA 是 upstream SAGA 和 matcher-test 基线，相关 matcher 未改；脚注同时定位 upstream 和 study copy |
| Section 3 | 未注明版本/工件定位，形式结果意义分散 | 注明 ProVerif 2.05 和研究仓库 proofs/evidence 下 2026-09-22 authz-bridge-turepass 运行；展开 Certificate Authority；明确来源一致性不等于策略合规 |
| Section 4 Environment | 泛称 fixtures 替换服务，停止位置含混 | 区分 consumer HEAD 与 upstream 基线；列出实际路径、fixture 外部依赖及原 matcher 返回值保留；说明 cutoff 拦截原 conversation 调用 |
| Section 4 controls/result | A/A、D/D 坐标未明确，重复逐项描述 Table 2 | 定义 specification/observed implementation 坐标；删重复结果叙述及 LLM/tool 枚举，保留实证终点和 D/D 限制 |
| Section 5 | 既有 scope/conclusion | 不修改 |

Major Concern 的修复依据是 Phase A 的版本/文件内容/执行记录匹配和 runtime patch 检查，
而不是把 study repository 改称“production”作为文字替代。
正文仅对已核实的 matcher、Provider、receiver、token crypto 来源作限定描述。

Reference [3] 仅补页码 `196--205`，不新增文献。
[ACM SIGMOD 托管的 ICSE 2005 目录](https://sigmod.org/publications/dblp/db/conf/icse/icse2005.html)
列出该页段；[出版者提交的 Crossref 记录](https://api.crossref.org/works/10.1145/1062455.1062502)
确认题目/会议及起始页 196；[作者提供的正文](https://www.cs.cmu.edu/~mtschant/pubs/fkmt-verif-change-impact-xacml.pdf)
为 10 页且支持文中关于 policy verification/change impact 的比较。ACM DL 页面本次未能读取。
作者、单位、membership、通信邮箱继续保持原 TODO，没有虚构。

## 4. 格式及最终核验

- 使用未修改的 `paper_letter/build.ps1`：pdflatex、bibtex、pdflatex、pdflatex，更新 main.pdf。
- Summary 47 words（以空白分词，连字符/斜线复合词为一词），原文未改。
- Keywords 5 个；正文引用仍为 4 条。标题、main.tex、macros、IEICE v2.3 class/style 未改。
- 最终 2 页：Table 1 第 1 页；Table 2、唯一 formal display、Section 5、References 均第 2 页。
- LaTeX errors=0；undefined references=0；undefined citations=0；duplicate labels=0；
  overfull boxes=0；BibTeX warnings=0。
- 保留会员状态空值 warning、`OT1/qhv/m/sl` 字体替代 warning 和 `Non-PDF special ignored` 提示。
  未通过填写虚假会员状态消除 warning。实际 PDF 页面为 210 × 280 mm。
- 已渲染检查两页，表格完整、公式和参考文献正常、无跨栏溢出/遮挡或新增空白页。
  首次构建末条参考文献溢至第 3 页；删去与 Table 2 重复的 prose 后恢复两页。
  运行定位脚注采用可自然换行的目录/日期说明；没有调整字体、边距、行距或添加 negative vspace。
- Table 1、Table 2 和唯一 display equation 的源码与修改前完全一致。
- `git diff --check` 通过。

## 5. Git 范围

预期提交文件：Section 1–4 的四个 tex、`paper_letter/references.bib`、
`paper_letter/main.pdf` 和本报告 `paper_letter/PROVENANCE_AUDIT.md`。

未修改 production code、historical evidence、ProVerif model/query、bridge、
consumer validation implementation、build.ps1、Section 5 或官方模板。
没有新增或执行研究实验，没有新增 query/model/property/policy case，也没有扩大安全结论。
最终 commit SHA 由完成报告后的 Git 提交生成，见本轮交付回复。
