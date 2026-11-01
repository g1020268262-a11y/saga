# OTK 转交模型与本地 SAGA 的对应

本表解释模型选择，不声称建立 Python 到 Tamarin 的形式化精化关系。具体输入版本由每次证据目录中 `manifest.json` 的源码 SHA-256 和 `inputs/saga/` 快照确定；行号用于方便阅读。

| 模型位置／规则 | 本地源码 | 保留的含义与抽象 |
|---|---|---|
| `Setup` / `Registered` / `Client` | `saga/agent.py:958–974, 999–1045, 1155–1159`；`saga/provider/provider.py:409–427` | 发送方 TLS 身份、Provider stamp 与访问控制公钥已经正确绑定。初始化直接给出绑定，不展开注册、证书及签名验证。 |
| `Sender_Requests_Access` / `TLSAccessRequest` | `saga/agent.py:280–289` | 以真实发送方身份请求接收方 A 的材料；请求在理想 mTLS 中传输。 |
| `Provider_Issues_OTK` 的 `ProviderAllows` | `saga/provider/provider.py:434–451` | policy 结果预置为 B/C 均允许；拒绝对照为 C 明确拒绝。未展开任意字符串模式或 matcher 优先级。 |
| `ProviderCredit` 与 `NoProviderCredit` | `saga/provider/provider.py:458–469, 499–517` | 每发送方检查、扣减领取配额，固定初值 1，用一次性线性事实实现；不删除该守卫以人为制造超发。 |
| `ProviderUnusedOTK` 与 `TLSOTKResponse` | `saga/provider/provider.py:524–549, 565–576` | 从 Provider 池中移除并返回一个 OTK；Provider 发放状态与 A 的本地未使用状态独立。 |
| `B_Forwards_OTK_To_C` / `C_Receives_Forwarded_OTK` | **威胁模型新增行为，无对应诚实发送方函数** | B 自愿共享领取到的公有 OTK；不要求长期私钥泄露或安全信道破坏。C 本来有自己的注册身份及私钥。该规则不是给诚实发送方实现增加了新功能。 |
| `Sender_Requests_Token` / `LocalAllows` | `saga/agent.py:794–836, 940–974, 1021–1045` | C 使用自己的身份、Provider 认证材料和 PAC，提交该 OTK；A 执行自己的本地策略拒绝检查。没有给 A 引入 Provider 的剩余计数。 |
| `ReceiverUnusedOTK` / `Receiver_Issues_Token` | `saga/agent.py:1062–1076` | 检查具体 OTK 是否在本地字典中，并在锁内删除以保证单次消费；该路径没有核对最初领取者的映射。 |
| DH、KDF 与 `Sender_Decrypts_Token` | `saga/agent.py:849–872, 1078–1094` | 保留双方 DH 输入及共同 KDF 域标签；字节编码、HKDF 与 X25519 用理想符号运算抽象。 |
| token 内容和 `ActiveToken` | `saga/agent.py:295–333, 1101–1103`；`saga/common/crypto.py:447–512` | 随机 token 内容绑定实际发送方 PAC；AES-GCM 抽象成理想对称加密，活动 token 由 A 记录。没有加入到期时钟。 |
| `Receiver_Accepts_Application_Request` | `saga/agent.py:337–381, 594–605` | token 必须存在、实际发送方 PAC 必须匹配。只观察每个新 token 的第一次请求；不把模型的线性 `ActiveToken` 当作实现 Q_MAX 竞态修复。 |

## 不混淆的三个数量

1. Provider 对 B/C 各自发放过多少个 OTK：本模型保留初值 1 的领取限制。
2. 某个 OTK 在 A 处被消费多少次：本模型保留 OTK 本地单次消费。
3. 一个 token 可以承载多少次应用请求：属于 ACT 的 `communication_quota/Q_MAX`；本模型只观察首次请求，不验证其一般上限或并发安全。

## 不能从本模型直接推出的结论

- Provider 真实实现超额发放 OTK，或被绕过了 MongoDB 原子扣减。
- C 破解了 DH、假冒 B，或直接解密／使用了发给 B 的已有 token。
- 默认策略拒绝的发送方能够通过；主轨迹的 C 在本地策略上仍获允许。
- 完整注册、策略更新、撤销、任意整数预算或任意恶意 Agent 的全部行为已经验证。
- 模型见证已经在真实 TLS／MongoDB／Agent backend 上重放。

“成功使用要求同人领取”与“使用不同 OTK 的数量不超过自身领取配额”是候选强性质。发放策略的字面计数限制，与这些强性质是否属于论文预期保证，需要在结果解释时分别说明。
