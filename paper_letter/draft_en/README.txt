SAGA English manuscript in the complete IEICE Letter template
Date: 2026-11-28 (scoped update to Subsection 2.1 and its flowchart)

Source: ../draft_zh
Chinese source for this synchronization: 3433f4c (缩减), plus the current working-tree simplifications to the Summary and Subsection 4.3 on 2026-11-26.
Main source: main.tex
Preview: main.pdf
Layout: bundled official IEICE Transactions v2.3 class, with the letter option.
Includes the LETTER heading, working title, author list, affiliation footnote, and IEICE running headers.
Author and affiliation details are reused from ../main.tex.
Working title: Formal and Empirical Analysis of SAGA's Authorization Mechanism.

Current page count: 4 pages including the title block, summary, five sections, and references.
The body and references both end on page 4. The 2026-11-28 flowchart update leaves the English page count unchanged at 4; the Chinese manuscript remains 3 pages. The earlier synchronization of the Chinese simplifications reduced the previous five-page English draft to four pages.
Publication identifiers, volume/issue, and publication year retain the class's default placeholders.
No manuscript receipt or revision dates have been invented.

Build from the repository root in PowerShell:
  & './paper_letter/draft_en/build.ps1'

The build reuses ../ieice_template and ../references.bib.
The summary and all five sections are translated from the current Chinese source.
The updated ACP Tamarin analysis and the second-stage Chinese revisions are included.
Subsection 2.1 includes Fig. 1 through figures/saga_authorization_compact.tikz, with identical English figure content in both manuscripts. The single-column diagram distinguishes Provider OTK retrieval quotas from the receiver's per-ACT quota shared across connections. Sender quota checks and deductions are shown separately; receiver validation, deduction, and processing use separate local boxes without an atomicity claim. The manuscript includes native TikZ, not a PNG.
The figure measures 80 x 95 mm, with 7.5-8 pt source text and a minimum line width of 0.4 pt (0.1406 mm). The two dashed quota notes each measure 28.5 x 17 mm. Standalone source: figures/saga_authorization_compact.tex; previews: figures/saga_authorization_compact.pdf and .png. The previous detailed and overview figures are retained.
Subsection 3.1 follows SAGA_Letter_3.1中英文定点压缩方案.docx and displays only policy_budget_agreement; the other properties remain described in prose.
The displayed Tamarin lemmas and TLA+ quota invariant match the current Chinese manuscript. The full Clamp, ACheck, and ADebit definitions are omitted from both versions; their behavior is described in prose.
The complete title/author/affiliation block and the template's default typography and margins are retained.
The current synchronization follows the Chinese simplifications to the Summary, introduction, workflow, ACT model, and results. It retains independent abbreviation expansions in the Summary and main text, along with the template typography and margins.
The reference implementation, formal models, and historical evidence are unchanged.
Layout refinement: raggedbottom keeps normal heading and paragraph spacing instead of stretching it to align column bottoms. The xurl package permits line breaks in long AIDs without altering their characters. Column widths, fonts, font sizes, margins, and body leading are unchanged.
Verification (2026-11-28): both standalone figures and the Chinese and English manuscripts compile successfully with XeLaTeX/BibTeX, without unresolved references or layout warnings. All three Chinese and four English pages, plus the standalone diagram, were visually checked. Fig. 1 is on page 1 in both manuscripts. The English body ends in the right column of page 4, 184.91 mm from the page top; references start there at 189.40 mm. The Chinese body ends in the right column of page 3 at 151.90 mm; references start there at 156.46 mm. These positions are unchanged from the baseline for this update. Subsection 2.2, all other sections, citation keys, and formal definitions are unchanged. Formal models and experiments were not rerun.
Word counts (TeXcount text words; excludes Summary, headings, captions, mathematics, bibliography, and verbatim): English Subsection 2.1 changes from 244 to 248 words; Sections 1-5 change from 2548 to 2552 words. The supplied replacement paragraphs are used without further compression.

Academic language revision report: ../academic_expression_review_20261126.txt

Original translation baseline hashes and structural verification (predating the above revisions):
  build/translation_20261125/translation-check.json
