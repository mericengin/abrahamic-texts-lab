# Sources and licenses

Verified 2026-11-24 from each source's own page, except where noted. The machine-readable version is [data/sources.toml](data/sources.toml). This is a record of what the license pages say, not legal advice. Always re-read a license before redistributing.

## Constraints that shape the project

1. **Non-commercial:** the Dead Sea Scrolls data (CC BY-NC 4.0) and Tanzil translations. The project must never be monetized.
2. **ShareAlike:** MorphGNT morphology (CC BY-SA 3.0) and First1KGreek (CC BY-SA 4.0). Derived data must carry the same license.
3. **Verbatim only:** the Tanzil Arabic text may not be changed, and its notice must travel with every copy or derived file. Annotations live in separate layers.

Third-party texts are not committed to this repository. `scripts/fetch_sources.py` fetches them from the original source.

## Status key

`ready` = checked and safe to fetch. `verify` = a detail is unconfirmed. `manual` = needs a human step. `blocked` = no usable open source.

| ID | Text | Language | License | Status |
|---|---|---|---|---|
| hebrew-morphhb | [Open Scriptures Hebrew Bible](https://github.com/openscriptures/morphhb) | Biblical Hebrew | CC BY 4.0 (WLC text public domain) | ready |
| greek-morphgnt | [MorphGNT SBLGNT](https://github.com/morphgnt/sblgnt) | Koine Greek | CC BY-SA 3.0 (morphology) | ready |
| greek-sblgnt-text | [SBLGNT, Faithlife](https://github.com/Faithlife/SBLGNT) | Koine Greek | CC BY 4.0 per README; MorphGNT says EULA applies | verify |
| quran-tanzil-arabic | [Tanzil Quran text](https://tanzil.net/docs/text_license) | Classical Arabic | verbatim copies only, attribution and link required | manual |
| dss-etcbc | [ETCBC Dead Sea Scrolls](https://github.com/ETCBC/dss) | Hebrew / Aramaic | CC BY-NC 4.0 | ready |
| coptic-scriptorium | [Coptic SCRIPTORIUM](https://github.com/CopticScriptorium/corpora) (Thomas, Pistis Sophia, Mysteries of John) | Coptic | CC BY 3.0/4.0 default | ready |
| coptic-ud | [UD Coptic-Scriptorium](https://github.com/UniversalDependencies/UD_Coptic-Scriptorium) | Coptic | CC BY 4.0 | ready |
| english-web-deutero | [WEB Classic with Deuterocanon](https://ebible.org/find/details.php?id=eng-web) | English | Public domain | ready |
| german-luther-1912 | [Luther 1912](https://ebible.org/bible/details.php?id=deu1912) | German | Public domain (not yet opened) | verify |
| enoch-charles | [Book of Enoch, Charles](https://www.gutenberg.org/ebooks/77935) | English | Public domain (US) | verify |
| jubilees-charles | [Book of Jubilees, Charles](https://sacred-texts.com/bib/jub/) | English | Public domain | verify |
| septuagint-first1k | [First1KGreek tlg0527](https://github.com/OpenGreekAndLatin/First1KGreek) | Koine Greek | CC BY-SA 4.0 (repo level) | verify |
| gospel-of-judas | none yet | Coptic / English | unresolved | blocked |

## Known gaps

- **Gospel of Judas:** no open Coptic edition found. The one free English text found names no translator and sits on a site with an "all rights reserved" footer. Resolve by asking for permission, transcribing from published images, or deferring.
- **Nag Hammadi:** only the Gospel of Thomas and Pistis Sophia exist in the open Coptic corpus. Pistis Sophia is not a Nag Hammadi text. Robinson's and Meyer's English translations are copyrighted.
- **Qur'an translations:** Tanzil translations are non-commercial and each belongs to its translator. Not bundled. An English translation with a clear license is still to be found.
- **Septuagint:** the Rahlfs text is avoided because of a reported TLG-derived license. Swete's edition in First1KGreek is unconfirmed.
- **Sahidica New Testament:** carries a special license that has not been read. Excluded.
- **Not yet researched:** Syriac (Peshitta), Greek and Hebrew Apocrypha originals.

## Attribution (fill in as sources are used)

Credit lines for each source are in the `attribution` field of `data/sources.toml` and are copied into `data/raw/<id>/MANIFEST.json` on fetch.
