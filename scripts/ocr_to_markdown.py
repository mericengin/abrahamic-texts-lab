#!/usr/bin/env python3
"""Turn the page files from ocr_pdf.py into Markdown, in two clearly separated layers.

  <id>-fraktur-ocr-raw.md         the OCR text exactly as Tesseract returned it, one section per page (nothing changed)
  <id>-fraktur-ocr-normalized.md  machine-normalized: (1) long s (ſ) written as s, a purely typographic letter form;
                                  (2) '<' inside a word becomes ch (Tesseract's reading of the Fraktur ch ligature);
                                  (3) rare words that look like known Fraktur OCR slips (lost or swapped letters around
                                  ch, u/n) are replaced by a much more frequent word from the same book.
                                  Every replacement is logged in CORRECTIONS.json. It is NOT proofread.

Both layers carry provenance and quality figures in their header. Output stays local (git-ignored).
Usage: python3 scripts/ocr_to_markdown.py <source-id>
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORD = re.compile(r"[A-Za-zÀ-ÿſ<>]+")
GERMAN_COMMON = {"und", "der", "die", "das", "den", "dem", "ist", "nicht", "sie", "ein", "eine", "zu", "mit", "von", "auf", "für", "aber",
                 "wir", "ihr", "euch", "hat", "sich", "werden", "sind", "wer", "dann", "wie", "bei", "oder", "auch", "wird", "als", "aus"}


def yaml_str(v) -> str:
    return json.dumps(v, ensure_ascii=False)


def common_score(text: str) -> float:
    words = [w.lower() for w in re.findall(r"[^\W\d_]{3,}", text)]
    return round(1000 * sum(w in GERMAN_COMMON for w in words) / max(len(words), 1), 1)


def candidates(w: str):
    """Single-edit repairs for typical Fraktur OCR slips. The caller only accepts one if it is far more frequent than the original."""
    out = set()
    for i, ch in enumerate(w):
        if ch == "h":
            out.add(w[:i] + "ch" + w[i + 1:])        # ch read as h (niht -> nicht)
        if ch == "c" and (i + 1 == len(w) or w[i + 1] != "h"):
            out.add(w[:i] + "ch" + w[i + 1:])        # ch read as c (nict -> nicht)
        if ch in "<>":
            out.add(w[:i] + "ch" + w[i + 1:])        # ch read as < (ſ<were -> schwere)
        if ch == "u":
            out.add(w[:i] + "n" + w[i + 1:])         # u/n swap (uicht -> nicht)
        if ch == "n":
            out.add(w[:i] + "u" + w[i + 1:])
        if ch == "i" and i + 1 < len(w) and w[i + 1] == "h":
            out.add(w[:i + 1] + "c" + w[i + 1:])      # ih -> ich (ſih -> sich)
    return out


# Letter confusions typical of Tesseract on Fraktur type (OCR reading -> what the printed letter probably is)
CONFUSIONS = {"b": "h", "h": "b", "f": "s", "s": "f", "u": "n", "n": "u", "e": "c", "c": "e", "I": "J", "J": "I", "N": "R", "R": "N", "m": "n", "n": "m", "t": "k", "k": "t"}


def candidates_v2(w: str):
    """Single-edit repairs: a typical Fraktur letter confusion, a lost c before h, or a lost h after c."""
    out = set(candidates(w))
    for i, ch in enumerate(w):
        if ch in CONFUSIONS:
            out.add(w[:i] + CONFUSIONS[ch] + w[i + 1:])
        if ch == "h" and (i == 0 or w[i - 1] != "c"):
            out.add(w[:i] + "c" + w[i:])
    if len(w) > 2 and w.endswith("c"):
        out.add(w + "h")
    return out


def build_lexicon() -> Counter:
    """Word frequencies of Luther's 1912 Bible: a large, period-appropriate German vocabulary used to tell real words from OCR slips."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import canon
    ver = canon.parse_usfx(ROOT / "data" / "raw" / "german-luther-1912" / "deu1912_usfx.zip", "deu1912_usfx.xml", "l", "L", "German")
    return Counter(w.lower() for b in ver.books for _, _, t in b.rows for w in re.findall(r"[A-Za-zÀ-ÿ]+", t))


def lexicon_fix(w: str, own_freq: Counter, lex: Counter):
    """Return a repaired word, or None.
    A word is replaced by a one-letter-confusion neighbour (see CONFUSIONS) only if that neighbour is a common word of Luther's German
    (at least 300 occurrences) and at least 40 times more frequent than the word we read (200 times if the word we read is itself in Luther's vocabulary), counting the word's own occurrences in the book at a tenth
    of their weight (a slip repeats often, but a real name or word is far rarer than the common word it could be mistaken for)."""
    lw = w.lower()
    if len(lw) < 2:
        return None
    cur = lex.get(lw, 0) + own_freq.get(lw, 0) / 10
    best, bf = None, 0
    for c in candidates_v2(lw):
        f = lex.get(c, 0)
        if f > bf:
            best, bf = c, f
    ratio = 40 if lex.get(lw, 0) < 10 else 200   # a word that is itself in Luther's vocabulary needs a much stronger reason to be replaced
    if best and bf >= 300 and bf >= ratio * max(cur, 1):
        return best.capitalize() if w[:1].isupper() else best
    return None


def main() -> int:
    sid = sys.argv[1]
    tag = sys.argv[2] if len(sys.argv) > 2 else ""      # e.g. -latf for the second OCR run
    pagedir = ROOT / "data" / "processed" / "ocr" / (sid + tag)
    ocr = json.loads((pagedir / "OCR.json").read_text())
    with (ROOT / "data" / "sources.toml").open("rb") as fh:
        src = next(s for s in tomllib.load(fh)["source"] if s["id"] == sid)
    pages = [(n, (pagedir / f"page-{n:03d}.txt").read_text(encoding="utf-8")) for n in range(1, ocr["pages"] + 1)]

    # ---- normalized layer
    norm_pages = [(n, t.replace("ſ", "s")) for n, t in pages]
    freq = Counter(w.lower() for _, t in norm_pages for w in WORD.findall(t))
    log: list[dict] = []
    LEX = build_lexicon() if (ROOT / 'data' / 'raw' / 'german-luther-1912' / 'deu1912_usfx.zip').exists() else None

    def fix_text(n: int, text: str) -> str:
        def repl(m):
            w = m.group(0)
            lw = w.lower()
            if "<" in w and re.search(r"[A-Za-zÀ-ÿ]", w):
                # '<' never occurs in German words; Tesseract writes the Fraktur ch ligature as '<' (ſi< = sich, no< = noch)
                new = w.replace("<h", "ch").replace("<", "ch")
                rule = "'<' is the ch ligature"
                if True:  # the OCR may also have swapped u and n (en< = euch): take a far more frequent single-swap word
                    alt = max((c for c in candidates(new.lower()) if "<" not in c and ">" not in c), key=lambda c: freq.get(c, 0), default=None)
                    if alt and freq.get(alt, 0) >= max(10, 5 * freq.get(new.lower(), 0)):
                        new = alt.capitalize() if w[:1].isupper() else alt
                        rule = "'<' is the ch ligature, plus a u/n swap"
                log.append({"page": n, "from": w, "to": new, "rule": rule})
                return new
            lf = lexicon_fix(w, freq, LEX) if LEX else None
            if lf:
                log.append({"page": n, "from": w, "to": lf, "rule": "not in the Luther 1912 vocabulary; single-edit repair to a word that is"})
                return lf
            if len(lw) < 4 or freq[lw] > 2:
                return w
            best, bf = None, 0
            for c in candidates(lw):
                if "<" in c or ">" in c:
                    continue
                if freq.get(c, 0) >= max(5, 5 * max(freq[lw], 1)) and freq[c] > bf:
                    best, bf = c, freq[c]
            if not best:
                return w
            new = best.capitalize() if w[:1].isupper() else best
            log.append({"page": n, "from": w, "to": new, "freq_from": freq[lw], "freq_to": bf, "rule": "rare word to a far more frequent single-edit word"})
            return new
        return WORD.sub(repl, text)

    fixed = [(n, fix_text(n, t)) for n, t in norm_pages]

    def layer(name: str, pages_: list[tuple[int, str]], note: str) -> dict:
        body = "\n".join(f"## Page {n}\n\n{t.strip()}\n" for n, t in pages_)
        words = WORD.findall(body)
        qf = Counter(w.lower() for w in words)
        stats = {"common_words_per_1000": common_score(body),
                 "tokens": len(words),
                 "tokens_seen_3_or_more_times_percent": round(100 * sum(1 for w in words if qf[w.lower()] >= 3) / max(len(words), 1), 1)}
        head = {"source_id": sid, "layer": name, "pages": ocr["pages"], "language": "German (Fraktur type)",
                "license": src["license"], "attribution": src["attribution"],
                "ocr_engine": ocr["tesseract"], "ocr_model": ocr["language_model"], "ocr_model_sha256": ocr["model_sha256"],
                "ocr_dpi": ocr["dpi"], "ocr_psm": ocr["psm"], "pdf_sha256": ocr["pdf_sha256"], "ocr_utc": ocr["ocr_utc"],
                "quality": stats, "status": "machine OCR, not proofread", "note": note,
                "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        text = "---\n" + "\n".join(f"{k}: {yaml_str(v)}" for k, v in head.items()) + "\n---\n\n" + f"# {src['name']} ({name})\n\n" + body
        out = ROOT / "data" / "processed" / "markdown" / sid / f"{sid}-fraktur-ocr-{name}{tag}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        return {"file": out.name, "bytes": len(text.encode()), **stats}

    raw = layer("raw", pages, "Tesseract output, unchanged. Long s (ſ) and OCR slips are still present.")
    norm = layer("normalized", fixed, "Long s written as s, plus logged single-letter repairs of rare words. See CORRECTIONS.json.")
    (ROOT / "data" / "processed" / "markdown" / sid / f"CORRECTIONS{tag}.json").write_text(
        json.dumps({"count": len(log), "top": Counter((c["from"], c["to"]) for c in log).most_common(40), "by_rule": dict(Counter(c["rule"] for c in log)), "all": log}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (ROOT / "data" / "processed" / "markdown" / sid / f"OCR_LAYERS{tag}.json").write_text(
        json.dumps({"raw": raw, "normalized": norm, "corrections": len(log), "by_rule": dict(Counter(c["rule"] for c in log)),
                    "near_empty_pages": ocr["empty_pages"]}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"raw": raw, "normalized": norm, "corrections": len(log), "empty_pages": ocr["empty_pages"]}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
