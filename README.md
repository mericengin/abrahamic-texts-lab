# Abrahamic Texts Lab

A free, non-profit research resource for exploring the texts of the Abrahamic traditions computationally: the Hebrew Bible, the New Testament, the Qur'an, the Dead Sea Scrolls, the Apocrypha and Pseudepigrapha, and Gnostic writings (Nag Hammadi and related). It is meant for anyone curious, and as the basis for an academic submission in computational humanities.

**Status: setup only.** The repository holds the plan, the source manifest and the fetch tooling. No texts have been downloaded yet, and no analysis exists yet.

## Principles

- **Descriptive, not evaluative.** The project describes how texts relate and are used. It never ranks or judges any tradition.
- **Open and non-commercial.** Free to use, never monetized. Several sources (the Dead Sea Scrolls data, Tanzil translations) allow non-commercial use only.
- **Provenance everywhere.** Every text records its source, license, retrieval time and checksum. Every finding records its uncertainty.
- **No fabricated results.** Anything not run is stated as not run. Negative results are reported.
- **Experts validate.** Annotation and gold-set claims need a domain scholar before they are presented as findings.

## Research spine

> How is the Genesis and creation tradition reused and transformed across Jewish, Christian, Gnostic and Qur'anic texts?

The planned components (corpus, reuse detection, Coptic tooling, stylometry, concept tracking, motif mining, a scripture long-context benchmark, an LLM comparison study, and a cited RAG assistant) all orbit this question. See [docs/roadmap.md](docs/roadmap.md).

## Layout

```
data/sources.toml      machine-readable source manifest (license, URL, status)
data/raw/              fetched third-party texts (git-ignored)
SOURCES.md             human-readable source and license table
scripts/fetch_sources.py   dry-run by default; --execute to download
tests/                 manifest sanity checks
docs/roadmap.md        phases and open decisions
```

## Usage

Python 3.11+, standard library only.

```bash
python3 scripts/fetch_sources.py              # dry run: prints the plan, downloads nothing
python3 scripts/fetch_sources.py --execute hebrew-morphhb   # fetch one source
python3 -m unittest discover -s tests         # check the manifest
```

Only sources marked `ready` are fetched. Sources marked `verify`, `manual` or `blocked` are skipped with a reason.

## Licenses

Code and original documentation: MIT (see [LICENSE](LICENSE)). Third-party texts are **not** covered by it and are **not** committed here; each keeps its own license, listed in [SOURCES.md](SOURCES.md). This is not legal advice.
