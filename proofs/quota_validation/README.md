# SAGA 双端配额与消息交付验证

本目录只维护 [SagaQuotaDelivery.tla](SagaQuotaDelivery.tla)。它同时表示 A 的并发配额检查／扣减，以及 B 发送后扣减、请求交付失败时的双端余额差额。源码对应、状态、环境假设与性质解释见 [DELIVERY_MODEL.md](DELIVERY_MODEL.md)。

## 文件入口

| 文件／目录 | 用途 |
|---|---|
| [SagaQuotaDelivery.tla](SagaQuotaDelivery.tla) | 唯一模型，从 A、B 相同初始额度开始，展开多连接、多轮收发与有限连接故障 |
| [DELIVERY_MODEL.md](DELIVERY_MODEL.md) | 模型流程、源码对应表、性质与抽象边界 |
| [delivery_configs/](delivery_configs/) | 十个有限配置，分别检查配额安全、候选计账性质、正常对照和分支可达性 |
| [run_delivery_tlc.py](run_delivery_tlc.py) | 自包含运行脚本：源码校验、SANY、TLC 与证据归档 |
| [bootstrap.ps1](bootstrap.ps1) | 下载并校验固定版本 Java/TLC；已配置时无需重复运行 |
| [结果报告](evidence/delivery-20261024T150331844425Z/REPORT_ZH.md) | 保留的一轮完整验证结果及反例说明 |

旧模型、旧注释副本、旧配置、旧运行器及过时的运行证据已移除。

## 保留的反例路径

完整证据目录：[evidence/delivery-20261024T150331844425Z/](evidence/delivery-20261024T150331844425Z/)。

| 场景 | 轨迹摘录 | 原始 TLC 输出 |
|---|---|---|
| 并发检查通过后先后扣减，A 累计准入超过额度 | [concurrent_race/trace.md](evidence/delivery-20261024T150331844425Z/concurrent_race/trace.md) | [stdout.log](evidence/delivery-20261024T150331844425Z/concurrent_race/stdout.log) |
| 第一条请求在 A 解析前中断，终态 B=49、A=50 | [request_abort/trace.md](evidence/delivery-20261024T150331844425Z/request_abort/trace.md) | [stdout.log](evidence/delivery-20261024T150331844425Z/request_abort/stdout.log) |
| 先完成一次交互，再中断下一条请求，终态 B=48、A=49 | [request_abort_after_progress/trace.md](evidence/delivery-20261024T150331844425Z/request_abort_after_progress/trace.md) | [stdout.log](evidence/delivery-20261024T150331844425Z/request_abort_after_progress/stdout.log) |
| 独立检查“B 消耗量不得超过 A 准入数” | [request_abort_consumption/trace.md](evidence/delivery-20261024T150331844425Z/request_abort_consumption/trace.md) | [stdout.log](evidence/delivery-20261024T150331844425Z/request_abort_consumption/stdout.log) |

[summary.json](evidence/delivery-20261024T150331844425Z/summary.json) 记录全部十个配置的结果；[manifest.json](evidence/delivery-20261024T150331844425Z/manifest.json) 绑定源码、工具和输入快照；[report-bindings.json](evidence/delivery-20261024T150331844425Z/report-bindings.json) 记录报告与结果文件的哈希。

证据目录的 `inputs/` 是生成这些结果时的冻结快照，保留当时的脚本和说明。它们与原始日志均未随本次清理改写；当前运行入口是本目录的 `run_delivery_tlc.py`。

## 运行

从仓库根目录执行：

```powershell
& '.\proofs\consumer_validation\.runtime\venv\Scripts\python.exe' -B '.\proofs\quota_validation\run_delivery_tlc.py'
```

也可使用 Python 3，无需第三方 Python 包。Java/TLC 缺失时先执行 `proofs/quota_validation/bootstrap.ps1`。可用 `--java`、`--jar` 指定已有工具；用 `--cases concurrent_race request_abort request_abort_after_progress` 只运行主要反例配置。

脚本每次新建独立证据目录，不覆盖保留的结果。整体退出 0 表示所有配置出现预期结果，其中包括预期的性质违反，不能解读为全部性质成立。

## 结论边界

并发超额检查的是 `ReceiverQuotaSafety`。连接中断后的余额差额检查的是候选终态计账性质；SAGA 原文未明确承诺所有故障下的退款或双端余额一致，二者应分别表述。

这些是有限配置下的模型结果。连接中断是显式环境假设；尚未完成对应轨迹的原生重放或真实 TLS 故障注入。`trace.md`／`trace.json` 是原始日志的派生阅读材料，不是原生执行记录。
