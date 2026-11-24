# D/A 原生反例逐步核对

本表直接读取 Tamarin 原生 JSON 图并按事实依赖进行拓扑排序；不使用 finite_replay.json。
原生节点 ID 是节点标识，不是数值时间。此表是一种合法线性展开。

| 步骤 | 原生节点 | 原生规则 | 原生事件 |
|---:|---|---|---|
| 1 | `#vr.5` | `Setup` | `Setup( )` |
| 2 | `#vr.16` | `Spec_Select_Better_0` | `SelectRule( ~sid, 'spec', 'r70', 'bneg1' )` |
| 3 | `#vr.15` | `Skip_Rule_1` | `SkipRule( ~sid, 'spec', 'r0', 'b10' )` |
| 4 | `#vr.14` | `Spec_Finish` | `SpecDecision( ~sid, 'A', 'B', 'bneg1', 'deny' )` |
| 5 | `#vr.13` | `Provider_Start` | `AccessRequested( ~sid, 'A', 'B' )` |
| 6 | `#vr.12` | `Impl_Select_Better_0` | `SelectRule( ~sid, 'provider_eval', 'r70', 'bneg1' )` |
| 7 | `#vr.10` | `Impl_Select_Better_1` | `SelectRule( ~sid, 'provider_eval', 'r0', 'b10' )` |
| 8 | `#vr.8` | `Provider_Finish` | `ProviderBudget( ~sid, 'A', 'B', 'b10' )` |
| 9 | `#vr.4` | `Provider_Release` | `ProviderIssue( ~sid, 'A', 'B', 'g'^~osk )`<br>`ProviderDebit( ~sid, 'A', 'B', 'b10', 'b9' )` |
| 10 | `#vr.2` | `Sender_Request_Token` | `TokenRequest( ~sid, 'A', 'B', 'g'^~osk )` |
| 11 | `#vr.7` | `Receiver_Start` | `ReceiverCheckStarted( ~sid, 'A', 'B' )` |
| 12 | `#vr.11` | `Impl_Select_Better_0` | `SelectRule( ~sid, 'receiver', 'r70', 'bneg1' )` |
| 13 | `#vr.9` | `Impl_Select_Better_1` | `SelectRule( ~sid, 'receiver', 'r0', 'b10' )` |
| 14 | `#vr.6` | `Receiver_Finish` | `ReceiverBudget( ~sid, 'A', 'B', 'b10' )` |
| 15 | `#vr.3` | `Receiver_Issue_Token` | `TokenIssue( ~sid, 'A', 'B', senc(<'ACT', ~token, 'g'^~bsk>, h(<'access-control-shdk-exchange', 'g'^(~bsk*~osk)>)))` |
| 16 | `#vr.1` | `Sender_Decrypt_Token` | `TokenReceive( ~sid, 'A', 'B', senc(<'ACT', ~token, 'g'^~bsk>, h(<'access-control-shdk-exchange', 'g'^(~bsk*~osk)>)))` |
| 17 | `#vr` | `Sender_Send_Chat` | `ChatSend( ~sid, 'A', 'B', senc(<'ACT', ~token, 'g'^~bsk>, h(<'access-control-shdk-exchange', 'g'^(~bsk*~osk)>)), ~msg)` |
| 18 | `#i` | `Receiver_Accept_Chat` | `ChatAccept( ~sid, 'A', 'B', senc(<'ACT', ~token, 'g'^~bsk>, h(<'access-control-shdk-exchange', 'g'^(~bsk*~osk)>)), ~msg)` |

所有逐步一致性检查通过。完整前提、事件和后继事实见 da-trace-review.json。
da-attack.native.json 是原生图的精确子集；联合 DOT 原始输出保留在 ../da/traces.dot。
