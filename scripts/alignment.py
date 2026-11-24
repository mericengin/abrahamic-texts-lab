#!/usr/bin/env python3
"""Verse-number mapping tables between the layers (the versification mapping of the corpus milestone).

  hebrew-bible.json   Hebrew (MT numbering, morphhb) -> English (WEB, English numbering) -> German (Luther 1912)
  new-testament.json  Greek (SBLGNT) -> English (WEB) -> German (Luther 1912), with the verses that exist in only one layer listed
  quran.json          standard numbering (Tanzil) -> the number printed in Pickthall's 1930 book -> Henning's number (not yet mapped)

Hebrew -> English uses the versification map that ships with morphhb (VerseMap.xml). English <-> German is identity because
Luther 1912 follows English numbering for the Old Testament (checked: identical per-chapter counts) and nearly all of the New Testament;
the exceptions are listed, not guessed. Output is metadata only (verse numbers), safe to keep and to publish.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon  # noqa: E402
from verify import NT_USFX, OSIS2USFX  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "alignment"


def refs(ver: canon.Version, ids: list[str] | None = None):
    """Set of (book id, chapter, verse). A bridged verse such as 28-29 counts as its first number (Deuterocanon only)."""
    import re
    out = set()
    for b in ver.books:
        bid = b.extra.get("usfx_id")
        for c, v, _ in b.rows:
            out.add((bid, int(c), int(re.match(r"\d+", v).group())))
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    web = canon.parse_usfx(RAW / "english-web-deutero" / "eng-web_usfx.zip", "eng-web_usfx.xml", "w", "W", "English")
    lu = canon.parse_usfx(RAW / "german-luther-1912" / "deu1912_usfx.zip", "deu1912_usfx.xml", "l", "L", "German")
    web_set, lu_set = refs(web), refs(lu)
    summary = {}

    # ---------------- Hebrew Bible
    heb = canon.parse_hebrew(RAW / "hebrew-morphhb")
    vm = ET.parse(RAW / "hebrew-morphhb" / "wlc" / "VerseMap.xml").getroot()
    ns = "{http://www.APTBibleTools.com/namespace}"
    mapping: dict[str, list[tuple[str, str]]] = {}
    parts: dict[str, set[str]] = {}
    for v in vm.iter(ns + "verse"):
        key = v.get("wlc")
        base = key.split("!")[0]
        if "!" in key:
            parts.setdefault(base, set()).add(key.split("!")[1])
        mapping.setdefault(base, []).append((v.get("kjv"), v.get("type")))
    for base, found in parts.items():
        if found != {"a", "b"}:
            mapping[base].append((base, "same"))
    rows, english_reached = [], set()
    import re
    for b in heb.books:
        for c, v, _ in b.rows:
            ref = f"{b.title}.{c}.{v}"
            targets = []
            for k, typ in mapping.get(ref, [(ref, "identity")]):
                bk, kc, kv = k.split(".")
                kc, kv = int(re.match(r"\d+", kc).group()), int(re.match(r"\d+", kv).group())
                ok = (OSIS2USFX[bk], kc, kv)
                if kv == 0:
                    targets.append({"english": None, "note": "psalm title: printed above verse 1 in English Bibles", "type": typ})
                    continue
                targets.append({"english": f"{ok[0]} {ok[1]}:{ok[2]}", "type": typ, "in_web": ok in web_set, "in_luther": ok in lu_set})
                english_reached.add(ok)
            rows.append({"hebrew": f"{b.title} {c}:{v}", "maps_to": targets})
    web_ot = {r for r in web_set if r[0] in OSIS2USFX.values()}
    unreached = sorted(web_ot - english_reached)
    summary["hebrew-bible"] = {"hebrew_verses": len(rows), "english_ot_verses": len(web_ot), "english_verses_reached": len(web_ot & english_reached),
                               "english_verses_with_no_hebrew_counterpart": [f"{a} {b}:{c}" for a, b, c in unreached],
                               "hebrew_verses_with_split_or_partial_mapping": sum(1 for r in rows if len(r["maps_to"]) > 1 or any(t["type"] == "partial" for t in r["maps_to"])),
                               "hebrew_verses_with_changed_number": sum(1 for r in rows if any(t.get("english") and t["english"].split(" ", 1)[1] != r["hebrew"].split(" ", 1)[1] for t in r["maps_to"])),
                               "luther_ot_verse_set_equals_web_ot": {r for r in lu_set if r[0] in OSIS2USFX.values()} == web_ot}
    (OUT / "hebrew-bible.json").write_text(json.dumps({"summary": summary["hebrew-bible"], "rows": rows}, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")

    # ---------------- New Testament
    sbl = canon.parse_sblgnt(RAW / "greek-sblgnt-text")
    greek = {(NT_USFX[i], int(c), int(v)) for i, b in enumerate(sbl.books) for c, v, _ in b.rows}
    web_nt = {r for r in web_set if r[0] in NT_USFX}
    lu_nt = {r for r in lu_set if r[0] in NT_USFX}
    nt_rows = [{"greek": f"{a} {b}:{c}", "english": f"{a} {b}:{c}" if (a, b, c) in web_nt else None, "german": f"{a} {b}:{c}" if (a, b, c) in lu_nt else None}
               for a, b, c in sorted(greek, key=lambda r: (NT_USFX.index(r[0]), r[1], r[2]))]
    fmt = lambda s: [f"{a} {b}:{c}" for a, b, c in sorted(s, key=lambda r: (NT_USFX.index(r[0]), r[1], r[2]))]
    summary["new-testament"] = {"greek_verses": len(greek), "english_nt_verses": len(web_nt), "german_nt_verses": len(lu_nt),
                                "greek_verses_with_same_number_in_english": sum(1 for r in nt_rows if r["english"]),
                                "greek_verses_with_same_number_in_german": sum(1 for r in nt_rows if r["german"]),
                                "greek_only_vs_english": fmt(greek - web_nt), "english_only_vs_greek": fmt(web_nt - greek),
                                "greek_only_vs_german": fmt(greek - lu_nt), "german_only_vs_greek": fmt(lu_nt - greek),
                                "note": "Verses listed under 'only' are either critical-text omissions (late additions in the traditional text) or places where the "
                                        "layers divide or order a passage differently (for example the closing doxology of Romans). They have no automatic counterpart and need "
                                        "an expert-confirmed entry before they are linked."}
    (OUT / "new-testament.json").write_text(json.dumps({"summary": summary["new-testament"], "rows": nt_rows}, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")

    # ---------------- Qur'an
    q = canon.parse_tanzil_xml(RAW / "quran-tanzil-arabic" / "quran-uthmani.xml", "x", "x")
    nm_path = ROOT / "data" / "processed" / "pickthall" / "pickthall-numbering-map.json"
    nm = json.loads(nm_path.read_text()) if nm_path.exists() else {"printed_number_by_standard_verse": {}, "offset_counts_by_sura": {}}
    printed = nm["printed_number_by_standard_verse"]
    qrows = []
    for b in q.books:
        for c, v, _ in b.rows:
            ref = f"{c}:{v}"
            qrows.append({"standard": ref, "pickthall_1930_printed": printed.get(ref), "henning_printed": None})
    shifted = sum(1 for r in qrows if r["pickthall_1930_printed"] is not None and r["pickthall_1930_printed"] != int(r["standard"].split(":")[1]))
    summary["quran"] = {"standard_verses": len(qrows), "with_pickthall_1930_printed_number": sum(1 for r in qrows if r["pickthall_1930_printed"] is not None),
                        "pickthall_printed_number_differs_from_standard": shifted,
                        "pickthall_offsets_by_sura": nm["offset_counts_by_sura"],
                        "henning": "not mapped yet: the layer is still unproofread OCR and its own verse numbering must be read from it first"}
    (OUT / "quran.json").write_text(json.dumps({"summary": summary["quran"], "rows": qrows}, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for k, v in summary.items():
        print(k, {a: (b if not isinstance(b, (list, dict)) else (b if len(str(b)) < 160 else f"[{len(b)} entries]")) for a, b in v.items() if a != "note"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
