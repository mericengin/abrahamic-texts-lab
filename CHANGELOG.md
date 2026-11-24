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

### Found
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
