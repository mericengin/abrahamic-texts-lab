#!/usr/bin/env python3
"""Check the Pickthall (1930) layer verse by verse against four independent OCR readings of the 1930 book.

Method (everything is computed on letter-only strings, so spacing, punctuation and line-end hyphens do not matter):
 1. Each scan's OCR text is aligned to the Gutenberg Pickthall text using long word sequences (20 letters) that occur exactly once in
    both, chained into a consistent order. This does not depend on printed verse numbers or page layout.
 2. Each Gutenberg verse is then aligned locally to the matching stretch of every scan. The differences between a scan and the
    Gutenberg verse are that scan's "variants" of the verse.
 3. A variant seen by two or more scans is a REAL difference between the 1930 text and Gutenberg (the 1930 text wins).
    A variant seen by only one scan, while another scan agrees with Gutenberg, is OCR noise and is dismissed.
Verdicts per verse: confirmed (two or more scans agree with the Gutenberg words), single-scan (only one scan reaches the verse),
no-scan (none does), differs (two or more scans agree on a different wording), conflict (scans disagree with each other and
with Gutenberg: needs the page image).
Output is local (git-ignored): data/processed/pickthall/.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from bisect import bisect_left
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "pickthall"
SCANS = {
    "scan-216140": RAW / "english-quran-pickthall" / "2015.216140.The-Meaning_djvu.txt",
    "scan-csl3756": RAW / "english-quran-pickthall-xcheck" / "dli.csl.3756_djvu.txt",
    "scan-min16944": RAW / "english-quran-pickthall-xcheck" / "dli.ministry.16944_djvu.txt",
    "scan-MN40248": RAW / "english-quran-pickthall-xcheck" / "MN40248ucmf_9_djvu.txt",
}
K = 20


def key(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", t)


def gutenberg() -> dict[tuple[int, int], str]:
    md = (ROOT / "data" / "processed" / "markdown" / "english-quran-pickthall-gutenberg" / "pickthall-only.md").read_text(encoding="utf-8")
    return {(int(s), int(v)): t for s, v, t in re.findall(r"(?m)^\*\*(\d+):(\d+)\*\* (.+)$", md)}


def chain(gfull: str, scan: str) -> list[tuple[int, int]]:
    """Monotone chain of (gutenberg position, scan position) pairs from 20-letter sequences unique in both texts."""
    counts = Counter(gfull[i:i + K] for i in range(len(gfull) - K + 1))
    gpos = {gfull[i:i + K]: i for i in range(len(gfull) - K + 1) if counts[gfull[i:i + K]] == 1}
    seen: dict[str, list[int]] = defaultdict(list)
    for i in range(len(scan) - K + 1):
        k = scan[i:i + K]
        if k in gpos:
            seen[k].append(i)
    pairs = sorted((gpos[k], v[0]) for k, v in seen.items() if len(v) == 1)
    # longest increasing subsequence on the scan positions
    tails, tail_idx, prev = [], [], [-1] * len(pairs)
    for i, (_, sp) in enumerate(pairs):
        j = bisect_left(tails, sp)
        if j == len(tails):
            tails.append(sp); tail_idx.append(i)
        else:
            tails[j] = sp; tail_idx[j] = i
        prev[i] = tail_idx[j - 1] if j else -1
    out, i = [], tail_idx[-1] if tail_idx else -1
    while i != -1:
        out.append(pairs[i])
        i = prev[i]
    return out[::-1]


def verse_variants(g: str, window: str):
    """Align one Gutenberg verse (letters) to a scan window. Returns (variants, matched fraction, unmatched start, unmatched end)."""
    sm = difflib.SequenceMatcher(None, g, window, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size >= 4]
    if not blocks:
        return None
    matched = sum(b.size for b in blocks)
    first, last = blocks[0], blocks[-1]
    core_a0, core_a1 = first.a, last.a + last.size
    variants = []
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == "equal" or a1 <= core_a0 or a0 >= core_a1:
            continue
        variants.append((a0, a1, window[b0:b1]))
    return variants, matched / max(len(g), 1), core_a0, len(g) - core_a1


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    guten = gutenberg()
    refs = sorted(guten)
    gkeys = {r: key(guten[r]) for r in refs}
    offs, pos = {}, 0
    for r in refs:
        offs[r] = pos
        pos += len(gkeys[r])
    gfull = "".join(gkeys[r] for r in refs)
    ev: dict[tuple[int, int], dict[str, dict]] = {r: {} for r in refs}
    report = {"scans": {}}
    for name, path in SCANS.items():
        text = re.sub(r"-\s*\n\s*", "", path.read_text(encoding="utf-8").replace("\f", "\n"))
        scan = key(text)
        pairs = chain(gfull, scan)
        gp = [p[0] for p in pairs]
        covered = 0
        for r in refs:
            g = gkeys[r]
            if len(g) < 8:
                continue
            gs = offs[r]
            i = bisect_left(gp, gs)
            before = pairs[i - 1] if i else None
            after = pairs[i] if i < len(pairs) else None
            cand = [a for a in (before, after) if a is not None and abs(a[0] - gs) <= 600]
            if not cand:
                continue
            a = min(cand, key=lambda x: abs(x[0] - gs))
            predicted = a[1] + (gs - a[0])
            window = scan[max(predicted - 40, 0): predicted + len(g) + 60]
            res = verse_variants(g, window)
            if res is None or res[1] < 0.55:
                continue
            variants, frac, lead, trail = res
            ev[r][name] = {"variants": variants, "matched": round(frac, 3), "unmatched_start": lead, "unmatched_end": trail}
            covered += 1
        report["scans"][name] = {"anchors": len(pairs), "verses_reached": covered, "of": len(refs)}
        print(f"{name}: {len(pairs):,} anchors, reaches {covered:,} of {len(refs):,} verses", flush=True)

    furniture_words = ("thegloriouskoran", "surah", "sorah", "sdrah", "suirah")

    def is_furniture(a, b, rep):
        return (a == b and len(rep) >= 15) or any(w in rep for w in furniture_words)   # running headers, captions and footnotes inside a verse's span

    verdicts, rows, review = Counter(), [], []
    furniture_total = 0
    for r in refs:
        e = ev[r]
        n = len(e)
        real_variants = {}
        for name, d in e.items():
            d["variants"] = [v for v in d["variants"] if not is_furniture(*v)]
        furniture_total += 0
        variant_count = Counter((a, b, rep) for d in e.values() for a, b, rep in d["variants"])
        # a variant is a real difference only if more scans show it than agree with Gutenberg at that spot
        real = [v for v, c in variant_count.items() if c >= 2 and c > n - c]
        tied = [v for v, c in variant_count.items() if c >= 2 and c == n - c]
        lone = [v for v, c in variant_count.items() if c == 1]
        edge = [name for name, d in e.items() if d["unmatched_start"] > 6 or d["unmatched_end"] > 6]
        clean = [name for name, d in e.items() if not d["variants"]]
        agree_g = [name for name, d in e.items() if not any(v in real or v in tied for v in d["variants"])]
        if n == 0:
            verdict = "no-scan"
        elif real:
            verdict = "differs"
        elif tied or (n >= 2 and len(agree_g) < 2 and lone and not clean):
            verdict = "conflict"
        elif len(agree_g) >= 2:
            verdict = "confirmed"
        else:
            verdict = "single-scan"
        if verdict == "confirmed" and len(edge) >= 2:
            verdict = "differs"           # two or more scans cannot find the verse's first or last words
        verdicts[verdict] += 1
        row = {"sura": r[0], "verse": r[1], "text": guten[r], "verdict": verdict, "scans_reaching": n, "scans_agreeing_with_gutenberg": len(agree_g),
               "real_variants": [{"gutenberg_letters": [a, b], "gutenberg": gkeys[r][a:b], "scan_reading": rep, "scans_showing": variant_count[(a, b, rep)]} for a, b, rep in real],
               "edge_unmatched_in": edge}
        rows.append(row)
        if verdict in ("differs", "conflict"):
            review.append({"ref": f"{r[0]}:{r[1]}", "verdict": verdict, "gutenberg": guten[r], "real_variants": row["real_variants"],
                           "per_scan": {k: {"variants": [[a, b, rep] for a, b, rep in d["variants"]], "unmatched_start": d["unmatched_start"], "unmatched_end": d["unmatched_end"]} for k, d in e.items()}})
    report.update({"verses": len(refs), "verdicts": dict(verdicts), "needs_review": len(review)})
    (OUT / "pickthall-1930-check.json").write_text(json.dumps(rows, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    (OUT / "needs-review.json").write_text(json.dumps(review, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (OUT / "check-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "scans"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
