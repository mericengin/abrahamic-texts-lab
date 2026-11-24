# Roadmap

Current phase: **M0, setup (complete).** Next: **M1, corpus foundation.**

How to read this file: a box is ticked only when the work exists in the repository and has been checked. Estimates are rough, solo-scale guesses, not commitments. Nothing is promised for a date.

The nine research directions (R1 to R9) share one spine question:

> How is the Genesis and creation tradition reused and transformed across Jewish, Christian, Gnostic and Qur'anic texts?

Details for each direction are in [docs/research-questions.md](docs/research-questions.md).

## Research directions at a glance

- [ ] **R1** Unified, cleaned, aligned corpus
- [ ] **R2** Parallel passages and intertextuality detection
- [ ] **R3** Low-resource tooling for Coptic (then Syriac)
- [ ] **R4** Computational stylometry, authorship and dating
- [ ] **R5** Concept evolution via diachronic embeddings
- [ ] **R6** Theme, argument and motif mining
- [ ] **R7** Long-context scripture benchmark
- [ ] **R8** How LLMs handle religious texts
- [ ] **R9** RAG scholarly research assistant with cited verses

A direction is ticked only when its deliverables below are all ticked.

---

## M0: Setup (done)

- [x] Repository, MIT license for code, `.gitignore` keeping third-party texts out of git
- [x] Source manifest (`data/sources.toml`) and human-readable `SOURCES.md` with licenses checked against primary pages
- [x] Fetch script, dry-run by default, with provenance records and manifest tests
- [x] Project docs: README, roadmap, changelog, CLAUDE.md, scope, research questions, architecture, ethics
- [x] Logo and banner

## M1: Corpus foundation (R1)

Goal: every `ready` source fetched, normalized to one schema, searchable.

- [ ] Owner approves the first download batch (filenames and sizes listed first)
- [ ] Fetch the `ready` sources; check the provenance records
- [ ] Resolve the `verify` items: SBLGNT EULA, Luther 1912 URL, Enoch and Jubilees host, Septuagint edition (confirm Swete)
- [ ] Decide the stable identifier scheme (ADR 0001)
- [ ] Parsers: OSIS (Hebrew), MorphGNT, Coptic CoNLL-U/TEI, USFX (WEB, Luther), Text-Fabric (DSS), Tanzil
- [ ] Unified schema and database (text, edition, language, license, per-row provenance)
- [ ] Verse and passage alignment across editions and translations
- [ ] Data-quality checks (gaps, duplicates, encoding, versification differences)
- [ ] Full-text search over all languages
- [ ] Decide the Gospel of Judas: permission, own transcription, or defer
- [ ] Choose an English Qur'an translation with a clear license
- [ ] Research the gaps: Syriac (Peshitta), Greek and Hebrew Apocrypha originals, Nag Hammadi Coptic beyond Thomas
- [ ] **R1 deliverable:** documented, versioned corpus build with a data card
- [ ] Parallel-reader prototype

## M2: Reuse and analysis (R2, R4, R5, R6)

Goal: the first findings on the spine question, each with evidence and uncertainty.

- [ ] Baseline reuse detection (lexical and fuzzy matching on aligned text)
- [ ] Cross-lingual retrieval with embeddings
- [ ] Gold set of parallels from published scholarly sources, reviewed by a domain expert
- [ ] **R2 deliverable:** reuse links with confidence, evaluated against the gold set
- [ ] Stylometry pipeline (features, clustering, bootstrap consensus), compared with scholarly consensus
- [ ] **R4 deliverable:** stylometry report with limits stated (short texts, translation effects, genre)
- [ ] Concept lexicon (light, spirit, wisdom/sophia, logos) with sense clustering
- [ ] Contextual-embedding drift analysis across periods (with date ranges, not point dates)
- [ ] **R5 deliverable:** concept-drift report
- [ ] Topic and motif annotation scheme (dualism, creation, demiurge) with expert-validated labels
- [ ] **R6 deliverable:** motif and theme mining results with inter-annotator agreement

## M3: Coptic and Syriac tooling (R3)

Goal: usable language tools for the Gnostic texts.

- [ ] Evaluation protocol and baselines on the Coptic treebank (UD Coptic-Scriptorium)
- [ ] POS tagging and lemmatization for Coptic
- [ ] Adapt a multilingual model to Coptic and measure it honestly (small corpus, modest numbers expected)
- [ ] Coptic-to-English translation experiment for Gnostic texts (our own translations, so license is clear)
- [ ] Syriac scoping and a first resource audit
- [ ] **R3 deliverable:** open tools, an evaluation, and a write-up of limits

## M4: LLM layer (R7, R8, R9)

Goal: evaluations and a demo, with memorization controls.

- [ ] Memorization controls designed first (perturbed verses, obscure texts, closed-book baselines)
- [ ] Long-context QA and cross-reference tasks built from the aligned corpus and gold links
- [ ] **R7 deliverable:** the benchmark, its data card, and baseline results
- [ ] Descriptive study of LLM behavior on religious texts (memorization versus reasoning, consistency across translations, bias across traditions)
- [ ] **R8 deliverable:** study with a neutral, descriptive framing, reviewed for fairness
- [ ] RAG assistant with verse-level citations
- [ ] Faithfulness evaluation (does each claim follow from the cited verses?)
- [ ] **R9 deliverable:** assistant demo and its evaluation
- [ ] Cost plan for any model API use (free or local models by default; ask before anything paid)

## M5: Web app and visual findings

Goal: a public, readable showcase of the corpus and all findings.

- [ ] Static site generation from precomputed results
- [ ] Parallel reader (Hebrew, Greek, Coptic, Arabic, English)
- [ ] Cross-reference arc diagram
- [ ] Reuse flow (Sankey or chord)
- [ ] Passage embedding map
- [ ] Stylometry dendrograms
- [ ] Concept-drift views
- [ ] LLM evaluation heatmaps
- [ ] Assistant view with highlighted citations
- [ ] License, source and uncertainty shown on every view
- [ ] Accessibility and mobile pass
- [ ] Public hosting on a free tier

## M6: Academic submission

- [ ] Choose a venue and read its call (candidates: computational-humanities and ancient-language workshops such as LT4HALA and ML4AL, the Computational Humanities Research conference, Digital Humanities conferences)
- [ ] Recruit a domain-expert collaborator
- [ ] Pre-register the evaluation plans where useful
- [ ] Draft: corpus and data card, reuse detection, Coptic tooling, evaluations
- [ ] Reproducibility package (pinned data versions, seeds, scripts)
- [ ] Internal review for fairness and framing
- [ ] Submit

## Open decisions

1. Gospel of Judas: ask for permission, transcribe from published images, or defer.
2. English Qur'an translation with a clear license.
3. German and Syriac layers: add or skip.
4. Domain-expert collaborator.
5. Target venue and timeline.
6. Frontend stack (see [docs/architecture.md](docs/architecture.md)).

## Known risks

- Small Coptic corpus: modest absolute numbers, stated openly.
- Few time slices make diachronic claims weak; dates are scholarly ranges.
- Gold sets and annotation need a domain expert.
- Scripture is memorized by LLMs, which confounds R7 to R9 without controls.
- License limits: non-commercial, ShareAlike and verbatim-only (see [SOURCES.md](SOURCES.md)).
