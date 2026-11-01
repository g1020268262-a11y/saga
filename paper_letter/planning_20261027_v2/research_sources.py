"""Archive primary sources and extract structure for the revised SAGA outline."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
import logging
from pathlib import Path
import re
import sys
import urllib.request

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
SOURCES = ROOT / "sources"
PAPERS = [
    dict(id="ieice2026-labyrinth", title="Formal Verification of Labyrinth in Messenger: Reconsidering Security against Abusing Revoked Device",
         venue="IEICE Transactions on Fundamentals E109.A(8), 1367-1381 (2026)", article_type="PAPER", expected_pages=15,
         doi="10.1587/transfun.2025EAP1150",
         article_url="https://www.jstage.jst.go.jp/article/transfun/E109.A/8/E109.A_2025EAP1150/_article/-char/en",
         pdf_url="https://www.jstage.jst.go.jp/article/transfun/E109.A/8/E109.A_2025EAP1150/_pdf/-char/en"),
    dict(id="ieice2025-emv3ds", title="Formal Verification of Challenge Flow in EMV 3-D Secure and Its Improvement",
         venue="IEICE Transactions on Fundamentals E108.A(8), 1052-1065 (2025)", article_type="PAPER", expected_pages=14,
         doi="10.1587/transfun.2024EAP1132",
         article_url="https://www.jstage.jst.go.jp/article/transfun/E108.A/8/E108.A_2024EAP1132/_article/-char/en",
         pdf_url="https://www.jstage.jst.go.jp/article/transfun/E108.A/8/E108.A_2024EAP1132/_pdf/-char/en"),
    dict(id="usenix2024-widevine", title="Formal Security Analysis of Widevine through the W3C EME Standard",
         venue="USENIX Security 2024, 6399-6415", article_type="conference paper", expected_pages=18,
         article_url="https://www.usenix.org/conference/usenixsecurity24/presentation/delaune",
         pdf_url="https://www.usenix.org/system/files/usenixsecurity24-delaune.pdf"),
    dict(id="usenix2023-blesc", title="Formal Analysis and Patching of BLE-SC Pairing",
         venue="USENIX Security 2023, 37-52", article_type="conference paper", expected_pages=17,
         article_url="https://www.usenix.org/conference/usenixsecurity23/presentation/shi-min",
         pdf_url="https://www.usenix.org/system/files/usenixsecurity23-shi-min.pdf"),
    dict(id="usenix2023-edhoc", title="A comprehensive, formal and automated analysis of the EDHOC protocol",
         venue="USENIX Security 2023, 5881-5898", article_type="conference paper", expected_pages=19,
         article_url="https://www.usenix.org/conference/usenixsecurity23/presentation/jacomme",
         pdf_url="https://www.usenix.org/system/files/usenixsecurity23-jacomme.pdf"),
    dict(id="usenix2020-wpa2", title="A Formal Analysis of IEEE 802.11's WPA2: Countering the Kracks Caused by Cracking the Counters",
         venue="USENIX Security 2020, 1-17", article_type="conference paper", expected_pages=18,
         article_url="https://www.usenix.org/conference/usenixsecurity20/presentation/cremers",
         pdf_url="https://www.usenix.org/system/files/sec20-cremers.pdf"),
    dict(id="ccs2017-tls13", title="A Comprehensive Symbolic Analysis of TLS 1.3", venue="ACM CCS 2017", article_type="conference paper", expected_pages=16,
         doi="10.1145/3133956.3134063",
         article_url="https://doi.org/10.1145/3133956.3134063",
         pdf_url="https://people.cispa.io/cas.cremers/downloads/papers/CHHSV2017-TLS13.pdf",
         existing="paper_letter/planning_20261026/sources/ccs2017-tls13.pdf"),
    dict(id="sp2019-fapi", title="An Extensive Formal Security Analysis of the OpenID Financial-grade API", venue="IEEE S&P 2019", article_type="conference paper", expected_pages=19,
         doi="10.1109/SP.2019.00067",
         article_url="https://doi.org/10.1109/SP.2019.00067",
         pdf_url="https://conferences.computer.org/sp/pdfs/sp/2019/AnExtensiveFormalSecurityAnalysisoftheOpenIDFi.pdf",
         existing="paper_letter/planning_20261026/sources/sp2019-fapi.pdf"),
]


def flatten_outline(reader, items=None):
    results = []
    for item in reader.outline if items is None else items:
        if isinstance(item, list):
            results.extend(flatten_outline(reader, item))
        else:
            try:
                results.append(dict(title=item.title, pdf_page=reader.get_destination_page_number(item) + 1))
            except Exception:
                pass
    return results


def collect(paper):
    record = dict(paper)
    try:
        if "existing" in paper:
            path = WORKSPACE / paper["existing"]
            blob = path.read_bytes()
            record["acquisition"] = "reused existing PDF, read again for structure"
        else:
            request = urllib.request.Request(paper["pdf_url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=45) as response:
                blob = response.read()
                record["resolved_pdf_url"] = response.url
            path = SOURCES / (paper["id"] + ".pdf")
            if path.exists() and path.read_bytes() != blob:
                raise ValueError("Refusing to replace a different existing source")
            if not blob.startswith(b"%PDF-"):
                raise ValueError("Not a PDF response")
            path.write_bytes(blob)
            record["acquisition"] = "new primary-source download"
        reader = PdfReader(io.BytesIO(blob), strict=False)
        if len(reader.pages) != paper["expected_pages"]:
            raise ValueError(f"Expected {paper['expected_pages']} pages, found {len(reader.pages)}")
        texts = [page.extract_text() or "" for page in reader.pages]
        (SOURCES / (paper["id"] + ".txt")).write_text("\n\n".join(f"===== PDF PAGE {i+1} =====\n{text}" for i, text in enumerate(texts)), encoding="utf-8")
        headings = []
        for i, text in enumerate(texts):
            lines = text.splitlines()
            for line_index, line in enumerate(lines):
                if re.match(r"^(?:[1-9](?:\.[0-9]+){0,2}\.?\s+[A-Z]|[1-9](?:\.[0-9]+){0,2}\.?$)", line.strip()) and len(line) < 145:
                    headings.append(dict(pdf_page=i+1, text=" ".join(lines[line_index:line_index+2])))
        record.update(status="PDF_VERIFIED", local_pdf=str(path.relative_to(WORKSPACE)), pages=len(reader.pages),
                      sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob),
                      bookmarks=flatten_outline(reader), heading_candidates=headings)
    except Exception as error:
        record.update(status="FAILED", error=str(error))
    return record


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    SOURCES.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(collect, PAPERS))
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(), papers=records,
                    reading_scope="Structure inspection and selected-page close reading; exact pages recorded separately; no revalidation of proofs or source experiments")
    (SOURCES / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    for record in records:
        print(json.dumps({key: record.get(key) for key in ("id", "status", "pages", "error")}, ensure_ascii=False))
        if record.get("status") == "PDF_VERIFIED":
            print(json.dumps({"id":record["id"], "bookmarks":record["bookmarks"], "headings":record["heading_candidates"]}, ensure_ascii=False))
    return 0 if all(record["status"] == "PDF_VERIFIED" for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
