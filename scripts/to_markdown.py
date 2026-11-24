#!/usr/bin/env python3
"""Convert fetched raw sources into Markdown, next to (never instead of) the originals.

Reads data/raw/<id>/ (as written by fetch_sources.py) and writes
data/processed/markdown/<id>/<filename>.md plus CONVERSION.json with checks.

Principles
- Never change the words. Text files are copied verbatim (CRLF normalized to LF);
  the only additions are a front-matter header and, for PDFs, page headings.
- Every output states its provenance, license and an OCR-quality flag, so a
  garbled OCR can never pass as a usable text.
- Output stays local (git-ignored): third-party texts keep their own licenses.
- PDFs with no text layer are reported as such, not silently emptied.

Usage:  .venv/bin/python scripts/to_markdown.py [source-id ...]
Needs pdfminer.six for PDFs (see requirements.txt).
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "markdown"
MANIFEST = ROOT / "data" / "sources.toml"
VERSION = "1"

COMMON = {
    "English": {"the", "and", "that", "who", "they", "not", "his", "them", "for", "with", "those", "thee", "thou", "unto", "was", "are"},
    "German": {"und", "der", "die", "das", "den", "dem", "ist", "nicht", "sie", "ein", "eine", "zu", "mit", "von", "auf", "für", "aber",
               "wir", "ihr", "euch", "hat", "sich", "werden", "sind", "wer", "dann", "wie", "bei", "oder", "auch", "wird", "als", "aus"},
}


def ocr_quality(text: str, language: str) -> dict:
    """Crude, language-aware OCR sanity score: common words per 1000 word tokens.
    Normal prose scores roughly 250-350. Below 80 the text is not usable."""
    words = [w.lower() for w in re.findall(r"[^\W\d_]{3,}", text)]
    common = COMMON.get(language.split()[0].rstrip(","), set())
    if not words or not common:
        return {"score": None, "flag": "unchecked"}
    score = round(1000 * sum(w in common for w in words) / len(words), 1)
    flag = "good" if score >= 150 else "poor" if score >= 80 else "unusable"
    return {"score": score, "flag": flag}


def yaml_str(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)  # JSON strings are valid YAML


def front_matter(src: dict, rec: dict, fname: str, how: str, quality: dict | None, extra: dict | None = None) -> str:
    items = {
        "source_id": src["id"],
        "file": fname,
        "sha256": rec.get("sha256"),
        "retrieved_utc": rec.get("retrieved_utc"),
        "license": src["license"],
        "attribution": src["attribution"],
        "conversion": how,
        "converted_by": f"scripts/to_markdown.py v{VERSION}",
        "converted_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ocr_quality": quality,
        "note": "Third-party text. Kept local and git-ignored; do not redistribute beyond its license.",
    }
    items.update(extra or {})
    lines = ["---"] + [f"{k}: {yaml_str(v)}" for k, v in items.items()] + ["---", ""]
    return "\n".join(lines)


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# ---------- plain text ----------
def convert_text(raw: str) -> tuple[str, str, dict]:
    body = raw.replace("\r\n", "\n")
    return body, "plain text copied verbatim (CRLF to LF)", {"lossless": norm_ws(body) == norm_ws(raw)}


# ---------- Gutenberg 16955: structured, still lossless ----------
CHAPTER = re.compile(r"^\s*Chapter (\d+):\s*$")
VERSE = re.compile(r"^(\d{3})\.(\d{3})\s*$")
VERSE_LOOSE = re.compile(r"^(\d{1,3})\.(\d{1,3})\s*$")  # corrupted ids such as 0.033 or 039.04 in the source
TRANS = re.compile(r"^([YPS]): ")


def convert_three_translations(raw: str) -> tuple[str, str, dict]:
    text = raw.replace("\r\n", "\n")
    out = []
    for line in text.split("\n"):
        if CHAPTER.match(line):
            out.append(CHAPTER.sub(r"## Chapter \1:", line))
        elif VERSE.match(line):
            out.append("#### " + line.strip())
        elif TRANS.match(line):
            out.append(f"**{line[0]}:**" + line[2:])
        else:
            out.append(line)
    body = "\n".join(out)
    undone = re.sub(r"^(#{2,4} )", "", body, flags=re.M)
    undone = re.sub(r"^\*\*([YPS]):\*\*", r"\1:", undone, flags=re.M)
    return body, "plain text with structure added (chapter and verse headings, bold translator tags); words unchanged", {
        "lossless": norm_ws(undone) == norm_ws(raw)
    }


def extract_pickthall(raw: str) -> tuple[str, dict]:
    """Pickthall-only extraction from the three-translation file. A derived file: the Y: and S: lines are dropped."""
    text = raw.replace("\r\n", "\n").split("\n")
    chapter = None
    expected: dict[int, int] = {}
    verses: dict[tuple[int, int], str] = {}
    cur = None
    repairs: list[dict] = []
    prev: tuple[int, int] | None = None
    all_ids: set[tuple[int, int]] = set()
    fixed_at: dict[int, tuple[int, int]] = {}
    for i, line in enumerate(text):  # first pass: ids, repairing corrupted ones from the running sequence
        if CHAPTER.match(line):
            prev = None
            continue
        m = VERSE.match(line)
        if m:
            prev = (int(m.group(1)), int(m.group(2)))
            all_ids.add(prev)
            continue
        if prev is not None and VERSE_LOOSE.match(line):
            guess = (prev[0], prev[1] + 1)
            fixed_at[i] = guess
            all_ids.add(guess)
            repairs.append({"line": i + 1, "found": line.strip(), "assigned": f"{guess[0]}:{guess[1]}"})
            prev = guess
    for i, line in enumerate(text):
        m = CHAPTER.match(line)
        if m:
            chapter = int(m.group(1))
            for ahead in text[i + 1:i + 6]:
                tv = re.search(r"Total Verses:\s*(\d+)", ahead)
                if tv:
                    expected[chapter] = int(tv.group(1))
                    break
            cur = None
            continue
        v = VERSE.match(line)
        if v:
            cur = (int(v.group(1)), int(v.group(2)))
            continue
        if i in fixed_at:
            cur = fixed_at[i]
            continue
        if cur is None:
            continue
        t = TRANS.match(line)
        if t:
            cur_tag = t.group(1)
            if cur_tag == "P":
                verses[cur] = line[3:].strip()
            continue
        if line.strip() and cur in verses and not re.match(r"^-{5,}", line) and not CHAPTER.match(line):
            # continuation of a wrapped Pickthall line (only while the last tag seen was P)
            prev_tag = None
            for back in range(i - 1, max(i - 6, 0), -1):
                tm = TRANS.match(text[back])
                if tm:
                    prev_tag = tm.group(1)
                    break
                if not text[back].strip():
                    break
            if prev_tag == "P":
                verses[cur] += " " + line.strip()
    lines = ["# Pickthall (1930), extracted from Project Gutenberg #16955", "",
             "Derived file: only the Pickthall (`P:`) lines, with standard sura:verse numbering. Not independently verified against the 1930 scan.", ""]
    per_sura: dict[int, int] = {}
    last = 0
    for (s, v), t in sorted(verses.items()):
        if s != last:
            lines += ["", f"## Sura {s}", ""]
            last = s
        lines.append(f"**{s}:{v}** {t}")
        per_sura[s] = per_sura.get(s, 0) + 1
    mism = {s: {"expected": n, "found": per_sura.get(s, 0)} for s, n in expected.items() if per_sura.get(s, 0) != n}
    stats = {
        "suras_found": len(per_sura),
        "verses_found": sum(per_sura.values()),
        "verses_expected_from_headers": sum(expected.values()),
        "suras_with_count_mismatch": mism,
        "empty_verses": [f"{s}:{v}" for (s, v), t in verses.items() if not t],
        "verse_ids_without_pickthall_line": [f"{s}:{v}" for (s, v) in sorted(all_ids - set(verses))],
        "verse_ids_in_file": len(all_ids),
        "repaired_corrupted_verse_ids": repairs,
        "suras_not_consecutive_from_1": [s for s in per_sura if sorted(v for (ss, v) in verses if ss == s) != list(range(1, per_sura[s] + 1))],
        "reference_total_verses_standard_count": 6236,
    }
    return "\n".join(lines) + "\n", stats


# ---------- PDF ----------
def convert_pdf(path: Path) -> tuple[str, str, dict]:
    try:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer
    except ImportError:
        raise SystemExit("pdfminer.six is needed for PDFs: .venv/bin/python -m pip install -r requirements.txt")
    import logging
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    parts, pages, with_text = [], 0, 0
    for page in extract_pages(str(path)):
        pages += 1
        txt = "".join(el.get_text() for el in page if isinstance(el, LTTextContainer)).strip()
        if txt:
            with_text += 1
        parts.append(f"## Page {pages}\n\n{txt}\n")
    body = "\n".join(parts)
    return body, "PDF text layer extracted per page with pdfminer.six (layout order, no reflow)", {
        "pages": pages, "pages_with_text": with_text, "has_text_layer": with_text > 0.5 * max(pages, 1)
    }


def main() -> int:
    with MANIFEST.open("rb") as fh:
        sources = {s["id"]: s for s in tomllib.load(fh)["source"]}
    ids = sys.argv[1:] or [d.name for d in sorted(RAW.iterdir()) if d.is_dir()]
    for sid in ids:
        rawdir = RAW / sid
        if sid not in sources or not (rawdir / "MANIFEST.json").exists():
            print(f"skip {sid}: not fetched")
            continue
        src = sources[sid]
        prov = json.loads((rawdir / "MANIFEST.json").read_text())
        recs = {r["file"]: {**r, "retrieved_utc": prov["retrieved_utc"]} for r in prov.get("files", [])}
        outdir = OUT / sid
        outdir.mkdir(parents=True, exist_ok=True)
        report = {"source_id": sid, "converted_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "files": {}}
        print(f"== {sid}")
        for fname, rec in recs.items():
            path = rawdir / fname
            quality = None
            if fname.endswith(".pdf"):
                body, how, checks = convert_pdf(path)
                if checks["has_text_layer"]:
                    sample = re.sub(r"## Page \d+\n", "", body)
                    quality = ocr_quality(sample, src["language"])
                else:
                    body = ("*This PDF is an image container with no text layer, so no text could be extracted from it. "
                            "Use the Markdown made from the archive's OCR text file of the same book, if present.*\n")
                    quality = {"score": None, "flag": "no-text-layer"}
            else:
                raw = path.read_text(encoding="utf-8")
                if fname == "16955.txt":
                    body, how, checks = convert_three_translations(raw)
                    pick, pstats = extract_pickthall(raw)
                    (outdir / "pickthall-only.md").write_text(
                        front_matter(src, rec, fname, "derived: Pickthall (P:) lines only", None, {"extraction_checks": pstats}) + "\n" + pick,
                        encoding="utf-8")
                    report["pickthall_only"] = pstats
                    print(f"   pickthall-only.md: {pstats['verses_found']} verses in {pstats['suras_found']} suras "
                          f"(headers say {pstats['verses_expected_from_headers']}; mismatches: {len(pstats['suras_with_count_mismatch'])})")
                else:
                    body, how, checks = convert_text(raw)
                    quality = ocr_quality(body, src["language"]) if "djvu" in fname else None
            md = front_matter(src, rec, fname, how, quality) + "\n" + body
            (outdir / f"{fname}.md").write_text(md, encoding="utf-8")
            report["files"][fname] = {"markdown": f"{fname}.md", "source_bytes": rec["bytes"], "md_bytes": len(md.encode()),
                                      "ocr_quality": quality, **checks}
            print(f"   {fname}.md  {report['files'][fname]['md_bytes']:,} bytes  quality={quality}  checks={checks}")
        (outdir / "CONVERSION.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
