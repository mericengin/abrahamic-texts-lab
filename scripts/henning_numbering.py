#!/usr/bin/env python3
"""Read Henning's own verse numbers from the OCR text and compare them with the standard numbering (Tanzil).

Suras are found from the "Geoffenbart zu ..." line under each sura heading (114 of them, in order). Verse numbers are the
numbers that open a paragraph and continue the sequence 1, 2, 3, ... Misread numbers (OCR slips such as "924") are matched
by the expected next number only when the text clearly starts a new verse; anything else is reported as unread, never guessed.
Output (metadata only, safe to publish): data/processed/henning/numbering.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import canon  # noqa: E402

MD = ROOT / "data" / "processed" / "markdown" / "german-quran-henning" / "german-quran-henning-fraktur-ocr-normalized-latf-pass2.md"
OUT = ROOT / "data" / "processed" / "henning"
NUM = re.compile(r"^[\s|'\-•.·]*(\d{1,3})[.,:;]\s+(\S.*)$")


def henning_body() -> list[tuple[int, str]]:
    """(pdf page, line) for the Qur'an text: from the first sura heading to the last page of sura 114, without page headers."""
    text = MD.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^## Page (\d+)\n", text)
    lines = []
    for i in range(1, len(parts), 2):
        page = int(parts[i])
        for ln in parts[i + 1].splitlines():
            if re.match(r"^\s*(\d{1,3}\s+)?Der\s+Kor\w*\W{0,3}\s*(\d{1,3})?\s*$", ln) or re.match(r"^\s*\*{1,3}\)", ln):
                continue
            lines.append((page, ln))
    return lines


def main() -> int:
    lines = henning_body()
    starts = [i for i, (p, ln) in enumerate(lines) if re.search(r"Geoffenbart\s+zu", ln) and 30 < p < 616]
    q = canon.parse_tanzil_xml(ROOT / "data" / "raw" / "quran-tanzil-arabic" / "quran-uthmani.xml", "x", "x")
    standard = {int(b.title.split()[-1]) if b.title.split()[-1].isdigit() else k + 1: len(b.rows) for k, b in enumerate(q.books)}
    print("sura headings found:", len(starts), "(expected 114)")
    result, texts = {}, {}
    for k, s in enumerate(starts):
        end = len(lines)
        if k + 1 < len(starts):   # the next heading ("... Sure." and a title) begins one to three lines before its "Geoffenbart" line
            nx = starts[k + 1]
            heads = [j for j in range(nx - 4, nx) if re.search(r"Sure\W{0,3}$", lines[j][1])]
            end = heads[0] if heads else nx - 2
        nxt, seq, unread = 1, [], []
        for page, ln in lines[s:end]:
            m = NUM.match(ln)
            if not m:
                if seq and not re.search(r"Sure\W{0,3}$", ln):
                    seq[-1]["text"] = seq[-1].get("text", "") + " " + ln.strip()
                continue
            n = int(m.group(1))
            if n == nxt:
                seq.append({"n": n, "page": page, "text": m.group(2)})
                nxt += 1
            elif nxt < n <= nxt + 3 and len(m.group(2)) > 3:   # numbers not read: record the gap, continue after this one
                unread.extend(range(nxt, n))
                seq.append({"n": n, "page": page, "text": m.group(2)})
                nxt = n + 1
        texts[k + 1] = {e["n"]: e["text"] for e in seq}
        result[k + 1] = {"standard_verses": standard.get(k + 1), "henning_highest": seq[-1]["n"] if seq else 0, "read": len(seq),
                         "unread_numbers": unread, "first_page": lines[s][0]}
    (OUT / "verse-texts.json").write_text(json.dumps(texts, ensure_ascii=False) + "\n", encoding="utf-8")   # local only: third-party text
    exact = [k for k, v in result.items() if v["henning_highest"] == v["standard_verses"]]
    differ = {k: (v["standard_verses"], v["henning_highest"]) for k, v in result.items() if v["henning_highest"] != v["standard_verses"]}
    summary = {"suras_found": len(starts), "suras_same_highest_number_as_standard": len(exact), "suras_that_differ(standard,henning)": differ,
               "verse_numbers_not_read": sum(len(v["unread_numbers"]) for v in result.values())}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "numbering.json").write_text(json.dumps({"summary": summary, "suras": result}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
