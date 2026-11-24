#!/usr/bin/env python3
"""Compare our Henning OCR with a typed copy of a Reclam edition (projekt-gutenberg.org, LOCAL REFERENCE ONLY; its site allows private use only).

The typed copy is never committed and never republished; this script only measures and reads off numbering. Output (local):
data/processed/henning/typed-compare.json with counts and verse-number pairs only (no text), safe to summarize.
"""
from __future__ import annotations

import difflib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "german-quran-henning-typed"
H = ROOT / "data" / "processed" / "henning"
VERSE = re.compile(r"(?<![\d(])(\d{1,3})\.\s*(?:\((\d{1,3})\.\)\s*)?(?=[A-ZÄÖÜ»«„\"(\[]|\s)")


def typed_sura(k: int):
    t = (RAW / f"chapter-{k:03d}.html").read_text(encoding="utf-8", errors="replace")
    m = re.search(r'book-reader__chapter-content-wrapper">(.*?)(?:</div>\s*</div>\s*</div>|<div class="book-reader__chapter-footer)', t, re.S)
    body = m.group(1) if m else t
    body = re.sub(r'<a name="page\d+"[^>]*></a>', "", body)
    body = re.sub(r"</p>", " ", body)
    body = html.unescape(re.sub(r"<[^>]+>", "", body))
    body = re.sub(r"\s+", " ", body)
    i = body.find("Barmherzigen!")
    body = body[i + 13:] if 0 <= i < 600 else body
    j = body.find(body[:80], 80)   # the page repeats the chapter (reading mode): keep the first copy
    if j > 0:
        body = body[:j]
    verses, nxt, pos, last = {}, 1, 0, None
    for mm in VERSE.finditer(body):
        n = int(mm.group(1))
        if n == nxt or (nxt < n <= nxt + 2 and (mm.group(2) or n == nxt + 1)):   # a verse that carries a bracketed number is surely a verse start
            nxt = n
        else:
            continue
        if last is not None:
            verses[last[0]]["text"] = body[last[2]:mm.start()].strip()
        verses[n] = {"cairo": int(mm.group(2)) if mm.group(2) else None}
        last = (n, mm.start(), mm.end())
        nxt += 1
    if last:
        verses[last[0]]["text"] = body[last[2]:].strip()
    return verses


def norm(s: str) -> str:
    s = s.lower().replace("ſ", "s").replace("ß", "ss").replace("th", "t")   # old/new spelling differences are not the point
    return re.sub(r"[^a-zäöüé]", "", s)


def main() -> int:
    ours = json.loads((H / "verse-texts.json").read_text())
    num = json.loads((H / "numbering.json").read_text())["suras"]
    out, sims = {}, []
    for k in range(1, 115):
        tv = typed_sura(k)
        ov = ours.get(str(k), {})
        pairs = {n: v["cairo"] for n, v in tv.items() if v["cairo"] is not None}
        common = [n for n in tv if str(n) in ov]
        s = []
        for n in common:
            a, b = norm(tv[n]["text"]), norm(ov[str(n)])
            if len(a) > 30 and len(b) > 30:
                s.append(difflib.SequenceMatcher(None, a[:400], b[:400], autojunk=False).ratio())
        out[k] = {"typed_verses": len(tv), "typed_highest": max(tv) if tv else 0, "scan_highest": num[str(k)]["henning_highest"],
                  "typed_with_cairo_number": len(pairs), "cairo_minus_henning": sorted({c - n for n, c in pairs.items()}),
                  "verses_compared": len(s), "mean_similarity": round(sum(s) / len(s), 3) if s else None}
        sims += s
    summary = {"suras": len(out), "mean_similarity_all": round(sum(sims) / len(sims), 3) if sims else None, "verses_compared": len(sims),
               "suras_with_same_highest": sum(1 for v in out.values() if v["typed_highest"] == v["scan_highest"]),
               "suras_with_different_highest": {k: (v["scan_highest"], v["typed_highest"]) for k, v in out.items() if v["typed_highest"] != v["scan_highest"]}}
    (H / "typed-compare.json").write_text(json.dumps({"summary": summary, "suras": out}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary)[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
