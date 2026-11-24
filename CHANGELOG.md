# Changelog

All notable changes are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/) once there is a released package or dataset.

## [Unreleased]

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
