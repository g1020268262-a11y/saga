SAGA English manuscript in the complete IEICE Letter template
Date: 2026-11-25

Source: ../draft_zh
Source revision: 8ead3a866b2c60f68638ad5dfcd02ae86742cc0a
Main source: main.tex
Preview: main.pdf
Layout: bundled official IEICE Transactions v2.3 class, with the letter option.
Includes the LETTER heading, working title, author list, affiliation footnote, and IEICE running headers.
Author and affiliation details are reused from ../main.tex.
Working title: Formal and Empirical Analysis of SAGA's Authorization Mechanism.

Current page count: 6 pages including the title block, summary, five sections, figure, and references.
The body and references both end on page 6.
Publication identifiers, volume/issue, and publication year retain the class's default placeholders.
No manuscript receipt or revision dates have been invented.

Build from the repository root in PowerShell:
  & './paper_letter/draft_en/build.ps1'

The build reuses ../ieice_template and ../references.bib.
The summary and all five sections are translated from the current Chinese source.
The updated ACP Tamarin analysis and the second-stage Chinese revisions are included.
Both figures are synchronized with the current Chinese draft; their labels are already English.
Native lemmas, TLA+ actions, identifiers, numerical results, citations, and cross-reference labels are retained.
The complete title/author/affiliation block and the template's default typography and margins are retained.
No content is removed to force a four-page count.
Chinese sources, the reference implementation, formal models, and historical evidence are unchanged.

Translation source hashes and structural verification:
  build/translation_20261125/translation-check.json
