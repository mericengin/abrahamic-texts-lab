# Plan to fix the English and German Qur'an layers

Status on 2026-11-24. Goal: move layers 8 (English, Pickthall 1930) and 9 (German, Henning 1901) from "ready with flags" to "verified" (see [data-readiness.md](data-readiness.md)). Free resources only; every download needs the owner's approval; no third-party text enters the repo.

## What the source search found (2026-11-24)

| Candidate | What it is | Usable? |
|---|---|---|
| Tanzil `en.pickthall` (tanzil.net/trans/) | A 2010 digital Pickthall text (fixes 14 Sep 2010), txt/xml/sql. The page does not say whether it follows the 1930 text or a revision. Terms: non-commercial only; redistribution not allowed. | As a LOCAL comparison source only. Not publishable, and not assumed independent of the Gutenberg revision. Not yet downloaded. |
| Wikisource, Pickthall 1930 | Scan index of the 1930 book. "To be proofread", "incomplete", pages 195 onward not created. Text CC BY-SA. | No usable proofread text. |
| Quran Archive (1930 reading version) | Pages returned 404/500. | Unverified; retry later. |
| sacred-texts.com, OPUS | 403 / 500. | Unverified. |
| Projekt Gutenberg-DE, Henning (typed) | All 114 suras; Reclam 1970 printing; site allows private use only. | Already downloaded; LOCAL comparison only. |
| Projekt Gutenberg-DE, Rückert | A 2001 Ergon edition, partial (103 chapters, suras 85 to 90 missing). | Not usable (partial, rights unclear). |
| Ullmann (Gutenberg-DE) | No book listed. | Not found. |
| de.wikisource, zeno.org | 404 / unreachable. | Retry later; Wikisource author pages not checked. |
| archive.org Henning, other copies | Only the Toronto scan we already use; a 1996 Reclam copy is lending-restricted. | No gain. |

Conclusion: no public-domain, typed, publishable replacement exists for either layer. The fix is to improve what we publish, using the typed or digital texts as local oracles that point us to errors, and to use page images as the judge.

## English Qur'an (layer 8)

Known problems: 88 vote-only verses never read by eye; shared OCR slips (about 0.5 to 1.5% of verses); lost diacritics; about 29 verses without final punctuation; unreviewed numbering map.

1. Read the 88 vote-only verses against the page images. Effort: about 88 page views. Gain: every verse has either agreement or an eye on the page.
2. Local oracle (needs approval to download the small Tanzil file): compare it with our layer verse by verse. Every difference becomes a candidate; each candidate is judged on the page image, never by the oracle. Expected: finds most remaining shared slips for little reading, and measures the slip rate over all 6,236 verses.
3. Residual-defect scanners (free, automatic): unmatched quotes and brackets, doubled or missing spaces, stray digits and symbols, odd capitalization ("allah"), words not in a lexicon, the 29 dangling endings, verses far longer or shorter than the Arabic would suggest. Each hit is checked on the page.
4. Random stratified sample of agreed verses (about 400, seeded) read against the page images to put a measured, bounded slip rate on the layer (about 1% expected; 400 verses gives a margin of about 1 point).
5. Diacritics of transliterated names: decide with the owner whether to restore them from the page images (low value, high effort) or document the loss. Default: document.
6. Numbering map: have a domain expert confirm the 483 differing verse numbers. Expert review of the whole layer.
Done when: no verse rests on a vote only without a page-image check, the measured slip rate is published with its margin, scanners return zero unexplained hits, and an expert has reviewed it.

## German Qur'an (layer 9)

Known problems: 1.3 to 2% word errors (letter-pair slips from Fraktur type, one-letter confusions), 86 unread verse numbers, mangled footnote marks and headings, an unreviewed verse mapping, only 20 of 622 pages read.

1. Oracle-guided page review (free): from the typed-text alignment, count OCR-type differences per page and read the pages in order of difficulty against the images (about 60 pages remove roughly half the errors, if errors cluster as the earlier ranking suggested). Fix through the local `manual-fixes.json`.
2. More automatic rules from the logged residual errors (each rule must pass the exclusion-list check and be measured against the typed text and the random sample, not only against the pages it came from).
3. Unread verse numbers: fill the 86 gaps from the typed alignment where the editions agree, check the rest on the page.
4. Headings and footnotes: re-read sura headings and footnote blocks, which the OCR mangles, in a separate pass (114 headings).
5. Re-measure against the typed text and a fresh seeded random sample of 10 pages by eye after each round; report the numbers.
6. Verse mapping: expert review. Resolve sura 101, where the 1901 scan and the typed 1970 edition divide verses differently, by reading the scan.
7. Optional: a second OCR engine reading of the same scan (free, local) to vote with the first, as for Pickthall.
Done when: the measured error rate is below 0.5% on a fresh sample, headings and numbers are complete, and the mapping is expert-reviewed.

## Order and decisions for the owner

1. Approve downloading the small Tanzil `en.pickthall` file (local comparison only). 2. Approve the read-through of the 88 English vote-only verses. 3. Approve the oracle-guided German page review (about 60 pages first).
Parallel: retry the failed sources (quran-archive.org, zeno.org, Wikisource author pages) in a later session.
