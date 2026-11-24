# Changelog

All notable changes are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/) once there is a released package or dataset.

## [Unreleased]

### Added
- `scripts/to_markdown.py`: writes a Markdown copy of every downloaded source next to the original (local, git-ignored), with provenance front matter, per-page headings for PDFs, an OCR-quality flag, and lossless checks. Also writes a Pickthall-only extraction from the Gutenberg text with verse-count checks and a log of repaired ids. Tests in `tests/test_to_markdown.py`.
- `--allow-unverified` for `fetch_sources.py` (only for explicitly named sources) and multi-file sources (`files` list) in the manifest.
- `requirements.txt` (pdfminer.six, optional, for PDF text).
- First downloads (owner-approved 2026-11-24): Pickthall 1930 scan (PDF and OCR text), Project Gutenberg #16955 text, and the Henning scan (PDF and OCR text), all from the Internet Archive.

- `scripts/canon.py`, `scripts/make_pdfs.py`, `scripts/ocr_pdf.py`, `scripts/ocr_to_markdown.py`, `scripts/data_report.py` and `docs/data-inventory.md`: parsers for OSIS, MorphGNT, SBLGNT, USFX and Tanzil text; per-book Markdown with a read-back check; generated reading PDFs (Chrome) for Hebrew, Greek and Arabic; Fraktur OCR (Tesseract) with provenance; and an inventory report. Tests in `tests/test_canon.py`.
- Downloaded the rest of the Phase 1 canon sources (2026-11-24): Hebrew WLC (OSIS), SBLGNT and MorphGNT, World English Bible (USFX and official PDF), Luther 1912 (USFX and official PDF), and Tanzil Uthmani and Simple Clean text.

### Changed
- SBLGNT text marked `ready` (CC BY 4.0 in the holders' own repository); Luther 1912 marked `ready` (eBible details page reads Public Domain).

- Fresh Fraktur OCR of all 622 Henning pages (Tesseract 5.5.3, Fraktur model), as raw and normalized Markdown with a log of 3,315 repairs; quality 280 (raw) and 329 (normalized) common German words per 1000, against 46 for the archive's OCR.

- Verification suite (`scripts/verify.py`, `scripts/verify_report.py`, `docs/data-verification.md`): independent word-for-word checks of every layer against the raw files and against second sources, plus a trust status per layer. Hebrew, Greek, WEB, Luther and Arabic pass.
- Verse mapping tables (`scripts/alignment.py`): Hebrew to English to German, Greek to English and German, and Qur'an standard numbering to the 1930 Pickthall numbering.
- Pickthall 1930 rebuilt from the OCR of four scans (`scripts/pickthall_reconcile.py`, `scripts/pickthall_build.py`); verification-only source `english-quran-pickthall-xcheck` (three more scans, text files only).

- Second Henning OCR run (`deu_latf` + `Fraktur` models) and a repair step using Luther 1912 vocabulary; `scripts/ocr_pdf.py --tag` and `scripts/ocr_to_markdown.py <id> <tag>` keep runs side by side. Measured on two page images: 1.5% word errors (first run 7.6% as read).

- Page-by-page English OCR of the 1930 scan (`ocr_pdf.py --lang eng`) and `scripts/pickthall_pages.py` to find each verse's page; the 38 hardest verses were read against the page images and recorded in a local `image-checks.json` that the build applies first.

- `scripts/pickthall_pageocr_check.py` and clean-up passes in `pickthall_build.py` (page furniture, broken hyphens, isolated OCR slips repaired from the fresh page OCR and the Gutenberg token).

- Completeness pass in `pickthall_build.py`: verses that run across a page break had lost their continuation (a bug in my first rebuild that also affected the Gutenberg text); the build now finds the verse in the fresh page OCR and appends the missing words when a page header marks the break or the sentence is plainly unfinished; narrower footnote removal; recorded text fixes (`text-fixes.json`).

- 12 more vote-only Pickthall verses read against the page images (the image-checks file now has 51 entries) and about 30 recorded cosmetic fixes (`text-fixes.json`); the review queue is empty.
- 29 more Pickthall verses read against the page images (image-checks now 80 entries): fixed stray footnote marks and dash artifacts (24:4, 37:62, 71:23, 38:48, 30:58 and 11 em-dash joins). Then 5 more (4:46, 4:127, 20:46, 34:15, 100:4) fixed against the page images (image-checks now 91; 6 more read: 11:42 lost dashes, 14:31 stray comma, 10:12 missing bracket repaired): footnote text and a page header that had leaked into verses (4:127, 10:12), lost words, and all 23 stray `^` footnote marks removed. Still open: 88 verses rest on a vote only (all 88 confirmed by fresh OCR, not by eye).
- Henning German Qur'an: `scripts/henning_proofread.py` repairs lost `ch` ligatures, `ß` read for `tz`/`ss`/`ch`, `b` read for `h`, `>` read for `ck`, and `3` read for `s`, only when exactly one repaired spelling is a known word; every repair is logged (local `CORRECTIONS-pass2.json`, 973 repairs). Measured on three hand-transcribed pages (new fixture page 450): 1.8% to 1.1% word errors. Rules were tuned on those pages, so the true rate is probably 1 to 2%. Not yet proofread by a person across the book.
- Henning: pages with the most unusual words were read against their images and corrected through a local `manual-fixes.json` (applied by `henning_proofread.py`, which reports any old text it cannot find); new automatic rules for `scch`/`cch`, `fh` for `sch`, `kf`, initial N/R, `an`/`en` read for `au`/`eu` and `fi` for `st`. Errors on these pages were about 3 to 6 per page.
- Henning: seeded random sample of 10 body pages (seed 20261124) read against the images: 34 word errors in 2,619 words, 1.3% (the honest estimate for the whole book, within the limits of counting by eye). The sample's pages were then corrected, and the rules gained `ce`/`ud`/`üd`/`cs` for lost `ck` and a relaxed `ß` rule.
- Henning's own verse numbers read from the text (`scripts/henning_numbering.py`, 114 suras found) and mapped to the standard numbering (`scripts/henning_align.py`, `alignment.py` writes it into `quran.json`): 99 suras have the same highest number as the standard, 14 differ by one or two verses (Henning follows a different division); 12 of those were checked by reading the German against the English at the place the length estimate pointed to (for example sura 8 splits standard verse 36, sura 45 joins verses 1 and 2), suras 71 and 74 mix splits and merges and are unresolved, sura 1 is unnumbered. 6,092 of 6,236 verses are mapped. Length alignment alone was too noisy to trust (it proposed spurious changes in suras with matching numbers), so it is used only to find candidate places. Draft for an expert; tests in `tests/test_henning_align.py`.
- Typed Henning found (projekt-gutenberg.org, 114 pages, downloaded 2026-11-24 with the owner's approval) and kept as a local comparison source only, because its site allows private use only. `scripts/henning_typed_compare.py` compares it with our OCR: wording agrees (mean similarity 0.966 over 5,192 verses), highest verse numbers equal in 102 of 114 suras, and its bracketed standard numbers can settle the verse mapping. Its source is a 1970 printing, whose verse division differs from our 1901 scan in at least sura 101, so the numbers are used as evidence, not copied.

### Found
- Reading the vote-only verses found real errors in the vote (2:259, 5:3, 9:110/9:111, 73:20, 6:93); vote-only text is the least reliable group.
- Gutenberg's Pickthall text is cut short in places (8:72, 2:85) and has words the 1930 book lacks or lacks words it has (20:109); the 1930 print itself has a misprint at 5:89.
- **The Project Gutenberg #16955 "Pickthall" is not the 1930 text** (593 verses differ where three or more scans agree), so it is no longer used.
- Henning's archive OCR and PDF text layer are unusable (Fraktur misread). A Fraktur OCR is needed.
- The Pickthall PDF is image-only; its OCR text is good.
- The Gutenberg #16955 Pickthall lines differ from the 1930 text in places, so they are used only as a scaffold and cross-check.

### Changed
- Phase 1 Qur'an layers confirmed by the owner (2026-11-24): Pickthall 1930 (English) and Henning 1901 (German), both public-domain translations that need OCR from scans. Replaced the blocked placeholder `english-quran` with `english-quran-pickthall` and rewrote the Henning entry, with the sources and layers to avoid recorded in `SOURCES.md` and the ethics doc.

## [0.0.2] - 2026-11-24

Planning release. Still no texts downloaded and no analysis run.

### Added
- Two-phase plan: Phase 1 delivers all nine research directions on the three canons (Hebrew Bible, New Testament, Qur'an) in the original language, English and German; Phase 2 extends all nine to the full corpus. See `ROADMAP.md`, `docs/scope.md` and `docs/research-questions.md`.
- `phase` field on every source in `data/sources.toml`, a `--phase` filter in `scripts/fetch_sources.py`, and a manifest test for it.
- Two Phase 1 sources: an English Qur'an translation (blocked until chosen) and the Henning 1901 German Qur'an (verify).
- Phase 1 and Phase 2 scope for each research direction.

### Changed
- Roadmap restructured from milestones M0 to M6 into Phase 0, Phase 1 and Phase 2. No goal was removed.
- Spine question widened to name Phase 2 Gnostic and Second Temple texts explicitly.

## [0.0.1] - 2026-11-24

Setup release. No texts downloaded, no analysis run.

### Added
- Repository with MIT license for code and original documentation, and a `.gitignore` that keeps third-party texts out of git.
- Source manifest (`data/sources.toml`) and `SOURCES.md` covering 13 candidate sources, with licenses checked against primary pages and a status for each.
- `scripts/fetch_sources.py`: dry-run by default, fetches only `ready` sources, records URL, time, license and checksum or commit.
- Manifest sanity tests (`tests/test_manifest.py`).
- Documentation: README, ROADMAP, CLAUDE.md, CONTRIBUTING, and `docs/` (scope, research questions, architecture, licensing and ethics).
- Logo and banner (`assets/`).

### Known gaps
- No clean open source yet for the Gospel of Judas.
- Several sources are marked `verify` (SBLGNT text, Luther 1912, Enoch, Jubilees, Septuagint).
