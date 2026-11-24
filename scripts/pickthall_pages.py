#!/usr/bin/env python3
"""Find the PDF page of the 1930 scan that holds each queued verse, so it can be checked against the page image.

Needs the page-by-page OCR made with: python3 scripts/ocr_pdf.py english-quran-pickthall 2015.216140.The-Meaning.pdf --lang eng --dpi 200 --tag=-pages
Writes data/processed/pickthall/queue-pages.json: for each queued verse, candidate PDF pages (a verse can span two pages).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pickthall_reconcile as pr  # noqa: E402

ROOT = pr.ROOT
D = ROOT / "data" / "processed" / "ocr" / "english-quran-pickthall-pages"
pages = {n: pr.key((D / f"page-{n:03d}.txt").read_text(encoding="utf-8")) for n in range(1, 711) if (D / f"page-{n:03d}.txt").exists()}
queue = json.loads((pr.OUT / "pickthall-1930-review-queue.json").read_text())
out = {}
for item in queue:
    g = pr.key(item["gutenberg"])
    anchors = [g[:20], g[len(g) // 2: len(g) // 2 + 20], g[-20:]]
    hits = {}
    for n, k in pages.items():
        score = sum(1 for a in anchors if len(a) >= 12 and a in k)
        if score:
            hits[n] = score
    best = sorted(hits, key=lambda n: (-hits[n], n))[:3]
    out[item["ref"]] = {"why": item["why"], "pages": best, "scores": {str(n): hits[n] for n in best}}
(pr.OUT / "queue-pages.json").write_text(json.dumps(out, indent=1))
located = sum(1 for v in out.values() if v["pages"])
print(f"{located} of {len(out)} queued verses located on a page")
print({r: v["pages"] for r, v in out.items()})
