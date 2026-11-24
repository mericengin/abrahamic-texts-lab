#!/usr/bin/env python3
"""Second repair pass over the Henning OCR (machine-assisted, NOT human proofreading).

The OCR of the Fraktur scan loses the "ch" ligature ("wahrscheinlihste" for "wahrscheinlichste") and reads "tz" as "ß" ("geseßgeber").
This pass repairs a word only when (1) the word we read is rare in the book and unknown in Luther's 1912 vocabulary, and
(2) exactly one repaired spelling, made of the confusions below, is a known word (Luther count >= 3, or >= 5 times in this book).
Every repair is logged. Input: the normalized run-2 layer. Output (local, git-ignored): <layer>-pass2.md and CORRECTIONS-pass2.json.
Accuracy is measured on the two hand-transcribed pages (see scripts/verify.py), never assumed.
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import ocr_to_markdown as om  # noqa: E402

MD = ROOT / "data" / "processed" / "markdown" / "german-quran-henning"
SRC = MD / "german-quran-henning-fraktur-ocr-normalized-latf.md"
OUT = MD / "german-quran-henning-fraktur-ocr-normalized-latf-pass2.md"
SWAP = {"b": "h", "3": "s"}   # only the slips whose repairs were checked to be reliable: b read for h, 3 read for s
# real words or truncated fragments that the rules would wrongly change (found by reading the repair log)
DENY = {"ausgeben", "eingeben", "aufgeben", "abgeben", "angeben", "übergeben", "vergeben", "hergeben", "ausgebt", "begebt", "vergebt", "gebt", "ebnen", "reibt", "beit", "bangen", "barre", "viebs", "höben", "wober", "shmu", "mobam", "bält", "balt", "sebe", "bebet", "bellen", "binnen", "hinnen", "nuten", "negen", "schen", "tren"}
WORD = re.compile(r"[A-Za-zÄÖÜäöüß3>]+")


SUBS = [("an", "au"), ("en", "eu"), ("fi", "st"), ("scl", "schl"), ("scw", "schw"), ("scr", "schr"), ("scm", "schm"), ("scn", "schn"), ("bm", "hm"), ("äb", "äh")]


def edits(w: str):
    """One-step spelling repairs for typical Fraktur slips."""
    out = set()
    for i, ch in enumerate(w):
        if ch == "h" and (i == 0 or w[i - 1] not in "cs") or (ch == "h" and w[i - 1:i] == "s"):
            out.add(w[:i] + "c" + w[i:])      # lost c of "ch" / "sch"
        if ch in SWAP:
            out.add(w[:i] + SWAP[ch] + w[i + 1:])
        if ch == "ß":
            out.add(w[:i] + "tz" + w[i + 1:])
            out.add(w[:i] + "ss" + w[i + 1:])
            out.add(w[:i] + "ch" + w[i + 1:])        # "spreßen" for "sprechen"
    for a, b in SUBS:
        for m in re.finditer(a, w):
            out.add(w[:m.start()] + b + w[m.end():])
    return out


def candidates(w: str):
    seen, frontier = set(), {w}
    for _ in range(2):
        frontier = {e for x in frontier for e in edits(x)} - seen - {w}
        seen |= frontier
    return seen


def apply_manual(text: str) -> str:
    """Corrections made by reading a page image (data/processed/henning/manual-fixes.json, local): {"pages": {"334": [[old, new], ...]}}.
    An old string that is not found is reported, never ignored."""
    path = ROOT / "data" / "processed" / "henning" / "manual-fixes.json"
    if not path.exists():
        return text
    fixes = json.loads(path.read_text(encoding="utf-8"))
    parts = re.split(r"(?m)^(## Page \d+\n)", text)
    out, missing = [parts[0]], []
    for i in range(1, len(parts), 2):
        n = re.match(r"## Page (\d+)", parts[i]).group(1)
        body = parts[i + 1]
        for old, new in fixes.get("pages", {}).get(n, []):
            if old in body:
                body = body.replace(old, new, 1)
            else:
                missing.append((n, old))
        out += [parts[i], body]
    if missing:
        print("manual fixes whose old text was not found:", missing)
    return "".join(out)


def main() -> int:
    text = SRC.read_text(encoding="utf-8")
    lex = om.build_lexicon()
    own = Counter(x.lower() for x in WORD.findall(text))
    known = lambda c: lex.get(c, 0) >= 3 or own.get(c, 0) >= 5
    log: Counter = Counter()

    def repl(m: re.Match) -> str:
        w = m.group(0)
        lw = w.lower()
        if "cch" in lw:   # never valid German ("encch" for "euch")
            lw = lw.replace("cch", "ch")
            w = lw.capitalize() if w[:1].isupper() else lw
        if ">" in lw:   # "ck" read as ">" or ">k" ("zurü>kehren" = zurückkehren, "frohlo>kend" = frohlockend); ">" never occurs in the book's German
            opts = [lw.replace(">k", "ck"), lw.replace(">", "ck")]
            ok = [o for o in opts if ">" not in o and known(o)]
            lw = ok[0] if ok else opts[1]
            log[(w.lower(), lw)] += 1
            w = lw.capitalize() if w[:1].isupper() else lw
        if len(lw) < (2 if "3" in lw else 4) or lex.get(lw, 0) > 0 or lw in DENY:
            return w
        for bad, good_ in (("fh", "sch"), ("kf", "kk")):   # doubled c; long s + h read as "fh"; "Mekfa"
            if bad in lw and known(lw.replace(bad, good_)) and not known(lw):
                lw = lw.replace(bad, good_)
                log[(w.lower(), lw)] += 1
                return lw.capitalize() if w[:1].isupper() else lw
        if lw[0] in "nr" and w[:1].isupper() and not known(lw) and known(("r" if lw[0] == "n" else "n") + lw[1:]) and own[lw] < 3:
            lw = ("r" if lw[0] == "n" else "n") + lw[1:]   # first capital N read for R or the reverse ("Nede" = Rede)
            log[(w.lower(), lw)] += 1
            return lw.capitalize()
        if "scch" in lw:   # doubled c ("scchweifen"): never valid German
            lw = lw.replace("scch", "sch")
            log[(w.lower(), lw)] += 1
            return lw.capitalize() if w[:1].isupper() else lw
        if lw[:2] == "j3":   # "Islam", "Israel": the capital I of the Fraktur type was read as J and long s as 3
            fixed = "is" + lw[2:]
            log[(lw, fixed)] += 1
            return fixed.capitalize() if w[:1].isupper() else fixed
        good = {c for c in candidates(lw) if known(c) and own[lw] * 3 < max(lex.get(c, 0), own.get(c, 0))}
        if len(good) != 1:
            return w
        fixed = good.pop()
        log[(lw, fixed)] += 1
        return fixed.capitalize() if w[:1].isupper() else fixed

    new = WORD.sub(repl, text)
    new = apply_manual(new)
    new = new.replace('status: "machine OCR, not proofread"', 'status: "machine OCR plus automatic repair pass 2; not proofread by a person"', 1)
    OUT.write_text(new, encoding="utf-8")
    (MD / "CORRECTIONS-pass2.json").write_text(json.dumps({"count": sum(log.values()), "distinct": len(log),
        "all": [[list(k), v] for k, v in log.most_common()]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{sum(log.values())} repairs, {len(log)} distinct; wrote {OUT.name}")
    print(log.most_common(25))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
