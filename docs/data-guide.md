# Data guide (Phase 1 texts)

Where every Phase 1 version lives on the owner's machine, as raw data, as a PDF and as Markdown. Third-party texts are **not in the git repository** (each has its own license); they sit under `data/`, which is git-ignored. Counts, sizes and checksums are in [data-inventory.md](data-inventory.md), generated from the provenance records.

Folders under `data/`: `raw/<source-id>/` is exactly what was downloaded (plus `MANIFEST.json` with URL, time, license and checksum); `processed/markdown/<source-id>/` has the Markdown; `processed/pdf/<source-id>/` has generated PDFs; `processed/ocr/<source-id>/` has page-by-page OCR output.

## One row per text and language

| Text | Language | Raw data | PDF | Markdown (`data/processed/markdown/`) |
|---|---|---|---|---|
| Hebrew Bible | Biblical Hebrew (Westminster Leningrad Codex) | `hebrew-morphhb/wlc/*.xml` (OSIS, with lemma and morphology) | generated: `processed/pdf/hebrew-morphhb/hebrew-wlc.pdf` | `hebrew-morphhb/hebrew-wlc/` (39 books, one file each) |
| Hebrew Bible | English (World English Bible) | `english-web-deutero/eng-web_usfx.zip` | official: `raw/english-web-deutero/eng-web_all.pdf` | `english-web-deutero/english-web/` (per book) and `eng-web_all.pdf.md` (per page of the PDF) |
| Hebrew Bible | German (Luther 1912) | `german-luther-1912/deu1912_usfx.zip` | official: `raw/german-luther-1912/deu1912_all.pdf` | `german-luther-1912/german-luther/` (per book) and `deu1912_all.pdf.md` |
| New Testament | Koine Greek (SBLGNT) | `greek-sblgnt-text/data/sblgnt/` (text and XML) and `greek-morphgnt/` (lemma and parsing) | generated: `processed/pdf/greek-sblgnt-text/greek-sblgnt.pdf` | `greek-sblgnt-text/greek-sblgnt/` and `greek-morphgnt/greek-morphgnt/` (27 books each) |
| New Testament | English (WEB) | same files as the Hebrew Bible English row | same official PDF | same Markdown folder |
| New Testament | German (Luther 1912) | same files as the Hebrew Bible German row | same official PDF | same Markdown folder |
| Qur'an | Classical Arabic (Tanzil Uthmani, v1.1) | `quran-tanzil-arabic/quran-uthmani.xml`, `quran-uthmani.txt`, `quran-simple-clean.txt` | generated: `processed/pdf/quran-tanzil-arabic/quran-uthmani-xml.pdf` | `quran-tanzil-arabic/quran-uthmani-xml/` (114 suras), plus `quran-uthmani-txt/` and `quran-simple-clean-txt/` |
| Qur'an | English (Pickthall, 1930) | `english-quran-pickthall/` (scan PDF and the archive's OCR text) and `english-quran-pickthall-gutenberg/16955.txt` | the scan: `raw/english-quran-pickthall/2015.216140.The-Meaning.pdf` (images only) | `english-quran-pickthall/…_djvu.txt.md` (the book's text) and `english-quran-pickthall-gutenberg/pickthall-only.md` (see caution below) |
| Qur'an | German (Henning) | `german-quran-henning/derkoran00henn.pdf` (scan) | the scan: `raw/german-quran-henning/derkoran00henn.pdf` | `german-quran-henning/…-fraktur-ocr-raw.md` and `…-fraktur-ocr-normalized.md` (page by page, machine OCR) |

Greek note: MorphGNT's Markdown has only the text column; lemma and parsing stay in the raw files. MorphGNT 6.12 lacks John 7:53 to 8:11 (12 verses, added to the SBLGNT in 2023), so it has 7,927 verses against the SBLGNT's 7,939; the SBLGNT is the Greek text layer. The WEB also contains the Apocrypha/Deuterocanon (15 books), which is Phase 2 material; those books are in the WEB Markdown folder and flagged in the files' metadata.

## What the Markdown contains

- One file per book (per sura for the Qur'an), a front-matter header (source, license, credit line, checksum or commit, retrieval time) and one line per verse as `**verse** text`, with `## Chapter N` headings. An `INDEX.md` lists the files and verse counts.
- The words are unchanged. Markup is removed: footnotes, cross references, headings and Strong's tags in the USFX Bibles; the `/` morpheme markers in the Hebrew OSIS (they are annotation, not text). Hebrew: where a word is a ketiv, the qere is added in square brackets after it; margin notes of other kinds are skipped (counts in the conversion report).
- Every version is read back after writing and compared verse by verse with the parsed source; the result is in `CONVERSION.json` (`markdown_roundtrip`).
- Tanzil files carry the Tanzil copyright notice, as its terms require.

## What the PDFs are

- **Official PDFs** (WEB, Luther 1912, and the two scans) are used exactly as downloaded.
- **Generated PDFs** (Hebrew, Greek, Arabic) are plain reading copies made from the parsed text with Google Chrome. They say on the title page that they are not official editions, and the words are unchanged. Hebrew, Greek and Arabic render with their vowel and recitation marks, right to left where needed (checked on sample pages).

## Cautions

- **Pickthall (English).** The Project Gutenberg #16955 "Pickthall" lines turned out NOT to be the 1930 text: they differ in wording in about one verse in eight (for example 2:57 "We wronged them not" in all four scans against "they wronged Us not"; 1930 "Mecca" and "stedfast" against "Makka" and "steadfast"). The English layer is therefore rebuilt from the OCR of four scans of the 1930 book (`english-quran-pickthall-1930/`), decided by vote: 96% of verses have two or more identical scan readings, and 251 verses are queued for a check against the page images. The scan PDF itself has no text layer.
- **Verse numbering differs between layers.** Hebrew numbering differs from English numbering in places, the 1930 Pickthall scan numbers verses by its own count, and Henning has its own count too. Mapping them to one scheme is part of the corpus milestone (R1).
- **Henning (German), best layer: `german-quran-henning-fraktur-ocr-normalized-latf.md`** (second OCR run with the `deu_latf` and `Fraktur` models together, then a logged repair step that uses Luther's 1912 German as a word list). Measured against my own transcription of two page images (about 580 words) it has about 1.5% word errors and 0.56% character errors; the first run's layers are kept for comparison. It is complete but unproofread, so it is good for reading and search and not yet for quotation.
- **Henning (German), earlier notes.** The archive's own OCR was unusable (Fraktur read as ordinary type). The page-by-page Fraktur OCR here (Tesseract 5.5.3, Fraktur model, 300 dpi) is far better, at 280 common German words per 1000 raw and 329 normalized (the archive's was 46; normal German is about 250 to 350), but it is still machine output: unproofread, with residual slips. The front matter shows this is Henning's own text with a foreword signed 1901 and no later editor's introduction; the printing date is not stated. The "raw" layer is the OCR unchanged; the "normalized" layer writes the long s (ſ) as s and applies logged single-letter repairs. See `CORRECTIONS.json`.
