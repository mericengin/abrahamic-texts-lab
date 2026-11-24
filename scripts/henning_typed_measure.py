#!/usr/bin/env python3
"""Measure the Henning OCR layers against the typed Reclam text (LOCAL reference only; only counts are written).

For each sura the Qur'an words of an OCR layer are aligned to the typed words (difflib on normalized words: lower case, no diacritics, ß=ss,
th=t, ph=f, so old and new spelling agree). A differing stretch counts as an "OCR-like" error when the two words are within 2 edits of each
other, and as "other" otherwise (different wording between the 1901 and 1970 texts, footnotes, headings, missing or merged text).
OCR-like errors are an upper-ish estimate of OCR errors: some are real spelling or wording differences of the typed edition.
Run on both the normalized layer and the layer with repair pass 2 to see what the repair pass gained over the whole book.
"""
from __future__ import annotations

import difflib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import henning_numbering as hn  # noqa: E402
import henning_typed_compare as tc  # noqa: E402

MDDIR = ROOT / "data" / "processed" / "markdown" / "german-quran-henning"
LAYERS = {"normalized": MDDIR / "german-quran-henning-fraktur-ocr-normalized-latf.md",
          "normalized + repair pass 2": MDDIR / "german-quran-henning-fraktur-ocr-normalized-latf-pass2.md"}
NUMLEAD = re.compile(r"^[\s|'\-•.·]*\d{1,3}[.,:;]\s*")


def nw(w: str) -> str:
    w = unicodedata.normalize("NFKD", w.lower().replace("ß", "ss"))
    w = "".join(c for c in w if not unicodedata.combining(c))
    w = w.replace("th", "t").replace("ph", "f").replace("ſ", "s")
    return re.sub(r"[^a-z]", "", w)


def edits(a: str, b: str) -> int:
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal")


def scan_sura_words(path: Path):
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
        words, carry = [], ""
        for _, ln in lines[s + 1:end]:
            ln = NUMLEAD.sub("", ln)
            if re.search(r"Im Namen Allahs|Erbarmers|^\s*Geoffenbart", ln):
                continue
            toks = ln.split()
            if carry and toks:                  # a word split by a line-end hyphen is rejoined
                toks[0] = carry + toks[0]
                carry = ""
            if toks and toks[-1].endswith("-") and len(toks[-1]) > 2:
                carry = toks.pop()[:-1]
            words += [x for x in (nw(w) for w in toks) if x]
        out.append(words)
    return out


def typed_words(k: int):
    v = tc.typed_sura(k)
    return [x for n in sorted(v) for x in (nw(w) for w in v[n]["text"].split()) if x]


def main() -> int:
    typed = {k: typed_words(k) for k in range(2, 115)}
    report = {}
    for label, path in LAYERS.items():
        suras = scan_sura_words(path)
        tot, ocr, other, same, broad = 0, 0, 0, 0, 0
        for k in range(2, 115):
            a, b = typed[k], suras[k - 1]
            sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                n = max(i2 - i1, j2 - j1)
                if tag == "equal":
                    same += n
                elif tag == "replace" and (i2 - i1) == (j2 - j1) and all(edits(a[i1 + t], b[j1 + t]) <= 2 for t in range(i2 - i1)):
                    ocr += n
                    broad += n
                elif tag == "replace" and (i2 - i1) == (j2 - j1) and all(edits(a[i1 + t], b[j1 + t]) <= max(2, 0.4 * len(a[i1 + t])) for t in range(i2 - i1)):
                    broad += n
                    other += n
                else:
                    other += n
            tot += len(a)
        report[label] = {"typed_words": tot, "equal": same, "ocr_like_word_errors": ocr, "broad_ocr_like_word_errors": broad, "broad_rate_percent": round(100 * broad / tot, 2), "other_differences": other,
                         "ocr_like_rate_percent": round(100 * ocr / tot, 2), "other_rate_percent": round(100 * other / tot, 2)}
        print(label, report[label], flush=True)
    (ROOT / "data" / "processed" / "henning" / "typed-measure.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
