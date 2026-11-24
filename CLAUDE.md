# CLAUDE.md

Guidance for Claude Code (and any AI coding assistant) working in this repository. Read it fully before making changes. Humans: it doubles as a summary of our working rules.

## Project summary

Abrahamic Texts Lab is a free, non-profit research workspace and public web app for exploring the Abrahamic texts computationally: Hebrew Bible, New Testament, Qur'an, Dead Sea Scrolls, Apocrypha and Pseudepigrapha, and Gnostic writings. It is also intended to support an academic submission in computational humanities. The scope and definition are in [docs/scope.md](docs/scope.md); the nine research directions (R1 to R9) are in [docs/research-questions.md](docs/research-questions.md) and tracked in [ROADMAP.md](ROADMAP.md).

**Phases.** Goals are delivered in two phases and Phase 2 extends every Phase 1 goal (nothing is dropped). **Phase 1:** all nine directions implemented and working on the three canons (Hebrew Bible, New Testament, Qur'an) in the original language, English and German. **Phase 2:** all nine across the full corpus (Dead Sea Scrolls, Apocrypha and Pseudepigrapha, Nag Hammadi and Gnostic texts, Syriac and Ge'ez optional). Do not start Phase 2 work until Phase 1 is complete, unless the owner says otherwise. Every source in `data/sources.toml` carries a `phase`.

**Current state:** setup stage. The repo contains docs, a source manifest, a fetch script and manifest tests. No texts have been downloaded and no analysis exists. Never imply otherwise in code, docs, results or the UI. Do not build features from a later milestone unless asked.

## Hard rules (never violate)

1. **Never download, fetch or add a text without the owner's approval.** List filenames, sources and sizes first and wait for a clear yes. `scripts/fetch_sources.py` is a dry run unless `--execute` is passed; do not pass it unprompted.
2. **Never commit third-party texts or datasets.** `data/raw/` and `data/processed/` stay git-ignored. Each source keeps its own license; this repo's MIT license covers only our code and original documentation.
3. **Respect each source's license.** Non-commercial data (DSS, Tanzil translations) means the project is never monetized. ShareAlike data (MorphGNT, First1KGreek) means derived data carries the same license. The Tanzil Arabic text must stay verbatim, with its notice, and annotations live in separate layers. See [SOURCES.md](SOURCES.md).
4. **Never mark a source `ready` without checking the primary license page.** Search snippets and aggregators are not enough. Record the exact wording and the date checked. If two sources disagree, record the conflict and keep the source at `verify`.
5. **Do not fabricate results, data, citations or scholarly claims.** If something was not run, say so. Report negative and weak results honestly. Verify a reference exists before citing it.
6. **Descriptive, never evaluative.** Do not rank, praise or disparage any tradition. Describe relationships between texts and the evidence for them. Use neutral terms ("Hebrew Bible", "New Testament", "Qur'an") and avoid loaded language.
7. **Show uncertainty.** Every automated link, date or label carries a confidence or an explicit "unvalidated" flag. Scholarly dates are ranges, not points.
8. **Domain-expert review before claims.** Gold sets, annotations and conclusions about scholarly questions are drafts until a domain expert has reviewed them. Say so in the output.
9. **No secrets.** No API keys, tokens or account IDs in code, configs, notebooks, tests or fixtures. Use environment variables and keep `.env.example` current.
10. **Never incur a cost without asking.** Free resources only: no paid plans, upgrades, overages or paid API use unless the owner approves in writing. Prefer local or free models, cap any usage, and cache results.
11. **No personal data.** Do not put the owner's personal details into requests to outside services, headers, URLs or fixtures.
12. **LLM evaluations need memorization controls** (perturbed verses, obscure or held-out texts, closed-book baselines) before any claim about reasoning (R7 to R9).

## Architecture in one paragraph

Layers: sources (raw, untouched) -> parsers -> a unified corpus with stable identifiers and provenance -> alignments (edition, translation, parallel passage) -> analyses (reuse, stylometry, concept drift, motifs, Coptic tools) -> evaluations (LLM benchmark, RAG) -> precomputed results -> a mostly static web app. Details and the proposed identifier scheme are in [docs/architecture.md](docs/architecture.md). Raw source files are never edited; every transformation is a scripted, reproducible step.

## Repository map

- `data/sources.toml` machine-readable source manifest; `SOURCES.md` the human view (keep them in sync)
- `data/raw/`, `data/processed/` git-ignored build outputs
- `scripts/` tooling (currently `fetch_sources.py`)
- `tests/` unit tests (`python3 -m unittest discover -s tests`)
- `docs/` scope, research questions, architecture, ethics
- `assets/` logo and banner
- `ROADMAP.md`, `CHANGELOG.md`, `CONTRIBUTING.md`

## Tooling and commands

- Python 3.11+. The fetch script and tests use the standard library only. Add dependencies only with a reason, and record significant choices as ADRs in `docs/adr/` (create the folder when the first ADR is written).
- Tests: `python3 -m unittest discover -s tests`
- Dry-run fetch plan: `python3 scripts/fetch_sources.py` (add `--phase 1` or `--phase 2` to filter)
- Markdown copies of downloaded sources: `.venv/bin/python scripts/to_markdown.py` (needs `requirements.txt`). Every download gets a Markdown version next to the original; never trust an OCR output without its quality flag.
- Fetch one source (owner approval required first): `python3 scripts/fetch_sources.py --execute <id>`

If a command does not work, check this file, `README.md` and `ROADMAP.md` rather than guessing, and tell the user what is missing.

## Coding conventions

- Match the surrounding code. Type hints on public functions; docstrings state assumptions (encoding, versification, language, edition).
- **Text handling:** read and write UTF-8; normalize Unicode explicitly and document the form (NFC or NFD). Never silently strip diacritics, vowel points, tashkeel or Coptic supralinear strokes; make any stripping an explicit, named, reversible step. Keep right-to-left text intact.
- **Identifiers:** use the scheme in `docs/architecture.md`. Versification differs between editions (Hebrew and English Bibles, Qur'an numbering); map explicitly, never assume verse numbers match.
- Randomness is seeded and the seed recorded with results.
- Pure functions for analysis where possible; side effects (network, disk) live in a thin ingestion layer.
- Result and schema changes are compatibility changes: bump versions deliberately and keep old outputs readable.
- Keep `CHANGELOG.md`, any package version and the README badge consistent.

## Testing expectations

- Every parser has tests on small hand-made fixtures (not copies of licensed text beyond a few short lines with attribution).
- Alignment and reuse code has tests with hand-computed expected links.
- Metrics (precision, recall, agreement, faithfulness) have unit tests with hand-computed values.
- Network code is tested against mocks, never by downloading in tests.

## Workflow for common tasks

**Adding a source**
1. Read the license on the primary page; quote the key sentences in `data/sources.toml` `notes` and `SOURCES.md`.
2. Add the entry with its `phase` (1 or 2) and status `verify` until the license and URL are both confirmed, then `ready`.
3. Add a parser and tests, then ask the owner before fetching.

**Adding an analysis (R2 to R9)**
1. Write the question, data, method, evaluation plan and limits into `docs/research-questions.md` first.
2. Decide the evaluation before looking at results.
3. Implement, record seeds and data versions, and report limits.
4. Tick the roadmap box only when the deliverable exists and has been checked.

**Changing the identifier scheme or schema**
Treat it as a compatibility change: ask first, write an ADR, and migrate outputs.

## UI work (when it starts)

Keep the app light and readable; precompute results and ship a mostly static site. Every view shows the source, license and uncertainty. The UI must never imply a capability that does not exist. Follow `assets/` for the visual identity (dark card, amber accent `#e8b45a`, sage `#7fc8a9`, periwinkle `#8fa8e8`).

## Definition of done

Tested where practical, documented, licenses respected and recorded, no secrets, no fabricated claims, uncertainty shown, results reproducible from config plus pinned data versions, CHANGELOG updated for user-visible changes, roadmap box ticked only when true.

## When unsure

Ask the user before: downloading anything, publishing or redistributing any text, choosing an English Qur'an translation, deciding the Gospel of Judas approach, using any paid or metered service, naming collaborators or venues, or making any claim about scholarly consensus. State assumptions explicitly instead of silently picking one.

## Reminder

This project does not provide religious, legal or theological guidance. Machine output is a research lead, not a verdict.
