#!/usr/bin/env python3
"""Propose automatic corrections of the Henning OCR from a LOCAL typed Reclam text (never published).

A scan word is replaced by the typed word only when ALL of these hold: the two words differ by at most three letters after spelling is
normalized; the scan word is not a word of Luther's 1912 German and occurs at most twice in the book; the typed word IS such a word (Luther
count >= 1, or >= 3 times in the book), which keeps the 1901 spelling; the scan word occurs exactly once on its page; capitalization of the
scan word is kept. Everything else stays a lead for reading the page. Output: data/processed/henning/typed-fixes.json ({page: [[old, new], ...]}),
local, applied by scripts/henning_proofread.py together with manual-fixes.json (manual fixes win).
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import henning_typed_compare as tc  # noqa: E402
import henning_typed_measure as tm  # noqa: E402
import henning_typed_pages as tp  # noqa: E402
import ocr_to_markdown as om  # noqa: E402

H = ROOT / "data" / "processed" / "henning"
PAIRS = {"bh", "hb", "ce", "ec", "nu", "un", "fk", "kf", "il", "li", "mn", "nm", "rn", "fs", "sf", "tl", "lt", "ao", "oa", "ee", "cc"}
LET = re.compile(r"[A-Za-zÄÖÜäöüß]+")


def main() -> int:
    layer = tm.MDDIR / "german-quran-henning-fraktur-ocr-normalized-latf-pass2-base.md"   # rule repairs only, before typed and manual fixes
    text = layer.read_text(encoding="utf-8")
    lex = om.build_lexicon()
    own = Counter(x.lower() for x in LET.findall(text))
    suras = tp.scan_words_with_pages(layer)
    page_text = {int(m.group(1)): m.group(2) for m in re.finditer(r"(?ms)^## Page (\d+)\n(.*?)(?=^## Page |\Z)", text)}
    fixes: dict[int, list] = {}
    n_prop = n_skip = 0
    for k in range(2, 115):
        v = tc.typed_sura(k)
        tw = [(tm.nw(w), w) for n in sorted(v) for w in v[n]["text"].split() if tm.nw(w)]
        a = [x[0] for x in tw]
        b = suras[k - 1]
        sm = difflib.SequenceMatcher(None, a, [x[0] for x in b], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "replace" or (i2 - i1) != (j2 - j1):
                continue
            for t in range(i2 - i1):
                key_t, surf_t = tw[i1 + t]
                key_s, surf_s, pg = b[j1 + t]
                d = tm.edits(key_t, key_s)
                if not 0 < d <= 3:
                    continue
                s_let = "".join(LET.findall(surf_s)).lower()
                t_let = "".join(LET.findall(surf_t)).lower()
                if len(s_let) < 3:
                    continue
                unknown = lex.get(s_let, 0) == 0 and own[s_let] <= 2
                swap = len(s_let) == len(t_let) and sum(x != y for x, y in zip(s_let, t_let)) == 1 and \
                    {x + y for x, y in zip(s_let, t_let) if x != y}.pop() in PAIRS       # one letter of the usual Fraktur confusions
                if not ((unknown and len(s_let) >= 4) or swap):
                    continue
                if not (lex.get(t_let, 0) >= 1 or own[t_let] >= 3):
                    continue
                if swap and not unknown and not (own[t_let] > 3 * own[s_let]):   # a real word replaced only when the typed word is clearly the common one
                    continue
                body = page_text.get(pg, "")
                if len(re.findall(r"(?<![A-Za-zÄÖÜäöüß])" + re.escape(surf_s) + r"(?![A-Za-zÄÖÜäöüß])", body)) != 1:
                    n_skip += 1
                    continue
                core = LET.search(surf_s)
                if not core:
                    continue
                new_core = t_let.capitalize() if core.group(0)[0].isupper() else t_let
                new = surf_s[:core.start()] + new_core + surf_s[core.end():]
                if new != surf_s:
                    fixes.setdefault(pg, []).append([surf_s, new])
                    n_prop += 1
    (H / "typed-fixes.json").write_text(json.dumps({str(p): f for p, f in sorted(fixes.items())}, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(f"{n_prop} proposed fixes on {len(fixes)} pages; {n_skip} skipped (word not unique on its page)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
