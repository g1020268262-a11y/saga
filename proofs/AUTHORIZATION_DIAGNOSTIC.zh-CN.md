# SAGA 授权覆盖诊断：第一阶段

> Current status update, 2026-09-19: Previous assessment outdated: matcher evidence was later confirmed through test-matcher. 本页保留 Stage 1 的历史诊断语境；关于当前四阶段审查状态、已确认的 matcher 实现级越权和下一步映射任务，见 [AUDIT_STATUS.md](AUDIT_STATUS.md)。

本次执行承接「saga」对话最后提出的任务：复制原通信模型，加入授权事件及 correspondence query，重跑原有性质，保存新增查询的实际反例轨迹。第二阶段的 matcher 形式化和业务消息接受模型尚未执行。

**已完成并实际运行验证：原通信模型的 3 条认证性质及 token 保密性仍为 `true`，新增授权 correspondence 为 `false`，且 ProVerif 成功重建了反例轨迹。** 这确认了本轮构造场景中的授权覆盖缺口；结论范围是 token 接收阶段，尚不包含 matcher 驱动的端到端消息越权。

## 1. 输入版本与修改边界

- 本地分支：`my-modification`。
- 基线提交：`7372111bea150e32cee390a616849316d2780bfc`。
- 验证器：本机 `D:\Proverif\proverif2.05\proverif.exe`，ProVerif 2.05。
- 开始修改前，Git 工作区干净。本轮新增模型和运行脚本未提交；结果绑定到基线提交与实际文件 SHA-256，不能说新增模型已绑定到某个提交。
- 原始 [agent_communication.pv](proverif/agent_communication.pv)、[registration.pv](proverif/registration.pv) 以及 Python 协议实现保持不变。
- 新文件 [agent_communication_authz.pv](proverif/agent_communication_authz.pv) 仅含五处 `AUTHZ-BEGIN / AUTHZ-END` 插入块；运行脚本机械检查：去掉这些块后，逐字节等于原通信模型。

本报告对模型和实现的判断以以上本地提交为准，不声称反映上游最新版本，也不重新评估论文全文。

## 2. 纠正对话中的角色和事件语义

原模型的数据流是 **PeerB 请求访问 PeerA，PeerA 签发 token，PeerB 验证并接收 token**。为保留对话中的事件名和参数位置，所有新事件统一采用 **issuer 在前、recipient 在后**。

| 事件 | 本轮定义 | 插入位置 |
|---|---|---|
| `PolicyAllow(issuer, recipient)` | issuer 的策略允许 recipient 联系自己 | 仅声明；本轮没有任何执行实例 |
| `PolicyDeny(issuer, recipient)` | issuer 的策略禁止 recipient 联系自己 | 主进程 `start()` 后，执行 `PolicyDeny(aid_A, aid_B)` |
| `TokenIssue(issuer, recipient, t)` | issuer 已签署并即将发送 token | PeerA 的 `EndAgentAuthA` 后、`out(c, ...)` 前 |
| `Accept(issuer, recipient, t)` | recipient 解密 token 并验证 issuer 的签名成功 | PeerB 的 `EndAgentAuthB` 后 |

因此 `PolicyDeny(aid_A, aid_B)` 在这里表示 **禁止 PeerB → PeerA**。不能同时把它解释为“禁止 PeerA → PeerB”，否则会把策略方向与 token 流向混淆。`Accept` 也不能解释为“PeerA 已接受 PeerB 提交的业务消息”：原模型在 token 交付后结束，没有 token 提交、有效期、quota 或业务消息处理流程。

新增性质为：

```prolog
query issuer: bitstring, recipient: bitstring, tok: bitstring;
    event(Accept(issuer, recipient, tok))
    ==> event(PolicyAllow(issuer, recipient)).
```

其含义是“每次成功接收 token，都应存在此前针对同一 issuer/recipient 的允许事件”。它是 token 接收阶段的授权诊断，不是完整的消息访问授权定理。

## 3. 实测结果

运行时间：2026-09-16 20:38:34 至 20:50:03（Asia/Shanghai）。三个 ProVerif 进程均以退出码 `0` 完成。

| 模型 | 实测结果 | 耗时 |
|---|---|---|
| 原注册模型 | 3 个事件可达；1 条认证 correspondence 为 `true` | 0.102 秒 |
| 原通信模型 | 7 个事件可达；3 条认证及 token 保密性为 `true` | 334.595 秒 |
| 授权扩展模型 | 全部 11 条基线结果逐条保留；新增授权 correspondence 为 `false` | 353.713 秒 |

关键实际输出如下；全部结果见 [verification-summary.txt](evidence/authz-stage1-20260916T123834944479Z/verification-summary.txt)。

```text
RESULT event(EndAgentAuthB(x,y,k)) ==> event(EndAgentAuthA(x,y,k)) is true.
RESULT event(EndAuthA(x,y,k)) ==> event(EndProviderAuthA(x,y,k)) is true.
RESULT event(EndAuthB(x,y,k)) ==> event(EndProviderAuthB(x,y,k)) is true.
RESULT not attacker_p6(token[]) is true.
RESULT event(Accept(issuer,recipient,tok)) ==> event(PolicyAllow(issuer,recipient)) is false.
```

注意：可达性查询会输出 `RESULT not event(...) is false.`，表示对应事件可达，并不是认证失败。注册与通信的认证事件均有可达性检查，避免把未执行协议下的 vacuous truth 当作成功认证证据。

### 新增查询的实际反例

[authorization-trace.txt](evidence/authz-stage1-20260916T123834944479Z/authorization-trace.txt) 是扩展模型完整 stdout 第 **5247–5698 行**的摘录，共 452 行，保留 Horn 推导、重建执行轨迹和最终 `RESULT`。文件末尾明确包含 `A trace has been found.`，不是 `cannot be proved` 或仅有未重建的抽象推导。

重建轨迹中的关键事件原文为：

```text
event PolicyDeny(aid_A,aid_B) at {11}
...
event TokenIssue(aid_A,aid_B,token) at {65} in copy a_5
...
event TokenIssue(aid_A,aid_B,token) at {65} in copy a_4
...
event Accept(aid_A,aid_B,token) at {91} in copy a_8 (goal)
```

这些行在摘录文件中分别位于 **366、428、436、448 行**。花括号内是 ProVerif 进程位置编号，不是源文件行号。

按该轨迹归纳，主进程先声明禁止 PeerB 联系 PeerA，CA/Provider 的注册认证流程继续执行；Provider 在 `{46}` 输出 PeerA 的证书与 OTK 等材料；PeerA 在 `{65}` 记录 token 签发并在 `{66}` 输出签名和密文；PeerB 在 `{87}` 接收 token、解密及验签后，于 `{91}` 记录接收成功。整个模型没有任何 `PolicyAllow(aid_A, aid_B)` 执行实例。

这是一条求解器重建的轨迹，包含多份复制进程和两次 `TokenIssue`；上面的归纳不声称轨迹最短，也不把它改写为严格单会话轨迹。全局 token 和复制进程均来自基线，不能由这两次事件额外推出部署中的 token 重放漏洞。

## 4. 如何理解本轮反例

本轮 `PolicyDeny` 是人为设置的实验前提，没有连接到任何 `if`、Provider 授权判断或执行阻断条件。`PolicyAllow` 只被声明，从未发生。

所以，只要原协议可以运行到 `Accept`，新增 correspondence 就会失败；即使删除 `PolicyDeny`，缺失 `PolicyAllow` 的问题仍然存在。反例用于确认原模型的认证和保密性质无法约束这个新增的授权语义。它不能单独证明 Python matcher 导致了协议越权，也不是一个新的密码学攻击。

原模型使用公开网络信道和符号密码学，默认主动网络攻击者可以调度、转发、构造其可推导的消息。固定的两个 peer 在模型内仍执行既定进程；本轮没有加入恶意注册 Agent、私钥泄露或策略管理员被攻破的能力。沿用的 `token` 是全局私有常量，不是每会话新生成的 token；沿用的认证性质为普通 `event` correspondence，不是 `inj-event`。

本轮保留原有密码学方程、阶段、复制进程、密钥及消息字段，未尝试解决原模型的其他抽象限制。

因此，`not attacker_p6(token[]) is true` 与接收端获得 token 并不冲突：PeerB 是模型内的角色，接收 token 不等于网络攻击者可推导 token。

## 5. 独立检查 Python matcher 候选缺陷

直接调用当前 [contact_policy.py](../saga/common/contact_policy.py) 中未修改的 `check_rulebook`、`aid_specificity` 和 `match`，得到：

```text
AID = alice@example.com:agent
rules = [
    {"pattern": "alice@example.com:*", "budget": -1},
    {"pattern": "*",                   "budget": 10}
]

check_rulebook(rules)              = True
specificity of the two patterns   = [70, 0]
match(rules, AID)                  = 10
match(reverse(rules), AID)         = -1
```

函数文档写的是“最具体规则对应的 budget”；按它自身的 specificity 计算，两个顺序下均应选到具体 deny，即 `-1`。实际代码在更新 `budget` 后没有更新 `best_pattern`，因此这个样例确实受到规则顺序影响。

当前调用位置也已检查：

- [provider.py](../saga/provider/provider.py) 第 444–451 行调用 `match`，分别拒绝负数和零；后续还要求目标存在、OTK 可用、counter 未耗尽等条件，不能把正 budget 直接等同于完成访问。
- [agent.py](../saga/agent.py) 第 951 行在接收端再次调用同一 matcher；该处拒绝 `< 0`。在其余身份、签名、OTK 等检查成功之后，第 1094 行才生成 token。

实测脚本和输出位于本次证据目录的 `policy-matcher-sanity.py`、`policy-matcher-sanity.json`。这只是函数级复现，没有启动 Provider、Agent 服务或外部网络攻击。它没有被用于驱动本轮 ProVerif 的策略事件；两份证据尚未组合成端到端证明。

## 6. 复现与证据

在仓库根目录执行：

```powershell
python proofs\run_authz_diagnostic.py
```

也可显式指定验证器：

```powershell
python proofs\run_authz_diagnostic.py --proverif D:\Proverif\proverif2.05\proverif.exe
```

脚本按顺序运行注册基线、通信基线、授权扩展；每次建立新的 UTC 时间戳证据目录。它保留完整 stdout/stderr，提取 `RESULT`，比较扩展前后的 11 条基线结果，并单独提取新增 query 的原始推导和轨迹。已有但内容不同的扩展模型不会被覆盖。

本次目录：[authz-stage1-20260916T123834944479Z](evidence/authz-stage1-20260916T123834944479Z/)。

| 文件 | 用途 |
|---|---|
| [verification-summary.txt](evidence/authz-stage1-20260916T123834944479Z/verification-summary.txt) | 三个模型的全部实际 `RESULT` |
| [authorization-trace.txt](evidence/authz-stage1-20260916T123834944479Z/authorization-trace.txt) | 新增授权查询对应的原始输出摘录 |
| [agent_communication_authz.stdout.txt](evidence/authz-stage1-20260916T123834944479Z/agent_communication_authz.stdout.txt) | 扩展模型完整运行输出 |
| `agent_communication.stdout.txt` | 原通信模型完整运行输出 |
| `registration.stdout.txt` | 原注册模型完整运行输出 |
| `*.stderr.txt` | 原始 stderr；空文件也保留 |
| [manifest.json](evidence/authz-stage1-20260916T123834944479Z/manifest.json) | 基线提交、分支、前后 Git 状态、命令、验证器版本、耗时和 SHA-256 |
| `policy-matcher-sanity.py` / `.json` | 独立 matcher 函数级复现及其源文件 SHA-256 |
| `model-additions.diff` | 新模型相对原通信模型的五处纯新增差异 |

运行 manifest 的 `post_run_git_status` 记录的是求解结束时的工作区状态，报告后续完成编辑的情况应以最终 Git 状态为准。模型和运行日志的哈希可独立复核。

运行脚本记录的 13 项检查全部通过，包括基线结果保留、授权反例重建、运行期间模型与脚本哈希不变，以及 Git HEAD 不变。原模型和 Python 实现没有修改，也没有提交或推送本次新增文件。

## 7. 下一阶段需要增加的证据

按原对话的分阶段边界，本轮到授权诊断和反例交付为止。下一阶段需要把“最具体规则”作为规范语义，把当前 matcher 的顺序行为作为实现语义，分别连接到 Provider 的 OTK 发放以及接收端的 token 签发条件。应保留允许路径作为非空性对照，并检查修正 matcher 后，禁止路径被阻断、允许路径仍可达。

策略规则及其顺序应作为明确的配置前提；不能通过默认赋予攻击者任意改写受害者策略的权限来制造越权结论。

若要声称实际消息越权，还必须增加 token 提交和接收端消息接受事件，并建立它们与代码检查的对应关系。当前 `Accept` 不能直接承担这一结论。
