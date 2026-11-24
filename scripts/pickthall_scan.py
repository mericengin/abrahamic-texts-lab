"""Parse the OCR text of a scan of Pickthall's 1930 translation into suras and verses (the book's own numbering).

The 1930 book prints each sura as: SURAH <roman numeral>, a title, a place of revelation, the bismillah (unnumbered),
then verses numbered 1., 2., ... with Pickthall's notes interleaved in the sura introductions. This parser takes only
the numbered verses, in order, and records every gap it cannot fill (an OCR error in a verse number, for example),
so nothing is silently dropped.
"""
from __future__ import annotations

import re

ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def roman(n: int) -> str:
    out = ""
    for v, s in ROMAN:
        while n >= v:
            out += s
            n -= v
    return out


def clean(text: str) -> str:
    text = text.replace("\f", "\n")
    return re.sub(r"[ \t]+", " ", text)


def find_suras(text: str) -> tuple[dict[int, int], list[int]]:
    """Positions of 'SURAH <numeral>' headings in order. Missing ones are reported, not guessed."""
    pos: dict[int, int] = {}
    cursor = 0
    missing = []
    for n in range(1, 115):
        pat = re.compile(r"(?m)^\s*S[OÖÜU0]R[AÄ]H\s+" + roman(n) + r"\b")
        m = pat.search(text, cursor)
        if not m:
            missing.append(n)
            continue
        pos[n] = m.start()
        cursor = m.end()
    return pos, missing


def parse(text: str):
    text = clean(text)
    pos, missing = find_suras(text)
    suras: dict[int, list[tuple[int, str]]] = {}
    gaps: dict[int, list[int]] = {}
    order = sorted(pos)
    for i, n in enumerate(order):
        end = pos[order[i + 1]] if i + 1 < len(order) else len(text)
        body = text[pos[n]:end]
        rows, cursor, expect = [], 0, 1
        misses = []
        starts = []
        while expect < 400:
            m = re.compile(rf"(?m)^\s*{expect}\s?[.,:;]\s+(?=\S)").search(body, cursor)
            if not m:
                # the number may be damaged by OCR: try the next one, otherwise stop
                nxt = re.compile(rf"(?m)^\s*{expect + 1}\s?[.,:;]\s+(?=\S)").search(body, cursor)
                if nxt and expect < 300:
                    misses.append(expect)
                    expect += 1
                    continue
                break
            starts.append((expect, m.start(), m.end()))
            cursor = m.end()
            expect += 1
        for k, (num, s, e) in enumerate(starts):
            stop = starts[k + 1][1] if k + 1 < len(starts) else len(body)
            verse = re.sub(r"\s+", " ", body[e:stop]).strip()
            rows.append((num, verse))
        suras[n] = rows
        if misses:
            gaps[n] = misses
    return suras, missing, gaps
