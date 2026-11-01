"""Download original IEICE Letter sources without changing their PDF bytes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
import logging
from pathlib import Path
import sys
import urllib.request

from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parent
PAPERS = [
    {
        "id": "01_spkse_2026",
        "title": "Security Analysis on \u201cSPKSE: Secure Public Key Searchable Encryption Withstand Keyword Guessing Attacks\u201d",
        "authors": ["Keita Emura", "Toshihiro Ohigashi", "Nobuyuki Sugio"],
        "year": 2026, "volume": "E109.A", "issue": 9, "pages": "1618-1620", "expected_pdf_pages": 3,
        "doi": "10.1587/transfun.2025DML0001", "article_type": "LETTER",
        "base_url": "https://www.jstage.jst.go.jp/article/transfun/E109.A/9/E109.A_2025DML0001/",
    },
    {
        "id": "02_multikeyword_2026",
        "title": "Security Analysis on \u201cMulti-Keyword Searchable Encryption for Smart Grid Edge Computing\u201d",
        "authors": ["Keita Emura", "Toshihiro Ohigashi", "Nobuyuki Sugio"],
        "year": 2026, "volume": "E109.A", "issue": 9, "pages": "1621-1622", "expected_pdf_pages": 2,
        "doi": "10.1587/transfun.2025DML0002", "article_type": "LETTER",
        "base_url": "https://www.jstage.jst.go.jp/article/transfun/E109.A/9/E109.A_2025DML0002/",
    },
    {
        "id": "03_keyword_blindness_2026",
        "title": "Security Analysis on \u201cBlockchain-Based Privacy-Preserving Public Key Searchable Encryption with Strong Traceability\u201d",
        "authors": ["Keita Emura", "Toshihiro Ohigashi", "Nobuyuki Sugio"],
        "year": 2026, "volume": "E109.A", "issue": 9, "pages": "1623-1624", "expected_pdf_pages": 2,
        "doi": "10.1587/transfun.2025DML0003", "article_type": "LETTER",
        "base_url": "https://www.jstage.jst.go.jp/article/transfun/E109.A/9/E109.A_2025DML0003/",
    },
    {
        "id": "04_khpke_security_notions_2021",
        "title": "On the Security of Keyed-Homomorphic PKE: Preventing Key Recovery Attacks and Ciphertext Validity Attacks",
        "authors": ["Keita Emura"],
        "year": 2021, "volume": "E104.A", "issue": 1, "pages": "310-314", "expected_pdf_pages": 5,
        "doi": "10.1587/transfun.2020EAL2039", "article_type": "LETTER",
        "base_url": "https://www.jstage.jst.go.jp/article/transfun/E104.A/1/E104.A_2020EAL2039/",
    },
]


def collect(paper):
    record = dict(paper)
    record["article_url"] = paper["base_url"] + "_article/-char/en"
    record["pdf_url"] = paper["base_url"] + "_pdf/-char/en"
    try:
        request = urllib.request.Request(record["pdf_url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=45) as response:
            blob = response.read()
            record["resolved_url"] = response.url
            record["content_type"] = response.headers.get("Content-Type")
        if not blob.startswith(b"%PDF-"):
            raise ValueError("The response is not a PDF")
        reader = PdfReader(io.BytesIO(blob), strict=False)
        pages = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
        if len(pages) != paper["expected_pdf_pages"]:
            raise ValueError(f"Unexpected page count: {len(pages)}")
        if "LETTER" not in pages[0]:
            raise ValueError("LETTER label missing from first page")
        destination = ROOT / (paper["id"] + ".pdf")
        if destination.exists() and destination.read_bytes() != blob:
            raise ValueError("Existing source PDF differs; refusing to overwrite")
        destination.write_bytes(blob)
        extraction = "\n\n".join(f"===== PDF PAGE {index + 1} =====\n{text}" for index, text in enumerate(pages))
        (ROOT / "reading" / (paper["id"] + ".txt")).write_text(extraction, encoding="utf-8")
        document = pdfium.PdfDocument(blob)
        for index in range(len(document)):
            page = document[index]
            bitmap = page.render(scale=1.4)
            bitmap.to_pil().save(ROOT / "reading" / f"{paper['id']}-p{index + 1}.png")
            bitmap.close()
            page.close()
        document.close()
        record.update(status="verified", pdf_file=destination.name,
                      sha256=hashlib.sha256(blob).hexdigest(), byte_count=len(blob), pdf_pages=len(pages),
                      source_version="final published PDF", pdf_bytes_modified=False)
    except Exception as error:
        record.update(status="failed", error=str(error))
    return record


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    (ROOT / "reading").mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(collect, PAPERS))
    manifest = {"retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "scope": "Primary-source IEICE Fundamentals LETTER PDFs selected for writing study; no independent revalidation of their proofs", "papers": records}
    (ROOT / "sources-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{key: row.get(key) for key in ("id", "status", "pdf_pages", "error")} for row in records], ensure_ascii=False, indent=2))
    return 0 if all(row["status"] == "verified" for row in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
