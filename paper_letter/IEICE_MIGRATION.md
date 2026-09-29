# IEICE Transactions 模板迁移与实际分页记录

日期：2026-09-29。分支：`my-modification`。
初次模板迁移采用的冻结正文基线：`6d58c95269313a47a6e02d625d0444ceea6122ea`。
初次模板迁移提交：`53a1ae535fd93dd9c7280522707af5aca981f5fc`。
以下保留初次迁移过程记录；Fundamentals 分类修正见 N 节，
用户随后授权的信息优先级重构及最新复核见 O 节。

## A–C. 官方来源、版本及文件

- 使用用户提供的 `D:/EdgeBrowerLoad/ieice_v2.3.zip`。
- 下载文件的 Windows `Zone.Identifier` 中，HostUrl 和 ReferrerUrl 均指向
  `https://www.ieice.org/ftp/tex/ieice/LaTeX2e/ieice_v2.3.zip?utm_source=chatgpt.com`。
- 官方来源（去除跟踪参数）：https://www.ieice.org/ftp/tex/ieice/LaTeX2e/ieice_v2.3.zip 。
  本轮没有重新从网站下载；来源记录和包内 README 一并核对。
- `readme-e.1st`、`template.tex` 和 class 标识版本为 **v2.3，2024/04/01**。
- class：`ieice.cls`；BibTeX 样式：`ieicetr.bst`；包内无独立 `.sty`。
  `ieicetr.bst` 自身注释称其为 unofficial/contributed style，但它确实随此官方模板包分发，
  README 列明贡献者，官方 sample 也给出了 `\bibliographystyle{ieicetr}`。
- 按 sample 加载 TeX Live 提供的 `graphicx`、`xcolor`、`amsmath[fleqn]`、
  `newtxtext`、`newtxmath[varg]`，并保持要求的加载顺序。
- 已阅读英文 README、指南和 sample：使用 `letter` 选项、官方作者/单位命令、
  `summary` 和 `keywords` 环境；指南附录明确允许使用 `pdflatex` 直接生成 PDF，
  图形驱动选择 `pdftex`。

SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| 原始 ZIP | `2e9d64b9a155c2f9890b9f9cbe13ee9d688fb463f31d84f9aa466d777f17ad36` |
| ieice.cls | `88f90d1b0cfb896ca92a00a61af01319beca06172a4ff27d1c0e8a89f6cc3b3a` |
| ieicetr.bst | `4e2eecf70d4606cd1eb16b9243159d9714960d2d574bbe5ac5cd3f8e6ebda8bd` |
| main.pdf | `283fdd5d4a749a1e7e29c77093b059e9ee10d0e918699bd8288d998e43c4d389` |

`ieice_template/` 中的五个上游文件均与 ZIP 条目逐字节相同。
本地 `.gitattributes` 仅让这些上游文件保持原始字节，并豁免其原有空白格式，
避免 Git 换行转换或为了 whitespace check 修改官方源码。

## D–E. 修改范围与正文冻结

修改文件：

- `main.tex`：官方 Letter class、字体/数学包、作者 TODO、summary/keywords 环境、官方包内 BST。
- `sections/02_authorization_decision_inconsistency.tex`：仅 matcher 表排版。
- `sections/04_consumer_validation.tex`：仅 consumer 表排版。

新增文件：

- `build.ps1`：Windows PowerShell 完整编译流程。
- `main.pdf`：最终实际编译 PDF。
- `IEICE_MIGRATION.md`：本记录。
- `ieice_template/.gitattributes`。
- `ieice_template/ieice.cls`。
- `ieice_template/ieicetr.bst`。
- `ieice_template/readme-e.1st`。
- `ieice_template/readme-e.tex`。
- `ieice_template/template.tex`。

上述路径均相对 `paper_letter/`。没有修改任何正文句子、公式、表格数据、表题文字、
Summary 内容、Keywords、参考文献数据库或引用集合。
第 1、3、5 节、`references.bib` 和 `macros.tex` 与冻结基线内容相同；
第 2、4 节剔除 table 环境后与基线相同，表内文本/数据/表题亦单独核对相同。

仅有的正文文件排版调整及原因：

1. 两张表的表题/label 移到表格上方，遵循官方 sample。
2. matcher 表第一列允许换行，预算表头分两行，移除两侧多余列间距；
   修复初次编译的 `42.1901pt` 超宽。
3. consumer 表头分行、移除两侧多余列间距；修复 `19.16206pt` 超宽。
4. 两张表使用官方 sample 的 `[tb]` 浮动选项。
   原 `[htbp]` 与 class 的低 float-page 阈值使 consumer 表独占第 2 页右栏，
   初次生成 3 页。取消独立浮动页选项后正常续排，最终为 2 页。
   未改 class、页面尺寸、栏宽、字号、行距、公式或正文措辞。

没有运行或修改实验、模型、bridge、consumer validation 实现、evidence 或 `paper/`。

## F–H. 待填写字段、Summary 和 Keywords

作者待填写：作者名单及顺序、姓名、各作者 IEICE membership status、会员号（适用时）、
单位对应关系、院系/机构、邮政地址及国家、通信作者及 email；如有现单位差异，再填写 present affiliation。
当前只有一个 `TODO Author` 排版占位，会员参数留空，单位/地址为 TODO，未虚构姓名、会员身份或 email。
class 将未知会员状态显示为 `??`，并发出对应 warning。

Transactions category is fixed to A (Fundamentals).
目标期刊为 IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences。
接收/修订日期及出版卷期、DOI 等由期刊确定。
PDF 中的 `??`、`Exx`、`200x` 和示例 DOI 是官方 class 的默认出版占位，不代表实际出版信息。

- Summary：**48 words**，按空白分词，连字符复合词作为一词；与冻结原文完全一致。
- Keywords：**5 个**：authorization, access control, formal verification, AI agents, ProVerif。

## I–J. 编译与检查

环境：Windows TeX Live 2025；pdfTeX 1.40.28；BibTeX 0.99d。

在仓库根目录执行：

```powershell
& ./paper_letter/build.ps1
```

脚本进入 `paper_letter/`，将 `ieice_template/` 加入 `TEXINPUTS` 和 `BSTINPUTS`，
将当前目录加入 `BIBINPUTS`，并保留 TeX 的默认搜索路径。完整命令为：

```text
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex
bibtex build/main
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex
```

最后复制 `build/main.pdf` 到 `main.pdf`。完整流程成功，最后一轮日志结果：

| 检查 | 数量 |
| --- | ---: |
| LaTeX errors | 0 |
| Undefined references | 0 |
| Undefined citations | 0 |
| Duplicate labels | 0 |
| Overfull boxes | 0 |
| Underfull boxes | 0 |
| BibTeX warnings | 0 |

仍存在两项可解释的 warning：未知会员参数；`OT1/qhv/m/sl` 9pt 字形替换为 italic。
另有 `Non-PDF special ignored` 提示：pdfTeX 忽略 DVI 的纸张 special，
但 PDF 实测尺寸为官方 **210 × 280 mm**，不影响实际页数。
未修改官方字体定义或 class 来压制这些提示。

`.aux/.bbl/.blg/.log` 等中间产物和逐页 PNG 均在已有 Git ignore 规则覆盖的 `build/`，不提交。
使用 `pdfinfo`、`pdftotext -layout`、aux 标签页码，并渲染检查全部两页。
两张表、公式及正文没有越界或重叠。

## K. 最终 PDF 实际分页

| 项目 | 实测结果 |
| --- | --- |
| PDF 总页数 | **2** |
| References 起始页 | **第 2 页右栏** |
| References 之前完整页面数 | **1 页**，另有第 2 页左栏及右栏前部正文 |
| References 前正文实际覆盖页码 | **第 1–2 页**；不能说正文只有 1 页 |
| 第 1 页 title / Summary / Keywords / Introduction | **全部包含** |
| Matcher table（Table 1） | **第 1 页右栏** |
| Consumer table（Table 2） | **第 2 页右栏** |
| Section 5: Scope and Conclusion | **第 2 页右栏** |

页数基于本次官方模板最终 PDF，包含当前作者/单位 TODO 占位。
没有根据旧 article 估算，没有删减正文以改变篇幅。

## L–M. Git

提交前执行 `git diff --check` 和 `git diff --cached --check`；均通过。
提交范围仅为本记录所列的 `paper_letter/` 文件。
本次 commit SHA 在交付消息中给出；报告与 PDF 包含在同一个迁移提交中。
完成本轮后停止，不继续压缩正文或修改研究内容。

## N. Fundamentals 分类修正及重新编译（2026-09-29）

相对初次模板迁移提交，本轮只修改 `main.tex` 和本记录。
`main.tex` 的 `\field{}` 改为 `\field{A}`，对应注释不再将 category 标为 TODO。
Transactions category is fixed to A (Fundamentals).
所有作者信息继续保持 TODO；未填写 Member/Nonmember 或其他未知作者资料。
五个正文文件、title、Summary、Keywords、表格、公式、参考文献、macros、
官方模板及 `build.ps1` 均未修改；未运行或修改研究实验、模型和证据。

使用现有 `build.ps1` 完整执行三轮 pdflatex 和一轮 BibTeX，编译通过。
最终日志：LaTeX errors、undefined refs、undefined cites、duplicate labels、
overfull boxes 均为 **0**。
仍保留未知会员状态 warning 和 `OT1/qhv/m/sl` 9pt 字体替代 warning；
另有不影响 PDF 纸张尺寸的 `Non-PDF special ignored` 提示。

使用 `pdfinfo`、逐页文本、aux 标签及全部两页的渲染图重新确认：

| 项目 | 本轮实测 |
| --- | --- |
| PDF 总页数 | **2** |
| References 起始页 | **第 2 页右栏** |
| Matcher table | **第 1 页右栏** |
| Consumer table | **第 2 页右栏** |
| Section 5: Scope and Conclusion | **第 2 页右栏** |
| 页眉分类 | **IEICE TRANS. FUNDAMENTALS** |

本轮复核 PDF 为 `build/main.pdf`，SHA-256：
`80683abe9bb52efad21afe92fa9c6470f2834393ab75b5c5ca63fe9751761981`。
该文件及编译中间产物位于 Git 忽略目录，不纳入本次提交。
脚本自动复制到 `main.pdf` 后，已恢复该受跟踪 PDF 的编译前字节，
以严格保持本次仅修改两个指定文件；因此受跟踪的 `main.pdf` 仍是初次迁移的历史快照，
不是本轮 `field=A` 复核 PDF。上方 SHA-256 表中的 `main.pdf` 哈希仍指该历史快照。

`git diff --check` 和暂存区 `git diff --cached --check` 均通过；
本次提交仅包含 `paper_letter/main.tex` 和 `paper_letter/IEICE_MIGRATION.md`。
Commit SHA 在本轮交付消息中报告。

## O. 信息优先级重构及最终分页（2026-09-29）

本轮基线：`f82e7dc077addfe603ccea825d19c54bf6b7f893`。
用户授权在冻结研究范围内重构表达，突出 matcher bug、controlled production
propagation 和 fixed-divergence formal consequence；不增加研究内容。

修改正文文件：`sections/01_introduction.tex`、
`sections/02_authorization_decision_inconsistency.tex`、
`sections/03_formal_consequence_analysis.tex`、
`sections/04_consumer_validation.tex`、`sections/05_scope_conclusion.tex`。
同时更新本记录和受跟踪的 `main.pdf`，使交付 PDF 与本轮源码一致。
`main.tex`（含 title、Summary、Keywords、field=A、作者 TODO）、`references.bib`、
引用集合、`macros.tex`、`build.ps1`、官方 class/style、字号、页边距和行距均未改变。

表达调整：

- Introduction 直接呈现 production matcher 的顺序不一致，然后依次说明
  token issuance/storage 的受控传播和独立的 symbolic consequence。
- 删除两个 Allow 定义的 display equations，以及 `Allow_spec` / `Allow_impl` 记号；
  改用 most-specific semantics、正负预算和两种规则顺序结果的 prose。
- 将 specification-deny / observed-implementation-allow 的 tuple display 改为 prose。
- 删除三种 policy 的独立 array，改用文字交代原有策略顺序、预算和每例一次执行条件。
- 共删除 **4 个 display math blocks**；唯一剩余的展示公式为原样保留的
  `ChatAccept(R,I,t,m) => TokenIssue(R,I,t)` non-injective correspondence。
- Table 1 完全保留。Table 2 改为两列 `Stage | Divergent case result`，
  六行依次为 specification deny (-1)、Provider matcher allow (10)、
  Provider /access HTTP 200 / OTK released、receiver matcher allow (10)、
  receiver OTK consumed、token issued and stored。
- A/A positive control 和 D/D Provider-blocking control 在正文中合并为一句说明；
  保留 A/A token sending/storage，以及 D/D HTTP 403、不释放 OTK、不改变状态、
  不到达 receiver、不能检验 receiver rejection 的限制。
- Model assumptions 压为一段；结论按 bug、production propagation、独立 symbolic
  consequence 顺序总结，并保留单一记录案例/已测策略、无 arbitrary-policy correctness、
  无 Python--ProVerif refinement、empirical endpoint 早于 message acceptance、无 deployed exploit。

Technical claims 没有新增或加强。尤其保留 prescribed symbolic peer process、
非 arbitrary-adversary reachability、ProVerif 不执行 Python/matcher、不发现实现不一致、
reachability 与 correspondence 分别报告、同一参与者/token 的先前 issuance、
不证明 intended policy permission、witness 中出现 issuance、无 standalone TokenIssue
reachability query，以及 formal/empirical 两种实验及端点相互区分。
没有运行或修改实验、query、模型、实现、bridge、consumer validation 或历史 evidence。

使用原 `build.ps1` 完整编译并检查所有两页渲染图：

| 项目 | 最终实测 |
| --- | --- |
| PDF 总页数 | **2** |
| References 起始页 | **第 2 页右栏** |
| Table 1: matcher rule-order inconsistency | **第 1 页右栏** |
| Table 2: divergent-case production propagation | **第 2 页右栏** |
| ChatAccept => TokenIssue 展示公式 | **第 2 页左栏** |
| Section 5 | **第 2 页右栏** |
| Overfull boxes | **0** |
| LaTeX errors / undefined refs / undefined cites / duplicate labels | **均为 0** |

仍保留会员身份 TODO 和官方字体斜体替代 warning；未为压页改变模板参数。
最终 `main.pdf` SHA-256：
`5a180ea55b99f426b59470b05ea60a8a68fb05122c7fb4ddfa4c4befb7323e43`。
前面章节的 PDF 哈希和快照说明均属于相应历史轮次；本节记录当前交付 PDF。
中间编译产物仍在 Git 忽略的 `build/`，不提交。
`git diff --check` 与暂存区检查均通过；本次只提交上述五个正文文件、本记录和最终 PDF。
Commit SHA 在本轮交付消息中报告，完成后停止。
