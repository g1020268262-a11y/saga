# SAGA 接收侧配额：源码与 TLA+ 模型对应表

日期：2026-10-24  
状态：建模准备稿。本轮核对源码、建立对应关系；未编写 `.tla` 文件、未运行 TLC、未重新执行原生探针。

## 1. 本表的对象与证据基线

研究对象保持为：合法持有同一 token 的 B，通过多个连接向诚实执行原生逻辑的 A 发送请求时，A 的累计配额准入是否可能超过该 token 的初始配额。

A 是签发 token、接收请求的一方；B 是持有 token、发起请求的一方。B 可以控制自己的客户端；不要求 B 遵守原生客户端的本地发送限额。A 的配额逻辑不被 B 修改。

本表依据可执行语句建立映射。源码注释用于辅助理解，不能替代实际控制流。它是人工抽象的可追溯说明，不是完整 Python 程序到 TLA+ 的翻译，也不构成已经证明的精化关系。

### 版本绑定

- 固定上游版本：`7372111bea150e32cee390a616849316d2780bfc`。
- 本轮工作区 HEAD：`a51c044eaaa844caff99ca99e4815a440a3f775d`。
- 本轮核对 `saga/agent.py`、`saga/config.py`、`saga/common/crypto.py`：工作区文件相对上述固定上游版本无差异，Git blob 一致。

| 文件 | 工作区原始文件 SHA-256 | Git blob |
|---|---|---|
| `saga/agent.py` | `94bebf70df4f76e55c0bb8a54c5f29b7fa688ead197ece18f8ac9dec8edae8d5` | `6c06245e21a33d4f54a7da625a76c7b87aa02cac` |
| `saga/config.py` | `5a42594196897d607c368c2cddc469a327d1dac92fe5d5de66c4b0bceb7f4e23` | `e5d9265cb832153a7ce63f6cc1a53c4c034cdeb9` |
| `saga/common/crypto.py` | `dca1a5fa145afbf419b1a71af068e0b98a3ac533a929862d12e023f5c8436b7b` | `fa5e53da802b38449ba1511022f3c194d528ec69` |

下文模型名称是拟用名称。确定其语义后再编写模型，不能把它们视为已经存在的 TLA+ 定义。

## 2. 原生流程与建模入口

原生流程分为以下部分：

1. A 初始化 `active_tokens` 及其锁；B 也有独立的 `received_tokens` 及其锁。
2. A 根据 `Q_MAX` 生成 token，将其解密后的元数据存入 `active_tokens[密文字符串]`。B 解密收到的 token，存入自己的 `received_tokens`。
3. A 为每个入站连接创建线程；连接处理器执行 matcher 和身份检查。持已有 token 的连接，还会在进入会话前调用 `token_is_valid()`。
4. A 在会话循环中读取一条消息，从该消息重新提取 token，再调用 `token_is_valid()`。
5. 检查成功返回、释放锁之后，A 再获取同一把锁，执行 `max(0, quota - 1)`。
6. A 处理终止消息、检查连接内查询次数，再调用后端并发送响应。

最小模型从“目标 token 已存储、参与连接已进入消息处理阶段、有一条普通请求待检查”开始。签发与握手作为前置条件保留来源，不在第一版展开密码计算。

**入口可达性义务：** 后续反例必须能对应到通过真实握手的连接。对于剩余额度为 1 的双连接场景，两个连接可先完成入口检查，再发送竞争最后额度的消息；入口检查不预留额度。因此，不能把消息级竞争误写成绕过握手，也不能无条件假定所有边界配置都能形成任意数量的已建立连接。

## 3. 常量、状态与辅助变量对应表

“参数”需要进一步区分：有些是固定常量，有些是运行时状态，还有一些只用于验证观察，原程序并没有相应变量。

| 编号 | 原生依据 | 拟用模型项 | 类别及初值／含义 | 保留要求 |
|---|---|---|---|---|
| M01 | [config.py:75](D:/Users/10202/Desktop/saga/saga/config.py:75)；[agent.py:321](D:/Users/10202/Desktop/saga/saga/agent.py:321) | `InitialQuota` | 常量，取非负整数；默认实例为 50 | 表示本次 token 签发时的初始额度，不能随消费递减 |
| M02 | [agent.py:1094](D:/Users/10202/Desktop/saga/saga/agent.py:1094)、[agent.py:1102](D:/Users/10202/Desktop/saga/saga/agent.py:1102) | `TokenId` | 选定的同一个 token 的抽象标识；单 token 模型可隐含 | 必须保持所有竞争连接使用同一份接收侧 token 记录 |
| M03 | [agent.py:353](D:/Users/10202/Desktop/saga/saga/agent.py:353)、[agent.py:605](D:/Users/10202/Desktop/saga/saga/agent.py:605) | `remaining` | 运行状态；从签发完成开始时等于 `InitialQuota` | 对应 A 的 `active_tokens[TokenId]["communication_quota"]`，由所有入站连接共享 |
| M04 | [agent.py:1175](D:/Users/10202/Desktop/saga/saga/agent.py:1175)、[agent.py:1180](D:/Users/10202/Desktop/saga/saga/agent.py:1180) | `Connections` | 有限常量集合，例如 `{c1, c2}` | 表示不同入站连接的处理线程，不是两个不同的接收 agent |
| M05 | [agent.py:598](D:/Users/10202/Desktop/saga/saga/agent.py:598)、[agent.py:604](D:/Users/10202/Desktop/saga/saga/agent.py:604)、[agent.py:631](D:/Users/10202/Desktop/saga/saga/agent.py:631) | `pc[c]` | 每个连接的控制位置；拟分 `Ready`、`Checked`、`Debited`、`Done`、`Rejected` | 保留“已通过检查、尚未扣减”的 `Checked` 状态 |
| M06 | [agent.py:348](D:/Users/10202/Desktop/saga/saga/agent.py:348)、[agent.py:604](D:/Users/10202/Desktop/saga/saga/agent.py:604) | 动作的原子边界 | 最小模型用原子 `Check` 和原子 `Consume` 表示两段互斥访问 | 不必先引入显式 `lockOwner`；但绝不能把两段合并成同一步 |
| M07 | [agent.py:349](D:/Users/10202/Desktop/saga/saga/agent.py:349)、[agent.py:358](D:/Users/10202/Desktop/saga/saga/agent.py:358)、[agent.py:377](D:/Users/10202/Desktop/saga/saga/agent.py:377) | `MetadataValid` | 初版固定前提：记录存在、未过期、PAC 匹配 | 只固定非配额条件；不能把完整 `token_is_valid` 永久设为真 |
| M08 | A 在 [agent.py:605](D:/Users/10202/Desktop/saga/saga/agent.py:605) 完成扣减并继续处理 | `accepted` | 验证辅助计数；初值 0，每次 `Consume` 加 1 | 原程序没有该累计变量；它观察准入事件，不替代 `remaining` |
| M09 | [agent.py:631](D:/Users/10202/Desktop/saga/saga/agent.py:631) | `backendCalls`（可选） | 验证辅助计数；调用后端时加 1 | 与 `accepted` 分开；后端调用、返回成功、业务完成也要区分 |
| M10 | 两个连接各自刚通过检查时的观察值 | `checkedRemaining[c]`（可选） | 只用于输出可读反例的辅助记录 | 不是原生缓存，不得用它替换扣减时读取的共享余额 |
| M11 | 默认配置的“先使用 49 次，再竞争最后一次”实验形态 | `PrefixUsed`（可选） | 表示已完成的合法顺序前缀；若启用，`remaining = InitialQuota - PrefixUsed`、`accepted = PrefixUsed` | 属于缩短模型路径的设置，必须补充该前缀可达的说明，不能凭空把余额 1 当作默认 50 的初态 |

### 不属于同一计数器的对象

| 原生对象 | 对本次模型的处理 | 原因 |
|---|---|---|
| B 的 `received_tokens[token]["communication_quota"]`：[agent.py:518](D:/Users/10202/Desktop/saga/saga/agent.py:518) | 不作为 A 的 `remaining` | 两端独立存储、独立扣减；B 的本地状态不能替代 A 的强制执行 |
| 密文 token 内的初始 `communication_quota`：[crypto.py:459](D:/Users/10202/Desktop/saga/saga/common/crypto.py:459) | 对应签发时的元数据 | 原生扣减更新内存字典；相关路径没有重新加密并替换消息中 token 的操作 |
| 连接内 `i` 与 `MAX_QUERIES = 100`：[agent.py:28](D:/Users/10202/Desktop/saga/saga/agent.py:28)、[agent.py:581](D:/Users/10202/Desktop/saga/saga/agent.py:581)、[agent.py:623](D:/Users/10202/Desktop/saga/saga/agent.py:623) | 最小单次请求模型中说明其不触发；扩展循环时按实际位置保留 | 这是每个会话调用的查询上限检查，位于配额扣减之后，不是 token 的跨连接配额 |

## 4. 动作与控制流对应表

下表是模型转换规则的设计说明，不是可直接运行的 TLA+ 模块。初版每个连接只处理一条待检查请求，以隔离最小竞争；扩展多轮循环需要另行加入返回下一条请求的动作和有限请求边界。

| 动作 | 源码位置 | 启用条件与状态变化 | 原子性说明 |
|---|---|---|---|
| `Init` | [agent.py:321](D:/Users/10202/Desktop/saga/saga/agent.py:321)、[agent.py:1102](D:/Users/10202/Desktop/saga/saga/agent.py:1102) | 选定 token 已签发并存储；`remaining = InitialQuota`，`accepted = 0`，各连接位于 `Ready` | 从建模入口开始；不声称把整个握手压成一个并发原子事务 |
| `Check(c)` | [agent.py:598](D:/Users/10202/Desktop/saga/saga/agent.py:598) 调用 [agent.py:348](D:/Users/10202/Desktop/saga/saga/agent.py:348) 至返回 | `pc[c] = Ready`；在固定元数据有效前提下，`remaining != 0` 时设 `pc[c] = Checked`；额度与累计准入均不变化 | 锁内读取和判断可合成一步；成功返回时释放锁，不预留额度 |
| `Reject(c)` | [agent.py:364](D:/Users/10202/Desktop/saga/saga/agent.py:364)、[agent.py:598](D:/Users/10202/Desktop/saga/saga/agent.py:598) | 元数据固定有效时，`pc[c] = Ready` 且 `remaining = 0`；设 `pc[c] = Rejected`，不扣减、不增加准入 | 与成功检查是对同一次检查结果的不同分支 |
| `Consume(c)` | [agent.py:604](D:/Users/10202/Desktop/saga/saga/agent.py:604)、[agent.py:605](D:/Users/10202/Desktop/saga/saga/agent.py:605) | 只要求 `pc[c] = Checked`；设 `remaining = max(0, remaining - 1)`、`accepted = accepted + 1`、`pc[c] = Debited` | 重新获取额度锁；源码没有再次检查余额，因此余额已经为 0 也不能禁止此动作 |
| `InvokeBackend(c)`（若展开） | [agent.py:609](D:/Users/10202/Desktop/saga/saga/agent.py:609) 至 [agent.py:634](D:/Users/10202/Desktop/saga/saga/agent.py:634) | 普通非终止消息、连接查询上限不触发时，从 `Debited` 调用后端，记录调用事件，之后到 `Done` | 在额度锁之外；调用事件的观察可以抽象，但不能据此声称整段 LLM 执行在真实程序中原子化 |
| `Finish(c)`（不展开后端时） | 扣减完成之后的后续路径 | `Debited` 到 `Done`，不改变额度与准入 | 对本次配额性质无影响的路径可折叠；不能把 `Done` 解读为业务成功 |
| 全局下一步 | [agent.py:1180](D:/Users/10202/Desktop/saga/saga/agent.py:1180) 的多线程处理方式 | 任意一个连接执行其当前启用的动作 | 同一连接遵守程序顺序；不同连接可交错。安全性质检查不依赖公平性保证 |

### 两个必须保留的源码细节

1. **判断是 `remaining_quota == 0`，不是 `<= 0`。** 初始额度限制为非负整数、扣减又截断为 0 时，检查通过可以写作 `remaining != 0`，且在这个域内等价于 `remaining > 0`。若将来研究负额度配置，必须扩大状态域并保留原判断，不能沿用这一等价变换。
2. **`Consume` 读取当时的共享余额。** 它没有使用检查时保存的余额，也没有再次调用检查函数。因此两个线程可以各自完成合法的检查，再依次执行扣减。

## 5. 事件定义与待检查性质

| 名称 | 明确定义 | 本次用途 |
|---|---|---|
| 检查通过 | `token_is_valid()` 返回 `True` | 不等同于已经完成一次配额扣减；用 `Checked` 控制位置记录 |
| 配额准入 | A 完成扣减，进入之后的处理路径 | `accepted` 的累计事件；终止消息或后端失败不会自动撤销已发生的事件 |
| 后端调用 | A 开始调用 `local_agent.run()` | 可选独立观察；已有探针主要使用此项计数 |
| 业务成功／远端收到响应 | 需要额外定义与证据 | 不从上述三个事件直接推出 |

核心安全性质：`accepted <= InitialQuota`。

辅助性质与检查：

- 类型与非负余额：`remaining` 为非负整数，`pc` 取值合法。
- 在本次单 token、无重置的模型内，`remaining` 不增加。
- 从 `Ready` 在余额为 0 时尝试检查，只能拒绝；这不限制此前已经进入 `Checked` 的线程继续执行原生扣减。
- 至少存在合法准入路径；不能通过让全部请求不可达来满足核心性质。
- 若记录后端调用，则单次请求按程序顺序先准入、再调用；不把后端计数直接当作全部准入事件的定义。

注意：这里明确的准入计数不同于“最多完成 Q 个业务任务”。模型编写与实验日志应沿用同一个定义。

## 6. 抽象边界与后续核查义务

| 机制 | 初版处理 | 对结论的限制／必须保留的核查 |
|---|---|---|
| 签发与密文标识 | 选定一个真实签发、已存储的 token | 不验证密码算法、伪造或多 token 刷新；不能把任意密文直接视为已知 token |
| 连接入口 matcher、证书、身份与 PAC | 假定这些前置检查通过，保持源码位置可查 | [agent.py:951](D:/Users/10202/Desktop/saga/saga/agent.py:951) 的 matcher 实际存在；本次不研究绕过它 |
| 复用 token 的入口检查 | 保留为前置可达性条件，见 [agent.py:1120](D:/Users/10202/Desktop/saga/saga/agent.py:1120) | 不同连接可先后通过；每条消息还会在 598 行重新检查，不能漏掉消息级检查 |
| 过期时间与 token 删除 | 固定未过期；采用非终止消息和非终止响应，模型期间没有 token 删除 | 不覆盖撤销、终止分支删除后的竞争或崩溃恢复 |
| 网络和解析 | 消息已经成功解析，且每条请求携带选定 token | 不覆盖丢包、断连、消息交付和两端计数一致性 |
| B 的本地检查 | B 可自行构造合法请求，不以其本地余额限制发送 | 验证 A 对持有效凭据但不遵守客户端限额的 B 是否仍能强制执行额度 |
| 锁与调度 | 各段临界区用原子动作表示，允许两段之间切换连接 | 若扩展到锁持有、异常或死锁性质，需要显式建模更多锁状态 |
| LLM 与响应 | 可省略，或仅记录后端调用事件 | 不证明后端成功、内容安全或业务交付；不估计资源损失金额 |
| 请求数量 | 初版每连接一条请求，参数有限 | 找到的可达反例可展示该配置下的问题；检查通过不能直接推广至任意连接和请求数量 |
| 顺序前缀压缩 | 可选 `PrefixUsed`，单独标明 | 默认 50 的“49 次顺序使用＋最后一次竞争”需补充前缀及连接准备过程的源码／执行对应 |

## 7. 建模前可读的最小交错示意

以下是根据源码整理的**候选执行说明**，尚未由 TLC 输出。初值 `InitialQuota = 1`、`remaining = 1`、`accepted = 0`，两个连接均已具备进入消息检查的条件。

| 步骤 | 连接与动作 | 剩余额度 | 累计准入 | 另一连接为什么仍能继续 |
|---|---|---:|---:|---|
| 0 | 初始化 | 1 | 0 | 两个请求等待检查 |
| 1 | c1 执行 `Check` 并释放锁 | 1 | 0 | 余额尚未扣减 |
| 2 | c2 执行 `Check` 并释放锁 | 1 | 0 | 两个连接都进入 `Checked` |
| 3 | c1 执行 `Consume` | 0 | 1 | c2 已通过检查，不再回到 `Ready` |
| 4 | c2 执行 `Consume` | 0 | 2 | 扣减语句把 `0 - 1` 截断为 0，但继续处理该请求 |

该示意说明为什么应同时保留 `remaining` 和 `accepted`。余额非负与累计准入超额可以同时出现。

## 8. 本阶段完成项与进入模型编写前的检查

本阶段已建立：版本绑定、原生调用路径、常量与状态映射、动作及锁边界、事件定义、抽象范围和候选交错。

进入模型编写时应逐项检查：

1. 使用上表的事件语义与非负额度域；名称变化时同步对应表。
2. 原版模型的 `Check` 与 `Consume` 分离，且 `Consume` 没有新增余额检查。
3. 最小反例先使用 Q=1、双连接；默认 Q=50 的实例单独配置并交代合法前缀。
4. 边界配置分别说明握手入口是否可达；不因省略握手而自动宣称端到端可达。
5. 原版与修复版模型分开；修复才将检查和扣减合并为同一个原子动作。
6. 保留正常准入与耗尽拒绝的对照检查，记录有限范围与未覆盖行为。

阶段状态：**源码与模型映射已成稿；TLA+ 模型和工具验证尚未开始。**
