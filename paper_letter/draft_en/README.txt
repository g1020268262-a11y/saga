SAGA English manuscript in the complete IEICE Letter template
Date: 2026-11-25

Source: ../draft_zh
Base revision: 52013d1; the working tree includes the requested bilingual subsection 3.1 revision.
Main source: main.tex
Preview: main.pdf
Layout: bundled official IEICE Transactions v2.3 class, with the letter option.
Includes the LETTER heading, working title, author list, affiliation footnote, and IEICE running headers.
Author and affiliation details are reused from ../main.tex.
Working title: Formal and Empirical Analysis of SAGA's Authorization Mechanism.

Current page count: 5 pages including the title block, summary, five sections, and references.
The body and references both end on page 5.
Publication identifiers, volume/issue, and publication year retain the class's default placeholders.
No manuscript receipt or revision dates have been invented.

Build from the repository root in PowerShell:
  & './paper_letter/draft_en/build.ps1'

The build reuses ../ieice_template and ../references.bib.
The summary and all five sections are translated from the current Chinese source.
The updated ACP Tamarin analysis and the second-stage Chinese revisions are included.
The flowchart and its in-text reference are omitted from the English manuscript at the user's request. Standalone figure assets are retained; the Chinese manuscript still includes its flowchart.
Subsection 3.1 follows SAGA_Letter_3.1中英文定点压缩方案.docx and displays only policy_budget_agreement; the other properties remain described in prose.
Native formulas retained in the manuscript, TLA+ actions, identifiers, numerical results, and citations are unchanged.
The complete title/author/affiliation block and the template's default typography and margins are retained.
The page count reflects the requested subsection compression and English flowchart removal, with no changes to template typography or margins.
Only subsection 3.1 is revised in the Chinese manuscript. The reference implementation, formal models, and historical evidence are unchanged.

Original translation baseline hashes and structural verification (predating the above revisions):
  build/translation_20261125/translation-check.json
