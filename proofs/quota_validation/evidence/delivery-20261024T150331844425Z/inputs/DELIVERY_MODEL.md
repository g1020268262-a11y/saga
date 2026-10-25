# 双端配额与消息交付扩展模型

模型：[SagaQuotaDelivery.tla](SagaQuotaDelivery.tla)。原来的 `SagaQuota.tla`、中文注释副本和历史证据保留不变。

## 本次补上的范围

原模型从 A 已具备处理消息的条件开始，重点验证共享额度检查和扣减的并发间隙。本模型从两端均保存同一个 token 的初始额度开始；没有顺序前缀。每个连接最多执行 `MaxRequests` 轮普通请求，不同连接可以交错。配置不预定哪一轮中断。

一轮基本流程：

```text
A 连接入口检查
  → B 本地 token 检查
  → B 发送函数正常返回（请求帧进入交付过程）
  → B 扣本地额度，然后等回复

交付过程可与 B 的本地扣减交错：
  A 收到并解析请求 → A 检查 → A 扣额度 → A 后端调用 → A 发送回复
  → B 收到回复 → 开始下一轮
```

`BSendReturn` 和 `BDebit` 分开，因此 A 也可以先处理请求、B 后扣减。A 的 `ACheck` 和 `ADebit` 保持分离；扣减不增加新的余额守卫，原来的并发超额执行仍被允许。

## 状态表示

| 状态 | 对应含义 |
|---|---|
| `senderRemaining` | B 的 `received_tokens[token]` 本地余额 |
| `receiverRemaining` | A 的 `active_tokens[token]` 本地余额 |
| `bpc[c]`、`apc[c]` | 连接 c 上两端各自的程序位置 |
| `link[c]` | 连接是否开放、是否有待处理请求帧／回复帧、发生哪类故障 |
| `counts[c]` | 成功发送返回、B 扣减事件、A 准入、A 后端调用和 B 收到回复的观察计数 |
| `faultCount` | 环境注入的连接故障数，受 `MaxFaults` 限制 |

`senderDebits` 计数扣减语句执行事件，不保证每次都实际减少一单位：余额到零时原生代码会截断。候选“未准入却消耗余额”性质使用真实消耗量 `InitialQuota - senderRemaining`。

`link` 与 `counts` 使用 TLA+ 函数／记录表示。观察计数不作为新的协议消息字段，没有加入 ACK、重试、去重、退款或对账动作。

## 故障模型：与正常传输明确区分

1. `RequestAbort`：B 发送调用已正常返回，A 尚未解析该请求，连接中止，未交付的应用帧不可再读。B 仍会执行已经排定的本地扣减；随后双方读失败退出。
2. `ResponseAbort`：A 已经准入当前请求，但 B 尚未收到响应时中止。A 可能继续后端调用，再遇到回复发送错误。双方可能已经各扣一次，B 的失败并不意味着 A 未处理。
3. `SendError`：发送调用在任何完整请求帧可读之前报错。原生 513 行抛错，尚未到 518–519 行，因此 B 没有本地扣减。这只是发送异常的一种分支，不能推广为“所有 sendall 报错均未送达”。

这些是显式环境动作。正常连接保持有序、无重复、单连接最多一个未完成请求；没有把普通 TCP 分片丢失建模成任意、静默、不可恢复的应用消息丢失。实际丢包通常由传输层重传。本次没有真实 TLS 故障注入或测量自然触发概率。

Python API 资料：[socket.sendall](https://docs.python.org/3.12/library/socket.html#socket.socket.sendall)、[SSLSocket](https://docs.python.org/3.12/library/ssl.html#ssl-sockets)。这里采用“本地函数正常返回”作为事件，A 是否解析／准入由独立动作表示；这不是应用层接收确认。

## 源码对应与抽象限制

| 模型动作 | `saga/agent.py` 依据 |
|---|---|
| 两端初态 | 424–425、871–874、1102–1103：存储解密后的 token 元数据 |
| `AEnter` / `ARejectEntry` | 1120–1128：复用 token 的入口检查 |
| `BCheck` / `BStopQuota` | 505–509、392–413：B 的有效性和本地余额检查 |
| `BSendReturn` | 513、447–456：序列化并调用 sendall，正常返回 |
| `BDebit` | 518–519：成功发送后单独获取锁、截断扣减 |
| `AReceive` / `AReadError` | 470–480、586–591、595：收帧、解析；错误返回后退出 |
| `ACheck` / `AReject` | 598–601、348–381：逐消息检查；失败后连接关闭 |
| `ADebit` | 604–605：再次加锁扣减，无余额重检查 |
| `ABackend` / `AReplyReturn` / `AReplyError` | 631–643：后端路径和回复发送；发送异常可退出处理器 |
| `BReceiveResponse` / `BReceiveError` | 535–540、542–567：等待回复、失败退出，没有额度恢复 |
| `StopAtBound` | 有限输入环境在 N 轮普通交互后关闭连接；不是源码新增的业务终止条件 |
| 三类故障动作 | 新增的环境假设，不是把故障触发条件当作已证明的原生执行 |

消息和响应均为普通非终止内容，token 不被删除／重新签发，非配额元数据稳定有效。每连接请求数最多 100，使原生查询次数检查不影响建模的后端路径。B 的本地 LLM 计算、A 后端计算及普通响应路径折叠为观察步骤；A 已读到请求、B 的 sendall 尚未返回的更早交错未展开。没有完整 TLS、超时、部分帧 EOF 循环、重连、应用重试、重复业务效果或身份伪造模型。

## 性质及其解释

- `ReceiverQuotaSafety`：A 累计准入不超过初始额度，沿用原配额安全目标。
- `TypeOK`、`SourceAccounting`：数据类型、事件顺序和两端各自的账目与原生截断扣减一致。
- `QuiescentAgreement`：仅当所有连接的两端都停止、待处理的扣减和帧已清空时，要求两端余额相等。
- `QuiescentAgreementAfterProgress`：仅报告此前已经收到过正常回复的执行中的终态差额，用来展示故障也能发生在后续轮次；它不改变模型动作和故障时机。
- `NoUnadmittedConsumption`：仅在上述终态，要求 B 实际消耗的额度不超过 A 累计准入数。
- `NoResponseAbort`、`NoSendError`：故意反向写出的可达性查询；违反表示对应故障分支确实可达。

后两个账目性质是拟研究的故障恢复／可用性要求。SAGA 原文没有明确承诺所有故障下双端余额相等，也没有定义按尝试、接收准入还是业务成功退款。因此，发现它们不成立应报告为该故障假设下的余额差额或额度保守消耗，不能直接称为接收侧配额绕过。

特别地，不要求发送后、A 尚未处理时立即相等；正常异步执行中的短暂差异不触发候选性质。等待终态也不代表已经证明最终一定终止：本次检查没有加入公平性／恢复活性定理。

## 配置与运行

```powershell
Set-Location 'D:\Users\10202\Desktop\saga'
& '.\proofs\consumer_validation\.runtime\venv\Scripts\python.exe' -B '.\proofs\quota_validation\run_delivery_tlc.py'
```

沿用原有 `.runtime` Java/TLC，不需要新安装。`run_delivery_tlc.py` 复用原运行器的只读校验／进程辅助函数，不修改原运行器。每次创建独立 `evidence/delivery-<UTC时间>/`，保存输入、版本、原生哈希、原始日志及反例摘录；原生业务逻辑和旧证据不变。

`delivery_configs/` 包括：正常单连接多轮、无故障并发超额、请求交付前中断、回复中断、发送先报错、故障分支可达性，以及多连接多轮混合故障的结构检查。候选一致性反例与接收侧超额反例分别标注。实际结果以各次 summary 和 stdout 为准；驱动整体退出 0 表示预期结果均被观察到，不表示全部安全性质成立。

本次没有提供修复。尤其不能对所有“没收到回复”的情况无条件退回额度：A 可能已经准入和处理，请求结果存在不确定性。可靠修复还需要先确定计账语义，并讨论请求标识、接收端记账、确认与重试去重。
