# Scope and definition

## One-sentence definition

Abrahamic Texts Lab is a free, open, non-commercial research workspace and public web app for the **comparative computational analysis of Abrahamic texts**: it builds an aligned, license-tracked corpus, runs analyses on how texts relate and change, and presents the findings with their evidence and uncertainty.

## Why it exists

The Abrahamic texts are among the most studied in history, yet the digital resources are scattered across projects with different formats, identifiers and licenses. Some of the original languages (Coptic, Syriac, Ge'ez, Biblical Hebrew, Koine Greek, Classical Arabic) are low-resource for modern language technology. A single, carefully documented, openly licensed resource, plus honest analyses on top of it, serves three groups:

- **Curious readers** who want to see how texts relate without reading scholarly apparatus.
- **Students and scholars** who want reproducible, citable starting points and a place to check machine output against the sources.
- **Computational-humanities and NLP researchers** who want a clean corpus, evaluation sets and baselines for ancient and low-resource languages.

## Two phases

The goals are delivered in two phases. Phase 2 extends every Phase 1 goal and drops none.

- **Phase 1, the three canons.** Hebrew Bible, New Testament and Qur'an, each in the original language, English and German (three layers per text). Done means all nine research directions (R1 to R9) are implemented and working on these texts and presented in the web app. Release v1.0.0.
- **Phase 2, the full corpus.** Adds the Dead Sea Scrolls, the Apocrypha and Pseudepigrapha, Nag Hammadi and other Gnostic texts (and the Gospel of Judas if its source is resolved), with Coptic, Aramaic and optionally Syriac and Ge'ez. Done means all nine directions are implemented and working across everything. Release v2.0.0.

The order is a research decision: prove the whole pipeline on texts that have clean licenses, three complete language layers and extensive reference literature, then apply it to denser, more fragmentary and harder-to-source material. Milestones and checklists are in [ROADMAP.md](../ROADMAP.md).

## The corpus

The table below is the full (Phase 2) corpus. Phase 1 uses the Hebrew Bible, New Testament and Qur'an rows only.

Candidate material (see [SOURCES.md](../SOURCES.md) for the license-checked list):

| Tradition area | Material |
|---|---|
| Hebrew Bible | Westminster Leningrad Codex with morphology; Septuagint (Greek); English and German translations |
| New Testament | SBL Greek New Testament with morphology; Sahidic Coptic (license pending); English and German translations |
| Qur'an | Arabic text (verbatim, per its terms); an openly licensed English translation (to be chosen) |
| Second Temple and Dead Sea | Dead Sea Scrolls transcriptions; Apocrypha and Deuterocanon; Pseudepigrapha such as Enoch and Jubilees |
| Gnostic and related | Nag Hammadi texts as available (Gospel of Thomas, Pistis Sophia first); Gospel of Judas (blocked, see below) |

Languages in scope: Biblical Hebrew, Aramaic (as it occurs in the DSS), Koine Greek, Sahidic Coptic, Classical Arabic, English, and German as an optional translation layer. Syriac is a candidate for later.

## The research questions

Nine directions (R1 to R9) share one spine question: **how is the Genesis and creation tradition reused and transformed across Jewish, Christian, Gnostic and Qur'anic texts?** They are defined in [research-questions.md](research-questions.md) and tracked in [ROADMAP.md](../ROADMAP.md).

## Deliverables

1. A documented, versioned corpus build with a data card (R1).
2. Reuse links with confidence, evaluated against an expert-reviewed gold set (R2).
3. Open Coptic language tools and an evaluation (R3).
4. Analyses: stylometry, concept drift, motif mining (R4 to R6).
5. A long-context scripture benchmark, an LLM behavior study and a cited RAG assistant (R7 to R9).
6. A public web app presenting the corpus and every finding with visualizations.
7. A reproducibility package and a paper draft for a computational-humanities venue.

## In scope

- Building and documenting the corpus from openly licensed or permissioned sources.
- Comparative analysis across languages, editions, translations and traditions.
- Visualizing and explaining the results for non-specialists.
- Evaluations of language models on these texts, framed descriptively.
- Open code, open documentation, and a license record for every text.

## Out of scope (non-goals)

- **Theology, apologetics or polemics.** The project never argues for or against any tradition, and never ranks them.
- **Authoritative interpretation.** It does not tell readers what a text means or what to believe.
- **Commercial use.** No monetization, ads or paid tiers. Some sources forbid it.
- **Redistributing copyrighted translations.** If a translation is not openly licensed or permissioned, it is not bundled.
- **Chasing authorship or dating "discoveries".** Stylometric and dating results are compared with scholarly consensus and reported with their limits.
- **Everything Abrahamic.** The corpus is bounded by the sources above. "The entirety of Abrahamic texts" is a corpus, not a question; the spine question keeps the work focused.

## Audiences and how they use it

| Audience | What they get |
|---|---|
| Curious reader | A readable parallel reader and visual findings, with plain-language explanations |
| Student | Citable passages, links to sources, and licenses |
| Scholar | Downloadable data, methods, confidence scores, and a way to flag errors |
| NLP researcher | Corpus build scripts, a Coptic evaluation, and a long-context benchmark |

## Success criteria

The project succeeds when:

- The corpus builds reproducibly from the source manifest and every row has provenance and a license.
- Each finding comes with its method, its evaluation against a stated reference, and its limits.
- A domain expert has reviewed the gold sets and the framing.
- The web app shows every claim beside its evidence and uncertainty.
- Negative and weak results are reported as plainly as strong ones.
- The work is reproducible by someone else from the repository and the pinned data versions.

## Academic extension

The same work is structured to support a submission to a computational-humanities or ancient-language-technology venue. Candidate venues named so far are workshops on computational humanities and ancient languages (for example LT4HALA and ML4AL), the Computational Humanities Research conference, and Digital Humanities conferences. Venue choice, deadlines and collaborators are open decisions, not commitments (see [ROADMAP.md](../ROADMAP.md)). Papers would not duplicate the web app; they would report methods, evaluations and honest limits, with the app as the public companion.

## Known constraints

- **Licenses.** Non-commercial, ShareAlike and verbatim-only sources shape what can be published together (see [licensing-and-ethics.md](licensing-and-ethics.md)).
- **Data gaps.** No clean open Gospel of Judas edition yet; only part of Nag Hammadi exists in an open Coptic corpus.
- **Small low-resource corpora.** Coptic results will be modest in absolute terms.
- **Expert availability.** Gold-set and annotation validation needs a domain scholar.
- **Memorization.** LLMs have seen scripture; evaluation designs must control for it.
- **Solo scale.** The plan is sized for one person with occasional expert help.
