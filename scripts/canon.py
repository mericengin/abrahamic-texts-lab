"""Parsers and writers for the Phase 1 canon sources (Hebrew Bible, Greek NT, WEB, Luther 1912, Tanzil Qur'an).

Every parser returns a Version: books, each a list of (chapter, verse, text) rows with the words unchanged.
Only markup is removed (see each parser's docstring). writers turn a Version into Markdown files and into a
print-ready HTML file (later made into a PDF). Standard library only.
"""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

OSIS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"

# English (Protestant) order, matching WEB and Luther, so layers line up file by file.
HB_ORDER = ["Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh",
            "Esth", "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah",
            "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal"]
NT_NAMES = ["Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians",
            "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
            "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"]
SBLGNT_FILES = ["Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim",
                "2Tim", "Titus", "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev"]
DEUTERO_IDS = {"TOB", "JDT", "ESG", "WIS", "SIR", "BAR", "LJE", "S3Y", "SUS", "BEL", "1MA", "2MA", "3MA", "4MA", "1ES", "2ES", "MAN", "PS2",
               "ODA", "PSS", "DAG", "EZA", "5EZ", "6EZ", "LAO", "ADE", "ADA"}


@dataclass
class Book:
    stem: str                 # file name stem, e.g. "01-Gen"
    title: str
    rows: list[tuple[str, str, str]]   # (chapter, verse, text)
    extra: dict = field(default_factory=dict)


@dataclass
class Version:
    key: str                  # short label for files, e.g. "hebrew-wlc"
    name: str
    language: str
    direction: str            # "ltr" or "rtl"
    books: list[Book]
    notice: str = ""          # text that must travel with every copy (Tanzil)
    notes: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# --------------------------------------------------------------------------- Hebrew (OSIS, morphhb)
def parse_hebrew(rawdir: Path) -> Version:
    """WLC text from OSIS XML. The / morpheme separators (annotation markup) are removed, so the text is the WLC text.
    Maqqef, sof pasuq, paseq and the paragraph markers pe/samekh are kept. Where a word is a ketiv, the qere reading from the
    margin note is added in square brackets right after it. Other notes (alternative, exegesis) are skipped and counted."""
    books, skipped_notes, qere_count = [], 0, 0
    for i, code in enumerate(HB_ORDER, 1):
        root = ET.parse(rawdir / "wlc" / f"{code}.xml").getroot()
        rows = []
        for v in root.iter(OSIS + "verse"):
            _, ch, vs = v.get("osisID").split(".")
            out: list[str] = []
            join_next = True
            for c in v:
                tag = c.tag.replace(OSIS, "")
                if tag == "w":
                    word = "".join(c.itertext()).replace("/", "")
                    out.append(word if join_next else " " + word)
                    join_next = False
                elif tag == "seg":
                    typ, sym = c.get("type"), "".join(c.itertext())
                    if typ == "x-maqqef":
                        out.append(sym); join_next = True
                    elif typ == "x-sof-pasuq":
                        out.append(sym)
                    elif typ == "x-paseq":
                        out.append(" " + sym)
                    else:  # x-pe, x-samekh: open/closed paragraph marks
                        out.append(" {" + sym + "}")
                elif tag == "note":
                    if c.get("type") == "variant":
                        q = [ws("".join(w.itertext())).replace("/", "") for r in c.iter(OSIS + "rdg") if r.get("type") == "x-qere" for w in r.iter(OSIS + "w")]
                        if q:
                            out.append(" [" + " ".join(q) + "]"); qere_count += 1
                    else:
                        skipped_notes += 1
            rows.append((ch, vs, "".join(out).strip()))
        books.append(Book(f"{i:02d}-{code}", code, rows))
    n = sum(len(b.rows) for b in books)
    return Version("hebrew-wlc", "Westminster Leningrad Codex (Open Scriptures Hebrew Bible text)", "Biblical Hebrew (with Aramaic passages)", "rtl", books,
                   notes=["Hebrew (Masoretic) verse numbering, which differs from English numbering in some places.",
                          f"Qere readings added in square brackets: {qere_count}. Margin notes skipped: {skipped_notes}.",
                          "Lemma and morphology are not in the Markdown; they stay in the raw OSIS XML."],
                   stats={"books": len(books), "verses": n, "qere_added": qere_count, "notes_skipped": skipped_notes})


# --------------------------------------------------------------------------- Greek (SBLGNT, Faithlife)
def parse_sblgnt(rawdir: Path) -> Version:
    """SBLGNT plain text per book, verbatim, including the apparatus signs (⸀ ⸂ ⸃) that the edition prints in the text."""
    books = []
    for i, stem in enumerate(SBLGNT_FILES, 1):
        lines = (rawdir / "data" / "sblgnt" / "text" / f"{stem}.txt").read_text(encoding="utf-8").splitlines()
        title, rows = lines[0].strip(), []
        for ln in lines[1:]:
            if not ln.strip():
                continue
            ref, _, text = ln.partition("\t")
            m = re.search(r"(\d+):(\d+)$", ref.strip())
            if not m:
                rows[-1] = (*rows[-1][:2], rows[-1][2] + " " + ln.strip()); continue
            rows.append((m.group(1), m.group(2), text.strip()))
        books.append(Book(f"{i:02d}-{stem}", f"{title} ({NT_NAMES[i - 1]})", rows))
    return Version("greek-sblgnt", "SBL Greek New Testament", "Koine Greek", "ltr", books,
                   notes=["Apparatus signs (⸀ ⸂ ⸃) and the text's own punctuation are kept as printed in the edition's text files."],
                   stats={"books": len(books), "verses": sum(len(b.rows) for b in books)})


def parse_morphgnt(rawdir: Path) -> Version:
    """MorphGNT: the 'text with punctuation' column (4th) joined per verse. Lemma and parsing stay in the raw files."""
    files = sorted(rawdir.glob("[0-9][0-9]-*-morphgnt.txt"))
    books = []
    for f in files:
        n = int(f.name[:2]) - 60
        verses: dict[tuple[str, str], list[str]] = {}
        order: list[tuple[str, str]] = []
        for ln in f.read_text(encoding="utf-8").splitlines():
            p = ln.split(" ")
            if len(p) < 7:
                continue
            ch, vs = str(int(p[0][2:4])), str(int(p[0][4:6]))
            if (ch, vs) not in verses:
                verses[(ch, vs)] = []; order.append((ch, vs))
            verses[(ch, vs)].append(p[3])
        books.append(Book(f"{n:02d}-{f.name.split('-')[1]}", NT_NAMES[n - 1], [(c, v, " ".join(verses[(c, v)])) for c, v in order]))
    return Version("greek-morphgnt", "MorphGNT SBLGNT (text column)", "Koine Greek", "ltr", books,
                   notes=["Only the text column is in the Markdown; lemma and parsing stay in the raw files."],
                   stats={"books": len(books), "verses": sum(len(b.rows) for b in books)})


# --------------------------------------------------------------------------- USFX (WEB, Luther 1912)
_SKIP = {"f", "fe", "x", "ef", "ex", "fig", "rq", "ref"}
_HEAD = {"h", "toc", "mt", "ms", "mr", "s", "r", "sp", "cl", "cp", "d", "id", "ip", "is", "imt", "ie", "rem"}


def parse_usfx(zip_path: Path, xml_name: str, key: str, name: str, language: str, only_books: set[str] | None = None) -> Version:
    """USFX verse text. Footnotes, cross references, headings and Strong's tags are dropped; the words of the verse stay.
    Every book in the file is kept; Deuterocanon is flagged in book.extra."""
    root = ET.fromstring(zipfile.ZipFile(zip_path).read(xml_name))
    books: list[Book] = []
    n = 0
    for b in root.iter("book"):
        bid = b.get("id")
        if bid in {"FRT", "BAK", "GLO", "CNC", "TDX", "OTH", "INT", "XXA", "XXB", "XXC", "XXD", "XXE", "XXF", "XXG"}:
            continue
        title_el = b.find("h")
        title = ws("".join(title_el.itertext())) if title_el is not None else bid
        rows: list[tuple[str, str, str]] = []
        state = {"c": "", "v": None, "buf": []}

        def flush():
            if state["v"] is not None:
                rows.append((state["c"], state["v"], ws("".join(state["buf"]))))
            state["v"], state["buf"] = None, []

        def walk(el):
            tag = el.tag
            if tag == "c":
                flush(); state["c"] = el.get("id")
            elif tag == "v":
                flush(); state["v"] = el.get("id")
            elif tag == "ve":
                flush()
            elif tag in _SKIP or tag in _HEAD:
                pass
            else:
                if state["v"] is not None and el.text:
                    state["buf"].append(el.text)
                for ch in el:
                    walk(ch)
                    if state["v"] is not None and ch.tail:
                        state["buf"].append(ch.tail)

        walk_children = list(b)
        for ch in walk_children:
            walk(ch)
            if state["v"] is not None and ch.tail:
                state["buf"].append(ch.tail)
        flush()
        rows = [r for r in rows if r[2]]
        if only_books and bid not in only_books:
            continue
        n += 1
        books.append(Book(f"{n:02d}-{bid}", title, rows, {"usfx_id": bid, "deuterocanon": bid in DEUTERO_IDS}))
    return Version(key, name, language, "ltr", books,
                   notes=["Footnotes, cross references, headings and Strong's number tags are removed; verse words are unchanged."],
                   stats={"books": len(books), "verses": sum(len(b.rows) for b in books),
                          "deuterocanon_books": sum(1 for b in books if b.extra["deuterocanon"])})


# --------------------------------------------------------------------------- Tanzil (Qur'an)
def tanzil_notice(raw: str) -> str:
    """The copyright block that Tanzil requires to travel with every copy (the comment lines starting with #)."""
    lines = [ln.rstrip() for ln in raw.splitlines() if ln.startswith("#")]
    if not lines:  # XML keeps it in an XML comment
        m = re.search(r"<!--(.*?)-->", raw, flags=re.S)
        lines = [ln.rstrip() for ln in (m.group(1) if m else "").splitlines()]
    return "\n".join(lines).strip("\n")


def parse_tanzil_xml(path: Path, key: str, name: str) -> Version:
    raw = path.read_text(encoding="utf-8")
    root = ET.fromstring(raw.encode("utf-8"))
    books = []
    for s in root.iter("sura"):
        i = int(s.get("index"))
        rows = [(str(i), a.get("index"), a.get("text")) for a in s.iter("aya")]
        bism = next((a.get("bismillah") for a in s.iter("aya") if a.get("bismillah")), "")
        books.append(Book(f"{i:03d}", f"Sura {i}: {s.get('name')}", rows, {"bismillah": bism, "arabic_name": s.get("name")}))
    return Version(key, name, "Classical Arabic", "rtl", books, notice=tanzil_notice(raw),
                   notes=["The text is exactly as Tanzil published it (verbatim). Sura 1 has the bismillah as verse 1; for other suras it is given once per sura."],
                   stats={"suras": len(books), "ayas": sum(len(b.rows) for b in books)})


def parse_tanzil_txt(path: Path, key: str, name: str) -> Version:
    raw = path.read_text(encoding="utf-8")
    suras: dict[int, list[tuple[str, str, str]]] = {}
    for ln in raw.splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        s, a, t = ln.split("|", 2)
        suras.setdefault(int(s), []).append((s, a, t))
    books = [Book(f"{i:03d}", f"Sura {i}", rows) for i, rows in sorted(suras.items())]
    return Version(key, name, "Classical Arabic", "rtl", books, notice=tanzil_notice(raw),
                   notes=["The text is exactly as Tanzil published it (verbatim)."],
                   stats={"suras": len(books), "ayas": sum(len(b.rows) for b in books)})


# --------------------------------------------------------------------------- writers
def yaml_str(v) -> str:
    import json
    return json.dumps(v, ensure_ascii=False)


def book_md(ver: Version, b: Book, front: dict) -> str:
    lines = ["---"] + [f"{k}: {yaml_str(v)}" for k, v in {**front, "book": b.title, "verses": len(b.rows), "direction": ver.direction, "language": ver.language}.items()] + ["---", "", f"# {b.title}", ""]
    ch = None
    for c, v, t in b.rows:
        if c != ch:
            if len({r[0] for r in b.rows}) > 1:
                lines += ["", f"## Chapter {c}", ""]
            ch = c
        lines.append(f"**{v}** {t}")
        lines.append("")
    if ver.notice:
        lines += ["---", "", "Tanzil notice (must stay with every copy):", "", "```text", ver.notice, "```", ""]
    return "\n".join(lines).replace("\n\n\n\n", "\n\n").rstrip() + "\n"


def write_md(ver: Version, outdir: Path, front: dict) -> list[str]:
    outdir.mkdir(parents=True, exist_ok=True)
    names = []
    index = ["---"] + [f"{k}: {yaml_str(v)}" for k, v in {**front, "language": ver.language, "direction": ver.direction}.items()] + ["---", "",
             f"# {ver.name}", ""] + [f"- {n}" for n in ver.notes] + ["", "| File | Book | Verses |", "|---|---|---|"]
    for b in ver.books:
        fn = f"{b.stem}.md"
        (outdir / fn).write_text(book_md(ver, b, front), encoding="utf-8")
        names.append(fn)
        index.append(f"| [{fn}]({fn}) | {b.title} | {len(b.rows)} |")
    if ver.notice:
        index += ["", "Tanzil notice (must stay with every copy):", "", "```text", ver.notice, "```"]
    (outdir / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return names


CSS = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
body { font-family: 'Times New Roman', 'Palatino', serif; font-size: 11pt; line-height: 1.55; color: #111; }
h1 { font-size: 22pt; margin: 0 0 6pt; } h2 { font-size: 15pt; margin: 22pt 0 6pt; page-break-before: always; border-bottom: 1px solid #999; padding-bottom: 3pt; }
h3 { font-size: 12pt; margin: 14pt 0 4pt; }
.meta { color: #333; font-size: 10pt; border-left: 3px solid #bbb; padding-left: 8pt; margin: 10pt 0; }
.verse { margin: 0 0 3pt; } .n { font: 600 8.5pt -apple-system, Helvetica, sans-serif; color: #666; margin: 0 4pt; }
.rtl .verse { direction: rtl; text-align: right; }
.he { font-family: 'SBL Hebrew', 'Ezra SIL', 'Arial Hebrew', 'Times New Roman', serif; font-size: 14pt; line-height: 2.0; }
.ar { font-family: 'KFGQPC Uthmanic Script HAFS', 'Scheherazade New', 'Al Nile', 'Geeza Pro', 'Times New Roman', serif; font-size: 16pt; line-height: 2.3; }
pre { white-space: pre-wrap; font-size: 8pt; border: 1px solid #ccc; padding: 6pt; }
"""


def write_html(ver: Version, path: Path, front: dict, font_class: str = "") -> None:
    rtl = ver.direction == "rtl"
    h = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{html.escape(ver.name)}</title><style>{CSS}</style></head><body>",
         f"<h1>{html.escape(ver.name)}</h1><div class='meta'>",
         f"<b>Language:</b> {html.escape(ver.language)}<br><b>Source:</b> {html.escape(front.get('source_id', ''))}<br>",
         f"<b>License:</b> {html.escape(front.get('license', ''))}<br><b>Attribution:</b> {html.escape(front.get('attribution', ''))}<br>",
         "<b>This PDF was generated from the source data by scripts/make_pdfs.py. It is a plain reading copy, not an official edition, "
         "and the words are unchanged.</b><br>"] + [html.escape(n) + "<br>" for n in ver.notes] + ["</div>"]
    if ver.notice:
        h.append(f"<pre>{html.escape(ver.notice)}</pre>")
    for b in ver.books:
        h.append(f"<h2>{html.escape(b.title)}</h2><div class='{'rtl ' if rtl else ''}{font_class}'>")
        ch = None
        for c, v, t in b.rows:
            if c != ch and len({r[0] for r in b.rows}) > 1:
                h.append(f"<h3 style='direction:ltr'>Chapter {html.escape(c)}</h3>"); ch = c
            h.append(f"<p class='verse'><span class='n'>{html.escape(v)}</span>{html.escape(t)}</p>")
        h.append("</div>")
    h.append("</body></html>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(h), encoding="utf-8")


# --------------------------------------------------------------------------- registry and checks
def builders(raw: Path) -> dict[str, list[tuple[str, object]]]:
    """source id -> [(version key, zero-argument parser)]"""
    t = raw / "quran-tanzil-arabic"
    return {
        "hebrew-morphhb": [("hebrew-wlc", lambda: parse_hebrew(raw / "hebrew-morphhb"))],
        "greek-sblgnt-text": [("greek-sblgnt", lambda: parse_sblgnt(raw / "greek-sblgnt-text"))],
        "greek-morphgnt": [("greek-morphgnt", lambda: parse_morphgnt(raw / "greek-morphgnt"))],
        "english-web-deutero": [("english-web", lambda: parse_usfx(raw / "english-web-deutero" / "eng-web_usfx.zip", "eng-web_usfx.xml",
                                                                    "english-web", "World English Bible (Classic), with Deuterocanon", "English"))],
        "german-luther-1912": [("german-luther", lambda: parse_usfx(raw / "german-luther-1912" / "deu1912_usfx.zip", "deu1912_usfx.xml",
                                                                    "german-luther", "Lutherbibel 1912", "German"))],
        "quran-tanzil-arabic": [
            ("quran-uthmani-xml", lambda: parse_tanzil_xml(t / "quran-uthmani.xml", "quran-uthmani-xml", "Quran, Tanzil Uthmani text (v1.1), from XML")),
            ("quran-uthmani-txt", lambda: parse_tanzil_txt(t / "quran-uthmani.txt", "quran-uthmani-txt", "Quran, Tanzil Uthmani text (v1.1), from text file")),
            ("quran-simple-clean-txt", lambda: parse_tanzil_txt(t / "quran-simple-clean.txt", "quran-simple-clean-txt", "Quran, Tanzil Simple (Clean) text (v1.1)")),
        ],
    }


EXPECTED_VERSES = {"hebrew-wlc": 23213, "greek-sblgnt": 7939, "german-luther": 31102, "quran-uthmani-xml": 6236,
                   "quran-uthmani-txt": 6236, "quran-simple-clean-txt": 6236}


def roundtrip(ver: Version, outdir: Path) -> dict:
    """Read the Markdown back and compare every verse with the parsed rows. Proves nothing was dropped or altered on write."""
    bad, total = [], 0
    for b in ver.books:
        text = (outdir / f"{b.stem}.md").read_text(encoding="utf-8").split("\n---\n")[0] if False else (outdir / f"{b.stem}.md").read_text(encoding="utf-8")
        body = text.split("\n# ", 1)[1]
        body = body.split("\n---\n\nTanzil notice")[0]
        chapter = b.rows[0][0] if b.rows else ""
        got = []
        for ln in body.splitlines():
            m = re.match(r"^## Chapter (.+)$", ln)
            if m:
                chapter = m.group(1); continue
            m = re.match(r"^\*\*(\S+)\*\* (.*)$", ln)
            if m:
                got.append((chapter, m.group(1), m.group(2)))
        total += len(got)
        if got != list(b.rows):
            bad.append(b.stem)
    return {"verses_read_back": total, "books_with_differences": bad, "ok": not bad}
