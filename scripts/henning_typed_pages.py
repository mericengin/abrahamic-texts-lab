#!/usr/bin/env python3
"""Rank Henning scan pages by OCR-type differences from the typed Reclam text (LOCAL reference only) and list the differing words per page.

Output stays local (data/processed/henning/typed-page-diffs.json, git-ignored: it holds words of the typed text). Used to decide which
pages to read against their images first; corrections are judged on the page image and written to manual-fixes.json.
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import henning_numbering as hn  # noqa: E402
import henning_typed_measure as tm  # noqa: E402

H = ROOT / "data" / "processed" / "henning"


def scan_words_with_pages(path: Path):
    hn.MD = path
    lines = hn.henning_body()
    starts = [i for i, (p, ln) in enumerate(lines) if re.search(r"Geoffenbart\s+zu", ln) and 30 < p < 616]
    out = []
    for k, s in enumerate(starts):
        end = len(lines)
        if k + 1 < len(starts):
            nx = starts[k + 1]
            heads = [j for j in range(nx - 4, nx) if re.search(r"Sure\W{0,3}$", lines[j][1])]
            end = heads[0] if heads else nx - 2
        words, carry = [], ("", 0)
        for page, ln in lines[s + 1:end]:
            ln = tm.NUMLEAD.sub("", ln)
            if re.search(r"Im Namen Allahs|Erbarmers|^\s*Geoffenbart", ln):
                continue
            toks = ln.split()
            if carry[0] and toks:
                toks[0] = carry[0] + toks[0]
                carry = ("", 0)
            if toks and toks[-1].endswith("-") and len(toks[-1]) > 2:
                carry = (toks.pop()[:-1], page)
            for w in toks:
                n = tm.nw(w)
                if n:
                    words.append((n, w, page))
        out.append(words)
    return out


def main() -> int:
    suras = scan_words_with_pages(tm.MDDIR / "german-quran-henning-fraktur-ocr-normalized-latf-pass2-base.md")
    perpage, diffs = defaultdict(int), defaultdict(list)
    for k in range(2, 115):
        a = tm.typed_words(k)
        b = suras[k - 1]
        sm = difflib.SequenceMatcher(None, a, [x[0] for x in b], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "replace" and (i2 - i1) == (j2 - j1):
                for t in range(i2 - i1):
                    if 0 < tm.edits(a[i1 + t], b[j1 + t][0]) <= 3:
                        pg = b[j1 + t][2]
                        perpage[pg] += 1
                        diffs[pg].append([b[j1 + t][1], a[i1 + t]])
    ranked = sorted(perpage.items(), key=lambda x: -x[1])
    (H / "typed-page-diffs.json").write_text(json.dumps({"ranked": ranked, "diffs": diffs}, ensure_ascii=False) + "\n", encoding="utf-8")
    print("pages with differences:", len(ranked), "| total:", sum(perpage.values()))
    print("top 30:", ranked[:30])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
