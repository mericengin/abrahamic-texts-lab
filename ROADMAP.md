# Roadmap

Current state: **Phase 0 (setup) is complete. Next: Phase 1.**

How to read this file: a box is ticked only when the work exists in the repository and has been checked. Estimates are rough, solo-scale guesses, not commitments. Nothing is promised for a date.

## The two phases

The project keeps one set of goals: nine research directions (R1 to R9) and the public web app. They are delivered in two phases, so everything is built and proven on well-resourced texts before moving to the harder, more fragmentary ones.

| | Phase 1: the three canons | Phase 2: the full corpus |
|---|---|---|
| **Texts** | Hebrew Bible, New Testament, Qur'an | Phase 1 texts plus the Dead Sea Scrolls, the Apocrypha and Pseudepigrapha, Nag Hammadi and other Gnostic texts (including the Gospel of Judas if its source is resolved), and optionally Syriac and Ge'ez |
| **Languages** | Original (Biblical Hebrew, Koine Greek, Classical Arabic), English and German, so three layers per text | Phase 1 languages plus Coptic (Sahidic), Aramaic, and optionally Syriac and Ge'ez |
| **Why this order** | Clean licenses, three complete language layers, huge reference literature, and the original sources are already identified | Denser, more fragmentary and harder to source; built on a pipeline already proven in Phase 1 |
| **Done means** | **All nine directions (R1 to R9) implemented and working on the three canons, with the web app presenting every finding** | **All nine directions implemented and working across everything discussed, including the Phase 2 texts** |
| **Release** | v1.0.0 | v2.0.0 |

Phase 2 does not replace or shrink any Phase 1 goal. It extends each direction to the full corpus. Phase 2 work does not start until Phase 1 is complete, unless the owner decides otherwise.

The spine question is the same in both phases, with its reach widening:

> How is the Genesis and creation tradition reused and transformed across Jewish, Christian, Qur'anic and (in Phase 2) Gnostic and Second Temple texts?

Per-direction scope for each phase is in [docs/research-questions.md](docs/research-questions.md).

## Research directions at a glance

A direction is ticked only when all of its deliverables in the milestones below are ticked and checked.

**Phase 1**
- [ ] R1 corpus (three canons)
- [ ] R2 parallel passages
- [ ] R3 Coptic tooling (biblical slice)
- [ ] R4 stylometry
- [ ] R5 concept evolution
- [ ] R6 theme and motif mining
- [ ] R7 long-context benchmark
- [ ] R8 LLM study
- [ ] R9 RAG assistant
- [ ] **Phase 1 complete (all nine, working, shown in the web app)**

**Phase 2**
- [ ] R1 corpus (full)
- [ ] R2 parallel passages (full)
- [ ] R3 Coptic and Syriac tooling (Gnostic texts)
- [ ] R4 stylometry (full)
- [ ] R5 concept evolution (full)
- [ ] R6 theme and motif mining (full)
- [ ] R7 long-context benchmark (full)
- [ ] R8 LLM study (full)
- [ ] R9 RAG assistant (full)
- [ ] **Phase 2 complete (all nine, working across everything, shown in the web app)**

---

## Phase 0: Setup (done)

- [x] Repository, MIT license for code, `.gitignore` keeping third-party texts out of git
- [x] Source manifest (`data/sources.toml`) and `SOURCES.md` with licenses checked against primary pages
- [x] Fetch script, dry-run by default, with provenance records and manifest tests
- [x] Project docs: README, roadmap, changelog, CLAUDE.md, scope, research questions, architecture, ethics
- [x] Logo and banner
- [x] Two-phase plan, with a phase on every source and a `--phase` filter in the fetch script

---

# Phase 1: the three canons

Scope: Hebrew Bible, New Testament and Qur'an, each in the original language, English and German.

| Text | Original | English | German |
|---|---|---|---|
| Hebrew Bible | Biblical Hebrew (WLC, morphhb) | WEB | Luther 1912 |
| New Testament | Koine Greek (SBLGNT, MorphGNT) | WEB | Luther 1912 |
| Qur'an | Classical Arabic (Tanzil, verbatim) | Pickthall 1930 (scan, OCR needed) | Henning 1901 (scan, OCR needed) |

Optional extra layer: the Septuagint (Greek Old Testament), useful for R2 because many New Testament quotations follow it. Coptic (UD Coptic-Scriptorium biblical slice) is used for R3.

## P1.1 Corpus foundation (R1)

- [x] Owner approves the downloads (the Qur'an scans on request, then a general go-ahead on 2026-11-24 for all Phase 1 canon files)
- [x] Fetch the Hebrew, Greek, English, German and Arabic sources and the Qur'an scans; check provenance records (sizes, file types, counts)
- [x] Markdown conversion for every downloaded source (`scripts/to_markdown.py`): local, lossless for text, with OCR-quality flags and checks
- [x] Resolve the SBLGNT license conflict (CC BY 4.0 in the holders' own repository) and the Luther 1912 URL and license
- [ ] Resolve the Septuagint edition (confirm Swete or drop the optional layer)
- [x] PDF and Markdown version of every Phase 1 text ([docs/data-guide.md](docs/data-guide.md)); generated PDFs for Hebrew, Greek and Arabic, official PDFs and scans for the rest
- [x] Owner confirms the English Qur'an layer: Pickthall 1930 (confirmed 2026-11-24)
- [x] Obtain the Pickthall scan and its OCR text (downloaded 2026-11-24; the PDF is image-only, the archive OCR is good)
- [ ] Proofread the Pickthall 1930 text against the scan and map its verse numbering (the scan numbers verses differently from the standard count)
- [ ] Compare the Project Gutenberg #16955 Pickthall lines with the 1930 text and log every wording difference (for example 1:4 "Master" versus "Owner")
- [x] Owner confirms the German Qur'an layer: Henning 1901 (confirmed 2026-11-24)
- [x] Obtain the Henning scan (downloaded 2026-11-24)
- [ ] Fraktur OCR of the Henning scan (the archive's OCR is unusable), then confirm the edition and date on its title page, measure quality, proofread, and map verse numbering. Not the Projekt Gutenberg-DE copy (private use only).
- [ ] Decide the stable identifier scheme (ADR 0001)
- [x] Text parsers: OSIS (Hebrew), MorphGNT, SBLGNT, USFX (WEB, Luther), Tanzil (`scripts/canon.py`, tested, read-back checked)
- [ ] Septuagint CTS/EpiDoc parser, if the layer is kept
- [ ] Unified schema and database with per-row provenance and license
- [ ] Versification mappings (Hebrew and English Bible numbering, Qur'an numbering) documented and tested
- [ ] Verse alignment across original, English and German for all three canons
- [ ] Data-quality checks (gaps, duplicates, encoding, versification divergences)
- [ ] Full-text search across all languages
- [ ] Parallel-reader prototype
- [ ] **R1 deliverable:** documented, versioned corpus build with a data card

## P1.2 Reuse and analysis (R2, R4, R5, R6)

- [ ] Baseline reuse detection (lexical and fuzzy matching on aligned text)
- [ ] Cross-lingual retrieval with embeddings
- [ ] Gold set: Hebrew Bible in the New Testament (explicit quotations and allusions), Gospel parallels, the Bible in the Qur'an, from published scholarly sources, reviewed by a domain expert
- [ ] **R2 deliverable:** reuse links with confidence, evaluated against the gold set
- [ ] Stylometry pipeline (Pauline letters in Greek; Qur'an chronological layers in Arabic), compared with scholarly consensus
- [ ] **R4 deliverable:** stylometry report with limits stated (short texts, translation effects, genre)
- [ ] Concept lexicon (spirit, word, light and similar terms across Hebrew, Greek and Arabic) with sense clustering
- [ ] Contextual-embedding comparison across canons, with date ranges not point dates
- [ ] **R5 deliverable:** concept-comparison report
- [ ] Motif annotation scheme (creation, covenant, prophecy, judgment) with expert-validated labels
- [ ] **R6 deliverable:** theme and motif results with inter-annotator agreement

## P1.3 Coptic tooling, biblical slice (R3)

- [ ] Evaluation protocol and baselines on the UD Coptic-Scriptorium treebank (includes Mark, 1 Corinthians, Ruth, Jonah)
- [ ] POS tagging and lemmatization for Coptic
- [ ] Adapt a multilingual model and measure it honestly (small corpus, modest numbers expected)
- [ ] Error analysis by text type
- [ ] **R3 deliverable:** open tools, an evaluation, and a write-up of limits. Gnostic domain adaptation and Syriac are Phase 2.

## P1.4 LLM layer (R7, R8, R9)

- [ ] Memorization controls designed first (perturbed verses, held-out variants, closed-book baselines)
- [ ] Long-context QA and cross-reference tasks built from the aligned corpus and gold links
- [ ] **R7 deliverable:** the benchmark, its data card and baseline results
- [ ] Descriptive study of LLM behavior (memorization versus reasoning, consistency across translations, treatment across canons)
- [ ] **R8 deliverable:** study with a neutral framing, reviewed for fairness
- [ ] RAG assistant with verse-level citations
- [ ] Faithfulness evaluation (does each claim follow from the cited verses?)
- [ ] **R9 deliverable:** assistant demo and its evaluation
- [ ] Cost plan for any model API use (free or local models by default; ask before anything paid)

## P1.5 Web app and visual findings

- [ ] Static site generation from precomputed results
- [ ] Parallel reader (Hebrew, Greek, Arabic, English, German)
- [ ] Cross-reference arc diagram
- [ ] Reuse flow (Sankey or chord)
- [ ] Passage embedding map
- [ ] Stylometry dendrograms
- [ ] Concept-comparison views
- [ ] LLM evaluation heatmaps
- [ ] Assistant view with highlighted citations
- [ ] License, source and uncertainty shown on every view
- [ ] Accessibility and mobile pass
- [ ] Public hosting on a free tier

## P1.6 Phase 1 release

- [ ] Domain-expert review of gold sets, annotations and framing
- [ ] Reproducibility package (pinned data versions, seeds, scripts)
- [ ] Docs, data cards and changelog brought up to date
- [ ] All nine Phase 1 boxes ticked
- [ ] Tag v1.0.0

---

# Phase 2: the full corpus

Scope: everything in Phase 1 plus the harder texts. No Phase 1 goal is dropped; each direction is extended and re-run on the larger corpus.

## P2.1 Source acquisition and licensing

- [ ] Dead Sea Scrolls (ETCBC/dss, CC BY-NC 4.0, so the project stays non-commercial)
- [ ] Apocrypha and Deuterocanon (WEB Deuterocanon, Septuagint)
- [ ] Pseudepigrapha: 1 Enoch, Jubilees (English public-domain Charles translations; German Kautzsch 1900 to verify; Ge'ez originals optional)
- [ ] Nag Hammadi and related Coptic texts: Gospel of Thomas, Pistis Sophia (in Coptic SCRIPTORIUM), Apocryphon of John, Hypostasis of the Archons, On the Origin of the World (open Coptic sources still to find)
- [ ] English translations for Nag Hammadi: Other Gospels public-domain translations (verify per text) and Mead for Pistis Sophia
- [ ] German layers where open sources exist (Pistis Sophia Schmidt 1905, Thomas working translation, Kautzsch for Enoch); otherwise leave empty and say so
- [ ] Gospel of Judas: ask for permission, transcribe from published images, or defer (owner decision)
- [ ] Syriac (Peshitta) scoping
- [ ] Resolve every `verify` entry, and add each new source to `sources.toml` with its phase

## P2.2 Corpus expansion (R1)

- [ ] Parsers for Text-Fabric (DSS), Coptic CoNLL-U and TEI, Gutenberg text, and other new formats
- [ ] Merge into the unified schema, with fragmentary and uncertain texts flagged
- [ ] Alignments and versification for the new texts
- [ ] **R1 deliverable:** full corpus build and updated data card

## P2.3 Extend the analyses (R2, R4, R5, R6)

- [ ] R2: Second Temple, Gnostic and Qur'anic reworkings of Genesis; gold set extended and reviewed
- [ ] R4: Gnostic and apocryphal texts compared stylistically with canonical ones, with stated limits
- [ ] R5: longer and wider concept comparison, including Gnostic usages of logos, wisdom/sophia, light
- [ ] R6: dualism and demiurge motifs added with expert-validated labels
- [ ] **Deliverables:** R2, R4, R5, R6 reports re-run on the full corpus

## P2.4 Coptic and Syriac tooling (R3)

- [ ] Domain adaptation to Gnostic Coptic text, with an evaluation sample
- [ ] Coptic-to-English translation experiment (our own translations, so license is clear)
- [ ] Syriac resource audit and first tools
- [ ] **R3 deliverable:** full Coptic and Syriac tooling write-up

## P2.5 LLM layer on the full corpus (R7, R8, R9)

- [ ] Benchmark extended to the whole corpus; less-memorized texts used as additional controls
- [ ] LLM study extended and re-run
- [ ] RAG assistant over the full corpus, with provenance flags for fragmentary and uncertain texts
- [ ] **Deliverables:** R7, R8, R9 results on the full corpus

## P2.6 Web app expansion

- [ ] New texts in the parallel reader, arcs, flows and maps
- [ ] Views for fragmentary texts (manuscript structure, uncertainty)
- [ ] Updated evaluation views
- [ ] Accessibility and performance pass on the larger data

## P2.7 Phase 2 release

- [ ] Domain-expert review of all new gold sets, annotations and framing
- [ ] Reproducibility package updated
- [ ] Docs, data cards and changelog brought up to date
- [ ] All nine Phase 2 boxes ticked
- [ ] Tag v2.0.0

---

## Cross-cutting: academic submission

- [ ] Choose a venue and read its call (candidates: computational-humanities and ancient-language workshops such as LT4HALA and ML4AL, the Computational Humanities Research conference, Digital Humanities conferences)
- [ ] Decide whether a first paper reports Phase 1 or waits for Phase 2
- [ ] Recruit a domain-expert collaborator
- [ ] Pre-register evaluation plans where useful
- [ ] Draft: corpus and data card, reuse detection, Coptic tooling, evaluations
- [ ] Internal review for fairness and framing
- [ ] Submit

## Open decisions

1. ~~English Qur'an layer~~ Decided: Pickthall (1930). OCR and proofreading still needed.
2. ~~German Qur'an layer~~ Decided: Henning (1901). OCR approach still to design.
3. Septuagint as an optional Greek layer in Phase 1: keep or drop.
4. Gospel of Judas: permission, own transcription, or defer (Phase 2).
5. German and Syriac layers for Phase 2 texts.
6. Domain-expert collaborator.
7. Target venue, and whether the first paper reports Phase 1 or Phase 2.
8. Frontend stack (see [docs/architecture.md](docs/architecture.md)).

## Known risks

- Small Coptic corpus: modest absolute numbers, stated openly.
- Few time slices make diachronic claims weak; dates are scholarly ranges.
- Gold sets and annotation need a domain expert.
- Scripture is memorized by LLMs, which confounds R7 to R9 without controls. Phase 1 texts are among the most memorized, so the controls matter most here.
- OCR quality of the German Qur'an scan is unknown until measured.
- License limits: non-commercial (Phase 2 Dead Sea Scrolls), ShareAlike and verbatim-only (see [SOURCES.md](SOURCES.md)).
