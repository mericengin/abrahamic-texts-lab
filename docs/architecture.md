# Architecture (proposed)

Everything here is a design, not an implementation. Choices marked **pending** need a decision (and an ADR in `docs/adr/` once decided).

## Pipeline

```
sources (raw, untouched) --> parsers --> unified corpus --> alignments --> analyses --> evaluations --> precomputed results --> web app
         data/raw/            scripts       data/processed/                R2..R6        R7..R9           static JSON            static site
```

Principles:

- **Raw is read-only.** Source files are never edited. Every change is a scripted step.
- **Reproducible.** Each build records the source versions (commit or checksum), parser version, seeds and date.
- **Provenance travels with the data.** Every row keeps its source id, edition and license.
- **Precompute, then publish.** Findings are computed offline and shipped as static data, so hosting is free and results are stable.

## Identifiers (proposed, pending ADR 0001)

Stable, human-readable IDs of the form `<corpus>:<work>.<unit>`:

| Example | Meaning |
|---|---|
| `hb:Gen.1.1` | Hebrew Bible, Genesis 1:1 (Hebrew versification) |
| `nt:Matt.5.3` | New Testament, Matthew 5:3 |
| `qur:2.255` | Qur'an, sura 2, aya 255 (one stated numbering scheme) |
| `dss:1QS.3.13` | Dead Sea Scrolls, 1QS column 3, line 13 |
| `cop:thomas.log.32` | Coptic Gospel of Thomas, logion 32 |
| `lxx:Gen.1.1` | Septuagint, Genesis 1:1 |

Rules: IDs never change once published; versification differences are handled by explicit mapping tables between schemes (for example Hebrew and English verse numbering), never by assuming numbers match.

## Data model (proposed)

| Table | Purpose |
|---|---|
| `source` | One row per fetched source: id, URL, retrieved time, checksum or commit, license, attribution |
| `work` | A text (Genesis, Gospel of Thomas, Sura 2): id, tradition area, language, date range with uncertainty |
| `edition` | A particular text of a work (WLC, SBLGNT, WEB, Luther 1912) tied to a `source` |
| `unit` | A verse, logion or line: stable id, edition, text, normalized text, position |
| `token` | Optional: tokens with lemma and morphology where the source provides them |
| `alignment` | Links between units across editions or translations, with type and confidence |
| `reuse_link` | R2 output: source unit, target unit, type, confidence, method, validated flag |
| `annotation` | Motifs, concepts and labels, with annotator and review status |

**Pending:** SQLite with FTS5 (simple, file-based, free) is the default candidate; Postgres is unnecessary at this scale.

## Text handling

- UTF-8 throughout; the normalization form (NFC or NFD) is decided once and documented.
- Diacritics, Hebrew points and cantillation, Arabic tashkeel and Coptic supralinear strokes are kept in the raw layer. Any stripping is an explicit, named, reversible step that produces a separate normalized field.
- Right-to-left text is stored logically and only reordered at display time.
- The Tanzil Arabic text is kept verbatim with its notice; our annotations are separate tables.

## Analysis layer

Each analysis (R2 to R6) is a module with a config file, a seeded run, a recorded data version and an evaluation script. Outputs are tables plus a metadata record. Nothing publishes a number that was not produced by this tracked pipeline.

## LLM layer (R7 to R9)

- Free or local models by default; any paid API use needs the owner's approval and a cost cap.
- Every evaluation has memorization controls and a pre-written protocol.
- The assistant retrieves over verse-level chunks, must cite verse IDs, and refuses when retrieval does not support an answer.

## Web app (proposed)

- **Mostly static.** Precomputed JSON plus a generated site; a small server only for search and the assistant, if hosted at all.
- **Views:** parallel reader, cross-reference arcs, reuse flow, passage embedding map, stylometry dendrograms, concept-drift views, evaluation heatmaps, assistant. See the README.
- **Every view shows** its source, license and confidence.
- **Visual identity** follows `assets/`: dark card, amber accent `#e8b45a`, sage `#7fc8a9`, periwinkle `#8fa8e8`.
- **Frontend stack: pending.** Candidates are a light framework (Svelte or similar) with D3 for custom diagrams, or plain HTML and JS in the spirit of a small, fast site. Decide before M5, weighing build complexity against interactivity.
- **Accessibility:** keyboard navigation, readable contrast, text alternatives, mobile layouts, and correct handling of mixed left-to-right and right-to-left text.

## Hosting and cost

Free tiers only (static hosting). Large model files and raw sources are not hosted; the build scripts fetch them. Repository size is kept small by not committing third-party data.

## Testing

Unit tests for parsers on tiny hand-made fixtures, alignment tests with hand-computed links, metric tests with hand-computed values, and network code tested with mocks. See `CLAUDE.md`.
