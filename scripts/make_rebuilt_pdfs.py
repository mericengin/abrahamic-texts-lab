#!/usr/bin/env python3
"""Reading PDFs for the two Qur'an translation layers that we rebuilt from scans (local, git-ignored output).

  english-quran-pickthall-1930   from data/processed/pickthall/pickthall-1930-built.json (standard verse numbers); verses that rest on a
                                 word vote are marked with a dagger, verses read against the page image with a double dagger
  german-quran-henning           from the repair-pass-2 OCR layer, page by page (the layer is not proofread; the title page says so)
Both PDFs carry a title page with the source, license and the measured quality, so a reader never mistakes them for the printed editions.
Usage: python3 scripts/make_rebuilt_pdfs.py     (needs Google Chrome)
"""
from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed" / "pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = "body{font-family:Georgia,serif;line-height:1.45;margin:2.2cm} h1,h2{font-family:Helvetica,sans-serif} .v{margin:.25em 0} .n{font-weight:bold;color:#555} .box{border:1px solid #999;padding:1em;margin:1em 0} h2{page-break-before:always} .p{white-space:pre-wrap}"


def pdf(html_path: Path, pdf_path: Path) -> None:
    pdf_path.unlink(missing_ok=True)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", f"file://{html_path}"],
                   check=True, capture_output=True, timeout=1500)


def pickthall() -> None:
    d = OUT / "english-quran-pickthall-1930"
    d.mkdir(parents=True, exist_ok=True)
    rows = json.loads((ROOT / "data" / "processed" / "pickthall" / "pickthall-1930-built.json").read_text())
    voted = sum(1 for r in rows if r["verdict"] == "voted")
    checked = sum(1 for r in rows if r["verdict"] == "image-checked")
    parts = [f"<html><head><meta charset='utf-8'><title>The Meaning of the Glorious Koran (Pickthall 1930), reconstructed text</title><style>{CSS}</style></head><body>",
             "<h1>The Meaning of the Glorious Koran</h1><p>Marmaduke Pickthall, 1930. Reconstructed reading text.</p>",
             "<div class='box'><b>What this is.</b> The 1930 text rebuilt from four scans of the printed book (Internet Archive) by comparing them word by word. "
             "It is not the printed edition and not the Project Gutenberg text, which differs from the 1930 book. Verse numbers are the standard (Cairo) numbers; the 1930 book numbers "
             "some verses differently. Diacritics of transliterated names are not reproduced.<br><br>"
             f"<b>Quality.</b> About 98% of verses were decided by agreement between scans. {checked} verses were read against the page images (marked &Dagger;), "
             f"{voted} rest on a word-by-word vote (marked &dagger;; a fresh OCR of the pages confirms all of them). Shared OCR slips are estimated at 0.5 to 1.5% of verses. "
             "Not reviewed by a domain expert.<br><br><b>License.</b> Public domain (published 1930; translator died 1936), per Wikimedia Commons and Wikisource. This reading copy is made by Abrahamic Texts Lab.</div>"]
    cur = None
    for r in rows:
        if r["sura"] != cur:
            cur = r["sura"]
            parts.append(f"<h2>Sura {cur}</h2>")
        mark = "&dagger;" if r["verdict"] == "voted" else "&Dagger;" if r["verdict"] == "image-checked" else ""
        parts.append(f"<p class='v'><span class='n'>{cur}:{r['verse']}</span> {html.escape(r['text'])}{mark}</p>")
    parts.append("</body></html>")
    (d / "pickthall-1930-reconstructed.html").write_text("\n".join(parts), encoding="utf-8")
    pdf(d / "pickthall-1930-reconstructed.html", d / "pickthall-1930-reconstructed.pdf")


def henning() -> None:
    d = OUT / "german-quran-henning"
    d.mkdir(parents=True, exist_ok=True)
    md = (ROOT / "data" / "processed" / "markdown" / "german-quran-henning" / "german-quran-henning-fraktur-ocr-normalized-latf-pass2.md").read_text(encoding="utf-8")
    pages = re.split(r"(?m)^## Page (\d+)\n", md)
    parts = [f"<html><head><meta charset='utf-8'><title>Der Koran, Max Henning (1901), machine-read text</title><style>{CSS}</style></head><body>",
             "<h1>Der Koran</h1><p>Max Henning, Reclam, Leipzig, 1901. Machine-read text of a scan, page by page.</p>",
             "<div class='box'><b>What this is.</b> OCR of a Fraktur scan (Internet Archive, University of Toronto copy) with an automatic repair pass. It is NOT proofread. "
             "Word errors are about 1.3 to 2% (measured against a typed copy of another edition and by eye on a random sample); page headers, footnotes and verse numbers are as the OCR read them. "
             "Spelling is the 1901 spelling. Use the scan for anything you quote.<br><br><b>License.</b> Henning's translation is public domain in Germany by the author-death rule (Henning died 1927); "
             "the scan carries no rights metadata. This reading copy is made by Abrahamic Texts Lab.</div>"]
    for i in range(1, len(pages), 2):
        parts.append(f"<h2>Scan page {int(pages[i])}</h2><div class='p'>{html.escape(pages[i + 1].strip())}</div>")
    parts.append("</body></html>")
    (d / "henning-1901-machine-read.html").write_text("\n".join(parts), encoding="utf-8")
    pdf(d / "henning-1901-machine-read.html", d / "henning-1901-machine-read.pdf")


if __name__ == "__main__":
    pickthall()
    henning()
    for p in sorted(OUT.glob("*/*.pdf")):
        info = subprocess.run(["pdfinfo", str(p)], capture_output=True, text=True).stdout
        pages = next((ln.split(":")[1].strip() for ln in info.splitlines() if ln.startswith("Pages:")), "?")
        print(p.relative_to(OUT), f"{p.stat().st_size:,} bytes", pages, "pages")
