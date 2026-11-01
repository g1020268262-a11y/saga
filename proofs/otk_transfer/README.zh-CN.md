# SAGA OTK 主动转交的小模型

本模型检查：Provider 按发送方限制 OTK 发放次数时，已领取的 OTK 是否仍可被另一发送方使用。模型保留两端策略检查、发送方身份／PAC 绑定、Provider 领取配额、两处 OTK 状态、DH、token 解密和一次应用请求受理。

这是独立新建的 Tamarin 模型；不是原作者 ProVerif 模型的逐行翻译，也不是完整 SAGA 或 Python 实现的正确性证明。原有源码、模型、论文及历史证据不作修改。

## 配置与研究问题

- Provider、接收方 A、两个身份独立的发送方 B 和 C。
- B、C 各有自己的访问控制密钥；注册身份、PAC 和 TLS 对端绑定作为已正确完成的初始化条件。
- A 有两个 OTK。B、C 对 A 的初始领取配额各为 1，Provider 每次发放消耗一个配额单位。
- 主模型中两端都允许 B、C；本模型不依赖 matcher 的优先级问题或 `0` 的不同处理。
- B 领取到自己的 OTK 后，可以主动把该公钥转交 C；没有转交私钥、长期密钥或已有 token。
- C 使用自己的真实身份和 PAC 联系 A，用自己的私钥完成 DH 并解密新 token。
- 对每个 token 观察一次应用请求；不建 token 多次使用、过期、线程竞态或任务语义。

必须区分两个目标：

1. **发放上限**：Provider 对每个发送方最多发放一个 OTK。这是模型保留的协议规则。
2. **使用上限／同人绑定**：某发送方不能使用发给他人的 OTK，或不能使用超过自身领取配额的不同 OTK。这是本次提出的更强候选性质，不能直接说原论文已经承诺在协作转交条件下满足它。

## 为什么建成主动转交

规则 `B_Forwards_OTK_To_C` 的前提是 B 已经从 Provider 的安全响应中收到 OTK，并持有相应的 `ForwardPermit`。它产生 `ForwardOTK` 事件；C 收到转交后才增加自己的 `HeldOTK`。

这里建的是 B 的主动共享行为。没有用“初始化时所有人都知道 OTK”、注册网络明文泄露、偶然内存泄露或长期私钥泄露来替代转交。B 到 C 的转交也用私有消息事实建模，因此第三方网络窃听不是轨迹的必要条件。

每个已领取 OTK 向 C 最多转交一次，用来避免重复发送同一公钥造成无意义的见证节点；`HeldOTK` 保持可复制，转交不会让 B 忘记它。转交本身不消耗 A 的 OTK；首次在 A 签发 token 时才消费该 OTK。

本模型只允许这项明确的偏离行为，并不覆盖任意恶意注册实体的所有动作或任意泄露组合。Tamarin 的公共网络 `Out` 在此只发布两个发送方的 PAC；TLS 消息不走公共 `Out/In`。

## 两处 OTK 状态与计数

| 事实 | 含义 | 何时消耗 |
|---|---|---|
| `ProviderCredit(A,sender)` | 该发送方剩余一次领取机会 | Provider 发放时 |
| `ProviderUnusedOTK(A,k)` | Provider 尚未发放的 OTK | Provider 发放时 |
| `ReceiverUnusedOTK(A,k,secret)` | A 尚未消费的 OTK 及本地私钥 | A 签发 token 时 |
| `HeldOTK(sender,A,k)` | 发送方已收到该 OTK | 持久知识，不因转交而删除 |
| `NoProviderCredit(A,sender)` | 该发送方领取配额已经耗尽 | 不恢复；再次领取被拒绝 |

`ProviderUnusedOTK` 与 `ReceiverUnusedOTK` 必须独立：Provider 发放了一个 OTK，不代表 A 已经使用它。模型没有给 A 添加源码中不存在的“当前提交者必须等于 Provider 领取者”守卫。

`ProviderCredit` 是固定预算 1 的线性资源表示，不是任意自然数预算的完整算术模型。初始化只执行一次，不能通过重复初始化补充额度。

## TLS、身份与密码学抽象

`TLSAccessRequest`、`TLSOTKResponse`、`TLSTokenRequest`、`TLSTokenResponse`、`TLSApplicationRequest` 是私有、带端点身份的消息事实。只有相应角色规则能产生它们；可延迟调度，不允许网络攻击者窃听、修改或伪造。注册证书、Provider stamp、用户签名的验证结果由固定 `Registered(sender,PAC)` 绑定抽象表示；不展开 CA、注册、证书链或 TLS 握手。

模型使用 Tamarin 的 DH 等式理论。A 以 `PAC_sender ^ SOTK` 导出密钥，发送方以 `OTK ^ SAC_sender` 导出同一密钥。双方使用同一 KDF 域标签。token 使用理想对称加密表示，内容绑定实际发送方 PAC；客户端规则只有匹配 DH 密钥并解密出该 PAC 后才可发送请求。接收方还匹配活动 token 与 TLS 实际身份。

因此，“C 用转交的 OTK 建立自己的 token”与“C 假冒 B”或“C 直接使用 B 已有 token”是不同场景；后两种动作没有在此模型中加入。

## 三组对照与十条查询

同一个模型文件通过预处理开关生成三种配置：

| 配置 | 参数 | 含义 |
|---|---|---|
| `forwarding` | 无 | B 可转交，B/C 均获两端策略允许 |
| `no_forwarding` | `-DNO_FORWARD` | 仅移除主动转交，其他协议规则保持 |
| `deny_C` | `-DDENY_C` | 两端明确拒绝 C；保留 B 到 C 转交行为 |

十条查询包括 B/C 正常可达性、耗尽后转交的完整见证、Provider 发放上限、两端 OTK 单次消费、受理与 token 签发／解密对应、长期私钥没有公开，以及两个候选性质。固定配置下可有任意多次访问／token 请求，但 OTK 池为 2、每个发送方领取配额为 1、每个 token 只观察一次应用请求。

主要 `exists-trace` 见证要求：C 自己的 OTK 已完成一次请求；Provider 因 C 额度耗尽拒绝 C 的再次领取；B 已领取另一个 OTK 并在该拒绝之后转交 C；C 解密新 token 并获 A 受理第二次请求。两次请求使用不同 OTK，均绑定 C 的 PAC。

`exists-trace` 的 `verified` 表示找到见证，`falsified` 表示该配置无此轨迹。`all-traces` 的 `falsified` 才表示找到对应安全性质的反例，不能混淆。

## 运行

本机已核实 WSL 发行版 `TamarinVerify` 提供 Tamarin 1.12.0 和 Maude 3.5.1。在仓库根目录的 PowerShell 中执行：

```powershell
wsl.exe -d TamarinVerify --exec sh -lc 'cd /mnt/d/Users/10202/Desktop/saga && python3 proofs/otk_transfer/run_model.py --timeout 180'
```

脚本依次解析并验证三组配置，每条外部命令有独立超时，推导检查时限为 30 秒，使用两个工作线程。每次创建独立 `evidence/run-<UTC时间>/`，保存模型、运行脚本、五个相关源码文件、工具版本与哈希、Git HEAD、实际命令、退出码、原始输出、证明及 JSON/DOT 轨迹。已有证据不覆盖。

模型与运行脚本的哈希在运行结束时再次核对。脚本要求十条查询在三组配置中都获得预期终局结果；超时、缺失、警告或其他结果均不作为成功。

输出目录中的 `REPORT.zh-CN.md` 汇总本次结果；`forwarding/witness.zh-CN.md` 是从原生 JSON 图提取的一种合法拓扑排序；`witness.json` 保存原始图标签、JSON 哈希和七项轨迹解释核对，不手工编造执行步骤。

`evidence/` 保留开发中的运行，包括尚未完成的运行。应核对所读目录的 `summary.json` 为 `all_expected: true`，并确认其模型／脚本快照哈希与当前文件一致；不能只根据目录存在或某个早期查询的结果认定最终验证完成。

## 源码与结论边界

具体映射见 [SOURCE_MAP.zh-CN.md](SOURCE_MAP.zh-CN.md)。模型有取舍：固定两发送方、单次初始化、固定初始配额、固定策略、理想 mTLS、没有注册过程、OTK 补充、策略同步、撤销、token 过期或任务完成流程，也没有 Python 异常及线程交错。

本模型证明或反驳的是这些规则及假设下的性质；不等于真实服务攻击复现，不是源码到模型的形式化精化证明，也不推出任意预算下的一般定理。原始 SAGA 论文是协议语义的参考：[IV-D2 与 IV-E](https://arxiv.org/html/2504.21034v2#S4.SS4.SSS2)；规则、状态和信道抽象参考 [Tamarin 官方手册](https://tamarin-prover.com/manual/master/book/011_advanced-features.html#different-channel-models)。
