# C 耗尽领取配额后使用转交 OTK：原生轨迹投影

来源：Tamarin `transfer_after_C_exhaustion_completes` 的 `exists-trace` 见证。

本文件从原始 `traces.json` 提取事件，没有手工编造执行步骤。下表是一种满足原图依赖的拓扑顺序，不表示唯一的全局执行顺序。

机器核对：Provider 向 B、C 各发放一个；C 使用两个不同 OTK；B 明确转交自己的那个 OTK；C 解密两个 token；Provider 已因 C 配额耗尽拒绝其领取请求。

见证公式额外要求：C 的第一次受理 < 配额耗尽拒绝 < B 转交 < C 收到转交 < 第二次受理。

| 节点 | 规则 | 原始观察事件 |
|---|---|---|
| `#vr.1` | `Setup` | `Setup( )`<br>`LongTermKey( 'B', ~bsk )`<br>`LongTermKey( 'C', ~csk )` |
| `#vr` | `Sender_Requests_Access` | `AccessRequested( 'A', 'C', ~request.2 )` |
| `#vr.2` | `Initialize_C_Policy` | 初始化／内部状态步骤 |
| `#vr.8` | `Sender_Requests_Access` | `AccessRequested( 'A', 'C', ~request )` |
| `#vr.9` | `Sender_Requests_Access` | `AccessRequested( 'A', 'B', ~request.1 )` |
| `#ib` | `Provider_Issues_OTK` | `ProviderIssue( 'A', 'B', 'g'^~otk2 )`<br>`ProviderQuotaExhausted( 'A', 'B' )` |
| `#ic` | `Provider_Issues_OTK` | `ProviderIssue( 'A', 'C', 'g'^~otk1 )`<br>`ProviderQuotaExhausted( 'A', 'C' )` |
| `#vr.10` | `Sender_Receives_OTK` | `OTKReceived( 'A', 'B', 'g'^~otk2 )` |
| `#vr.7` | `Sender_Receives_OTK` | `OTKReceived( 'A', 'C', 'g'^~otk1 )` |
| `#vr.5` | `Sender_Requests_Token` | `TokenRequested( 'A', 'C', 'g'^~otk1, ~sid )` |
| `#vr.6` | `Receiver_Issues_Token` | `ReceiverTokenIssued( 'A', 'C', 'g'^~otk1, ~token.1, 'g'^~csk )` |
| `#vr.4` | `Sender_Decrypts_Token` | `ClientDecryptedToken( 'A', 'C', 'g'^~otk1, ~token.1, 'g'^~csk )` |
| `#vr.3` | `Sender_Sends_Application_Request` | `ClientSendsRequest( 'A', 'C', 'g'^~otk1, ~token.1, 'g'^~csk )` |
| `#ac` | `Receiver_Accepts_Application_Request` | `RequestAccepted( 'A', 'C', 'g'^~otk1, ~token.1, 'g'^~csk )` |
| `#deny` | `Provider_Rejects_Exhausted_Request` | `ProviderRejectExhausted( 'A', 'C' )` |
| `#f` | `B_Forwards_OTK_To_C` | `ForwardOTK( 'A', 'B', 'C', 'g'^~otk2 )` |
| `#r` | `C_Receives_Forwarded_OTK` | `ForwardReceived( 'A', 'B', 'C', 'g'^~otk2 )` |
| `#vr.13` | `Sender_Requests_Token` | `TokenRequested( 'A', 'C', 'g'^~otk2, ~sid.1 )` |
| `#vr.14` | `Receiver_Issues_Token` | `ReceiverTokenIssued( 'A', 'C', 'g'^~otk2, ~token, 'g'^~csk )` |
| `#vr.12` | `Sender_Decrypts_Token` | `ClientDecryptedToken( 'A', 'C', 'g'^~otk2, ~token, 'g'^~csk )` |
| `#vr.11` | `Sender_Sends_Application_Request` | `ClientSendsRequest( 'A', 'C', 'g'^~otk2, ~token, 'g'^~csk )` |
| `#ab` | `Receiver_Accepts_Application_Request` | `RequestAccepted( 'A', 'C', 'g'^~otk2, ~token, 'g'^~csk )` |

解释边界：这是固定两发送方、每方领取配额为 1、两个 OTK、理想 mTLS 与选定转交行为下的模型见证；没有运行原生 SAGA 网络服务。
