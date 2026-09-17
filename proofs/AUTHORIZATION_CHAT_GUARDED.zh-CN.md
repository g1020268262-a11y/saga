# SAGA 聊天消息授权控制模型

本阶段在 Stage 1 的 token 接收模型之外，建立一个**授权门控正确执行**时的单消息模型，用来检查事件放置、token 绑定和正常/拒绝两条控制路径。它不表示当前 Python matcher 的行为，也不构造策略拒绝但消息被接受的执行链。

## 模型与角色

新增模型：

- `proverif/agent_communication_authz_chat_allow.pv`：固定允许 PeerB 联系 PeerA。
- `proverif/agent_communication_authz_chat_deny.pv`：固定拒绝 PeerB 联系 PeerA。

PeerA 是 token 签发方、聊天接收方；PeerB 是 token 接收方、聊天发送方。所有新事件的前两个参数均为 `(PeerA, PeerB)`。Stage 1 的 `Accept` 保留为“PeerB 解密并验签后收到 token”，而 `ChatAccept` 才表示 PeerA 通过本模型的 token 检查并即将处理一条业务消息。

`Authorized(A,B)` 是抽象授权门控：允许模型在启动时插入该状态；拒绝模型不插入。Provider 发布访问材料前、PeerA 签发 token 前都必须读取它。该门控并未计算真实 rulebook 或运行 `match()`，因此允许模型的 `PolicyAllow` 只是预置场景前提，不能被解释为对生产实现授权正确性的证明。

`tls_chat` 是 private channel，用来抽象已认证且保密的 Agent-to-Agent 传输；本模型不验证 TLS 自身。`ActiveToken(A,B,token_wire,PAC_B)` 记录 PeerA 已生成的加密 wire token 及 PeerB 的 PAC。PeerB 解密并验签后提交该 wire token 和一条新消息；PeerA 只有在发送方身份与 `ActiveToken` 四元组匹配后才记录 `ChatAccept`。

单消息足以检查接收事件的可达性与关联关系。本模型未表达 token 过期、配额递减、撤销、多轮会话、Provider 数据库细节和工具调用；`ChatAccept` 不等于 `local_agent.run()` 的具体副作用。

## 查询与证据

查询包括 `ChatAccept` 可达性，以及 `ChatAccept` 对 `PolicyAllow`、`MatcherAllow`、`TokenIssue` 和 `ChatSend` 的 correspondence。拒绝模型的 correspondence 如果为真，仍须由单独的可达性查询说明是否只是不可达所致。

运行器 `run_authz_chat_guarded.py` 对两个模型保存完整 stdout/stderr、全部 `RESULT`、ProVerif 可执行文件和输入文件 SHA-256、Git HEAD 与前后状态，并对预期的控制结果做机械检查。基线、Stage 1 和 Python 文件在运行期间仅参与哈希检查，不会被修改或重复求解。

## ProVerif 2.05 实测结果

本次在 `my-modification`、HEAD `78e06379ec01f49d7b07067402ee60585dfe36c4` 上运行。两个模型均以退出码 `0` 完成；allow 用时 761.319 秒，deny 用时 365.059 秒。运行器全部八项机械检查通过。

| 查询 | allow 控制 | deny 控制 | 正确解释 |
|---|---|---|---|
| `not event(ChatAccept(A,B,t,m))` | `false` | `true` | allow 中消息接受可达；deny 中不可达 |
| `ChatAccept ==> PolicyAllow` | `true` | `true` | allow 中为非空路径上的对应关系；deny 中因接受不可达而空真 |
| `ChatAccept ==> MatcherAllow` | `true` | `true` | 同上 |
| `ChatAccept ==> TokenIssue` | `true` | `true` | allow 中已接受的 wire token 有先前签发事件 |
| `ChatAccept ==> ChatSend` | `true` | `true` | allow 中已接受的消息有先前发送事件 |

原始 [verification-summary.txt](evidence/authz-chat-guarded-20260917T080131985337Z/verification-summary.txt)、两个模型的完整 stdout/stderr、[manifest.json](evidence/authz-chat-guarded-20260917T080131985337Z/manifest.json) 和验证器版本均保存在 [本次证据目录](evidence/authz-chat-guarded-20260917T080131985337Z/)。manifest 记录了运行命令、耗时、可执行文件与源码哈希、Git 状态和检查结果。运行前后 HEAD 与所有受保护输入哈希均未改变；原注册模型、原通信模型和 Stage 1 扩展模型的当前哈希也与 Stage 1 manifest 一致。

这些结果仅说明：在**预先一致的授权门控**下，模型能够接受一条有签发和发送依据的消息，并在拒绝控制下阻断该消息。`PolicyAllow` 在 allow 控制中是场景前提，并非由 `match()` 或 rulebook 求值推得。本阶段没有把 Python matcher 的顺序敏感行为接入 ProVerif，也没有生成拒绝策略下消息被接受的轨迹。因此不能据此声称参考实现存在已经形式化重建的端到端越权。
