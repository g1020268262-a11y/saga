# 本次 TLA+ 实现与原生代码的映射

本表承接 `output/analysis/qmax-source-model-map-20261024/源码与模型对应表.md`。原准备稿保留；下面记录实际模型相对拟用名称的具体化。

源文件绑定：`saga/agent.py`、`saga/config.py`、`saga/common/crypto.py` 均须匹配固定上游 `7372111bea150e32cee390a616849316d2780bfc`。运行脚本检查原始 SHA-256 和 Git blob，清单保留在每次 `manifest.json` 中。

## 原子边界与主要动作

| 模型定义 | 原生依据 | 具体化及抽象 |
|---|---|---|
| `Init`、`InitialQuota` | `config.py:75`；`agent.py:321-333, 1102-1103` | 从签发、存储已经完成时开始；余额为真实初始额度，准入数为零；不证明签发密码学安全 |
| `remaining` | `agent.py:353, 363, 605` | 选定 token 在 A 的共享余额；不是 B 的 `received_tokens`，也不是每连接独立余额 |
| `Connections`、`pc` | `agent.py:1175-1182` | 每个连接一个处理线程，共享同一接收 agent 的状态 |
| `Enter`、`RejectEntry` | `agent.py:1120-1128` 调用 `token_is_valid` | 实际展开已有 token 的入口额度判断；通过不扣减、不预留额度；其他身份与 matcher 条件固定通过 |
| `Check`、`Reject` | `agent.py:595-601`，调用 `337-381` | 每消息再次检查；保留 `remaining == 0` 的原判断；锁内判断作为一个动作 |
| `Consume` | `agent.py:604-605` | 另一次原子加锁区间；只要求此前检查成功；按当时共享余额执行截断扣减；没有新增余额检查 |
| `checkedRemaining` | `agent.py:363` 的观测 | 辅助记录检查读数；不作为扣减的数据来源 |
| `accepted` | `agent.py:605` 后的准入事件 | 原程序没有的辅助累计计数；它随 `Consume` 增加，不随 `Check` 增加 |
| `InvokeBackend`、`backendCalls` | `agent.py:609-634` | 普通消息、首个请求时 `i=0`，查询上限不触发；观察后端调用，不展开 LLM 执行和响应 |
| `Done` | 单连接一次请求的有界观察边界 | 不代表业务任务完成，不触发原生 task-finished token 删除分支 |
| `TerminalStutter` | 模型终止处理 | 仅给终止状态添加自循环，不修改任何额度逻辑，不关闭全局死锁检查 |

## 从可选压缩前缀到显式执行前缀

原准备稿允许用 `PrefixUsed` 表示“先使用 49 次”，同时要求证明该前缀可达。本次直接展开前缀，减少人工初始化可达性的负担：

- `Init` 固定从 `remaining = InitialQuota`、`accepted = 0` 开始。
- `PrefixCheck`、`PrefixConsume`、`PrefixBackend` 顺序重复，分别对应消息检查、扣减与后端调用事件。
- `prefixDone` 统计完成的顺序请求；`prefixPC` 保留前缀内部检查与扣减的间隙。
- 前缀完成后执行 `BeginConnections`，随后每个新连接自己执行 `Enter` 或 `RejectEntry`，再进入消息级检查。
- 前缀连接来自最初签发 token 的会话路径（`agent.py:1111-1115`），其后正常关闭接收返回路径（`586-591`）不删除 token。网络动作未建模，只保留它们不改变额度与 token 记录的正常路径。
- 前缀普通响应不使用 task-finished token；`PrefixUsed <= 100`，原生 `i > MAX_QUERIES` 在前缀后端调用之前均不触发。默认实例只使用 49 次。

因此默认 50 的反例配置不会用“初始余额 1、初始累计使用 49”跳过前缀；所有累计数来自模型动作。前缀暂不与后续连接并发，这是选定的合法环境调度，不是原生实现保证两阶段互斥。

## 原版与对应表之间的保留点

1. `Check` 与 `Consume` 分离；`Checked` 是可被其他连接打断的位置。
2. 原检查拒绝零余额；非负状态域内用 `remaining # 0` 表示成功配额条件。
3. 扣减读取当前共享余额；其条件表达式与非负域内的 `max(0, remaining - 1)` 相同。
4. `MetadataValid` 只汇总记录存在、未过期和 PAC 匹配等非配额条件；本次所有配置固定 TRUE。
5. 入口检查和消息检查都保留；最小配置先从 token 已签发、尚未消费开始。
6. B 的本地发送检查与余额不限制模型请求，这是持合法 token、控制自身客户端的 B 的威胁假设。
7. `accepted`、`backendCalls` 和 `checkedRemaining` 是观察变量，不作为原生程序的新准入条件。

## 尚未建立的对应关系

人工源代码映射并非 Python 精化证明。模型没有展开 TLS、密码算法、matcher 判定内部流程、异常、过期时间变化、token 删除／更新、业务终止、响应交付和崩溃恢复。

原生重放、修复模型与修复实现仍属于后续阶段；本轮不以已有历史探针替代新模型反例的逐步重放。
