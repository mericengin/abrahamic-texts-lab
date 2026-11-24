#!/usr/bin/env python3
"""Map Henning's verse numbers to the standard (Tanzil/Cairo) numbering by verse LENGTH (needs scripts/henning_numbering.py first).

Method: for every sura, Henning's verses and the standard verses (lengths of the rebuilt Pickthall 1930 text, which follows the standard
verse boundaries) are aligned in order with a dynamic program that allows 1:1, 1:2, 2:1, 1:3 and 3:1 steps; the cost of a step is the
log of the length ratio relative to the sura's overall ratio. This is an automatic, UNVALIDATED estimate: a link is only as good as the
length evidence, so every link carries a confidence ("same number and same length profile", "length-aligned") and suras where the DP prefers
a different mapping than "same number" are listed for an expert. Sura 1 is unnumbered in Henning and is mapped by line order.
Output (metadata only): data/processed/henning/alignment.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
H = ROOT / "data" / "processed" / "henning"
STEPS = [(1, 1), (1, 2), (2, 1), (1, 3), (3, 1), (2, 2)]


def constrained(hl: list[float], pl: list[int], delta: int):
    """Align where Henning has `delta` more (delta > 0: that many standard verses are split in two) or fewer (delta < 0: two standard
    verses are merged into one) verses than the standard numbering. Every other verse is 1:1. Returns the best placements with costs.
    Costs are the log of the length ratio relative to the sura's overall ratio; the placements are the verse positions of the splits/merges."""
    from itertools import combinations
    k = abs(delta)
    n, m = len(hl), len(pl)
    r = max(sum(hl), 1) / max(sum(pl), 1)
    res = []
    for pos in combinations(range(m - (1 if delta < 0 else 0)), k):
        cost, hi, ok = 0.0, 0, True
        j = 0
        pset = set(pos)
        while j < m:
            if j in pset:
                if delta > 0:       # standard verse j is split into two Henning verses
                    if hi + 2 > n:
                        ok = False
                        break
                    sh, sp, hi, j = hl[hi] + hl[hi + 1], pl[j], hi + 2, j + 1
                else:               # standard verses j and j+1 are one Henning verse
                    if hi + 1 > n or j + 2 > m:
                        ok = False
                        break
                    sh, sp, hi, j = hl[hi], pl[j] + pl[j + 1], hi + 1, j + 2
            else:
                if hi + 1 > n:
                    ok = False
                    break
                sh, sp, hi, j = hl[hi], pl[j], hi + 1, j + 1
            cost += abs(math.log((sh + 8) / (sp * r + 8)))
        if ok and hi == n:
            res.append((cost, pos))
    return sorted(res)[:3]


# Places where Henning divides or joins the standard verses, CHECKED by reading the German verses against the English (Pickthall 1930)
# at the place the length estimate pointed to. ("split", s): standard verse s is two Henning verses; ("merge", a): standard verses a and a+1
# are one Henning verse. "until": links after that standard verse are left unmapped because a second event is only guessed.
# Suras 71 and 74 mix splits and merges and are not resolved. This table is still a draft for a domain expert to confirm.
REVIEWED = {4: {"events": [("merge", 118)]}, 7: {"events": [("merge", 1)]}, 8: {"events": [("split", 36)]}, 9: {"events": [("split", 61)]},
            26: {"events": [("split", 227)]}, 27: {"events": [("split", 44)], "until": 64}, 45: {"events": [("merge", 1)]},
            47: {"events": [("split", 4)], "until": 14}, 78: {"events": [("split", 40)]}, 85: {"events": [("merge", 21)]},
            86: {"events": [("merge", 2)]}, 101: {"events": [("merge", 6), ("merge", 8)]}}


def henning_numbers(sura: int, verse: int, total: int):
    """Henning's number(s) for a standard verse, or None when not mapped. Same numbering where Henning's highest number equals the standard."""
    rev = REVIEWED.get(sura)
    if rev is None:
        return None
    shift = 0
    for kind, at in rev["events"]:
        if kind == "split":
            if verse == at:
                return [verse + shift, verse + shift + 1]
            if verse > at:
                shift += 1
        else:
            if verse == at + 1:
                return [at + shift]
            if verse > at + 1:
                shift -= 1
    if rev.get("until") and verse > rev["until"]:
        return None
    return [verse + shift]


def main() -> int:
    num = json.loads((H / "numbering.json").read_text())["suras"]
    texts = json.loads((H / "verse-texts.json").read_text())
    built = json.loads((ROOT / "data" / "processed" / "pickthall" / "pickthall-1930-built.json").read_text())
    std: dict[int, dict[int, int]] = {}
    for r in built:
        std.setdefault(r["sura"], {})[r["verse"]] = len(r["text"])
    out = {}
    for k in sorted(int(x) for x in num):
        info = num[str(k)]
        if k == 1:
            out["1"] = {"status": "unnumbered in Henning", "note": "the lines after the invocation follow the standard order; not machine-checked"}
            continue
        hi, sv = info["henning_highest"], info["standard_verses"]
        if hi == sv:
            out[str(k)] = {"status": "same numbering", "henning_verses": hi, "standard_verses": sv,
                           "note": "same highest number; a hidden swap inside the sura cannot be excluded without a person comparing the texts"}
            continue
        ht = texts[str(k)]
        mean = sum(len(v) for v in ht.values()) / max(len(ht), 1)
        hl = [len(ht[str(n)]) if str(n) in ht else mean for n in range(1, hi + 1)]
        snums = sorted(std[k])
        pl = [std[k][x] for x in snums]
        best = constrained(hl, pl, hi - sv)
        if not best:
            out[str(k)] = {"status": "differs; no placement found", "henning_verses": hi, "standard_verses": sv}
            continue
        margin = (best[1][0] - best[0][0]) if len(best) > 1 else None
        kind = "split" if hi > sv else "merge"
        out[str(k)] = {"status": f"differs by {hi - sv:+d}", "henning_verses": hi, "standard_verses": sv,
                       "best_guess": {"kind": f"standard verse(s) {[snums[p] for p in best[0][1]]} {kind} in Henning" if kind == 'split' else f"standard verse(s) {[(snums[p], snums[p] + 1) for p in best[0][1]]} are one verse in Henning",
                                      "cost": round(best[0][0], 2)},
                       "runner_up_cost_margin": None if margin is None else round(margin, 2),
                       "confidence": "unvalidated length estimate; low" if margin is None or margin < 0.6 else "unvalidated length estimate; moderate",
                       "needs": "an expert or a person comparing the texts at this place"}
    for k, v in REVIEWED.items():
        out[str(k)]["checked_by_reading"] = True
    summary = {"checked_by_reading": sorted(REVIEWED), "unresolved_mixed": [71, 74], "same_numbering": sum(1 for v in out.values() if v["status"] == "same numbering"),
               "differs": {k: v["status"] for k, v in out.items() if v["status"].startswith("differs")},
               "unnumbered": [k for k, v in out.items() if v["status"] == "unnumbered in Henning"]}
    (H / "alignment.json").write_text(json.dumps({"summary": summary, "suras": out}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    for k, v in out.items():
        if v["status"].startswith("differs"):
            print(k, v["status"], v.get("best_guess", {}).get("kind"), v.get("runner_up_cost_margin"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
