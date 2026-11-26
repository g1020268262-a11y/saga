SAGA English manuscript in the complete IEICE Letter template
Date: 2026-11-26

Source: ../draft_zh
Base revision for this language revision: af1568c (4.1).
Main source: main.tex
Preview: main.pdf
Layout: bundled official IEICE Transactions v2.3 class, with the letter option.
Includes the LETTER heading, working title, author list, affiliation footnote, and IEICE running headers.
Author and affiliation details are reused from ../main.tex.
Working title: Formal and Empirical Analysis of SAGA's Authorization Mechanism.

Current page count: 5 pages including the title block, summary, five sections, and references.
The body and references both end on page 5. The manuscript still exceeds the four-page Letter target.
Publication identifiers, volume/issue, and publication year retain the class's default placeholders.
No manuscript receipt or revision dates have been invented.

Build from the repository root in PowerShell:
  & './paper_letter/draft_en/build.ps1'

The build reuses ../ieice_template and ../references.bib.
The summary and all five sections are translated from the current Chinese source.
The updated ACP Tamarin analysis and the second-stage Chinese revisions are included.
The flowchart and its in-text reference are omitted from both the Chinese and English manuscripts at the user's request. Standalone figure assets are retained.
Subsection 3.1 follows SAGA_Letter_3.1中英文定点压缩方案.docx and displays only policy_budget_agreement; the other properties remain described in prose.
Native formulas retained in the manuscript, TLA+ actions, identifiers, numerical results, and citations are unchanged.
The complete title/author/affiliation block and the template's default typography and margins are retained.
The current revision improves academic expression and expands abbreviations independently in the Summary and main text. It retains the template typography, margins, and native formal definitions.
The reference implementation, formal models, and historical evidence are unchanged.
Layout refinement: raggedbottom keeps normal heading and paragraph spacing instead of stretching it to align column bottoms. The long TLA+ display is split only between complete Clamp, ACheck, and ADebit definitions; all native code lines are retained. The xurl package permits line breaks in long AIDs without altering their characters. Column widths, fonts, font sizes, margins, and body leading are unchanged.

Academic language revision report: ../academic_expression_review_20261126.txt

Original translation baseline hashes and structural verification (predating the above revisions):
  build/translation_20261125/translation-check.json
