----------------------------- MODULE SagaQuota_Annotated -----------------------------
\* [ZH-NOTE-BEGIN module]
\* 这是模块头。MODULE 后面的名字必须与 .tla 文件名对应。
\* 本文件是 SagaQuota.tla 的中文阅读副本，因此模块名改为 SagaQuota_Annotated。
\* 原文件的其余代码保持不变；中文说明都使用 TLA+ 的行注释格式。
\* 原模型 SHA-256：B0A473EEAABF5A32E45648A8713487504485D3E60404C2F1F9CF01528982592B。
\* 阅读顺序：参数与状态 → 初始状态 → 顺序前缀 → 并发连接 → 下一步关系 → 检查性质。
\* [ZH-NOTE-END module]
EXTENDS Integers, FiniteSets
\* [ZH-NOTE-BEGIN extends]
\* EXTENDS 引入标准模块提供的数学定义。
\* Integers 提供整数运算，并间接包含 Nat（非负整数）等自然数定义。
\* FiniteSets 提供有限集合的 IsFiniteSet 和集合大小 Cardinality。
\* 这里没有执行 Python 代码，也没有创建线程；它只提供后面公式需要的数学工具。
\* [ZH-NOTE-END extends]

(***************************************************************************
 Source-bound, single-token receiver-quota model of the unmodified code.
 Upstream: 7372111bea150e32cee390a616849316d2780bfc
 All source references below are to saga/agent.py unless stated otherwise.

 Scope: known token, fixed matching identity, stable expiry/policy, ordinary
 messages and responses, no token deletion/reissue, no network/LLM failures.
 B controls its own client; B's received_tokens balance is not an A-side guard.
 Each racing connection submits one request. PrefixUsed ordinary requests
 are executed explicitly on an earlier, sequential issuance connection.
 No Python refinement theorem or cryptographic proof is asserted.
***************************************************************************)
\* [ZH-NOTE-BEGIN scope]
\* 上面的英文块注释声明模型的研究边界与固定上游版本。
\* A 是签发 token、接收请求的一方；B 合法持有 token，并可以控制自己的客户端。
\* 模型只考虑一个已存储的 token、固定身份与有效期、普通消息及正常后端路径。
\* B 的本地 received_tokens 余额不作为 A 的强制限制，A 仍必须执行自己的额度检查。
\* 每个后续并发连接只发送一条请求；更早的顺序请求通过 PrefixUsed 显式展开。
\* TLS、密码学、网络故障、删除或重新签发 token 等机制没有完整展开。
\* 所以这是有范围的状态模型，不是整个 Python 程序的等价翻译或密码学证明。
\* [ZH-NOTE-END scope]

CONSTANTS InitialQuota, Connections, PrefixUsed, MetadataValid
\* [ZH-NOTE-BEGIN constants]
\* CONSTANTS 声明一次模型运行中保持不变、由 .cfg 配置提供的参数。
\* InitialQuota：本次 token 签发时的初始额度，例如 50；它不会随着请求递减。
\* Connections：参与后续竞争的连接集合，例如 {c1, c2}，共同访问同一个 A。
\* PrefixUsed：并发阶段之前顺序执行多少次请求，例如 49；不是直接预扣 49。
\* MetadataValid：汇总 token 存在、未过期和 PAC 匹配等非额度条件。
\* 本次所有配置都将 MetadataValid 设为 TRUE；额度条件仍在动作中单独检查。
\* [ZH-NOTE-END constants]

ASSUME /\ InitialQuota \in Nat
       /\ IsFiniteSet(Connections)
       /\ Connections # {}
       /\ PrefixUsed \in 0..InitialQuota
       /\ PrefixUsed <= 100
       /\ MetadataValid \in BOOLEAN
\* [ZH-NOTE-BEGIN assume]
\* ASSUME 写出参数必须满足的前提；这些前提定义本模型的适用范围。
\* /\ 表示逻辑“并且”，\in 表示属于，# 表示不等于。
\* InitialQuota \in Nat：初始额度是非负整数，因此本模型不研究负额度配置。
\* Connections 必须有限且非空；Connections # {} 表示至少有一个连接。
\* 0..InitialQuota 是包含两端的整数区间；顺序前缀不能超过初始额度。
\* PrefixUsed <= 100 限制前缀规模，使原生连接内 i > MAX_QUERIES 的检查不触发。
\* BOOLEAN 是 {TRUE, FALSE}。这里仅要求布尔类型，具体真值来自配置。
\* 这些都是参数假设，不是在这里假定 QuotaSafety 已经成立。
\* [ZH-NOTE-END assume]

VARIABLES remaining, accepted, backendCalls, pc, checkedRemaining,
          phase, prefixPC, prefixDone
\* [ZH-NOTE-BEGIN variables]
\* VARIABLES 声明会随执行变化的状态。模型有八个状态分量。
\* remaining：A 保存的共享剩余额度，真正会随着扣减变化。
\* accepted：累计发生的配额准入事件；它是模型新增的观察计数，源码没有同名累计变量。
\* backendCalls：累计后端调用事件，与 accepted 分开记录。
\* pc：从连接到程序位置的函数；pc[c] 表示连接 c 当前执行到哪一步。
\* checkedRemaining：每个连接检查时看到的余额快照，仅用于解释反例。
\* phase：整个选定场景处于顺序前缀、并发阶段，还是前缀中止。
\* prefixPC、prefixDone：顺序连接的程序位置，以及已完成的顺序请求数。
\* pc 和这些控制状态是从源码控制流提取的表示，不要求源码存在同名变量。
\* [ZH-NOTE-END variables]

vars == <<remaining, accepted, backendCalls, pc, checkedRemaining,
          phase, prefixPC, prefixDone>>
\* [ZH-NOTE-BEGIN vars]
\* == 表示“定义为”，不是程序里的赋值；vars 是全部状态变量组成的元组。
\* << ... >> 是元组写法，用来统一指代本模型的所有状态分量。
\* 后面的 UNCHANGED vars 和 [Next]_vars 都会使用这个元组。
\* vars 不是额外的第九个状态变量，也不是保存初始状态的一份快照。
\* [ZH-NOTE-END vars]

ConnectionStates == {"Entry", "Ready", "Checked", "Debited", "Done",
                     "Rejected", "EntryRejected"}
\* [ZH-NOTE-BEGIN ConnectionStates]
\* ConnectionStates 定义后续并发连接可以使用的程序位置标签。
\* Entry：等待已有 token 的连接入口检查；Ready：入口通过，等待消息级检查。
\* Checked：这条消息已检查成功、锁已释放，但尚未扣减额度。
\* Debited：已经执行额度扣减和准入记录，尚未观察后端调用。
\* Done：这次有界请求的后端调用已被记录，不表示业务完成或响应交付。
\* Rejected：消息级检查拒绝；EntryRejected：连接入口检查拒绝。
\* 这些字符串是控制位置，不是每个连接各自拥有一份 token 余额。
\* [ZH-NOTE-END ConnectionStates]
PrefixStates == {"Ready", "Checked", "Debited", "Done", "Rejected"}
\* [ZH-NOTE-BEGIN PrefixStates]
\* PrefixStates 是顺序前缀连接的程序位置集合。
\* Ready、Checked、Debited 分别对应下一条请求的检查前、检查后、扣减后。
\* Done 表示整个选定前缀阶段结束；Rejected 表示前缀请求的检查失败。
\* 前缀由一个顺序连接执行，因此用单个 prefixPC，而不是 pc[c]。
\* [ZH-NOTE-END PrefixStates]
FinalStates == {"Done", "Rejected", "EntryRejected"}
\* [ZH-NOTE-BEGIN FinalStates]
\* FinalStates 列出后续连接在本次有界观察中的终止位置。
\* 后端调用已记录，或者入口/消息检查拒绝，都不再为该连接生成下一条请求。
\* 它不表示 SAGA 服务停止，也不表示 agent 业务任务结束。
\* 本模型每个并发连接只有一条请求；若扩展多轮，需要增加返回 Ready 的动作。
\* [ZH-NOTE-END FinalStates]

\* 321, 1102-1103: begin after a real token is issued and stored at A.
\* Unlike a compressed-prefix model, accepted ALWAYS starts at zero.
Init ==
    /\ remaining = InitialQuota
    /\ accepted = 0
    /\ backendCalls = 0
    /\ pc = [c \in Connections |-> "Entry"]
    /\ checkedRemaining = [c \in Connections |-> 0]
    /\ phase = "Prefix"
    /\ prefixPC = "Ready"
    /\ prefixDone = 0
\* [ZH-NOTE-BEGIN Init]
\* Init 定义允许的初始状态，是一个关于当前状态的条件。
\* 这里从 token 已经签发并存入 A 之后开始，不展开签发握手的每一个密码步骤。
\* remaining 从 InitialQuota 开始，accepted 和 backendCalls 都从零开始。
\* [c \in Connections |-> "Entry"] 是函数构造：每个连接 c 都映射到 Entry。
\* checkedRemaining 也为每个连接设置一个初始零值，表示还没有成功检查读数。
\* phase = Prefix，prefixPC = Ready，prefixDone = 0：先处理选定的顺序前缀。
\* 若 PrefixUsed = 0，后面会直接进入并发阶段，不会虚构前缀请求。
\* 这里的 = 是等式条件。Init 不是按照书写顺序逐行赋值的命令序列。
\* [ZH-NOTE-END Init]

\* 348-381: one successful check, with its lock released on return.
PrefixCheck ==
    /\ phase = "Prefix"
    /\ prefixPC = "Ready"
    /\ prefixDone < PrefixUsed
    /\ MetadataValid /\ remaining # 0
    /\ prefixPC' = "Checked"
    /\ UNCHANGED <<remaining, accepted, backendCalls, pc, checkedRemaining,
                    phase, prefixDone>>
\* [ZH-NOTE-BEGIN PrefixCheck]
\* PrefixCheck 描述顺序前缀的一次检查成功，是一个当前态到下一态的动作。
\* 前四行是启用条件：处于前缀阶段、准备检查、前缀还未完成、元数据有效且余额非零。
\* 不带撇号的变量描述当前状态；prefixPC' 中的撇号表示下一状态的值。
\* 只有 prefixPC 变成 Checked；remaining、accepted 等其他分量明确保持不变。
\* UNCHANGED <<...>> 表示列出的每个分量在这一步前后相等。
\* 这对应原生 token_is_valid 返回成功并释放锁，检查没有预留或扣除额度。
\* 动作中的 /\ 连接同一个状态转换必须同时满足的条件，不是逐行执行顺序。
\* [ZH-NOTE-END PrefixCheck]

PrefixReject ==
    /\ phase = "Prefix"
    /\ prefixPC = "Ready"
    /\ prefixDone < PrefixUsed
    /\ (~MetadataValid \/ remaining = 0)
    /\ prefixPC' = "Rejected"
    /\ phase' = "Aborted"
    /\ UNCHANGED <<remaining, accepted, backendCalls, pc, checkedRemaining,
                    prefixDone>>
\* [ZH-NOTE-BEGIN PrefixReject]
\* PrefixReject 是顺序前缀检查失败的分支。
\* ~ 表示逻辑否定，\/ 表示逻辑“或者”；元数据无效或余额为零时可以拒绝。
\* prefixPC' 变为 Rejected，同时 phase' 变为 Aborted，后续不再处理前缀。
\* 它没有修改额度、准入数或后端计数。
\* 本次配置元数据有效、前缀又不超过初始额度，正常前缀不应走到这里。
\* 保留拒绝分支可以明确检查的失败结果，而不是把所有检查都写成必定成功。
\* [ZH-NOTE-END PrefixReject]

\* 604-605: a DIFFERENT lock interval. There is no fresh quota check here.
\* The conditional is max(0, remaining - 1) over our nonnegative domain.
PrefixConsume ==
    /\ phase = "Prefix"
    /\ prefixPC = "Checked"
    /\ remaining' = IF remaining = 0 THEN 0 ELSE remaining - 1
    /\ accepted' = accepted + 1
    /\ prefixPC' = "Debited"
    /\ UNCHANGED <<backendCalls, pc, checkedRemaining, phase, prefixDone>>
\* [ZH-NOTE-BEGIN PrefixConsume]
\* PrefixConsume 是顺序连接检查成功之后的扣减步骤，与检查是另一个原子动作。
\* 启用条件只要求之前已到 Checked；代码没有新增“现在余额必须大于零”的守卫。
\* IF ... THEN ... ELSE ... 是条件表达式；在非负额度域内等价于 max(0, remaining - 1)。
\* accepted' = accepted + 1 记录这次请求已完成配额扣减、进入后续处理路径。
\* prefixPC 变为 Debited；后端还没有调用，所以 backendCalls 保持不变。
\* 这对应原生源码重新获取 active_tokens_lock 后执行扣减。
\* 真正递减的是 remaining，而不是常量 InitialQuota。
\* [ZH-NOTE-END PrefixConsume]

\* 631, 634: project the ordinary successful prefix onto its backend-call
\* event and next iteration. PrefixUsed <= 100 keeps i > MAX_QUERIES false.
PrefixBackend ==
    /\ phase = "Prefix"
    /\ prefixPC = "Debited"
    /\ backendCalls' = backendCalls + 1
    /\ prefixDone' = prefixDone + 1
    /\ prefixPC' = "Ready"
    /\ UNCHANGED <<remaining, accepted, pc, checkedRemaining, phase>>
\* [ZH-NOTE-BEGIN PrefixBackend]
\* PrefixBackend 表示顺序前缀在普通正常路径上的后端调用及进入下一轮。
\* backendCalls 加一，prefixDone 加一，prefixPC 回到 Ready。
\* 因为这个请求先前已在 PrefixConsume 准入，这一步不再增加 accepted，也不再扣额度。
\* 它把不影响配额的正常后端、响应和继续循环路径折叠为一个观察动作。
\* 这不证明真实 LLM 调用是原子的，也不覆盖失败或响应丢失。
\* 默认配置需要先顺序执行 49 次，这个三步循环就会实际重复 49 轮。
\* [ZH-NOTE-END PrefixBackend]

\* The prefix session can close without deleting the token (586-591).
\* Racing connections are subsequently allowed to perform the existing-
\* token entrance check at 1120. No existing quota is reset or invented.
BeginConnections ==
    /\ phase = "Prefix"
    /\ prefixPC = "Ready"
    /\ prefixDone = PrefixUsed
    /\ phase' = "Race"
    /\ prefixPC' = "Done"
    /\ UNCHANGED <<remaining, accepted, backendCalls, pc, checkedRemaining,
                    prefixDone>>
\* [ZH-NOTE-BEGIN BeginConnections]
\* BeginConnections 表示顺序前缀结束，允许后续连接开始复用 token。
\* 只有 prefixDone = PrefixUsed 且前缀没有未完成的请求时，才切换到 Race。
\* prefixPC 设为 Done；额度和两个累计计数全部保留，没有重新初始化。
\* 当初始额度 50、前缀 49 时，执行到这里会自然得到 remaining = 1、accepted = 49。
\* 原生前缀连接可以正常关闭，接收返回路径不删除这个 token。
\* 先完成前缀再启动后续连接，是本模型选择的一种合法调度，不是源码中的全局阶段锁。
\* [ZH-NOTE-END BeginConnections]

\* 1120-1128: existing-token entrance check, NOT a quota reservation.
Enter(c) ==
    /\ phase = "Race" /\ pc[c] = "Entry"
    /\ MetadataValid /\ remaining # 0
    /\ pc' = [pc EXCEPT ![c] = "Ready"]
    /\ UNCHANGED <<remaining, accepted, backendCalls, checkedRemaining,
                    phase, prefixPC, prefixDone>>
\* [ZH-NOTE-BEGIN Enter]
\* Enter(c) 是连接 c 复用已有 token 时的入口检查成功分支。
\* 它对应 handle_i_agent_connection 中对 token_is_valid 的调用，早于每条消息的检查。
\* 元数据有效且余额非零时，将 pc[c] 从 Entry 改为 Ready。
\* [pc EXCEPT ![c] = "Ready"] 表示构造一个新函数，仅替换 c 对应的值。
\* 因此 pc' 接收这个新函数，其他连接的程序位置保持原值。
\* 这里只检查并允许进入，既不扣额度，也不预留一个名额。
\* [ZH-NOTE-END Enter]

RejectEntry(c) ==
    /\ phase = "Race" /\ pc[c] = "Entry"
    /\ (~MetadataValid \/ remaining = 0)
    /\ pc' = [pc EXCEPT ![c] = "EntryRejected"]
    /\ UNCHANGED <<remaining, accepted, backendCalls, checkedRemaining,
                    phase, prefixPC, prefixDone>>
\* [ZH-NOTE-BEGIN RejectEntry]
\* RejectEntry(c) 描述已有 token 的连接入口被拒绝。
\* 元数据无效或余额为零时，将该连接标为 EntryRejected。
\* 额度、累计准入和后端调用计数都不变化。
\* 这保留了真实代码的入口检查，模型没有假定所有新连接都可以无条件进入会话。
\* 入口拒绝与下面的消息级拒绝分别记录，便于解释可达路径。
\* [ZH-NOTE-END RejectEntry]

\* 595, 598, 348-381: every parsed message is checked again.
\* Non-quota checks are summarized by stable MetadataValid, never by
\* assuming token_is_valid itself is always true.
Check(c) ==
    /\ phase = "Race" /\ pc[c] = "Ready"
    /\ MetadataValid /\ remaining # 0
    /\ pc' = [pc EXCEPT ![c] = "Checked"]
    /\ checkedRemaining' = [checkedRemaining EXCEPT ![c] = remaining]
    /\ UNCHANGED <<remaining, accepted, backendCalls, phase, prefixPC,
                    prefixDone>>
\* [ZH-NOTE-BEGIN Check]
\* Check(c) 对应 receive_conversation 从消息提取 token 后再次调用 token_is_valid。
\* 连接须已经处于 Ready；元数据有效且剩余额度非零，才进入 Checked。
\* checkedRemaining[c] 记录这个连接在检查时观察到的余额。
\* 它只是辅助快照：后面的扣减仍读取共享 remaining，不读取这份快照。
\* 这一步不修改 remaining、accepted 或 backendCalls。
\* 检查返回后锁已释放，因此可能先后有两个连接都检查到余额 1。
\* 这正是需要保留的检查与扣减之间的执行间隙。
\* [ZH-NOTE-END Check]

Reject(c) ==
    /\ phase = "Race" /\ pc[c] = "Ready"
    /\ (~MetadataValid \/ remaining = 0)
    /\ pc' = [pc EXCEPT ![c] = "Rejected"]
    /\ UNCHANGED <<remaining, accepted, backendCalls, checkedRemaining,
                    phase, prefixPC, prefixDone>>
\* [ZH-NOTE-BEGIN Reject]
\* Reject(c) 是每条消息的有效性检查失败分支。
\* 它只适用于 Ready 位置，元数据无效或余额为零时将该连接设为 Rejected。
\* 被拒绝的请求没有扣减，也不增加 accepted 或 backendCalls。
\* 已经处于 Checked 的连接不会回到这里重新检查。
\* 因此某连接看到余额耗尽而被拒绝，不代表另一个早已通过检查的连接也会被重新拦截。
\* [ZH-NOTE-END Reject]

\* 604-605: guard only on the prior control location, not remaining > 0.
\* accepted is an observer of quota admission; it is NOT a native variable.
Consume(c) ==
    /\ phase = "Race" /\ pc[c] = "Checked"
    /\ remaining' = IF remaining = 0 THEN 0 ELSE remaining - 1
    /\ accepted' = accepted + 1
    /\ pc' = [pc EXCEPT ![c] = "Debited"]
    /\ UNCHANGED <<backendCalls, checkedRemaining, phase, prefixPC,
                    prefixDone>>
\* [ZH-NOTE-BEGIN Consume]
\* Consume(c) 是并发超额分析的关键动作，直接保留原生第二段加锁逻辑。
\* 它只要求 pc[c] = Checked，没有 remaining > 0 的额外启用条件。
\* 即使别的连接已将余额减为 0，该连接仍可执行这个动作。
\* 例如 remaining 为 0 时，截断扣减仍得到 0，但 accepted 继续加一。
\* 同一步中，pc[c] 变为 Debited；所有带撇号的等式共同描述一个下一状态。
\* 这不是先写 remaining 再用新值计算 accepted 的顺序赋值代码。
\* SourceAccounting 检查这些观察计数的一致性；QuotaSafety 才检查有没有超过初始额度。
\* [ZH-NOTE-END Consume]

\* 609-634: ordinary message, first request on this connection (i = 0).
\* Record invocation separately from quota admission. Done means this
\* bounded observation is complete, not task completion or delivery.
InvokeBackend(c) ==
    /\ phase = "Race" /\ pc[c] = "Debited"
    /\ backendCalls' = backendCalls + 1
    /\ pc' = [pc EXCEPT ![c] = "Done"]
    /\ UNCHANGED <<remaining, accepted, checkedRemaining, phase, prefixPC,
                    prefixDone>>
\* [ZH-NOTE-BEGIN InvokeBackend]
\* InvokeBackend(c) 适用于已经完成扣减的连接，独立记录后端调用事件。
\* backendCalls 加一，pc[c] 变为 Done；额度和准入计数保持不变。
\* 它对应普通消息通过终止消息检查、连接内查询上限检查之后调用 local_agent.run。
\* 本次并发连接只有第一条请求，原生 i = 0，查询上限不会拦截这一步。
\* Done 只表示本模型对这条请求的观察结束，不表示业务成功或响应送达。
\* 某个准入反例可能在到达这个动作之前就已被 TLC 找到。
\* [ZH-NOTE-END InvokeBackend]

Terminated ==
    \/ phase = "Aborted"
    \/ /\ phase = "Race"
       /\ \A c \in Connections : pc[c] \in FinalStates
\* [ZH-NOTE-BEGIN Terminated]
\* Terminated 是关于当前状态的终止判断，本身不会修改任何变量。
\* 它由两个分支“或者”组成：前缀已经 Aborted；或者处于 Race 且所有连接都在 FinalStates。
\* \A c \in Connections : ... 表示集合中每个连接都满足后面的条件。
\* 嵌套的 /\ 要求并发阶段条件和所有连接结束同时成立。
\* 这是本次有界场景的终止条件，不是服务器进程终止条件，也没有承诺一定最终到达。
\* [ZH-NOTE-END Terminated]

\* Stutter ONLY at legitimate terminal states for TLC's Next exploration.
\* Deadlock checking remains enabled; unexpected nonterminal blocking is
\* not hidden by a global TRUE/UNCHANGED action or a -deadlock flag.
TerminalStutter == Terminated /\ UNCHANGED vars
\* [ZH-NOTE-BEGIN TerminalStutter]
\* TerminalStutter 给已经 Terminated 的状态提供一个所有变量不变的显式自环。
\* UNCHANGED vars 相当于要求八个状态分量的下一值都等于当前值。
\* 这样 TLC 在正常终止时仍能找到 Next 后继，不把有界执行结束误报成意外阻塞。
\* 本模型没有关闭死锁检查，也没有在 Next 中给每个非终止状态都加自环。
\* 注意区分：后面的 Spec 使用 [Next]_vars，语义上仍在任意状态允许隐式停顿。
\* 因此“只在终止状态有自环”仅指 Next 中这里显式定义的这个动作。
\* [ZH-NOTE-END TerminalStutter]

Next ==
    \/ PrefixCheck
    \/ PrefixReject
    \/ PrefixConsume
    \/ PrefixBackend
    \/ BeginConnections
    \/ \E c \in Connections :
           Enter(c) \/ RejectEntry(c) \/ Check(c) \/ Reject(c)
           \/ Consume(c) \/ InvokeBackend(c)
    \/ TerminalStutter
\* [ZH-NOTE-BEGIN Next]
\* Next 汇总允许发生的下一步，\/ 表示多个动作之间的选择。
\* 前五个动作控制顺序前缀；带 \E 的部分允许某个连接执行它当前启用的动作。
\* \E c \in Connections : ... 表示存在一个连接 c，使其动作能构成这一步。
\* 每次全局转换选择一个启用的动作，不要求各连接按固定次序轮流运行。
\* 同一连接由 pc 保证程序顺序，不同连接可以在 Check 与 Consume 之间交错。
\* 这不是按 Next 公式书写顺序执行全部动作，也没有自动加入公平调度条件。
\* [ZH-NOTE-END Next]

Spec == Init /\ [][Next]_vars
\* [ZH-NOTE-BEGIN Spec]
\* Spec 是模型的完整行为描述：首状态满足 Init，之后的每一步满足 [Next]_vars。
\* [] 是“始终”；[Next]_vars 等价于 Next 或者 vars 完全保持不变。
\* 因此整个公式允许正常动作，也允许不改变已建模状态的停顿步骤。
\* 这里没有弱公平 WF 或强公平 SF 条件，不承诺某个已启用动作最终一定执行。
\* 本轮主要检查安全性质；不能由此宣称没有饥饿、最终响应一定交付等活性结论。
\* 语法释义参照官方摘要：https://lamport.azurewebsites.net/tla/summary-standalone.pdf 。
\* [ZH-NOTE-END Spec]

TypeOK ==
    /\ remaining \in 0..InitialQuota
    /\ accepted \in 0..(PrefixUsed + Cardinality(Connections))
    /\ backendCalls \in 0..(PrefixUsed + Cardinality(Connections))
    /\ pc \in [Connections -> ConnectionStates]
    /\ checkedRemaining \in [Connections -> 0..InitialQuota]
    /\ phase \in {"Prefix", "Race", "Aborted"}
    /\ prefixPC \in PrefixStates
    /\ prefixDone \in 0..PrefixUsed
\* [ZH-NOTE-BEGIN TypeOK]
\* TypeOK 检查每个状态分量是否落在预期范围中，定义本身不会限制 Next 生成状态。
\* 只有在 .cfg 中列为 INVARIANT(S)，TLC 才会检查它，并在发现违反时报告。
\* remaining 允许从 0 到初始额度；状态标签、前缀完成数等也各有取值范围。
\* [Connections -> ConnectionStates] 是函数集合，要求每个连接都有一个合法位置标签。
\* accepted 和 backendCalls 的上界是前缀次数加连接数，因为后续每连接最多一个请求。
\* 这个上界故意不是 InitialQuota：模型必须允许生成潜在超额状态，再让安全性质发现它。
\* 因此 TypeOK 成立只能说明状态形状正确，不能说明配额执行正确。
\* [ZH-NOTE-END TypeOK]

AdmittedConnections == {c \in Connections : pc[c] \in {"Debited", "Done"}}
\* [ZH-NOTE-BEGIN AdmittedConnections]
\* AdmittedConnections 是从当前 pc 计算出来的集合，不是新的状态变量。
\* {c \in Connections : 条件} 表示筛选满足条件的连接。
\* 处于 Debited 或 Done 的连接都已经完成了额度扣减，所以都计入准入。
\* 这个集合大小用于核对 accepted 是否如实记录了发生过的准入事件。
\* [ZH-NOTE-END AdmittedConnections]
BackendConnections == {c \in Connections : pc[c] = "Done"}
\* [ZH-NOTE-BEGIN BackendConnections]
\* BackendConnections 筛选 pc[c] = Done 的后续连接。
\* 在本模型中，只有 InvokeBackend 会把连接推进到 Done，因此这些连接都已记录后端调用。
\* Cardinality(BackendConnections) 就是后续并发阶段已记录的后端调用数量。
\* 这个推导依赖本模型每连接一次请求的范围，不能直接用于任意多轮会话。
\* [ZH-NOTE-END BackendConnections]
PendingPrefixAdmission == IF prefixPC = "Debited" THEN 1 ELSE 0
\* [ZH-NOTE-BEGIN PendingPrefixAdmission]
\* PendingPrefixAdmission 表示顺序前缀中是否有一条已经准入、尚未完成后端观察的请求。
\* prefixPC = Debited 时为 1，其余位置为 0。
\* 因为 prefixDone 只在 PrefixBackend 时增加，核对 accepted 时必须补上这个暂挂的 1。
\* 它是当前状态的派生表达式，不会额外扣额度或改变模型控制流。
\* [ZH-NOTE-END PendingPrefixAdmission]

\* Structural sanity checks; these should hold EVEN when quota is exceeded.
SourceAccounting ==
    /\ accepted = prefixDone + PendingPrefixAdmission
                     + Cardinality(AdmittedConnections)
    /\ backendCalls = prefixDone + Cardinality(BackendConnections)
    /\ backendCalls <= accepted
    /\ remaining = IF accepted <= InitialQuota
                   THEN InitialQuota - accepted ELSE 0
\* [ZH-NOTE-BEGIN SourceAccounting]
\* SourceAccounting 是观察计数和状态之间的一致性检查，共有四项。
\* 第一项：累计准入 = 已完成前缀 + 前缀暂挂准入 + 已准入的后续连接数。
\* 第二项：后端调用 = 已完成前缀 + 后续已记录后端调用的连接数。
\* 第三项：后端调用不超过准入，因为源码先扣减再进入后端调用。
\* 第四项：余额按累计准入做截断扣减；超过初始额度后，余额仍固定为零。
\* 所以它与 accepted > InitialQuota 可以同时成立，不能替代真正的额度安全性质。
\* 这里是待检查的状态关系，不是把期望结果预先塞进 Next 的执行条件。
\* [ZH-NOTE-END SourceAccounting]

QuotaSafety == accepted <= InitialQuota
\* [ZH-NOTE-BEGIN QuotaSafety]
\* QuotaSafety 是本研究核心安全性质：累计配额准入不得超过初始额度。
\* 例如 InitialQuota 为 50 时，accepted 到 51 就违反它，即使 remaining 仍为 0。
\* 在配置中将它列为不变量，TLC 就会检查所选有限配置的可达状态。
\* 这个定义没有禁止模型产生超额状态；原版逻辑能到达时应由工具给出反例。
\* 检查范围由模型、配置和假设共同决定，不是对完整 Python 实现的任意参数证明。
\* [ZH-NOTE-END QuotaSafety]
BackendQuotaSafety == backendCalls <= InitialQuota
\* [ZH-NOTE-BEGIN BackendQuotaSafety]
\* BackendQuotaSafety 单独检查后端调用数是否超过初始额度。
\* 它与 QuotaSafety 使用不同计数，也可能在不同执行位置首次被违反。
\* 如果 TLC 因 QuotaSafety 先停止，不能仅凭那条截断反例就说后端已经调用超额。
\* 因此另有配置只针对 BackendQuotaSafety 搜索，保留两个事件层次的区别。
\* 后端调用次数仍不等于成功完成的业务任务数。
\* [ZH-NOTE-END BackendQuotaSafety]

\* Witness queries, NOT desired safety requirements. A violation of one
\* below means its named event is reachable; configs label this explicitly.
NoAdmission == accepted = 0
\* [ZH-NOTE-BEGIN NoAdmission]
\* NoAdmission 的字面意思是“还没有发生任何准入”。
\* 这里故意把它作为可达性查询：若 TLC 找到违反它的状态，就说明准入事件可达。
\* 这用于排除模型把正常请求全部挡住、导致配额性质空泛成立的情况。
\* 所以此查询出现 invariant violated 代表找到了所需见证，不是发现了新的安全问题。
\* 它不是希望系统永远满足的业务安全要求，配置中也与真正的安全检查分开。
\* [ZH-NOTE-END NoAdmission]
NoMessageRejection == \A c \in Connections : pc[c] # "Rejected"
\* [ZH-NOTE-BEGIN NoMessageRejection]
\* NoMessageRejection 表示没有任何连接进入消息级 Rejected。
\* 若把它列为查询不变量并得到反例，就证明至少一条消息级拒绝路径可达。
\* 它不检查 EntryRejected，因此不能用单纯的入口拒绝来冒充消息级拒绝见证。
\* 与 NoAdmission 一样，这属于故意反向写出的可达性查询。
\* 判断输出时必须先看配置检查的性质名称，不能把所有 invariant violated 都称为漏洞。
\* [ZH-NOTE-END NoMessageRejection]

=============================================================================
\* [ZH-NOTE-BEGIN footer]
\* 连续等号结束本模块。到这里模型的代码和逐段说明全部结束。
\* 本副本只增加中文注释并更改模块名；原模型、配置和历史验证证据均保持原样。
\* 语法中的动作描述状态之间的关系；检查与扣减的两次加锁区间仍然是两个不同动作。
\* [ZH-NOTE-END footer]
