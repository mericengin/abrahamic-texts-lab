# Sources and licenses

Verified 2026-11-24 from each source's own page, except where noted. The machine-readable version is [data/sources.toml](data/sources.toml). This is a record of what the license pages say, not legal advice. Always re-read a license before redistributing.

## Constraints that shape the project

1. **Non-commercial:** the Dead Sea Scrolls data (CC BY-NC 4.0) and Tanzil translations. The project must never be monetized.
2. **ShareAlike:** MorphGNT morphology (CC BY-SA 3.0) and First1KGreek (CC BY-SA 4.0). Derived data must carry the same license.
3. **Verbatim only:** the Tanzil Arabic text may not be changed, and its notice must travel with every copy or derived file. Annotations live in separate layers.

Third-party texts are not committed to this repository. `scripts/fetch_sources.py` fetches them from the original source.

What is actually on disk, with file sizes, checksums and check results, is listed in [docs/data-inventory.md](docs/data-inventory.md), which a script generates from the provenance records.

## Status key

`ready` = checked and safe to fetch. `verify` = a detail is unconfirmed. `manual` = needs a human step. `blocked` = no usable open source.

## Phase 1: the three canons (original, English, German)

| ID | Text | Language | License | Status |
|---|---|---|---|---|
| hebrew-morphhb | [Open Scriptures Hebrew Bible](https://github.com/openscriptures/morphhb) | Biblical Hebrew | CC BY 4.0 (WLC text public domain) | ready, downloaded |
| greek-morphgnt | [MorphGNT SBLGNT](https://github.com/morphgnt/sblgnt) | Koine Greek | CC BY-SA 3.0 (morphology) | ready, downloaded |
| greek-sblgnt-text | [SBLGNT, Faithlife](https://github.com/Faithlife/SBLGNT) | Koine Greek | CC BY 4.0 (full legal code in the holders' own repository; conflict with MorphGNT's older EULA note resolved) | ready, downloaded |
| quran-tanzil-arabic | [Tanzil Quran text](https://tanzil.net/docs/text_license) | Classical Arabic | verbatim copies only, attribution and link required (terms accepted on the owner's instruction, 2026-11-24) | ready, downloaded |
| english-web-deutero | [WEB Classic with Deuterocanon](https://ebible.org/find/details.php?id=eng-web) | English (Hebrew Bible and New Testament; Deuterocanon is Phase 2) | Public domain | ready, downloaded |
| german-luther-1912 | [Luther 1912](https://ebible.org/bible/details.php?id=deu1912) | German (Hebrew Bible and New Testament) | Public domain (eBible details page, read 2026-11-24) | ready, downloaded |
| english-quran-pickthall | [Pickthall 1930](https://commons.wikimedia.org/wiki/File:The_Meaning_of_the_Glorious_Koran_(1930).pdf) (scan, OCR needed) | English | Public domain per Commons and Wikisource, unverified independently | verify |
| german-quran-henning | [Henning 1901 scan](https://archive.org/details/derkoran00henn) (OCR text available) | German | Translation public domain by author-death rule; scan has no rights metadata | verify |
| german-quran-henning-typed | [Henning, typed (projekt-gutenberg.org)](https://projekt-gutenberg.org/authors/max-henning/books/der-koran/) | German | Site: 'gemeinfrei' but 'privaten Gebrauch' only, no redistribution (Impressum, read 2026-11-24). LOCAL COMPARISON ONLY, never published | manual |
| septuagint-first1k | [First1KGreek tlg0527](https://github.com/OpenGreekAndLatin/First1KGreek) | Koine Greek (optional layer) | CC BY-SA 4.0 (repo level) | verify |
| coptic-ud | [UD Coptic-Scriptorium](https://github.com/UniversalDependencies/UD_Coptic-Scriptorium) | Coptic (R3 biblical slice) | CC BY 4.0 | ready |

## Phase 2: the full corpus

| ID | Text | Language | License | Status |
|---|---|---|---|---|
| dss-etcbc | [ETCBC Dead Sea Scrolls](https://github.com/ETCBC/dss) | Hebrew / Aramaic | CC BY-NC 4.0 | ready |
| coptic-scriptorium | [Coptic SCRIPTORIUM](https://github.com/CopticScriptorium/corpora) (Thomas, Pistis Sophia, Mysteries of John) | Coptic | CC BY 3.0/4.0 default | ready |
| enoch-charles | [Book of Enoch, Charles](https://www.gutenberg.org/ebooks/77935) | English | Public domain (US) | verify |
| jubilees-charles | [Book of Jubilees, Charles](https://sacred-texts.com/bib/jub/) | English | Public domain | verify |
| gospel-of-judas | none yet | Coptic / English | unresolved | blocked |

Phase 2 also needs sources not yet in the manifest: English translations for Nag Hammadi (the [Other Gospels](https://othergospels.com/about/) public-domain translations, to verify text by text), Mead's Pistis Sophia, German layers where open ones exist (Kautzsch 1900 for Enoch, a working translation of Thomas, Schmidt 1905 for Pistis Sophia), and Syriac and Ge'ez sources.

## Known gaps

- **Gospel of Judas:** no open Coptic edition found. The one free English text found names no translator and sits on a site with an "all rights reserved" footer. Resolve by asking for permission, transcribing from published images, or deferring.
- **Nag Hammadi:** only the Gospel of Thomas and Pistis Sophia exist in the open Coptic corpus. Pistis Sophia is not a Nag Hammadi text. Robinson's and Meyer's English translations are copyrighted.
- **OCR quality (Phase 1 Qur'an scans):** the Pickthall 1930 OCR is good but its PDF is image-only. The archive's Henning OCR and PDF text layer were unusable (Fraktur read as ordinary type), so the book was re-OCRed page by page with a Fraktur model (good quality, still unproofread). The Project Gutenberg #16955 Pickthall lines differ from the 1930 text in places and serve only as a scaffold.
- **Qur'an translations (Phase 1):** Tanzil translations are non-commercial and not bundled. Chosen layers (confirmed by the owner 2026-11-24): **Pickthall 1930** (English) and **Henning** (German). The English layer is rebuilt from the 1930 scans; the Project Gutenberg #16955 "Pickthall" lines are NOT the 1930 text (see [docs/data-verification.md](docs/data-verification.md)). Neither exists as a clean, redistributable machine-readable text, so both need OCR from public-domain scans and proofreading. Do not use the Projekt Gutenberg-DE copy of Henning (private use only, 1970 edition with editorial glosses), Tanzil's Pickthall file (non-commercial, no redistribution) or the Wikisource Pickthall transcription (unproofread, incomplete, CC BY-SA). Yusuf Ali is avoided because its US copyright status is disputed.
- **Septuagint:** the Rahlfs text is avoided because of a reported TLG-derived license. Swete's edition in First1KGreek is unconfirmed.
- **Sahidica New Testament:** carries a special license that has not been read. Excluded.
- **Not yet researched:** Syriac (Peshitta), Greek and Hebrew Apocrypha originals.

## Attribution (fill in as sources are used)

Credit lines for each source are in the `attribution` field of `data/sources.toml` and are copied into `data/raw/<id>/MANIFEST.json` on fetch.
