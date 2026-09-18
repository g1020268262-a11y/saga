# SAGA Provider 与接收方独立授权门控控制模型

本次修订解决旧版 `agent_communication_authz_chat_allow.pv` / `agent_communication_authz_chat_deny.pv` 共用一张 `Authorized(A,B)` 表的问题。旧版拒绝场景没有插入该表，因此只能说明“至少一道门控阻断了聊天”，不能分别判断 Provider 与 PeerA 接收方的作用。旧模型与既有证据保持原样，供追溯；以下三个新模型是当前控制实验。

## 模型变化

- Provider 读取 `ProviderAuthorized(A,B)`，通过后发布访问材料并记录 `ProviderRelease(A,B)`。
- PeerA 读取 `ProviderReleased(A,B)` 与独立的 `ReceiverAuthorized(A,B)`，通过后才签发 token。`ProviderReleased` 是 **Provider 放行已传递到接收方** 的额外控制流程抽象，不是原通信模型或生产 Python 代码中已证明存在的机制。
- 场景输入用 `ScenarioProviderAllow/Deny`、`ScenarioReceiverAllow/Deny` 表示。它们只标记人为设定的允许/拒绝状态；新模型不再把初始化事件称作 `MatcherAllow`，也不查询它来声称验证了策略匹配器。
- `ChatAccept` 仍表示 PeerA 校验已签发的 wire token 与发送方 PAC 后接受一条消息。`Accept` 仍仅表示 PeerB 收到并验证 token。`tls_chat` 为 private channel，抽象经过认证的聊天传输；本模型不验证 TLS 本身。

三个模型由 [build_authz_chat_gates.py](build_authz_chat_gates.py) 从历史控制模型生成，分别是 [双允许](proverif/agent_communication_authz_chat_p_allow_r_allow.pv)、[Provider 拒绝／接收方允许](proverif/agent_communication_authz_chat_p_deny_r_allow.pv)、[Provider 允许／接收方拒绝](proverif/agent_communication_authz_chat_p_allow_r_deny.pv)。除场景状态外，它们的协议和查询相同。`ProviderRelease`、`TokenIssue`、`ChatAccept` 的单独可达性查询用来定位阻断阶段；双允许场景另检查 `ChatAccept` 与先前 `TokenIssue`、`ChatSend` 的对应关系。

## ProVerif 2.05 结果

| 场景 | ProviderRelease 可达 | TokenIssue 可达 | ChatAccept 可达 |
|---|---|---|---|
| Provider 允许、接收方允许 | 是 | 是 | 是 |
| Provider 拒绝、接收方允许 | 否 | 否 | 否 |
| Provider 允许、接收方拒绝 | 是 | 否 | 否 |

双允许场景中，`ChatAccept ==> TokenIssue` 与 `ChatAccept ==> ChatSend` 均为 `true`，且 `ChatAccept` 本身可达，所以不是空真。两个单侧拒绝场景中的对应关系也为 `true`，但由于 `ChatAccept` 不可达，它们是空真，不能据此推断消息级认证强度。

[运行器](run_authz_chat_gates.py)的七项机械检查全部通过。验证从干净的 `my-modification` 提交 `2685d956b2f98fb1c4634dd6ec817fe4d9c448b8` 启动；三个模型退出码均为 `0`，输入文件 SHA-256 与 Git HEAD 在运行前后保持一致。运行器在 [证据目录](evidence/authz-chat-gates-20260918T023621017067Z/) 保存完整 stdout/stderr、[结果摘要](evidence/authz-chat-gates-20260918T023621017067Z/verification-summary.txt)、[manifest](evidence/authz-chat-gates-20260918T023621017067Z/manifest.json) 和 ProVerif 版本信息。manifest 使用仓库相对路径记录模型与命令，不包含本机绝对路径。

这些结果只证明**上述额外门控抽象**在三个设定场景中的行为。模型不计算真实 contact rulebook 的最具体规则，不执行 Python `match()`，也不覆盖 token 过期、配额、撤销、真实 TLS 或业务处理副作用。因此它不能被表述为对生产实现授权正确性或实际越权路径的形式化证明。
