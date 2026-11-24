#!/usr/bin/env python3
"""Generate reading PDFs for sources that have no official PDF (Hebrew WLC, Greek SBLGNT, Arabic Qur'an).

Builds an HTML file from the parsed source text (same parsers as to_markdown.py, words unchanged) and prints it to PDF
with headless Google Chrome. The result is a plain reading copy, not an official edition, and says so on its title page.
Official PDFs (WEB, Luther 1912, the Pickthall and Henning scans) are used as downloaded and are not regenerated.

Output (local, git-ignored): data/processed/pdf/<source-id>/<version>.pdf and .html, plus PDFS.json.
Usage: python3 scripts/make_pdfs.py [source-id ...]      Needs Google Chrome and (for page counts) poppler's pdfinfo.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed" / "pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# source id -> [(version key, CSS font class)]
TARGETS = {
    "hebrew-morphhb": [("hebrew-wlc", "he")],
    "greek-sblgnt-text": [("greek-sblgnt", "")],
    "quran-tanzil-arabic": [("quran-uthmani-xml", "ar")],
}


def main() -> int:
    with (ROOT / "data" / "sources.toml").open("rb") as fh:
        sources = {s["id"]: s for s in tomllib.load(fh)["source"]}
    ids = sys.argv[1:] or list(TARGETS)
    builders = canon.builders(RAW)
    for sid in ids:
        src = sources[sid]
        prov = json.loads((RAW / sid / "MANIFEST.json").read_text())
        front = {"source_id": sid, "license": src["license"], "attribution": src["attribution"]}
        record = {"source_id": sid, "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "pdfs": {}}
        for key, font in TARGETS[sid]:
            ver = dict(builders[sid])[key]()
            html_path = OUT / sid / f"{key}.html"
            pdf_path = OUT / sid / f"{key}.pdf"
            canon.write_html(ver, html_path, front, font)
            pdf_path.unlink(missing_ok=True)
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
                            f"file://{html_path}"], check=True, capture_output=True, timeout=1500)
            info = subprocess.run(["pdfinfo", str(pdf_path)], capture_output=True, text=True).stdout
            pages = next((int(ln.split(":")[1]) for ln in info.splitlines() if ln.startswith("Pages:")), None)
            record["pdfs"][key] = {"pdf": pdf_path.name, "bytes": pdf_path.stat().st_size, "pages": pages,
                                   "verses": ver.stats.get("verses", ver.stats.get("ayas")), "source_retrieved_utc": prov["retrieved_utc"]}
            print(f"{sid}/{key}.pdf: {pdf_path.stat().st_size:,} bytes, {pages} pages", flush=True)
        (OUT / sid / "PDFS.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
