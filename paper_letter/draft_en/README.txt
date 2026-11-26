SAGA English manuscript in the complete IEICE Letter template
Date: 2026-11-26

Source: ../draft_zh
Chinese source for this synchronization: 3433f4c (缩减), plus the current working-tree simplifications to the Summary and Subsection 4.3 on 2026-11-26.
Main source: main.tex
Preview: main.pdf
Layout: bundled official IEICE Transactions v2.3 class, with the letter option.
Includes the LETTER heading, working title, author list, affiliation footnote, and IEICE running headers.
Author and affiliation details are reused from ../main.tex.
Working title: Formal and Empirical Analysis of SAGA's Authorization Mechanism.

Current page count: 4 pages including the title block, summary, five sections, and references.
The body and references both end on page 4. Synchronizing the Chinese simplifications reduced the previous five-page draft to four pages.
Publication identifiers, volume/issue, and publication year retain the class's default placeholders.
No manuscript receipt or revision dates have been invented.

Build from the repository root in PowerShell:
  & './paper_letter/draft_en/build.ps1'

The build reuses ../ieice_template and ../references.bib.
The summary and all five sections are translated from the current Chinese source.
The updated ACP Tamarin analysis and the second-stage Chinese revisions are included.
The flowchart and its in-text reference are omitted from both the Chinese and English manuscripts at the user's request. Standalone figure assets are retained.
Subsection 3.1 follows SAGA_Letter_3.1中英文定点压缩方案.docx and displays only policy_budget_agreement; the other properties remain described in prose.
The displayed Tamarin lemmas and TLA+ quota invariant match the current Chinese manuscript. The full Clamp, ACheck, and ADebit definitions are omitted from both versions; their behavior is described in prose.
The complete title/author/affiliation block and the template's default typography and margins are retained.
The current synchronization follows the Chinese simplifications to the Summary, introduction, workflow, ACT model, and results. It retains independent abbreviation expansions in the Summary and main text, along with the template typography and margins.
The reference implementation, formal models, and historical evidence are unchanged.
Layout refinement: raggedbottom keeps normal heading and paragraph spacing instead of stretching it to align column bottoms. The xurl package permits line breaks in long AIDs without altering their characters. Column widths, fonts, font sizes, margins, and body leading are unchanged.
Verification: XeLaTeX/BibTeX compilation succeeded, with no unresolved references or layout warnings. All four rendered pages were visually checked. The Chinese source files were unchanged by this synchronization; chapter labels, citation keys, and displayed formal definitions were checked against them. Formal models and experiments were not rerun.

Academic language revision report: ../academic_expression_review_20261126.txt

Original translation baseline hashes and structural verification (predating the above revisions):
  build/translation_20261125/translation-check.json
