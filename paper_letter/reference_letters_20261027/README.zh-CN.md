# IEICE Letter 写作参考：四篇安全分析短文

整理日期：2026-10-27。目标是学习短篇安全分析如何提出问题、组织多个发现并限定结论。四篇均为 **IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences** 的正式 **LETTER**；PDF 保留出版社原始字节。

**建议先读 01 和 02，再读 03 的讨论部分；04 用于学习安全性质和假设的组织。** 与 SAGA 的相似性主要在论证方式，不代表这些论文研究过 SAGA、OTK Budget 或 ACT 并发配额。

| 编号 | 原文与书目信息 | 最值得学习的写法 |
|---|---|---|
| 01 | [SPKSE 安全分析](01_spkse_2026.pdf)，2026，E109.A(9):1618–1620，3 页；[期刊页面](https://www.jstage.jst.go.jp/article/transfun/E109.A/9/E109.A_2025DML0001/_article/-char/en) | 清楚承认分析超出了原文安全游戏允许的能力，再用具体执行说明设计角色为何值得重新审视；最贴近 OTK 发放／使用的论证边界。 |
| 02 | [多关键词搜索加密安全分析](02_multikeyword_2026.pdf)，2026，E109.A(9):1621–1622，2 页；[期刊页面](https://www.jstage.jst.go.jp/article/transfun/E109.A/9/E109.A_2025DML0002/_article/-char/en) | 把两个发现分别挂到两个明确性质下；仅保留反例需要的组件，并说明两项结果的重要性差异。 |
| 03 | [关键词盲性安全分析](03_keyword_blindness_2026.pdf)，2026，E109.A(9):1623–1624，2 页；[期刊页面](https://www.jstage.jst.go.jp/article/transfun/E109.A/9/E109.A_2025DML0003/_article/-char/en) | 主攻击符合原文模型；讨论中的另一观察超出模型，作者明确不给它同样的攻击结论。适合学习证据与贡献分层。 |
| 04 | [KH-PKE 安全性质分析](04_khpke_security_notions_2021.pdf)，2021，E104.A(1):310–314，5 页；[期刊页面](https://www.jstage.jst.go.jp/article/transfun/E104.A/1/E104.A_2020EAL2039/_article/-char/en) | 先说明威胁能力与安全定义，再分别建立两项安全结论；适合学习性质、假设与结果的对应。 |

**这批中，01 是最贴近我们“现有定义与更强使用目标之间差别”的范文，02 是最容易照着拆结构的范文。** 前三篇来自同一作者组、同一期专题，能提供一致的短文写法；它们不是对全刊写作偏好的统计样本。第 04 篇正文占第 1–4 页，第 5 页是参考文献；其总页数只作为已发表事实，不据此推定我们的投稿页数要求。

详细阅读位置及对应到 policy → OTK → ACT 的方式，见 [逐篇阅读与写作拆解.md](逐篇阅读与写作拆解.md)。来源、页数与 SHA-256 见 [sources-manifest.json](sources-manifest.json)。`reading/` 保存逐页渲染和文本提取，方便对照原文；没有另行验证这些论文的数学证明，也没有修改 SAGA 正文或运行模型。
