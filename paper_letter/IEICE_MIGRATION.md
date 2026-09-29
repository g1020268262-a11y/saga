# IEICE Transactions 模板迁移与实际分页记录

日期：2026-09-29。分支：`my-modification`。
冻结正文基线：`6d58c95269313a47a6e02d625d0444ceea6122ea`。

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

此外，Transactions 分类 A/B/C/D 尚未指定；接收/修订日期及出版卷期、DOI 等由期刊确定。
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
