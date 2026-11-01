# 接收方接受的身份是否经过 Provider 确认及 OTK 发放

本次以原始 [agent_communication.pv](proverif/agent_communication.pv) 为基线，只增加观察事件和 query，生成 [agent_communication_provider_otk.pv](proverif/agent_communication_provider_otk.pv)。原文件不改写；删除副本中的 `PROVIDER-OTK-BEGIN/END` 区域，可以逐字节还原原文件。

## 要验证的关系

对接收方 A 而言，如果 A 接受发起方 B 的身份并进入 token 签发步骤，则此前 Provider 应当：

1. 确认过同一个 B 的身份、设备信息和访问控制公钥；
2. 为同一对 A、B 发放过 A 的同一个 OTK，并关联同一个 B 的访问控制公钥。

这里 OTK 是 **A 的公有一次性密钥，由 Provider 提供给 B**；并非 B 自己的 OTK。Provider 对 B 注册时上传的 `OTK1_B` 的认证不能替代这一发放关系。

论文 [IV-D2 与 IV-E](https://arxiv.org/html/2504.21034v2#S4.SS5) 把接触授权、A 的 OTK 获取和后续 token 建立分成不同步骤。原始 ProVerif 模型的现有认证 query 没有直接连接“接收端接受 B”与“向 B 发放 A 的 OTK”。

主 query 是：

```proverif
query receiver: bitstring, initiator: bitstring,
      ed: bitstring, pac: pkey, otk: pkey;
  event(ReceiverAcceptsInitiator(receiver, initiator, ed, pac, otk))
  ==> event(ProviderConfirmsInitiator(initiator, ed, pac))
      && event(ProviderIssuesOTK(receiver, initiator, ed, pac, otk)).
```

共享变量要求身份和密钥一致：不能拿“Provider 确认过其他实体”或“给其他实体发过另一个 OTK”充数。该查询是非单射事件对应：要求此前存在匹配事件，不要求每次接受对应一个新的、唯一的 OTK 发放事件。

## 事件插入位置

| 新事件 | 原始位置 | 精确含义 |
|---|---|---|
| `ProviderConfirmsInitiator(B, ED_B, PAC_B)` | Provider 验证 B 的证书与签名、产生 `EndProviderAuthB` 后 | 注册身份认证完成；不代表已经通过 A 的接触策略 |
| `ProviderIssuesOTK(A, B, ED_B, PAC_B, OTK_A)` | Provider 原有 `out(prov_b, ...)` 之前 | 记录本次即将发出 OTK 材料及其关联身份；不额外断言材料经保密认证信道送达 B |
| `ReceiverAcceptsInitiator(A, B, ED_B, PAC_B, OTK_A)` | A 的 `EndAgentAuthA` 后、输出加密 token 前 | A 验证 Provider 对 B 的签名，并准备签发 token；不代表 TLS 握手或 B 的密钥持有证明完成 |
| `InitiatorCompletesConnection(A, B, ED_B, PAC_B, OTK_A)` | B 解密 token、验证 A 的签名并产生 `EndAgentAuthB` 后 | B 已收到并验证 token；仍不是应用消息接受事件 |

`receiver` 和 `initiator` 分别是 A、B 的 agent ID，`ed` 是 B 的设备／网络信息，`pac` 是 B 的访问控制公钥，`otk` 是 A 的一次性公钥。查询中的实体是这些字段标识的逻辑身份；不能仅凭记录中的 B 身份就认定网络消息实际由 B 进程发送。

## 为什么增加辅助 query

新增五条查询，保留原始十一条查询，共十六条：

- 主 query：A 接受时，Provider 确认与 OTK 发放均有匹配事件。
- 拆分 query：A 接受时，单独检查 Provider 的注册身份确认，用于区分身份认证与 OTK 发放。
- 完成端 query：把左侧换为 `InitiatorCompletesConnection`，检查 B 已验证 token 时同样的对应关系。
- 两条可达性 query：确认 A 的接受点、B 的完成点可达，避免把从不执行的成功路径当作安全。

可达性查询输出 `not event(...) is false` 表示该事件可达。它不是主对应性质的失败；必须分别看每条 `RESULT`。

## 原模型边界

副本没有新增策略检查、授权表、私有信道、OTK 消耗或密钥确认消息，没有通过添加执行守卫使目标自动成立。

原模型的 `prov_b` 和代理消息信道 `c` 都公开。A 在注册阶段就将 OTK 公钥及签名发到 `c`；A 收到的 token 请求元组没有 OTK 字段，而是直接使用本地固定的 `SOTK1_A`。Provider 也没有单独的访问请求、contact-policy 计算或 OTK 配额检查过程，其发放操作是注册流程之后的输出。

这些位置可直接核对基线文件：19 行声明公开 `prov_b`，99 行发布 A 的注册材料，110 行接收未包含 OTK 的请求元组，225 行完成 B 的 Provider 认证，230 行输出 A 的 OTK 材料。

因此，`ProviderIssuesOTK` 只能观察原模型的发放位置，不能被重新命名为“真实 contact policy 正确判定为允许”来替代缺失的策略过程。模型只包含固定 A、B 身份及它们的复制会话；这也不等于已覆盖任意恶意注册实体。

原生实现包含本副本未补建的检查：`provider.py:409–427` 将请求方与 TLS 客户端证书关联，444–451 行执行 matcher；`agent.py:951` 执行接收方 matcher，958–974 行将对端证书与 Provider stamp 验证关联，1062–1076 行接收并消费具体 OTK。若对应 query 不成立，应先检查反例依赖哪些建模抽象，不能直接称为这些原生检查被绕过。

## 运行及证据

```powershell
& '.\proofs\consumer_validation\.runtime\venv\Scripts\python.exe' -B '.\proofs\run_provider_otk_query.py'
```

需要可执行的 ProVerif；可用 `--proverif 'D:\Proverif\proverif2.05\proverif.exe'` 指定。`--build-only` 只构建并核对副本，`--timeout` 限制每次工具运行时间。

脚本先解析再验证，并创建独立 `proofs/evidence/provider-otk-<UTC时间>/`，保存基线与副本、脚本、源码及工具哈希、原始输出、结果摘要和运行清单。脚本退出 0 表示工具正常完成且十六条结果与文件完整性检查完成，不代表所有 query 为真。

副本保留了基线文件原有的历史验证输出注释。该注释不是本次新增 query 的结果；本次结果以新证据目录中的原始输出为准。

## 本次实际结果

ProVerif 2.05 已运行完成：[完整报告](evidence/provider-otk-20261025T023748919760Z/REPORT_ZH.md)、[十六条原始结论](evidence/provider-otk-20261025T023748919760Z/verification-summary.txt)。

| 新增对应关系 | 结果 |
|---|---|
| A 接受 ⇒ Provider 身份确认 | `true` |
| A 接受 ⇒ Provider 身份确认且 OTK 发放 | `false`，反例已重建 |
| B 验证 token 完成 ⇒ Provider 身份确认且 OTK 发放 | `false`，反例已重建 |

两个新增成功点均可达，原始十一条结果保留。两条反例的具体执行包含 Provider 对 B 的注册认证，却没有对应的 `ProviderIssuesOTK` 事件。主反例利用公开身份材料触发 A 的接受；B 完成点的反例还利用公开注册材料拼装 `prov_b` 输入。它们反映上述原模型抽象下的对应关系缺口，不是原生 TLS／授权检查绕过的证明。

轨迹分别保存在 [A 接受反例](evidence/provider-otk-20261025T023748919760Z/receiver-accept.trace.txt) 和 [B 完成反例](evidence/provider-otk-20261025T023748919760Z/initiator-complete.trace.txt)。
