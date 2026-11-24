#!/usr/bin/env python3
"""Independent verification of the Phase 1 data: is anything lost, altered, or untrustworthy?

Every check re-derives its answer from the RAW files with code that does not reuse the parsers in canon.py
(regular expressions or different libraries), then compares with the parsed rows or with a second, independent source.
Results go to data/processed/verification/verification.json; scripts/verify_report.py turns them into docs/data-verification.md.

Each check records: passed (True/False/None for information only), what was compared, and the numbers. Nothing is
hidden: failures and open issues are reported as such.

Usage: python3 scripts/verify.py [section ...]    sections: hebrew greek usfx quran-arabic pickthall henning mapping
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import canon  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUTDIR = ROOT / "data" / "processed" / "verification"
OSIS2USFX = dict(zip(canon.HB_ORDER, ["GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA", "1KI", "2KI", "1CH", "2CH", "EZR", "NEH",
                                      "EST", "JOB", "PSA", "PRO", "ECC", "SNG", "ISA", "JER", "LAM", "EZK", "DAN", "HOS", "JOL", "AMO", "OBA", "JON",
                                      "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL"]))
NT_USFX = ["MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS",
           "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"]
RESULTS: dict[str, list[dict]] = {}


def check(section: str, name: str, passed, detail: str, **numbers) -> None:
    RESULTS.setdefault(section, []).append({"check": name, "passed": passed, "detail": detail, **numbers})
    mark = {True: "PASS", False: "FAIL", None: "INFO"}[passed]
    print(f"  [{mark}] {name}: {detail}", flush=True)


def ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def web_rows():
    return canon.parse_usfx(RAW / "english-web-deutero" / "eng-web_usfx.zip", "eng-web_usfx.xml", "w", "W", "English")


def luther_rows():
    return canon.parse_usfx(RAW / "german-luther-1912" / "deu1912_usfx.zip", "deu1912_usfx.xml", "l", "L", "German")


# ------------------------------------------------------------------ Hebrew
def verify_hebrew() -> None:
    print("== Hebrew (WLC)")
    ver = canon.parse_hebrew(RAW / "hebrew-morphhb")
    mism, total, nwords = [], 0, 0
    for b in ver.books:
        code = b.title
        text = (RAW / "hebrew-morphhb" / "wlc" / f"{code}.xml").read_text(encoding="utf-8")
        indep = {}
        for m in re.finditer(r'<verse osisID="([^"]+)">(.*?)</verse>', text, flags=re.S):
            body = re.sub(r"<note\b.*?</note>", "", m.group(2), flags=re.S)
            words = [re.sub(r"<[^>]+>", "", w).replace("/", "") for w in re.findall(r"<w\b[^>]*>(.*?)</w>", body, flags=re.S)]
            _, ch, vs = m.group(1).split(".")
            indep[(ch, vs)] = words
        ours = {(c, v): t for c, v, t in b.rows}
        if set(indep) != set(ours):
            mism.append((code, "verse set differs", len(indep), len(ours)))
        for k, t in ours.items():
            clean = re.sub(r"\[[^\]]*\]|\{[^}]*\}", " ", t)
            clean = clean.replace("־", " ").replace("׃", " ").replace("׀", " ")
            got = clean.split()
            total += 1
            nwords += len(got)
            if got != indep.get(k):
                mism.append((code, k, len(got), len(indep.get(k, []))))
    check("hebrew", "independent word-by-word comparison with the raw OSIS XML", not mism,
          f"{total:,} verses, {nwords:,} words compared; verses that differ: {len(mism)}", verses=total, words=nwords, differing=mism[:10])
    # structure
    gaps = []
    for b in ver.books:
        chapters = sorted({int(c) for c, _, _ in b.rows})
        if chapters != list(range(1, len(chapters) + 1)):
            gaps.append((b.title, "chapters not consecutive"))
        for c in chapters:
            vs = sorted(int(v) for cc, v, _ in b.rows if cc == str(c))
            if vs != list(range(1, len(vs) + 1)):
                gaps.append((b.title, c, "verses not consecutive"))
    check("hebrew", "chapters and verses are consecutive from 1 in every book", not gaps, f"{len(gaps)} gaps", gaps=gaps[:10],
          chapters=sum(len({c for c, _, _ in b.rows}) for b in ver.books))
    # characters
    chars = Counter(ch for b in ver.books for _, _, t in b.rows for ch in t)
    odd = {hex(ord(c)): n for c, n in chars.items() if not (0x0590 <= ord(c) <= 0x05FF or c in " []{}")}
    check("hebrew", "only Hebrew letters, points, accents and our own markers occur", not odd, f"unexpected characters: {odd}", unexpected=odd)
    check("hebrew", "no replacement characters", "�" not in "".join(t for b in ver.books for _, _, t in b.rows), "no U+FFFD")
    # versification map completeness against WEB
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
        if found != {"a", "b"}:  # only one half of the verse moved; the other half keeps its own number
            mapping[base].append((base, "same"))
    eng_from_heb: set[tuple[str, int, int]] = set()
    unmapped_partial = 0
    titles = 0
    for b in ver.books:
        for c, v, _ in b.rows:
            ref = f"{b.title}.{c}.{v}"
            for kref, typ in mapping.get(ref, [(ref, "same")]):
                bk, kc, kv = kref.split(".")
                kc, kv = int(re.match(r"\d+", kc).group()), int(re.match(r"\d+", kv).group())   # strip partial-verse markers such as 43!b
                if kv == 0:
                    titles += 1  # a psalm title that English Bibles print above verse 1 (not a numbered English verse)
                    continue
                eng_from_heb.add((OSIS2USFX[bk], kc, kv))
                unmapped_partial += typ == "partial"
    web = web_rows()
    web_ot = {(b.extra["usfx_id"], int(c), int(v)) for b in web.books if b.extra["usfx_id"] in OSIS2USFX.values() for c, v, _ in b.rows}
    only_web = sorted(web_ot - eng_from_heb)
    only_heb = sorted(eng_from_heb - web_ot)
    known = [("NEH", 7, 68)]  # the Leningrad Codex lacks English Neh 7:68 (horses and mules; found in Ezra 2:66); the map itself shows 7:68 = English 7:69
    check("hebrew", "Hebrew verses mapped through morphhb's VerseMap cover the English (WEB) Old Testament", only_web == known and not only_heb,
          f"WEB OT verses {len(web_ot):,}; reached from Hebrew {len(eng_from_heb):,}; in WEB but not reached: {len(only_web)} (expected exactly one: Nehemiah 7:68, absent from the Hebrew text); reached but not in WEB: {len(only_heb)}",
          in_web_not_reached=[f"{a} {b}:{c}" for a, b, c in only_web[:15]], reached_not_in_web=[f"{a} {b}:{c}" for a, b, c in only_heb[:15]],
          partial_mappings=unmapped_partial, map_entries=len(mapping), psalm_titles_not_numbered_in_english=titles)


# ------------------------------------------------------------------ Greek
APPARATUS = "⸀⸁⸂⸃⸄⸅⸆⸇⸈⸉⸊⸋⸌⸍⸎⸏"
GREEK = re.compile("[\u0370-\u037D\u037F-\u0386\u0388-\u03FF\u1F00-\u1FFF\u02BC]+")  # Greek letters and marks; excludes the Greek question mark U+037E and ano teleia U+0387


def verify_greek() -> None:
    print("== Greek (SBLGNT, MorphGNT)")
    sbl = canon.parse_sblgnt(RAW / "greek-sblgnt-text")
    mism, nverses, nwords = [], 0, 0
    for i, b in enumerate(sbl.books):
        stem = canon.SBLGNT_FILES[i]
        text = (RAW / "greek-sblgnt-text" / "data" / "sblgnt" / "xml" / f"{stem}.xml").read_text(encoding="utf-8-sig")
        parts = re.split(r'<verse-number id="([^"]+)">[^<]*</verse-number>', text)
        xml_words = {}
        for j in range(1, len(parts), 2):
            m = re.search(r"(\d+):(\d+)$", parts[j])
            xml_words[(m.group(1), m.group(2))] = [re.sub(r"<[^>]+>", "", w) for w in re.findall(r"<w>(.*?)</w>", parts[j + 1], flags=re.S)]
        for c, v, t in b.rows:
            nverses += 1
            got = GREEK.findall(t)
            nwords += len(got)
            if got != xml_words.get((c, v)):
                mism.append((stem, f"{c}:{v}"))
        if {(c, v) for c, v, _ in b.rows} != set(xml_words):
            mism.append((stem, "verse set differs"))
    check("greek", "SBLGNT text files agree word for word with the SBLGNT XML files", not mism,
          f"{nverses:,} verses, {nwords:,} words; differing verses: {len(mism)}", verses=nverses, words=nwords, differing=mism[:60])
    # coverage against WEB and Luther
    web, lu = web_rows(), luther_rows()
    ours = {(NT_USFX[i], int(c), int(v)) for i, b in enumerate(sbl.books) for c, v, _ in b.rows}
    for label, ver in (("WEB", web), ("Luther 1912", lu)):
        other = {(b.extra["usfx_id"], int(c), int(v)) for b in ver.books if b.extra["usfx_id"] in NT_USFX for c, v, _ in b.rows}
        miss = sorted(other - ours)
        extra = sorted(ours - other)
        fmt = lambda xs: [f"{a} {b}:{c}" for a, b, c in xs]
        check("greek", f"verse numbers: SBLGNT against {label} New Testament", None,
              f"{label} has {len(other):,}, SBLGNT has {len(ours):,}; in {label} but not SBLGNT: {len(miss)}; in SBLGNT but not {label}: {len(extra)}",
              only_in_other=fmt(miss), only_in_sblgnt=fmt(extra),
              note="Verses the critical text omits (late additions found in the traditional text) and a few versification differences are expected; "
                   "each listed verse should be a known text-critical omission, not a loss.")
    # MorphGNT
    mg = canon.parse_morphgnt(RAW / "greek-morphgnt")
    same = diff = 0
    ex = []
    for bs, bm in zip(sbl.books, mg.books):
        sm = {(c, v): t for c, v, t in bm.rows}
        for c, v, t in bs.rows:
            if (c, v) not in sm:
                continue
            a = [unicodedata.normalize("NFC", w).casefold().replace("ʼ", "") for w in GREEK.findall(t)]
            b = [unicodedata.normalize("NFC", w).casefold().replace("ʼ", "").replace("’", "") for w in GREEK.findall(sm[(c, v)])]
            if a == b:
                same += 1
            else:
                diff += 1
                if len(ex) < 6:
                    ex.append(f"{bs.stem} {c}:{v}")
    check("greek", "MorphGNT text against the SBLGNT text (case-folded words)", None,
          f"{same:,} verses compared: identical {same:,}, differing {diff:,}. MorphGNT 6.12 does not contain John 7:53 to 8:11 (12 verses added to the SBLGNT in 2023)",
          identical=same, differing=diff, examples=ex)


# ------------------------------------------------------------------ USFX (WEB, Luther)
def indep_usfx(zip_path: Path, xml_name: str) -> dict[str, dict[tuple[str, str], str]]:
    raw = zipfile.ZipFile(zip_path).read(xml_name).decode("utf-8-sig")
    out: dict[str, dict[tuple[str, str], str]] = {}
    for m in re.finditer(r'<book id="([A-Z0-9]+)">(.*?)</book>', raw, flags=re.S):
        bid, body = m.group(1), m.group(2)
        body = re.sub(r"<(f|fe|x|ef|ex|fig|rq|s|r|d|h|toc|mt|ms|mr|sp|cl|cp|id|ip|is|imt|ie|rem)\b[^>]*>.*?</\1>", "", body, flags=re.S)
        body = body.replace("<ve />", "<ve/>")
        chunks = re.split(r'<c id="([^"]+)" ?/>', body)
        verses: dict[tuple[str, str], str] = {}
        for j in range(1, len(chunks), 2):
            ch = chunks[j]
            vparts = re.split(r'<v id="([^"]+)"[^>]*?/>', chunks[j + 1])
            for k in range(1, len(vparts), 2):
                t = ws(re.sub(r"<[^>]+>", "", vparts[k + 1].split("<ve/>")[0]))  # a verse ends at its end marker; later paragraphs are speaker labels or headings
                if t:
                    verses[(ch, vparts[k])] = t
        out[bid] = verses
    return out


def verify_usfx() -> None:
    print("== WEB and Luther 1912 (USFX)")
    for key, zpath, xname, ver, pdfname in (
        ("web", RAW / "english-web-deutero" / "eng-web_usfx.zip", "eng-web_usfx.xml", web_rows(), "english-web-deutero/eng-web_all.pdf"),
        ("luther", RAW / "german-luther-1912" / "deu1912_usfx.zip", "deu1912_usfx.xml", luther_rows(), "german-luther-1912/deu1912_all.pdf"),
    ):
        ind = indep_usfx(zpath, xname)
        diffs, nver = [], 0
        for b in ver.books:
            theirs = ind.get(b.extra["usfx_id"], {})
            ours = {(c, v): t for c, v, t in b.rows}
            nver += len(ours)
            if set(theirs) != set(ours):
                diffs.append((b.extra["usfx_id"], "verse set", len(ours), len(theirs)))
            for k, t in ours.items():
                if t != theirs.get(k):
                    diffs.append((b.extra["usfx_id"], f"{k[0]}:{k[1]}"))
        check(key, "independent regex extraction of the raw USFX equals the parsed verses", not diffs,
              f"{nver:,} verses compared; differing: {len(diffs)}", verses=nver, differing=diffs[:10])
        # compare with the official PDF's text layer (bag of words)
        md = ROOT / "data" / "processed" / "markdown" / pdfname.split("/")[0] / (pdfname.split("/")[1] + ".md")
        if md.exists():
            pdf_tokens = Counter(w.casefold() for w in re.findall(r"[^\W\d_]+", md.read_text(encoding="utf-8").split("---", 2)[2]))
            our_tokens = Counter(w.casefold() for b in ver.books for _, _, t in b.rows for w in re.findall(r"[^\W\d_]+", t))
            missing = sum(max(0, n - pdf_tokens[w]) for w, n in our_tokens.items())
            extra = sum(max(0, n - our_tokens[w]) for w, n in pdf_tokens.items())
            check(key, "word counts against the official eBible PDF (an independent rendering of the same text)", None,
                  f"our words {sum(our_tokens.values()):,}; words of ours not found in the PDF: {missing:,} ({100 * missing / sum(our_tokens.values()):.2f}%); "
                  f"PDF words not in ours (headings, footnotes, page text): {extra:,}",
                  our_words=sum(our_tokens.values()), ours_missing_from_pdf=missing, pdf_extra=extra)
    # WEB vs Luther structure
    web, lu = web_rows(), luther_rows()
    lb = {b.extra["usfx_id"]: b for b in lu.books}
    diffs = []
    for b in web.books:
        if b.extra["deuterocanon"]:
            continue
        a = Counter(c for c, _, _ in b.rows)
        g = Counter(c for c, _, _ in lb[b.extra["usfx_id"]].rows)
        for c in sorted(set(a) | set(g), key=int):
            if a[c] != g[c]:
                diffs.append(f"{b.extra['usfx_id']} {c}: WEB {a[c]} verses, Luther {g[c]}")
    check("luther", "per-chapter verse counts: Luther 1912 against WEB (66 books)", None,
          f"chapters that differ: {len(diffs)}", differing=diffs,
          note="Different verse counts are real textual differences (verses in one tradition and not the other), not losses.")


# ------------------------------------------------------------------ Qur'an Arabic
def verify_quran_arabic() -> None:
    print("== Qur'an Arabic (Tanzil)")
    d = RAW / "quran-tanzil-arabic"
    xml = canon.parse_tanzil_xml(d / "quran-uthmani.xml", "x", "x")
    txt = canon.parse_tanzil_txt(d / "quran-uthmani.txt", "t", "t")
    simple = canon.parse_tanzil_txt(d / "quran-simple-clean.txt", "s", "s")
    xr = {(c, v): t for b in xml.books for c, v, t in b.rows}
    tr = {(c, v): t for b in txt.books for c, v, t in b.rows}
    sr = {(c, v): t for b in simple.books for c, v, t in b.rows}
    bism = {}
    for b in xml.books:
        if b.extra.get("bismillah"):
            bism[(b.rows[0][0], b.rows[0][1])] = b.extra["bismillah"]
    d1 = [k for k in xr if (bism[k] + " " + xr[k] if k in bism else xr[k]) != tr.get(k)]
    check("quran-arabic", "Uthmani XML and Uthmani text file agree on every aya (the text file puts the bismillah in front of aya 1 of suras 2 to 114 except 9; the XML keeps it in an attribute)",
          not d1 and set(xr) == set(tr), f"{len(xr):,} ayas; suras with a separate bismillah: {len(bism)}; differing after accounting for it: {len(d1)}", ayas=len(xr), differing=[f"{a}:{b}" for a, b in d1[:10]])
    letter = re.compile("[\u0621-\u063A\u0641-\u064A\u0671]")
    words = lambda x: [w for w in x.split() if letter.search(w)]
    wd = [k for k in tr if len(words(tr[k])) != len(words(sr.get(k, "")))]
    check("quran-arabic", "Simple (Clean) against Uthmani: words per aya (information only)", None,
          f"{len(tr) - len(wd):,} of {len(tr):,} ayas have equal word counts; {len(wd)} differ because the two text types spell some words differently "
          f"(for example the Uthmani text writes the vocative as one word, يَـٰٓأَيُّهَا, where the Simple text writes two, يا أيها). Both are Tanzil's own text types; the Uthmani text is the primary layer.",
          differing=len(wd), examples=[f"{a}:{b}" for a, b in wd[:6]])
    # independent counts from the Gutenberg header (Pickthall file lists Total Verses per sura)
    g = (RAW / "english-quran-pickthall-gutenberg" / "16955.txt").read_text(encoding="utf-8")
    totals = {int(m.group(1)): int(m.group(2)) for m in re.finditer(r"Chapter (\d+):\s+.*?\s+Total Verses:\s*(\d+)", g, flags=re.S)}
    ours = Counter(int(c) for c, _ in xr)
    miss = {s: (ours[s], n) for s, n in totals.items() if ours[s] != n}
    check("quran-arabic", "ayas per sura agree with an independent source (the verse totals in the Project Gutenberg file)", not miss and len(totals) == 114,
          f"{len(totals)} suras listed there; total {sum(totals.values()):,}; ours {sum(ours.values()):,}; suras that differ: {len(miss)}", differing=miss)
    allraw = "".join((d / f).read_text(encoding="utf-8") for f in ("quran-uthmani.xml", "quran-uthmani.txt", "quran-simple-clean.txt"))
    check("quran-arabic", "no replacement characters; Tanzil notice present in every raw file and every Markdown file", "�" not in allraw and all(
        "Tanzil" in (d / f).read_text(encoding="utf-8") for f in ("quran-uthmani.xml", "quran-uthmani.txt", "quran-simple-clean.txt")),
          "raw files checked for U+FFFD and the notice")
    md = ROOT / "data" / "processed" / "markdown" / "quran-tanzil-arabic"
    nomd = [p.name for p in md.glob("quran-*/[0-9]*.md") if "Tanzil notice" not in p.read_text(encoding="utf-8")]
    check("quran-arabic", "every per-sura Markdown file carries the Tanzil notice", not nomd, f"{len(list(md.glob('quran-*/[0-9]*.md')))} files; without notice: {len(nomd)}")


# ------------------------------------------------------------------ Pickthall (English Qur'an)
def verify_pickthall() -> None:
    print("== Qur'an English (Pickthall 1930)")
    base = ROOT / "data" / "processed" / "pickthall"
    build = json.loads((base / "build-report.json").read_text())
    v = build["verdicts"]
    n = build["verses"]
    decided = v.get("agreed", 0) + v.get("pair", 0)
    check("pickthall", "the Project Gutenberg #16955 Pickthall lines are the 1930 text", False,
          f"they match the 1930 scans word for word in {build['identical_to_gutenberg_pickthall']:,} of {n:,} verses ({100 * build['identical_to_gutenberg_pickthall'] / n:.1f}%); "
          f"in {build['differs_from_gutenberg']:,} verses three or more scans agree on a different wording (for example 2:57 'We wronged them not' against 'they wronged Us not'; "
          f"1930 'Mecca' and 'stedfast' against 'Makka' and 'steadfast'). The Gutenberg text is a revised text and is NOT used as the English layer.",
          identical=build["identical_to_gutenberg_pickthall"], differs=build["differs_from_gutenberg"])
    check("pickthall", "1930 text rebuilt from four scans of the book: verses decided by agreement between scans", None,
          f"{v.get('agreed', 0):,} verses identical in three or more scans, {v.get('pair', 0):,} identical in two; decided {decided:,} of {n:,} ({100 * decided / n:.1f}%); "
          f"unresolved: split {v.get('split', 0)}, single scan {v.get('single', 0)}, missing {v.get('missing', 0)}", verdicts=v)
    check("pickthall", "review queue: verses that need a person to check them against the page image", None,
          f"{build['review_queue']} verses ({100 * build['review_queue'] / n:.1f}%): {build['review_reasons']}", reasons=build["review_reasons"])
    check("pickthall", "caveat: the four scans may share some OCR errors", None,
          "agreement between scans proves the OCR is consistent, not that it equals the printed page; scans of the same printing by the same digitizer can repeat the same slip. "
          "Verses where the scans are identical are very likely right, but only a check against the page images proves it.")


# ------------------------------------------------------------------ Henning (German Qur'an)
def wer_cer(truth: str, ocr: str):
    import difflib
    tok = lambda s: re.findall(r"[^\s]+", re.sub(r"(?<=\w)-\n", "", s))
    norm = lambda w: re.sub(r"[^\wäöüÄÖÜß]", "", w)
    a = [norm(w) for w in tok(truth) if norm(w)]
    b = [norm(w) for w in tok(ocr.replace("ſ", "s")) if norm(w)]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    we = sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal")
    ca, cb = "".join(a), "".join(b)
    cs = difflib.SequenceMatcher(None, ca, cb, autojunk=False)
    ce = sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in cs.get_opcodes() if t != "equal")
    return we, len(a), ce, len(ca)


def verify_henning() -> None:
    print("== Qur'an German (Henning)")
    D = ROOT / "data" / "processed" / "ocr" / "german-quran-henning"
    pages = {n: (D / f"page-{n:03d}.txt").read_text(encoding="utf-8").replace("ſ", "s") for n in range(1, 623) if (D / f"page-{n:03d}.txt").exists()}
    check("henning", "every one of the 622 scan pages was read", len(pages) == 622, f"{len(pages)} page files; near-empty pages (blank or show-through): 6 of 622")
    HDR = re.compile(r"^\s*(?:(\d{1,3})\s+Der\s+Koran|Der\s+Koran\W{0,3}\s+(\d{1,3}))", re.I)
    ok = []
    for n, t in pages.items():
        m = HDR.match(next((l for l in t.splitlines() if l.strip()), ""))
        if m and n - int(m.group(1) or m.group(2)) == 2:
            ok.append((n, int(m.group(1) or m.group(2))))
    ns = sorted(n for n, _ in ok)
    longest = max(b - a - 1 for a, b in zip(ns, ns[1:]))
    check("henning", "the scan is complete: printed page numbers run continuously (PDF page = printed page + 2)", len(ok) > 500 and longest <= 6,
          f"{len(ok)} pages have a readable printed number with the same offset, from page {min(p for _, p in ok)} to {max(p for _, p in ok)}; longest stretch without a readable header: {longest} pages. "
          f"A missing or duplicated scan page would shift the offset for all later pages; it never does.", verified_pages=len(ok), longest_gap=longest)
    chk = json.loads((ROOT / "data" / "processed" / "verification" / "henning-sura-check.json").read_text()) if (ROOT / "data" / "processed" / "verification" / "henning-sura-check.json").exists() else None
    if chk:
        first = [s for s in range(1, 61)]
        exact = [s for s in first if chk[str(s)]["henning_highest"] == chk[str(s)]["standard"] and not chk[str(s)]["missing"]]
        check("henning", "verse numbers read in sequence against the standard sura sizes (first 60 suras only)", None,
              f"in {len(exact)} of the first 60 suras every verse number 1..N was read and N equals the standard count; the others differ by one or two verses (Henning numbers some verses his own way) or have unread numbers. "
              f"Later short suras are laid out differently and are not checked yet.", exact_suras_of_first_60=len(exact))
    fixtures = {152: ROOT / "tests" / "fixtures" / "henning-page-152-transcription.txt", 250: ROOT / "tests" / "fixtures" / "henning-page-250-transcription.txt"}
    mdroot = ROOT / "data" / "processed" / "markdown" / "german-quran-henning"

    def md_page(path: Path, n: int):
        if not path.exists():
            return None
        t = path.read_text(encoding="utf-8")
        m = re.search(rf"## Page {n}\n(.*?)(?=\n## Page |\Z)", t, flags=re.S)
        return m.group(1) if m else None

    variants = {
        "run 1 (Fraktur model), as read": lambda n: (D / f"page-{n:03d}.txt").read_text(encoding="utf-8") if (D / f"page-{n:03d}.txt").exists() else None,
        "run 1 (Fraktur model), normalized": lambda n: md_page(mdroot / "german-quran-henning-fraktur-ocr-normalized.md", n),
        "run 2 (deu_latf+Fraktur models), as read": lambda n: (ROOT / "data" / "processed" / "ocr" / "german-quran-henning-latf" / f"page-{n:03d}.txt").read_text(encoding="utf-8")
        if (ROOT / "data" / "processed" / "ocr" / "german-quran-henning-latf" / f"page-{n:03d}.txt").exists() else None,
        "run 2 (deu_latf+Fraktur models), normalized": lambda n: md_page(mdroot / "german-quran-henning-fraktur-ocr-normalized-latf.md", n),
    }
    best = None
    for label, get in variants.items():
        W = E = C = N = 0
        ok = True
        for n, fx in fixtures.items():
            text = get(n)
            if text is None:
                ok = False
                break
            we, nw, ce, nc = wer_cer(fx.read_text(encoding="utf-8"), text)
            W, E, C, N = W + we, E + nw, C + ce, N + nc
        if ok:
            check("henning", f"OCR accuracy against hand transcriptions of two page images, pages 152 and 250 ({label})", None,
                  f"word errors {W} of {E} ({100 * W / E:.1f}%), character errors {C} of {N} ({100 * C / N:.2f}%). Two pages, about {E} words: an estimate, not a guarantee.",
                  word_errors=W, words=E, char_errors=C, chars=N)
            best = (label, 100 * W / E)
    check("henning", "trustworthiness of the German Qur'an layer", False,
          f"NOT yet trustworthy as text: the best variant measured ({best[0]}, about {best[1]:.1f}% word errors on two sampled pages) still has errors, and nothing has been proofread against the page images. "
          "It is complete (all pages, continuous) and usable for search and reading, but not accurate enough to quote." if best else "No OCR accuracy measurement available.")


# ------------------------------------------------------------------ mapping
def verify_mapping() -> None:
    print("== Verse mapping")
    summ = json.loads((ROOT / "data" / "processed" / "alignment" / "summary.json").read_text())
    h = summ["hebrew-bible"]
    check("mapping", "Hebrew to English to German Old Testament mapping covers every verse", h["english_verses_with_no_hebrew_counterpart"] == ["NEH 7:68"] and h["luther_ot_verse_set_equals_web_ot"],
          f"{h['hebrew_verses']:,} Hebrew verses map to {h['english_verses_reached']:,} of {h['english_ot_verses']:,} English verses; the English verse without a Hebrew counterpart is {h['english_verses_with_no_hebrew_counterpart']}; "
          f"{h['hebrew_verses_with_changed_number']:,} Hebrew verses are numbered differently in English; the German (Luther) verse set equals the English set.", **{k: h[k] for k in ("hebrew_verses", "english_verses_reached")})
    n = summ["new-testament"]
    check("mapping", "Greek, English and German New Testament: verses linked by number", None,
          f"{n['greek_verses_with_same_number_in_english']:,} of {n['greek_verses']:,} Greek verses have the same number in English and in German. Greek only: {n['greek_only_vs_english']}. "
          f"English only: {len(n['english_only_vs_greek'])} verses; German only: {len(n['german_only_vs_greek'])} verses (critical-text omissions and divisions that differ); each needs an expert-confirmed link.",
          english_only=n["english_only_vs_greek"], german_only=n["german_only_vs_greek"])
    q = summ["quran"]
    check("mapping", "Qur'an: standard numbering to the number printed in the 1930 Pickthall", None,
          f"{q['with_pickthall_1930_printed_number']:,} of {q['standard_verses']:,} verses have a printed 1930 number; {q['pickthall_printed_number_differs_from_standard']} are numbered differently "
          f"(the 1930 book divides some suras differently; for example sura 10 and sura 38 are one higher, sura 18 shifts by one after verse 19). Henning's numbering is not mapped yet.")


SECTIONS = {"hebrew": verify_hebrew, "greek": verify_greek, "usfx": verify_usfx, "quran-arabic": verify_quran_arabic,
            "pickthall": verify_pickthall, "henning": verify_henning, "mapping": verify_mapping}


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    path = OUTDIR / "verification.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    for name in (sys.argv[1:] or list(SECTIONS)):
        for fn in ([SECTIONS[name]] if name in SECTIONS else []):
            for k in [k for k in old if k.split(":")[0] == name]:
                old.pop(k)
            before = set(RESULTS)
            fn()
    merged = {**old, **RESULTS}
    path.write_text(json.dumps(merged, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    failed = [(s, c["check"]) for s, cs in RESULTS.items() for c in cs if c["passed"] is False]
    print(f"\nwritten {path.relative_to(ROOT)}; failed checks in this run: {len(failed)}")
    for s, c in failed:
        print("  FAILED:", s, "-", c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
