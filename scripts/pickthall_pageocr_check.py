#!/usr/bin/env python3
"""Compare chosen Pickthall verses with a fresh page-by-page OCR (modern engine) of the 1930 scan's page images.

The fresh OCR reads the same page images as one of the four older OCR texts but with a different engine, so it does not share that engine's slips.
A verse is 'confirmed' when all its words appear in order in the page text with at most one replaced word (extra words are footnotes or headers).
Mismatches are listed with their PDF pages so a person can look at the page image.
Usage: python3 scripts/pickthall_pageocr_check.py [sample-size-of-agreed-verses]   (seeded, so the sample is reproducible)
"""
import difflib
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pickthall_reconcile as pr  # noqa: E402

D = pr.ROOT / "data" / "processed" / "ocr" / "english-quran-pickthall-pages"
pages = {n: (D / f"page-{n:03d}.txt").read_text(encoding="utf-8") for n in range(1, 711)}
# one long word list with the page of every word
words, wpage = [], []
for n in range(1, 711):
    for w in re.sub(r"-\s*\n\s*", "", pages[n]).split():
        k = re.sub(r"[^a-z]", "", w.lower())
        if k:
            words.append(k)
            wpage.append(n)
rows = json.loads((pr.OUT / "pickthall-1930-built.json").read_text())
sample_n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
rng = random.Random(1930)
agreed = [r for r in rows if r["verdict"] in ("agreed", "pair")]
targets = [("voted", r) for r in rows if r["verdict"] == "voted"] + [("agreed-sample", r) for r in rng.sample(agreed, min(sample_n, len(agreed)))]
index = {}
for i in range(len(words) - 2):
    index.setdefault((words[i], words[i + 1], words[i + 2]), []).append(i)


def check(text: str):
    g = [re.sub(r"[^a-z]", "", w.lower()) for w in text.split() if re.sub(r"[^a-z]", "", w.lower())]
    if len(g) < 4:
        return "short", []
    best = None
    for start in index.get(tuple(g[:3]), []):
        window = words[start: start + len(g) + 40]
        sm = difflib.SequenceMatcher(None, g, window, autojunk=False)
        matched = sum(b.size for b in sm.get_matching_blocks())
        replaced = sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t == "replace")
        deleted = sum(i2 - i1 for t, i1, i2, j1, j2 in sm.get_opcodes() if t == "delete")
        score = (matched / len(g), -replaced - deleted)
        if best is None or score > best[0]:
            best = (score, start, replaced, deleted, matched / len(g))
    if best is None:
        return "not found", []
    _, start, replaced, deleted, cov = best
    pgs = sorted({wpage[k] for k in range(start, min(start + len(g) + 10, len(wpage)))})
    ok = cov >= 0.98 and replaced + deleted <= 1
    return ("confirmed" if ok else "mismatch"), pgs


out = {"voted": {"confirmed": 0, "mismatch": [], "not found": [], "short": 0}, "agreed-sample": {"confirmed": 0, "mismatch": [], "not found": [], "short": 0}}
for group, r in targets:
    ref = f"{r['sura']}:{r['verse']}"
    verdict, pgs = check(r["text"])
    if verdict in ("confirmed", "short"):
        out[group][verdict] += 1
    else:
        out[group][verdict].append({"ref": ref, "pdf_pages": pgs})
(pr.OUT / "pageocr-check.json").write_text(json.dumps(out, indent=1))
for g, v in out.items():
    n = v["confirmed"] + v["short"] + len(v["mismatch"]) + len(v["not found"])
    print(f"{g}: {n} verses | confirmed by the fresh page OCR {v['confirmed']} | too short to test {v['short']} | mismatch {len(v['mismatch'])} | not found {len(v['not found'])}")
    print("  to look at:", [(x['ref'], x['pdf_pages']) for x in v["mismatch"] + v["not found"]][:60])
