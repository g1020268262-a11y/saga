# Provider 身份确认与 OTK 发放对应：本次验证结果

在固定上游原始通信模型中仅增加观察事件与查询后，ProVerif 2.05 给出了十六条结果，并对两个新增对应关系重建了反例。未修改协议消息、执行守卫或原文件，没有运行原生网络实验。

## 结果

| 检查 | 工具结果 | 含义 |
|---|---|---|
| 原始七个事件可达性 | 七条 `not event(...) is false` | 原始成功路径可达 |
| 原始三个认证对应关系 | 三条 `true` | 原始认证结果保留 |
| 原始 token 保密性 | `true` | 原始保密性结果保留 |
| A 接受 B ⇒ Provider 已确认 B | `true` | 接受的身份信息有匹配的 Provider 注册认证事件 |
| A 接受 B ⇒ Provider 已确认 B 且为其发放 A 的同一 OTK | `false`，轨迹已重建 | 主目标在本模型中不成立 |
| B 收到并验证 token ⇒ 同样的 Provider 确认与 OTK 发放 | `false`，轨迹已重建 | 换成 B 的完成点，完整对应仍不成立 |
| 两个新增成功事件可达性 | 两条 `not event(...) is false` | 新增对应检查不是因为成功事件不可达而空成立 |

原始十一条结果与固定模型的历史基线结果逐条相同。完整原始结论见 [verification-summary.txt](verification-summary.txt)，原始推导与具体执行见 [verify.stdout.txt](verify.stdout.txt)。验证耗时约 716 秒；时间只描述本次运行。

## 主反例：A 的本地接受点

[receiver-accept.trace.txt](receiver-accept.trace.txt) 是原始输出第 4913–5189 行的逐字摘录。

该具体执行中，Provider 完成 B 的注册认证，产生 `ProviderConfirmsInitiator(aid_B, ED_B, pk(SAC_B))` 并输出注册签名。攻击者利用公开的身份材料及这一签名拼装发给 A 的请求。A 验证通过，产生 `ReceiverAcceptsInitiator(aid_A, aid_B, ED_B, pk(SAC_B), pk(SOTK1_A))`。

直到该接受事件，具体执行没有 `ProviderIssuesOTK` 事件。因此，反例失败的是 OTK 发放对应，并不是 Provider 身份签名被伪造。A 在此位置尚未取得 B 实际持有私钥的密钥确认，不能把这一点直接称为真实 TLS 对端已认证。

## B 已验证 token 的反例

[initiator-complete.trace.txt](initiator-complete.trace.txt) 是原始输出第 5743–6193 行的逐字摘录。

该具体执行同样包含 B 的 Provider 注册认证和 A 的 token 签发。B 的公开 `prov_b` 输入可以由攻击者使用公开注册材料拼装；原模型的 B 检查 A 的证书及签名，但没有验证该输入是否来自一次绑定 B 的 Provider 访问响应。随后 B 收到并验证 token，产生 `InitiatorCompletesConnection`；整个具体执行仍没有 `ProviderIssuesOTK` 事件。

原模型在 A 注册时已公开 A 的 OTK 及其签名，故此处不需要破解 DH 或伪造签名。该轨迹没有证明现实 Provider 经 TLS 发送的材料能够被以同样方式窃取。

## 应如何表述

可以表述为：原始 ProVerif 模型保留的身份认证与 token 保密性性质，没有建立“成功接受／完成事件须对应此前的 Provider OTK 发放记录”这一关系；对该关系新增事件对应查询后，可重建不包含相应发放事件的模型执行。

不能表述为：未注册实体已经攻破原生 SAGA，或真实接触策略、TLS、OTK 消耗检查已被绕过。原模型未展开这些过程；本次观察事件也没有补入它们。`ProviderConfirmsInitiator` 表示注册认证，不等于接触策略允许。

## 证据绑定

- 固定上游：7372111bea150e32cee390a616849316d2780bfc。
- 基线 SHA-256：3faf15a801658dc70ceacf1752557cec62ad965854304ad703dce8bdee008302。
- [manifest.json](manifest.json) 保存工具版本、可执行文件哈希、输入哈希、实际命令、退出码与耗时。
- [summary.json](summary.json) 保存十六条实际结果及模型未修改检查。
- [trace-sources.json](trace-sources.json) 绑定两份轨迹摘录与原始输出的行号、哈希，并列出具体执行事件。
- [report-bindings.json](report-bindings.json) 是验证完成后生成的派生报告完整性记录；没有改写原始工具输出或运行清单。
