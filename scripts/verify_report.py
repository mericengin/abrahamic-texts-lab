#!/usr/bin/env python3
"""Write docs/data-verification.md from data/processed/verification/verification.json (run scripts/verify.py first).

The report is metadata only: counts, verdicts and a few short word comparisons, never the texts, so it is safe to commit.
Every check is listed with its result; failures are not hidden. The summary table gives each layer one honest status.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V = json.loads((ROOT / "data" / "processed" / "verification" / "verification.json").read_text())

LAYERS = [
    # (title, section keys, what exists, extra note)
    ("Hebrew Bible, Hebrew (WLC)", ["hebrew"], "39 books, 23,213 verses, 305,507 words"),
    ("New Testament, Greek (SBLGNT; MorphGNT for morphology)", ["greek"], "27 books, 7,939 verses (MorphGNT: 7,927, lacks John 7:53 to 8:11)"),
    ("Hebrew Bible and New Testament, English (WEB)", ["web"], "66 books plus 15 Deuterocanon books, 38,029 verses"),
    ("Hebrew Bible and New Testament, German (Luther 1912)", ["luther"], "66 books, 31,102 verses"),
    ("Qur'an, Arabic (Tanzil Uthmani)", ["quran-arabic"], "114 suras, 6,236 ayas"),
    ("Qur'an, English (Pickthall 1930, rebuilt from scans)", ["pickthall"], "6,236 verses, reconstructed by vote"),
    ("Qur'an, German (Henning, OCR of a Fraktur scan)", ["henning"], "622 scan pages, OCR text"),
    ("Verse mapping between layers", ["mapping"], "Hebrew to English to German; Greek to English to German; Qur'an numbering"),
]

STATUS = {
    "hebrew": ("Verified", "Every verse and word equals an independent extraction from the raw OSIS XML; every English verse is reachable from the Hebrew except Nehemiah 7:68, which the Hebrew text lacks."),
    "greek": ("Verified", "The text files equal the edition's own XML word for word; MorphGNT's text is identical to the SBLGNT wherever it has the verse. Differences from the English and German verse sets are listed, not hidden."),
    "web": ("Verified", "Independent extraction equals the parsed verses; no word of ours is missing from the official PDF."),
    "luther": ("Verified", "Same checks as the WEB, all passed; verse counts per chapter agree with the WEB except where the traditions differ."),
    "quran-arabic": ("Verified", "Text kept verbatim; XML and text files agree; verse counts per sura agree with an independent source; the Tanzil notice is present everywhere."),
    "pickthall": ("Mostly verified, not complete", "The 1930 text rebuilt from four scans is decided by agreement or alignment for about 98% of verses; 91 hard or vote-only verses were read against the page images (this found and fixed real errors: lost words, a footnote mixed into 73:20, a verse mixed into 9:110, stray footnote marks, footnote and page-header text mixed into verses); 88 verses still rest only on a word-by-word vote, and the fresh page OCR confirms all 88. Leftover footnote marks (OCR read them as ^) were removed from 23 verses; those removals rest on the 5 page images viewed, not on each verse. Nothing is queued, but only the viewed verses are proven against the page image. The Gutenberg Pickthall text is NOT the 1930 text and is not used."),
    "henning": ("Not trustworthy yet", "The scan is complete and continuous. The best layer (OCR plus an automatic repair pass) has about 1% word errors on three hand-transcribed pages (about 1.8% before the repair pass); the repair rules were tuned on those pages, so treat 1 to 2% as the estimate. A seeded random sample of 10 body pages not used for tuning (40, 82, 179, 204, 215, 291, 476, 490, 518, 544) was read against the images: 34 word errors in 2,619 words (1.3%) in the layer as it stood before those pages were corrected, counted by eye, so some may be missed. Those pages and nine others (31, 152, 250, 300, 334, 450, 533, 563, 585, 590) were corrected by hand; pages 615 to 618 are publisher advertisements in another typeface and are not part of the work. The rest has not been read by a person."),
    "mapping": ("Built; some links need an expert", "Hebrew, English and German are aligned except a few listed verses; Greek verses that exist in only one layer are not linked yet. Henning's verse numbers are mapped to the standard numbering for 6,211 of 6,236 verses, using a typed copy of a Reclam edition (local reference only) that prints the standard number in brackets, aligned to our 1901 scan by text. The earlier mapping by equal highest number was wrong inside many suras (a length-consistency check improved from 0.33 to 0.19 with the new mapping). Sura 1 is unnumbered in Henning. Draft for an expert."),
}


def main() -> int:
    out = ["# Data verification", "",
           "Is anything lost, altered or untrustworthy? Each check below recomputes its answer from the raw files with code that does not reuse the converters "
           "(`scripts/verify.py`), or compares two independent sources. Results are regenerated by `scripts/verify.py` then `scripts/verify_report.py`. "
           "This page holds metadata only: counts and verdicts, never the texts.", "",
           f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", "",
           "## Summary", "", "| Layer | What it is | Status | Why |", "|---|---|---|---|"]
    for title, keys, what in LAYERS:
        k = keys[0]
        st, why = STATUS[k]
        fails = [c for kk in keys for c in V.get(kk, []) if c["passed"] is False]
        if fails and k in ("hebrew", "greek", "web", "luther", "quran-arabic", "mapping"):
            st, why = "A check failed", f"{len(fails)} check(s) failed, see the list below: " + "; ".join(c["check"] for c in fails)
        out.append(f"| {title} | {what} | **{st}** | {why} |")
    out += ["", "What \"verified\" means here: nothing was lost or changed between the source file and our Markdown, and the layer agrees with at least one independent source. "
            "It does not mean the underlying edition has no errors. What it does not cover: proofreading of OCR text against page images, which only a person can do.", "",
            "## All checks", ""]
    for title, keys, _ in LAYERS:
        out += [f"### {title}", ""]
        for k in keys:
            for c in V.get(k, []):
                mark = {True: "PASS", False: "FINDING", None: "INFO"}[c["passed"]]
                out.append(f"- **{mark}: {c['check']}.** {c['detail']}")
            if k == "greek":
                for c in V.get(k, []):
                    if c.get("only_in_other"):
                        out.append(f"  - In the other layer but not in the SBLGNT: {', '.join(c['only_in_other'])}")
        out.append("")
    out += ["## Open items", "",
            "- Read the remaining vote-only verses (`verdict: voted` in `data/processed/pickthall/pickthall-1930-built.json`, local) against the page images, and a larger random sample of the agreed verses, to measure how often the scans share an OCR slip.",
            "- Proofread the Henning OCR against the page images (so far 20 pages were read against their images, 10 of them a random sample). Have an expert confirm Henning's verse mapping (it rests on a 1970 typed edition bridged to the 1901 scan; sura 101 is divided differently in the two).",
            "- Confirm by an expert the links for Greek verses that exist in only one layer (critical-text omissions and divisions that differ).",
            "- The four Pickthall scans may share OCR slips; a check of a random sample against the page images would measure that.", ""]
    (ROOT / "docs" / "data-verification.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("wrote docs/data-verification.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
