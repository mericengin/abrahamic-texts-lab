#!/usr/bin/env python3
"""Rebuild Pickthall's 1930 text from the OCR of four scans of the 1930 book, by vote.

Why: the Project Gutenberg #16955 "Pickthall" lines turned out NOT to be the 1930 text (they differ in wording in roughly one verse
in ten, for example 2:57 "We wronged them not" in all four scans against "they wronged Us not"). So the 1930 layer is built from the
scans themselves. The Gutenberg text is used only as a coordinate system: it tells us where each sura starts in each scan.

Steps per scan: (1) find each sura's start with the anchor chain from pickthall_reconcile; (2) read the book's own numbered verses
in order inside that sura (1., 2., ...), after removing running headers and footnotes; (3) key each verse as letters only.
Steps per verse: vote across the scans by letter string. Verdicts: agreed (3 or more scans identical), pair (2 identical),
split (no two identical: needs the page image), single (only one scan has the verse). Output (local, git-ignored): data/processed/pickthall/.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from bisect import bisect_left
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pickthall_reconcile as pr  # noqa: E402

OUT = pr.OUT
ROOT_DIR = pr.ROOT
HEADER = re.compile(r"(?im)^[ \t]*(\d+[ \t]+)?the[ \t]+glorious[ \t]+koran([ \t]+[a-zöü0]+)?[ \t]*(\d+)?[ \t]*$")
MARK = re.compile(r"(?m)^[ \t]*(\d{1,3}|I|l)[ \t]?[.,:;·][ \t]*(?=\S)")


def clean_raw(text: str) -> str:
    text = text.replace("\f", "\n")
    text = re.sub(r"-[ \t]*\n[ \t]*", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = HEADER.sub("", text)
    # running headers that the OCR joined into running text: "VII THE HEIGHTS 159", "XXX the romans 415", "5i6 the glorious KORAN sOrah XLV"
    text = re.sub(r"(?i)\b\S{0,4}[ \t]+the[ \t]+glorious[ \t]+koran[ \t]+s[oöu0]r[aä]h[ \t]*[ivxlc]*\b", " ", text)
    text = re.sub(r"\b[IVXLC]{1,7}[ \t]+(?:THE|the|The)[ \t]+[A-Za-z'’ \t]{3,28}?[ \t]+\d{2,3}\b", " ", text)
    text = re.sub(r"\b\d{2,3}[ \t]+(?:THE|the)[ \t]+(?:GLORIOUS|glorious)[ \t]+(?:KORAN|koran)\b", " ", text)
    # footnotes: a line that starts with * or † up to the next blank line
    text = re.sub(r"(?m)^[ \t]*[*†‡][^\n]*(\n(?![ \t]*\n)[^\n]*)*", "", text)
    return text


def letters_index(text: str):
    chars, idx = [], []
    for i, ch in enumerate(text):
        for c in unicodedata.normalize("NFKD", ch.lower()):
            if "a" <= c <= "z":
                chars.append(c)
                idx.append(i)
    return "".join(chars), idx


def trim_tail(text: str, ref: str) -> str:
    """Drop text after the verse's last words (footnotes, headers, the next verse's number) when the Gutenberg verse is matched to its end."""
    import difflib
    lt, it = letters_index(text)
    g = pr.key(ref)
    if len(g) < 12 or not lt:
        return text
    sm = difflib.SequenceMatcher(None, g, lt, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size >= 4]
    if not blocks:
        return text
    last = blocks[-1]
    if len(g) - (last.a + last.size) <= 3 and len(lt) - (last.b + last.size) > 6:
        end = it[last.b + last.size - 1] + 1
        while end < len(text) and text[end] in ".,;:!?)”’'\"*":   # keep the verse's own closing punctuation
            end += 1
        return text[:end].rstrip()
    return text


def sura_starts(letters: str, idx: list[int], guten, gkeys, offs):
    """Raw-text position near each sura's first verse, from the anchor chain."""
    gfull = "".join(gkeys[r] for r in sorted(guten))
    pairs = pr.chain(gfull, letters)
    gp = [p[0] for p in pairs]
    out = {}
    for s in range(1, 115):
        refs = [r for r in sorted(guten) if r[0] == s and len(gkeys[r]) >= 14]
        if not refs:
            continue
        r = refs[0]
        gs = offs[r]
        i = bisect_left(gp, gs)
        cand = [a for a in (pairs[i - 1] if i else None, pairs[i] if i < len(pairs) else None) if a and abs(a[0] - gs) <= 800]
        if cand:
            a = min(cand, key=lambda x: abs(x[0] - gs))
            pred = max(0, min(a[1] + (gs - a[0]), len(idx) - 1))
            out[s] = pred
    return out


def parse_scan(path: Path, guten, gkeys, offs, sizes):
    """Locate every standard verse by alignment (coarse), then snap to the book's own printed verse number nearby (exact)."""
    raw = clean_raw(path.read_text(encoding="utf-8"))
    letters, idx = letters_index(raw)
    gfull = "".join(gkeys[r] for r in sorted(guten))
    pairs = pr.chain(gfull, letters)
    gp = [p[0] for p in pairs]
    marks = [(1 if m.group(1) in ("I", "l") else int(m.group(1)), m.start(), m.end()) for m in MARK.finditer(raw)]
    starts: dict[tuple[int, int], tuple[int, int, int | None]] = {}   # verse -> (text start, boundary start, printed number)
    for r in sorted(guten):
        gs = offs[r]
        i = bisect_left(gp, gs)
        cand = [a for a in (pairs[i - 1] if i else None, pairs[i] if i < len(pairs) else None) if a and abs(a[0] - gs) <= 600]
        if not cand:
            continue
        a = min(cand, key=lambda x: abs(x[0] - gs))
        pred = idx[max(0, min(a[1] + (gs - a[0]), len(idx) - 1))]
        near = [(abs(pred - en), n, st, en) for n, st, en in marks if pred - 250 <= en <= pred + 80]
        if near:
            _, n, st, en = min(near)
            starts[r] = (en, st, n)
        else:
            starts[r] = (pred, pred, None)
    verses: dict[tuple[int, int], str] = {}
    numbering: dict[tuple[int, int], int] = {}
    snapped = 0
    order = sorted(starts)
    for k, r in enumerate(order):
        st, _, printed = starts[r]
        if printed is not None:
            snapped += 1
            numbering[r] = printed
        same_sura_next = k + 1 < len(order) and order[k + 1][0] == r[0]
        end = starts[order[k + 1]][1] if k + 1 < len(order) else len(raw)
        ref_len = len(guten[r])
        if not same_sura_next:  # last verse of a sura: stop where the next sura's heading begins
            h = re.compile(r"(?i)\b(s[oöu0]r[aä]h\b|revealed\s+at)").search(raw, st + 20, end)
            if h:
                end = h.start()
        text = re.sub(r"\s+", " ", raw[st:end]).strip()
        words = text.split(" ")
        text = " ".join(words[: int(max(ref_len / 5.0, 4) * 1.6) + 10])
        text = trim_tail(text, guten[r])
        if text:
            verses[r] = text
    notes = {"verses_located": len(starts), "snapped_to_printed_number": snapped, "not_located": [f"{a}:{b}" for a, b in sorted(guten) if (a, b) not in starts][:12]}
    notes["numbering"] = {f"{a}:{b}": n for (a, b), n in numbering.items()}
    return verses, notes


def main() -> int:
    guten = pr.gutenberg()
    refs = sorted(guten)
    gkeys = {r: pr.key(guten[r]) for r in refs}
    offs, pos = {}, 0
    for r in refs:
        offs[r] = pos
        pos += len(gkeys[r])
    sizes = Counter(s for s, _ in refs)
    per_scan, report = {}, {"scans": {}}
    for name, path in pr.SCANS.items():
        v, notes = parse_scan(path, guten, gkeys, offs, sizes)
        per_scan[name] = v
        report["scans"][name] = {"verses_read": len(v), **notes}
        print(f"{name}: read {len(v):,} verses; snapped to the printed verse number: {notes['snapped_to_printed_number']:,}", flush=True)

    rows, verdicts = [], Counter()
    for r in refs:
        reads = {n: per_scan[n][r] for n in per_scan if r in per_scan[n] and pr.key(per_scan[n][r])}
        keys = {n: pr.key(t) for n, t in reads.items()}
        count = Counter(keys.values())
        top, c = count.most_common(1)[0] if count else ("", 0)
        winners = [n for n, k in keys.items() if k == top]
        if c >= 3:
            verdict = "agreed"
        elif c == 2:
            verdict = "pair"
        elif len(keys) >= 2:
            verdict = "split"
        elif len(keys) == 1:
            verdict = "single"
        else:
            verdict = "missing"
        verdicts[verdict] += 1
        text = reads[winners[0]] if winners else ""
        rows.append({"sura": r[0], "verse": r[1], "verdict": verdict, "scans_with_verse": len(keys), "identical": c, "text": text,
                     "gutenberg_identical": pr.key(guten[r]) == top, "readings": {n: t for n, t in reads.items()} if verdict in ("split", "single", "pair") else {}})
    same = sum(1 for x in rows if x["gutenberg_identical"])
    report.update({"verses": len(rows), "verdicts": dict(verdicts), "identical_to_gutenberg_pickthall": same,
                   "differs_from_gutenberg": sum(1 for x in rows if x["verdict"] in ("agreed", "pair") and not x["gutenberg_identical"])})
    # --- numbering map: the number printed in the 1930 book for each standard verse (majority over the scans)
    printed: dict[str, Counter] = {}
    for sc in report["scans"].values():
        for ref, n in sc["numbering"].items():
            printed.setdefault(ref, Counter())[n] += 1
    numbering = {ref: c.most_common(1)[0][0] for ref, c in printed.items()}
    offsets: dict[int, Counter] = {}
    for ref, n in numbering.items():
        su, v = map(int, ref.split(":"))
        offsets.setdefault(su, Counter())[n - v] += 1
    sura_offsets = {su: dict(c.most_common()) for su, c in sorted(offsets.items())}
    (OUT / "pickthall-numbering-map.json").write_text(json.dumps({"printed_number_by_standard_verse": numbering, "offset_counts_by_sura": sura_offsets,
                                                               "note": "offset = number printed in the 1930 book minus the standard verse number"}, indent=0) + "\n", encoding="utf-8")
    # --- review queue: undecided verses, and agreed verses whose text looks contaminated (very long or very short against Gutenberg)
    review = []
    for x in rows:
        ref = (x["sura"], x["verse"])
        glen, tlen = len(pr.key(guten[ref])), len(pr.key(x["text"]))
        why = None
        if x["verdict"] in ("split", "single", "missing"):
            why = x["verdict"]
        elif tlen > glen * 1.35 + 25:
            why = "text much longer than Gutenberg (page furniture or a footnote may have leaked in)"
        elif glen > 20 and tlen < glen * 0.6:
            why = "text much shorter than Gutenberg (a boundary may be misplaced)"
        if why:
            x["review"] = why
            review.append({"ref": f"{ref[0]}:{ref[1]}", "why": why, "chosen_text": x["text"], "gutenberg": guten[ref], "readings": x["readings"]})
    (OUT / "pickthall-1930-review-queue.json").write_text(json.dumps(review, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    report["review_queue"] = len(review)
    report["review_reasons"] = dict(Counter(r["why"].split(" (")[0] for r in review))
    # --- Markdown layer
    mdroot = ROOT_DIR / "data" / "processed" / "markdown" / "english-quran-pickthall-1930"
    mdroot.mkdir(parents=True, exist_ok=True)
    by_sura: dict[int, list[dict]] = {}
    for x in rows:
        by_sura.setdefault(x["sura"], []).append(x)
    for su, vs in by_sura.items():
        lines = ["---", f"source_id: \"english-quran-pickthall-1930\"", f"sura: {su}", "language: \"English\"",
                 "status: \"reconstructed from the OCR of four scans of the 1930 book by vote; not proofread; see the verse comments\"",
                 "numbering: \"standard verse numbers (the 1930 book prints some verses under other numbers; see pickthall-numbering-map.json)\"", "---", "", f"# Sura {su}", ""]
        for x in vs:
            flag = x.get("review") or x["verdict"]
            lines += [f"<!-- verdict: {x['verdict']}; scans identical: {x['identical']} of {x['scans_with_verse']}" + (f"; REVIEW: {x['review']}" if x.get("review") else "") + " -->", f"**{x['verse']}** {x['text']}", ""]
        (mdroot / f"{su:03d}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (mdroot / "INDEX.md").write_text("# Pickthall 1930, reconstructed by vote\n\nOne file per sura. Built by scripts/pickthall_build.py from the OCR of four scans of the 1930 edition. "
                                     "Verses carry a verdict comment (agreed, pair, split, single, missing) and a REVIEW note where the text may be contaminated. Not proofread.\n", encoding="utf-8")
    (OUT / "pickthall-1930-built.json").write_text(json.dumps(rows, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    (OUT / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "scans"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
