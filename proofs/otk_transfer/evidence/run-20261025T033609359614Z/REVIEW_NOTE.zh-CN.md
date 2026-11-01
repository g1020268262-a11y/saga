# 未完成运行的判读说明

本次运行的 `forwarding` 和 `no_forwarding` 各取得十条结果；`deny_C` 因 Tamarin 默认的 5 秒 derivation-check 时限退出，没有取得该配置的性质结果。`summary.json` 的 `all_expected` 为 `false`，原始输出与清单保持不变。

本目录 `REPORT.zh-CN.md` 表内的“缺失”应按没有结论解读。其关于明确拒绝 C 对照的文字是预期判读，不能当作本次运行已经证明该对照。最终验证以提高推导检查时限后新建的运行目录为准；该调整没有改变模型规则。
