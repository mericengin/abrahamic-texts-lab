#!/usr/bin/env python3
"""Align our Henning OCR (1901 scan) to the typed Reclam text and read the standard verse numbers off the typed text's brackets.

Local reference use only (see data/sources.toml: german-quran-henning-typed). Output is numbers only (data/processed/henning/typed-alignment.json).

Step 1, typed verses -> standard numbers. In the typed text a verse "n. (c.)" starts at standard verse c; an unbracketed verse follows the
previous one. Between two bracketed verses (n1, c1) and (n2, c2): if n2-n1 equals c2-c1 every verse is 1:1; if the typed text has more verses,
the extra pieces are continuations of one standard verse (only unique when c2-c1 = 1); if fewer, one typed verse covers several standard
verses (only unique when n2-n1 = 1). Other cases are marked uncertain, never guessed.
Step 2, scan verses -> typed verses. Both texts are reduced to letters; letter 12-grams that occur once in each are chained into a monotone
alignment, positions in between are interpolated, and each scan verse is assigned the typed verses it overlaps.
"""
from __future__ import annotations

import json
import re
import sys
from bisect import bisect_left
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import henning_typed_compare as tc  # noqa: E402

H = ROOT / "data" / "processed" / "henning"
K = 12


def key(s: str) -> str:
    s = s.lower().replace("ſ", "s").replace("ß", "ss").replace("th", "t").replace("ph", "f")
    return re.sub(r"[^a-zäöü]", "", s)


GROUPS = [(1, 1), (1, 2), (1, 3), (2, 1), (3, 1)]


def resolve_segment(tl: list[int], pl: list[int], r: float):
    """Ambiguous stretch: assign the typed verses (lengths tl) to the standard verses (lengths pl) in groups (1:1, 1:2, 1:3, 2:1, 3:1) that
    minimize the log length ratio; returns a list of (first, last) standard index per typed verse, or None."""
    import math
    n, m = len(tl), len(pl)
    INF = 1e18
    best = [[INF] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if best[i][j] >= INF:
                continue
            for a, b in GROUPS:
                ni, nj = i + a, j + b
                if ni > n or nj > m:
                    continue
                cost = abs(math.log((sum(tl[i:ni]) + 8) / (sum(pl[j:nj]) * r + 8))) + (0 if (a, b) == (1, 1) else 0.3)
                if best[i][j] + cost < best[ni][nj]:
                    best[ni][nj], back[ni][nj] = best[i][j] + cost, (i, j)
    if best[n][m] >= INF:
        return None
    out, i, j = [None] * n, n, m
    while (i, j) != (0, 0):
        pi, pj = back[i][j]
        for t in range(pi, i):
            out[t] = (pj, j - 1)
        i, j = pi, pj
    return out


def typed_cairo(verses: dict, standard: int, plen: dict | None = None):
    """{typed verse n: (first standard verse, last standard verse, certain?)}"""
    hn = sorted(verses)
    anchors = [(1, 1)] if verses[hn[0]]["cairo"] is None else []
    anchors += [(n, verses[n]["cairo"]) for n in hn if verses[n]["cairo"] is not None]
    anchors.append((hn[-1] + 1, standard + 1))
    out = {}
    for (n1, c1), (n2, c2) in zip(anchors, anchors[1:]):
        d, e = n2 - n1, c2 - c1
        for i, n in enumerate(range(n1, n2)):
            if n not in verses:
                continue
            if d == e:
                out[n] = (c1 + i, c1 + i, True)
            elif d > e and e == 1:
                out[n] = (c1, c1, True)
            elif d < e and d == 1:
                out[n] = (c1, c2 - 1, True)
            else:
                out[n] = (c1, c2 - 1, False)
        if d != e and not (e == 1 or d == 1) and plen:   # ambiguous stretch: settle it by length inside its two anchors
            ns = [n for n in range(n1, n2) if n in verses]
            tl = [len(verses[n]["text"]) for n in ns]
            pl = [plen.get(c, 1) for c in range(c1, c2)]
            res = resolve_segment(tl, pl, sum(tl) / max(sum(pl), 1)) if ns else None
            if res:
                for n, (a, b) in zip(ns, res):
                    out[n] = (c1 + a, c1 + b, "length")
    return out


def chain(a: str, b: str):
    """Monotone chain of (position in a, position in b) from 12-grams unique in both."""
    ca = Counter(a[i:i + K] for i in range(len(a) - K + 1))
    pos = {a[i:i + K]: i for i in range(len(a) - K + 1) if ca[a[i:i + K]] == 1}
    seen = defaultdict(list)
    for j in range(len(b) - K + 1):
        k = b[j:j + K]
        if k in pos:
            seen[k].append(j)
    pairs = sorted((pos[k], v[0]) for k, v in seen.items() if len(v) == 1)
    tails, idx, prev = [], [], [-1] * len(pairs)
    for i, (_, bp) in enumerate(pairs):
        j = bisect_left(tails, bp)
        if j == len(tails):
            tails.append(bp); idx.append(i)
        else:
            tails[j] = bp; idx[j] = i
        prev[i] = idx[j - 1] if j else -1
    out, i = [], idx[-1] if idx else -1
    while i != -1:
        out.append(pairs[i]); i = prev[i]
    return out[::-1]


def main() -> int:
    ours = json.loads((H / "verse-texts.json").read_text())
    num = json.loads((H / "numbering.json").read_text())["suras"]
    result, stats, final = {}, Counter(), {}
    pl_by_sura: dict[int, dict[int, int]] = {}
    for r in json.loads((ROOT / "data" / "processed" / "pickthall" / "pickthall-1930-built.json").read_text()):
        pl_by_sura.setdefault(r["sura"], {})[r["verse"]] = len(r["text"])
    for k in range(2, 115):
        tv = tc.typed_sura(k)
        std = num[str(k)]["standard_verses"]
        sv = {int(n): t for n, t in ours[str(k)].items()}
        if not tv or not sv:
            result[k] = {"status": "not aligned: no verses read"}
            continue
        tc_map = typed_cairo(tv, std, pl_by_sura.get(k))
        # streams with verse start offsets
        t_stream, t_start = "", {}
        for n in sorted(tv):
            t_start[n] = len(t_stream)
            t_stream += key(tv[n]["text"])
        s_stream, s_start = "", {}
        for n in sorted(sv):
            s_start[n] = len(s_stream)
            s_stream += key(sv[n])
        pairs = chain(s_stream, t_stream)            # (scan pos, typed pos)
        if len(pairs) < 3:
            result[k] = {"status": "not aligned: too few matching passages"}
            continue
        sp = [p[0] for p in pairs]

        def to_typed(x: int) -> int:
            i = bisect_left(sp, x)
            if i == 0:
                return pairs[0][1] - (pairs[0][0] - x)
            if i == len(pairs):
                return pairs[-1][1] + (x - pairs[-1][0])
            (a0, b0), (a1, b1) = pairs[i - 1], pairs[i]
            return b0 + (b1 - b0) * (x - a0) // max(a1 - a0, 1)

        t_nums = sorted(tv)
        t_ends = {n: (t_start[t_nums[i + 1]] if i + 1 < len(t_nums) else len(t_stream)) for i, n in enumerate(t_nums)}
        s_nums = sorted(sv)
        links = {}
        for i, n in enumerate(s_nums):
            a = to_typed(s_start[n])
            b = to_typed(s_start[s_nums[i + 1]] if i + 1 < len(s_nums) else len(s_stream))
            cov = []
            for tn in t_nums:
                lo, hi = max(a, t_start[tn]), min(b, t_ends[tn])
                ov, tl, sl = hi - lo, t_ends[tn] - t_start[tn], max(b - a, 1)
                if ov > 0 and (ov >= 0.6 * tl or ov >= 0.6 * sl):   # the typed verse lies (mostly) inside the scan verse, or the scan verse inside it
                    cov.append(tn)
            if not cov:
                links[n] = None
                continue
            lo = min(tc_map[t][0] for t in cov)
            hi = max(tc_map[t][1] for t in cov)
            links[n] = {"typed": cov, "standard": [lo, hi], "certain": all(tc_map[t][2] is True for t in cov), "by_length": any(tc_map[t][2] == "length" for t in cov)}
        covered = sum(1 for v in links.values() if v)
        certain = sum(1 for v in links.values() if v and v["certain"])
        identity = sum(1 for n, v in links.items() if v and v["certain"] and v["standard"] == [n, n])
        unread = set(num[str(k)]["unread_numbers"])
        contaminated = {n for n in s_nums if (n + 1) in unread}   # the scan text of verse n also holds the unread verse(s) after it
        clean = {n: v for n, v in links.items() if v and n not in contaminated}
        agree = sum(1 for n, v in clean.items() if v["typed"] == [n])
        final[k] = {"scan_links": {n: v for n, v in links.items() if v}, "typed_cairo": {n: tc_map[n] for n in t_nums}, "agreement": agree / max(len(clean), 1), "clean": len(clean)}
        result[k] = {"agreement_scan_number_equals_typed_number": round(agree / max(len(clean), 1), 3), "contaminated_scan_verses": sorted(contaminated), "anchors": len(pairs), "scan_verses": len(s_nums), "linked": covered, "linked_certain": certain, "same_number_certain": identity,
                     "differs": {str(n): v["standard"] for n, v in links.items() if v and v["certain"] and v["standard"] != [n, n]},
                     "uncertain": [n for n, v in links.items() if v and not v["certain"]], "unlinked": [n for n, v in links.items() if not v]}
        stats["scan_verses"] += len(s_nums); stats["linked_certain"] += certain; stats["same_number"] += identity
    # final mapping standard verse -> Henning (1901 scan) numbers
    fin = {}
    for k, f in final.items():
        by_std = defaultdict(set)
        if f["agreement"] >= 0.97:       # the scan and the typed text number their verses the same way: read the typed brackets directly
            basis = "typed brackets; scan and typed verse numbers agree"
            for n, (lo, hi, ok) in f["typed_cairo"].items():
                if ok:                      # True (read from brackets) or "length" (settled by length between two brackets)
                    for c in range(lo, hi + 1):
                        by_std[c].add(n)
        else:
            basis = "scan verses aligned to the typed text"
            for n, v in f["scan_links"].items():
                if v["certain"] and n not in set(result[k]["contaminated_scan_verses"]):
                    for c in range(v["standard"][0], v["standard"][1] + 1):
                        by_std[c].add(n)
        fin[k] = {"basis": basis, "agreement": round(f["agreement"], 3), "map": {str(c): sorted(v) for c, v in sorted(by_std.items())}}
    (H / "final-mapping.json").write_text(json.dumps(fin) + "\n", encoding="utf-8")
    summary = {"suras_scan_and_typed_numbers_agree_97pct": sum(1 for f in fin.values() if f["basis"].startswith("typed")), "scan_verses": stats["scan_verses"], "linked_with_certain_standard_number": stats["linked_certain"],
               "of_which_same_number": stats["same_number"], "suras_with_differences": sorted(int(k) for k, v in result.items() if v.get("differs"))}
    (H / "typed-alignment.json").write_text(json.dumps({"summary": summary, "suras": result}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    for k in (8, 45, 71, 74, 101, 27, 47, 4):
        r = result[k]
        print(k, {a: r[a] for a in ("linked", "linked_certain", "scan_verses", "differs", "uncertain", "unlinked") if a in r})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
