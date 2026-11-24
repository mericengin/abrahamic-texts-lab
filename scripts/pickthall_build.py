#!/usr/bin/env python3
"""Rebuild Pickthall's 1930 text from the OCR of four scans of the 1930 book, by vote.

Why: the Project Gutenberg #16955 "Pickthall" lines turned out NOT to be the 1930 text (they differ in wording in roughly one verse
in ten, for example 2:57 "We wronged them not" in all four scans against "they wronged Us not"). So the 1930 layer is built from the
scans themselves. The Gutenberg text is used only as a coordinate system: it tells us where each sura starts in each scan.

Steps per scan: (1) find each sura's start with the anchor chain from pickthall_reconcile; (2) read the book's own numbered verses
in order inside that sura (1., 2., ...), after removing running headers and footnotes; (3) key each verse as letters only.
Steps per verse: vote across the scans by letter string. Verdicts: agreed (3 or more scans identical), pair (2 identical),
split (no two identical: needs the page image), single (only one scan has the verse). Output (local, git-ignored): data/processed/pickthall/.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from bisect import bisect_left
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pickthall_reconcile as pr  # noqa: E402

OUT = pr.OUT
ROOT_DIR = pr.ROOT
HEADER = re.compile(r"(?im)^[ \t]*(\d+[ \t]+)?the[ \t]+glorious[ \t]+koran([ \t]+[a-zöü0]+)?[ \t]*(\d+)?[ \t]*$")
MARK = re.compile(r"(?m)^[ \t]*(\d{1,3}|I|l)[ \t]?[.,:;·][ \t]*(?=\S)")


def clean_raw(text: str) -> str:
    text = text.replace("\f", "\n")
    text = re.sub(r"-[ \t]*\n[ \t]*", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = HEADER.sub("", text)
    # running headers that the OCR joined into running text: "VII THE HEIGHTS 159", "XXX the romans 415", "5i6 the glorious KORAN sOrah XLV"
    text = re.sub(r"(?i)\b\S{0,4}[ \t]+the[ \t]+glorious[ \t]+koran[ \t]+s[oöu0]r[aä]h[ \t]*[ivxlc]*\b", " ", text)
    text = re.sub(r"\b[IVXLC]{1,7}[ \t]+(?:THE|the|The)[ \t]+[A-Za-z'’ \t]{3,28}?[ \t]+\d{2,3}\b", " ", text)
    text = re.sub(r"\b\d{2,3}[ \t]+(?:THE|the)[ \t]+(?:GLORIOUS|glorious)[ \t]+(?:KORAN|koran)\b", " ", text)
    # footnotes: a line that starts with * or † up to the next blank line
    text = re.sub(r"(?m)^[ \t]*[*†‡][^\n]*(\n(?![ \t]*\n)[^\n]*)*", "", text)
    return text


def letters_index(text: str):
    chars, idx = [], []
    for i, ch in enumerate(text):
        for c in unicodedata.normalize("NFKD", ch.lower()):
            if "a" <= c <= "z":
                chars.append(c)
                idx.append(i)
    return "".join(chars), idx


def trim_tail(text: str, ref: str) -> str:
    """Drop text after the verse's last words (footnotes, headers, the next verse's number) when the Gutenberg verse is matched to its end."""
    import difflib
    lt, it = letters_index(text)
    g = pr.key(ref)
    if len(g) < 12 or not lt:
        return text
    sm = difflib.SequenceMatcher(None, g, lt, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size >= 4]
    if not blocks:
        return text
    last = blocks[-1]
    if len(g) - (last.a + last.size) <= 3 and len(lt) - (last.b + last.size) > 6:
        end = it[last.b + last.size - 1] + 1
        while end < len(text) and text[end] in ".,;:!?)”’'\"*":   # keep the verse's own closing punctuation
            end += 1
        return text[:end].rstrip()
    return text


def token_vote(reads: list[str]):
    """Word-by-word majority over the readings of one verse. Returns the voted text, or None if the result matches (or nearly matches) fewer than two readings."""
    import difflib
    tk = lambda w: re.sub(r"[^a-z]", "", w.lower())
    pivot = max(reads, key=lambda a: sum(difflib.SequenceMatcher(None, pr.key(a), pr.key(b)).ratio() for b in reads))
    pt = pivot.split()
    votes = [Counter() for _ in pt]
    for t in reads:
        if t is pivot:
            for i, w in enumerate(pt):
                votes[i][tk(w)] += 1
            continue
        other = t.split()
        sm = difflib.SequenceMatcher(None, [tk(w) for w in pt], [tk(w) for w in other], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    votes[i1 + k][tk(pt[i1 + k])] += 1
            elif tag == "replace" and i2 - i1 == j2 - j1:
                for k in range(i2 - i1):
                    votes[i1 + k][tk(other[j1 + k])] += 1
    out = []
    for i, w in enumerate(pt):
        win = votes[i].most_common(1)[0][0]
        out.append(w if tk(w) == win else next((x for t in reads for x in t.split() if tk(x) == win), w))
    voted = " ".join(out)
    kv = pr.key(voted)
    close = sum(1 for t in reads if difflib.SequenceMatcher(None, pr.key(t), kv).ratio() > 0.985)
    return voted if close >= 2 else None


FURNITURE = re.compile(r"(?i)^(?:\S{0,6}rah|[^\w\s]{0,2}[a-z0-9^{}<>()~|]{0,4}rah|sur\.?|sura|surah|koran|glorious|\d{1,3}[,.:;]?|[ivxlc1l|]{1,4}[,.:;]?|i\.?e\.?|[ivxlc1]+[,.]?)$")


def clean_furniture(text: str, ref: str) -> str:
    """Remove page furniture (running headers, footnote references, page numbers) that leaked into a verse.
    Only tokens that the Gutenberg verse does not have, that sit at the start or end of the text or form a run containing a furniture token, are removed.
    Every word that matches or replaces a word of the verse is kept."""
    import difflib
    tk = lambda w: re.sub(r"[^a-z]", "", w.lower())
    t, g = text.split(), ref.split()
    sm = difflib.SequenceMatcher(None, [tk(w) for w in g], [tk(w) for w in t], autojunk=False)
    keep = [True] * len(t)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "insert":
            continue
        run = t[j1:j2]
        at_edge = j1 == 0 or j2 == len(t)
        has_furniture = any(FURNITURE.match(w) or "koran" in w.lower() or "rah" in w.lower() for w in run)
        if not at_edge and len(run) >= 8:
            for k in range(j1, j2):      # a long run in the middle of a verse is a footnote; at the end it may be a real continuation, so that is left alone
                keep[k] = False
        elif (at_edge and has_furniture) or (has_furniture and len(run) >= 1 and (len(run) >= 4 or all(FURNITURE.match(w) for w in run))):
            for k in range(j1, j2):
                keep[k] = False
        elif at_edge and j1 != 0 and len(run) >= 1 and all(len(tk(w)) <= 2 or not tk(w) for w in run):
            for k in range(j1, j2):
                keep[k] = False
    return " ".join(w for w, k in zip(t, keep) if k)


def load_page_words():
    """Word list of the fresh page-by-page OCR of the 1930 scan (a modern engine reading the same page images), for repairing isolated slips."""
    d = ROOT_DIR / "data" / "processed" / "ocr" / "english-quran-pickthall-pages"
    if not d.exists():
        return None
    words = []
    for n in range(1, 711):
        f = d / f"page-{n:03d}.txt"
        if f.exists():
            words += re.sub(r"-\s*\n\s*", "", f.read_text(encoding="utf-8")).split()
    keyw = [re.sub(r"[^a-z]", "", w.lower()) for w in words]
    idx: dict = {}
    for i in range(len(keyw) - 2):
        idx.setdefault((keyw[i], keyw[i + 1], keyw[i + 2]), []).append(i)
    return words, keyw, idx


def repair_slips(text: str, pages, vocab: Counter) -> tuple[str, int]:
    """Replace an isolated garbled token (rare in the book) by the aligned token of the fresh page OCR when that token is a well-attested word
    (at least 3 uses in verses the scans agree on) and the two differ by at most two letters. Nothing else is changed."""
    import difflib
    words, keyw, idx = pages
    t = text.split()
    tk = lambda w: re.sub(r"[^a-z]", "", w.lower())
    g = [tk(w) for w in t]
    if len(g) < 4:
        return text, 0
    best = None
    for st in idx.get(tuple(g[:3]), []):
        win = keyw[st: st + len(g) + 40]
        sm = difflib.SequenceMatcher(None, g, win, autojunk=False)
        m = sum(b.size for b in sm.get_matching_blocks())
        if best is None or m > best[0]:
            best = (m, st, sm)
    if best is None or best[0] / len(g) < 0.85:
        return text, 0
    _, st, sm = best
    changed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace" and i2 - i1 == j2 - j1:
            for k in range(i2 - i1):
                ours, theirs = t[i1 + k], words[st + j1 + k]
                ko, kt = tk(ours), tk(theirs)
                if vocab[ko] < 3 and vocab[kt] >= 3 and ko and kt and difflib.SequenceMatcher(None, ko, kt).ratio() >= 0.7:
                    # keep our punctuation, take the other spelling
                    lead = re.match(r"^\W*", ours).group(0)
                    tail = re.search(r"\W*$", ours).group(0)
                    t[i1 + k] = lead + re.sub(r"^\W+|\W+$", "", theirs) + tail
                    changed += 1
    return " ".join(t), changed


def repair_with_gutenberg(text: str, gtext: str, vocab: Counter) -> tuple[str, int]:
    """A token that is rare in the book and absent from the Gutenberg verse, aligned one-to-one with a Gutenberg token that is a common word and
    one or two letters away, is a shared OCR slip (for example 'causech' for 'causeth'): take the Gutenberg token. Spelling variants are kept
    because they are not rare words."""
    import difflib
    tk = lambda w: re.sub(r"[^a-z]", "", w.lower())
    t, g = text.split(), gtext.split()
    sm = difflib.SequenceMatcher(None, [tk(w) for w in g], [tk(w) for w in t], autojunk=False)
    changed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace" and i2 - i1 == j2 - j1:
            for k in range(i2 - i1):
                ko, kg = tk(t[j1 + k]), tk(g[i1 + k])
                if ko and kg and vocab[ko] < 3 and vocab[kg] >= 3 and difflib.SequenceMatcher(None, ko, kg).ratio() >= 0.8:
                    lead = re.match(r"^\W*", t[j1 + k]).group(0)
                    tail = re.search(r"\W*$", t[j1 + k]).group(0)
                    t[j1 + k] = lead + re.sub(r"^\W+|\W+$", "", g[i1 + k]) + tail
                    changed += 1
    return " ".join(t), changed


def sura_starts(letters: str, idx: list[int], guten, gkeys, offs):
    """Raw-text position near each sura's first verse, from the anchor chain."""
    gfull = "".join(gkeys[r] for r in sorted(guten))
    pairs = pr.chain(gfull, letters)
    gp = [p[0] for p in pairs]
    out = {}
    for s in range(1, 115):
        refs = [r for r in sorted(guten) if r[0] == s and len(gkeys[r]) >= 14]
        if not refs:
            continue
        r = refs[0]
        gs = offs[r]
        i = bisect_left(gp, gs)
        cand = [a for a in (pairs[i - 1] if i else None, pairs[i] if i < len(pairs) else None) if a and abs(a[0] - gs) <= 800]
        if cand:
            a = min(cand, key=lambda x: abs(x[0] - gs))
            pred = max(0, min(a[1] + (gs - a[0]), len(idx) - 1))
            out[s] = pred
    return out


def parse_scan(path: Path, guten, gkeys, offs, sizes):
    """Locate every standard verse by alignment (coarse), then snap to the book's own printed verse number nearby (exact)."""
    raw = clean_raw(path.read_text(encoding="utf-8"))
    letters, idx = letters_index(raw)
    gfull = "".join(gkeys[r] for r in sorted(guten))
    pairs = pr.chain(gfull, letters)
    gp = [p[0] for p in pairs]
    marks = [(1 if m.group(1) in ("I", "l") else int(m.group(1)), m.start(), m.end()) for m in MARK.finditer(raw)]
    starts: dict[tuple[int, int], tuple[int, int, int | None]] = {}   # verse -> (text start, boundary start, printed number)
    for r in sorted(guten):
        gs = offs[r]
        i = bisect_left(gp, gs)
        cand = [a for a in (pairs[i - 1] if i else None, pairs[i] if i < len(pairs) else None) if a and abs(a[0] - gs) <= 600]
        if not cand:
            continue
        a = min(cand, key=lambda x: abs(x[0] - gs))
        pred = idx[max(0, min(a[1] + (gs - a[0]), len(idx) - 1))]
        near = [(abs(pred - en), n, st, en) for n, st, en in marks if pred - 250 <= en <= pred + 80]
        if near:
            _, n, st, en = min(near)
            starts[r] = (en, st, n)
        else:
            starts[r] = (pred, pred, None)
    verses: dict[tuple[int, int], str] = {}
    numbering: dict[tuple[int, int], int] = {}
    snapped = 0
    order = sorted(starts)
    for k, r in enumerate(order):
        st, _, printed = starts[r]
        if printed is not None:
            snapped += 1
            numbering[r] = printed
        same_sura_next = k + 1 < len(order) and order[k + 1][0] == r[0]
        end = starts[order[k + 1]][1] if k + 1 < len(order) else len(raw)
        ref_len = len(guten[r])
        if not same_sura_next:  # last verse of a sura: stop where the next sura's heading begins
            h = re.compile(r"(?i)\b(s[oöu0]r[aä]h\b|revealed\s+at)").search(raw, st + 20, end)
            if h:
                end = h.start()
        text = re.sub(r"\s+", " ", raw[st:end]).strip()
        words = text.split(" ")
        text = " ".join(words[: int(max(ref_len / 5.0, 4) * 1.6) + 10])
        text = trim_tail(text, guten[r])
        if text:
            verses[r] = text
    notes = {"verses_located": len(starts), "snapped_to_printed_number": snapped, "not_located": [f"{a}:{b}" for a, b in sorted(guten) if (a, b) not in starts][:12]}
    notes["numbering"] = {f"{a}:{b}": n for (a, b), n in numbering.items()}
    return verses, notes


def main() -> int:
    guten = pr.gutenberg()
    refs = sorted(guten)
    gkeys = {r: pr.key(guten[r]) for r in refs}
    offs, pos = {}, 0
    for r in refs:
        offs[r] = pos
        pos += len(gkeys[r])
    sizes = Counter(s for s, _ in refs)
    per_scan, report = {}, {"scans": {}}
    for name, path in pr.SCANS.items():
        v, notes = parse_scan(path, guten, gkeys, offs, sizes)
        per_scan[name] = v
        report["scans"][name] = {"verses_read": len(v), **notes}
        print(f"{name}: read {len(v):,} verses; snapped to the printed verse number: {notes['snapped_to_printed_number']:,}", flush=True)

    rows, verdicts = [], Counter()
    for r in refs:
        reads = {n: per_scan[n][r] for n in per_scan if r in per_scan[n] and pr.key(per_scan[n][r])}
        keys = {n: pr.key(t) for n, t in reads.items()}
        count = Counter(keys.values())
        top, c = count.most_common(1)[0] if count else ("", 0)
        winners = [n for n, k in keys.items() if k == top]
        if c >= 3:
            verdict = "agreed"
        elif c == 2:
            verdict = "pair"
        elif len(keys) >= 2:
            verdict = "split"
        elif len(keys) == 1:
            verdict = "single"
        else:
            verdict = "missing"
        text = reads[winners[0]] if winners else ""
        if verdict == "split":
            voted = token_vote([t for t in reads.values() if t])
            if voted:
                verdict, text = "voted", voted      # settled by a word-by-word majority; still unverified against the page image
        verdicts[verdict] += 1
        rows.append({"sura": r[0], "verse": r[1], "verdict": verdict, "scans_with_verse": len(keys), "identical": c, "text": text,
                     "gutenberg_identical": pr.key(guten[r]) == top, "readings": {n: t for n, t in reads.items()} if (verdict in ("split", "single", "pair", "voted") or len(pr.key(text)) > len(pr.key(guten[r])) * 1.35 + 25) else {}})
    same = sum(1 for x in rows if x["gutenberg_identical"])
    report.update({"verses": len(rows), "verdicts": dict(verdicts), "identical_to_gutenberg_pickthall": same,
                   "differs_from_gutenberg": sum(1 for x in rows if x["verdict"] in ("agreed", "pair") and not x["gutenberg_identical"])})
    for x in rows:   # remove leaked page furniture from every reading-based verse
        if x["text"] and x["verdict"] in ("agreed", "pair", "voted", "split", "single"):
            x["text"] = clean_furniture(x["text"], guten[(x["sura"], x["verse"])])
    for x in rows:   # line-break hyphens left by the scans ("punish¬ ment")
        x["text"] = re.sub(r"\s*¬\s*", "", x["text"])
    pages_ = load_page_words()
    if pages_:
        vocab = Counter(re.sub(r"[^a-z]", "", w.lower()) for x in rows if x["verdict"] == "agreed" for w in x["text"].split())
        repaired = 0
        for x in rows:
            if x["verdict"] in ("agreed", "pair", "voted") and x["text"]:
                x["text"], c = repair_slips(x["text"], pages_, vocab)
                repaired += c
        report["slips_repaired_from_fresh_ocr"] = repaired
        g_rep = 0
        for x in rows:
            if x["verdict"] in ("agreed", "pair", "voted") and x["text"]:
                x["text"], c = repair_with_gutenberg(x["text"], guten[(x["sura"], x["verse"])], vocab)
                g_rep += c
        report["slips_repaired_from_gutenberg_token"] = g_rep
    # --- second line of evidence: the alignment check (pickthall_reconcile.py) confirms a verse when two or more scans match the Gutenberg wording word for word
    chk_path = OUT / "pickthall-1930-check.json"
    chk = {(c["sura"], c["verse"]): c for c in json.loads(chk_path.read_text())} if chk_path.exists() else {}
    resolved_by = Counter()
    for x in rows:
        ref = (x["sura"], x["verse"])
        c = chk.get(ref)
        gk, tk_ = pr.key(guten[ref]), pr.key(x["text"])
        if x["verdict"] in ("split", "single", "missing") and c and c["verdict"] == "confirmed":
            x["text"], x["verdict"] = guten[ref], "confirmed-by-alignment"      # two or more scans match the Gutenberg wording exactly
            resolved_by["confirmed by alignment with two or more scans"] += 1
        elif gk and tk_.startswith(gk) and len(tk_) > len(gk) * 1.3 + 12 and c and c["verdict"] in ("confirmed", "single-scan"):
            x["text"], x["verdict"] = guten[ref], "confirmed-by-alignment"      # the scan reading begins with the verse and then runs into the next sura's introduction
            resolved_by["leaked introduction trimmed (verse confirmed by alignment)"] += 1
        elif c and c["verdict"] == "confirmed" and gk and (len(tk_) > len(gk) * 1.35 + 25 or (len(gk) > 20 and len(tk_) < len(gk) * 0.6)):
            x["text"], x["verdict"] = guten[ref], "confirmed-by-alignment"      # the printed-number boundary was misplaced here; two or more scans match the verse's own words
            resolved_by["misplaced boundary: verse confirmed by alignment instead"] += 1
        elif x["verdict"] == "single" and gk and tk_ == gk:
            x["verdict"] = "pair-with-gutenberg"                                  # one scan and Gutenberg agree word for word
            resolved_by["one scan agrees word for word with Gutenberg"] += 1
    import difflib
    tkw = lambda w: re.sub(r"[^a-z]", "", w.lower())

    def words_confirmed(gtext: str, reading: str) -> bool:
        """The verse's words appear in order in the reading; anything else in the reading is inserted clutter (a footnote or a running header), with no replaced words."""
        g = [tkw(w) for w in gtext.split() if tkw(w)]
        r = [tkw(w) for w in reading.split() if tkw(w)]
        if len(g) < 3:
            return False
        sm = difflib.SequenceMatcher(None, g, r, autojunk=False)
        matched = sum(b.size for b in sm.get_matching_blocks())
        replaced = sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t == "replace")
        deleted = sum(i2 - i1 for t, i1, i2, j1, j2 in sm.get_opcodes() if t == "delete")
        return matched / len(g) >= 0.96 and replaced <= max(1, len(g) // 25) and deleted <= max(1, len(g) // 25)

    for x in rows:
        ref = (x["sura"], x["verse"])
        glen, tlen = len(pr.key(guten[ref])), len(pr.key(x["text"]))
        queued = x["verdict"] in ("split", "single", "missing") or tlen > glen * 1.35 + 25 or (glen > 20 and tlen < glen * 0.6)
        if queued and x["verdict"] not in ("confirmed-by-alignment", "pair-with-gutenberg"):
            good = [n for n, t in x["readings"].items() if t and words_confirmed(guten[ref], t)] if x["readings"] else []
            if len(good) >= 2:
                x["text"], x["verdict"] = guten[ref], "words-confirmed"
                resolved_by["verse words found in order in two or more scans (surrounding footnote or header text ignored)"] += 1
    trimmed = 0
    for x in rows:   # a reading that begins exactly like the verse and then runs on into leaked page text: cut it where the verse's own letters end
        gk = pr.key(guten[(x["sura"], x["verse"])])
        if len(gk) >= 8 and x["text"] and pr.key(x["text"]).startswith(gk) and len(pr.key(x["text"])) > len(gk) * 1.3 + 12:
            acc, out = "", []
            for w in x["text"].split():
                out.append(w)
                acc += pr.key(w)
                if len(acc) >= len(gk):
                    break
            x["text"], x["trimmed_leak"] = " ".join(out), True
            trimmed += 1
    resolved_by["leaked page text trimmed where the verse ends"] += trimmed
    for k in ("confirmed-by-alignment", "pair-with-gutenberg"):
        verdicts[k] = sum(1 for x in rows if x["verdict"] == k)
    verdicts = Counter(x["verdict"] for x in rows)
    report["resolved_by_second_evidence"] = dict(resolved_by)
    report["verdicts"] = {k: v for k, v in verdicts.items() if v}
    # --- verses a person has read against the page image (data/processed/pickthall/image-checks.json): these decisions win over everything else
    ic_path = OUT / "image-checks.json"
    ic = json.loads(ic_path.read_text()) if ic_path.exists() else {}
    for x in rows:
        e = ic.get(f"{x['sura']}:{x['verse']}")
        if e:
            x["text"] = guten[(x["sura"], x["verse"])] if e["text"] == "GUTENBERG" else e["text"]
            x["verdict"], x["image_check"] = "image-checked", {"pdf_pages": e["pdf_pages"], "note": e["note"]}
    verdicts = Counter(x["verdict"] for x in rows)
    report["verdicts"] = {k: v for k, v in verdicts.items() if v}
    report["image_checked"] = len(ic)
    # --- numbering map: the number printed in the 1930 book for each standard verse (majority over the scans)
    printed: dict[str, Counter] = {}
    for sc in report["scans"].values():
        for ref, n in sc["numbering"].items():
            printed.setdefault(ref, Counter())[n] += 1
    numbering = {ref: c.most_common(1)[0][0] for ref, c in printed.items()}
    offsets: dict[int, Counter] = {}
    for ref, n in numbering.items():
        su, v = map(int, ref.split(":"))
        offsets.setdefault(su, Counter())[n - v] += 1
    sura_offsets = {su: dict(c.most_common()) for su, c in sorted(offsets.items())}
    (OUT / "pickthall-numbering-map.json").write_text(json.dumps({"printed_number_by_standard_verse": numbering, "offset_counts_by_sura": sura_offsets,
                                                               "note": "offset = number printed in the 1930 book minus the standard verse number"}, indent=0) + "\n", encoding="utf-8")
    # --- review queue: undecided verses, and agreed verses whose text looks contaminated (very long or very short against Gutenberg)
    review = []
    for x in rows:
        ref = (x["sura"], x["verse"])
        glen, tlen = len(pr.key(guten[ref])), len(pr.key(x["text"]))
        why = None
        if x["verdict"] in ("split", "single", "missing"):
            why = x["verdict"]
        elif x["verdict"] in ("confirmed-by-alignment", "pair-with-gutenberg", "words-confirmed", "image-checked"):
            why = None
        elif tlen > glen * 1.35 + 25:
            why = "text much longer than Gutenberg (page furniture or a footnote may have leaked in)"
        elif glen > 20 and tlen < glen * 0.6:
            why = "text much shorter than Gutenberg (a boundary may be misplaced)"
        if why:
            x["review"] = why
            review.append({"ref": f"{ref[0]}:{ref[1]}", "why": why, "chosen_text": x["text"], "gutenberg": guten[ref], "readings": x["readings"]})
    (OUT / "pickthall-1930-review-queue.json").write_text(json.dumps(review, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    report["review_queue"] = len(review)
    report["review_reasons"] = dict(Counter(r["why"].split(" (")[0] for r in review))
    # --- Markdown layer
    mdroot = ROOT_DIR / "data" / "processed" / "markdown" / "english-quran-pickthall-1930"
    mdroot.mkdir(parents=True, exist_ok=True)
    by_sura: dict[int, list[dict]] = {}
    for x in rows:
        by_sura.setdefault(x["sura"], []).append(x)
    for su, vs in by_sura.items():
        lines = ["---", f"source_id: \"english-quran-pickthall-1930\"", f"sura: {su}", "language: \"English\"",
                 "status: \"reconstructed from the OCR of four scans of the 1930 book by vote; not proofread; see the verse comments\"",
                 "numbering: \"standard verse numbers (the 1930 book prints some verses under other numbers; see pickthall-numbering-map.json)\"", "---", "", f"# Sura {su}", ""]
        for x in vs:
            flag = x.get("review") or x["verdict"]
            lines += [f"<!-- verdict: {x['verdict']}; scans identical: {x['identical']} of {x['scans_with_verse']}" + (f"; REVIEW: {x['review']}" if x.get("review") else "") + " -->", f"**{x['verse']}** {x['text']}", ""]
        (mdroot / f"{su:03d}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (mdroot / "INDEX.md").write_text("# Pickthall 1930, reconstructed by vote\n\nOne file per sura. Built by scripts/pickthall_build.py from the OCR of four scans of the 1930 edition. "
                                     "Verses carry a verdict comment (agreed, pair, split, single, missing) and a REVIEW note where the text may be contaminated. Not proofread.\n", encoding="utf-8")
    (OUT / "pickthall-1930-built.json").write_text(json.dumps(rows, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    (OUT / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "scans"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
