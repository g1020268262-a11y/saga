SAGA English manuscript in the complete IEICE Letter template
Date: 2026-11-24

Source: ../draft_zh
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
The figures are copied into this folder. Formal definitions and numerical results are retained.
This template integration changes only main.tex and this README; the existing English body is retained.
It does not synchronize the later Chinese second-round prose revisions.
