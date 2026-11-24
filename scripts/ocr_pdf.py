#!/usr/bin/env python3
"""OCR a scanned PDF page by page with Tesseract (needs tesseract and poppler's pdftoppm; see README).

Writes data/processed/ocr/<source-id>/page-NNN.txt (one file per page) and OCR.json (tool versions, model checksum,
settings, per-page character counts), so the result is reproducible and every page is accounted for.
Output stays local (git-ignored).

Usage: scripts/ocr_pdf.py <source-id> <pdf file name in data/raw/<source-id>/> [--lang Fraktur] [--dpi 300] [--psm 6] [--jobs 6]
Models live in .tools/tessdata (TESSDATA_PREFIX is set for you).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def page_count(pdf: Path) -> int:
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(next(line.split(":")[1] for line in out.splitlines() if line.startswith("Pages:")))


def ocr_page(pdf: Path, n: int, outdir: Path, lang: str, dpi: int, psm: int, env: dict) -> tuple[int, int]:
    target = outdir / f"page-{n:03d}.txt"
    if target.exists():
        return n, len(target.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "p"
        subprocess.run(["pdftoppm", "-r", str(dpi), "-gray", "-f", str(n), "-l", str(n), "-png", str(pdf), str(prefix)], check=True)
        png = next(Path(tmp).glob("p-*.png"))
        res = subprocess.run(["tesseract", str(png), "-", "-l", lang, "--psm", str(psm)], capture_output=True, text=True, env=env, check=True)
    target.write_text(res.stdout, encoding="utf-8")
    return n, len(res.stdout)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source_id")
    ap.add_argument("pdf")
    ap.add_argument("--lang", default="Fraktur")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--psm", type=int, default=6)
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--tag", default="", help="suffix for the output folder so a second run does not overwrite the first (e.g. -latf)")
    a = ap.parse_args()

    pdf = ROOT / "data" / "raw" / a.source_id / a.pdf
    outdir = ROOT / "data" / "processed" / "ocr" / (a.source_id + a.tag)
    outdir.mkdir(parents=True, exist_ok=True)
    tessdata = ROOT / ".tools" / "tessdata"
    env = {**os.environ, "TESSDATA_PREFIX": str(tessdata), "OMP_THREAD_LIMIT": "1"}
    pages = page_count(pdf)
    print(f"{pdf.name}: {pages} pages, lang={a.lang}, dpi={a.dpi}, psm={a.psm}, jobs={a.jobs}", flush=True)
    done = 0
    sizes: dict[int, int] = {}
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for n, size in ex.map(lambda n: ocr_page(pdf, n, outdir, a.lang, a.dpi, a.psm, env), range(1, pages + 1)):
            sizes[n] = size
            done += 1
            if done % 50 == 0 or done == pages:
                print(f"  {done}/{pages} pages", flush=True)
    models = [tessdata / f"{m}.traineddata" for m in a.lang.split("+")]
    version = subprocess.run(["tesseract", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    record = {
        "source_id": a.source_id, "pdf": a.pdf, "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(), "pages": pages,
        "tesseract": version, "language_model": a.lang, "model_sha256": "+".join(hashlib.sha256(m.read_bytes()).hexdigest() for m in models),
        "model_source": "https://github.com/tesseract-ocr/tessdata_best (script/Fraktur.traineddata and deu_latf.traineddata, Apache-2.0)",
        "dpi": a.dpi, "psm": a.psm, "ocr_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "chars_per_page": {str(k): v for k, v in sorted(sizes.items())},
        "empty_pages": [k for k, v in sorted(sizes.items()) if v < 20],
    }
    (outdir / "OCR.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"done: {pages} pages, {sum(sizes.values()):,} characters, {len(record['empty_pages'])} near-empty pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
