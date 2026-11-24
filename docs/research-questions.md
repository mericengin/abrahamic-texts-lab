# Research questions

Nine directions (R1 to R9) share one spine question:

> How is the Genesis and creation tradition reused and transformed across Jewish, Christian, Gnostic and Qur'anic texts?

Each direction below states its question, why it matters, the data it needs, the method, how it will be evaluated, the outputs, and its limits. Status for every direction is **not started**; progress is tracked as checkboxes in [ROADMAP.md](../ROADMAP.md). Evaluation plans are decided before results are seen. Nothing here is a finding.

Dependency order: R1 first; then R2, R3, R4, R5, R6 (R2 and R3 feed the others); then R7, R8, R9, which also need R1 and the R2 gold links.

---

## R1. Unified, cleaned, aligned corpus

**Question.** Can the scattered open resources be integrated into one corpus with consistent metadata, stable verse-level IDs, aligned editions and translations, and a license recorded for every row?

**Why.** Everything else depends on it, and good integration is real, publishable work in its own right (a data paper with a data card).

**Data.** The `ready` and `verify` sources in [SOURCES.md](../SOURCES.md): morphhb, MorphGNT/SBLGNT, Tanzil Arabic, ETCBC DSS, Coptic SCRIPTORIUM, UD Coptic, WEB with Deuterocanon, Luther 1912, Enoch and Jubilees (Charles), Septuagint (First1KGreek).

**Method.** Parsers per format (OSIS, plain-text columns, CoNLL-U/TEI, USFX, Text-Fabric, Tanzil text); a unified schema; explicit versification mappings between editions (Hebrew versus English verse numbering, Qur'an numbering schemes); alignment between original-language texts and translations; data-quality checks.

**Evaluation.** Automated checks (coverage, gaps, duplicates, encoding round-trips), a sample audit against the source by hand, and a documented list of known divergences.

**Outputs.** A versioned corpus build, a data card, a schema document, search and the parallel reader.

**Limits.** Coverage depends on what is openly licensed. Versification mappings are judgment calls and must be documented. Gospel of Judas and most of Nag Hammadi are currently missing.

---

## R2. Parallel passages and intertextuality detection

**Question.** Where do texts quote, echo or rework one another (Torah in the Gospels, Gospel parallels, the Bible in the Qur'an, Gnostic reworkings of Genesis), and how confident can we be?

**Why.** It is the core engine of the spine question and the source of the most readable visualizations.

**Data.** The aligned corpus (R1); a gold set of parallels drawn from published scholarly sources and reviewed by a domain expert.

**Method.** Start with lexical and fuzzy matching on aligned text; add cross-lingual retrieval with multilingual embeddings; combine with alignment to rank candidate links; give every link a confidence and a type (quotation, allusion, thematic parallel, reworking).

**Evaluation.** Precision, recall and F1 against the gold set, reported per language pair and per link type, with the gold-set construction described. Baselines (lexical only) compared with embedding methods. Expert review of a random sample of top-ranked and low-ranked links.

**Outputs.** A link table with confidence, the cross-reference arc diagram, reuse flow diagrams.

**Limits.** Gold sets reflect scholarly judgment and are incomplete. Translation effects can create or hide apparent parallels. Thematic parallels are hard to separate from shared motifs.

---

## R3. Low-resource tooling for Coptic (then Syriac)

**Question.** How well can POS tagging, lemmatization and machine translation into English be adapted to Coptic, and does it enable reading the Gnostic texts?

**Why.** Most Gnostic material is Coptic. Tools help both the humanities and low-resource NLP.

**Data.** UD Coptic-Scriptorium treebank (about 59k tokens, no Gnostic texts), Coptic SCRIPTORIUM corpora, and our own translations of Gnostic texts where license requires them.

**Method.** Baselines first (rule-based and classical taggers), then adaptation of a multilingual model; domain-shift evaluation, since the training text is mostly Biblical and monastic while the target is Gnostic; a translation experiment with our own references.

**Evaluation.** Accuracy on the UD test split and on a small hand-annotated Gnostic sample; error analysis by text type; for translation, human spot checks plus automatic metrics with their limits stated.

**Outputs.** Open tools, an evaluation, and a limits write-up. Syriac begins as a resource audit.

**Limits.** The training corpus is small and domain-skewed, so expect modest numbers. Absolute scores will not transfer cleanly across dialects or periods.

---

## R4. Computational stylometry, authorship and dating

**Question.** Do the Pauline letters cluster as scholars claim, and where do Gnostic texts fall stylistically relative to canonical ones?

**Why.** A well-known test of method against scholarly consensus, and a chance to show honest uncertainty.

**Data.** Greek NT with morphology, the Coptic Gnostic texts, and later other Greek material; controlled for translation by using original languages.

**Method.** Function-word and morphological features; clustering and bootstrap consensus trees; comparison across feature sets and text lengths.

**Evaluation.** Agreement with scholarly consensus is reported, not assumed. Robustness checks across feature sets, text-length sampling and resampling.

**Outputs.** A stylometry report, dendrograms with bootstrap support.

**Limits.** Short texts, genre, scribal and translation effects, and cross-language comparisons are serious confounds. The project reports patterns, not authorship verdicts.

---

## R5. Concept evolution via diachronic embeddings

**Question.** How do terms such as logos, spirit, wisdom/sophia and light shift in meaning across traditions and periods?

**Why.** It ties lexical semantics and word-sense work to the corpus and gives the project a "how language changes" story.

**Data.** The aligned corpus with period metadata expressed as scholarly date ranges.

**Method.** Contextual embeddings with sense clustering per term (not word2vec trained on tiny slices); usage-based comparison across traditions and periods.

**Evaluation.** Hand-checked sense inventories for each term, agreement between independent annotators where possible, and sensitivity to how time is sliced.

**Outputs.** Concept-drift views and a short report per concept.

**Limits.** Few time slices and little text per slice. Dates are uncertain ranges. Cross-language comparison depends on translation and alignment quality.

---

## R6. Theme, argument and motif mining

**Question.** Can topics and motifs (dualism, creation narratives, the demiurge) be mined across the corpus and validated by scholars?

**Why.** It surfaces patterns the reuse analysis misses and gives structured data for the reader.

**Data.** The aligned corpus and a motif scheme drafted from scholarly literature.

**Method.** Topic modeling and embedding-based clustering, followed by scholar-validated annotation of a sample against a written scheme.

**Evaluation.** Inter-annotator agreement, coverage, and comparison of automatic output with expert labels.

**Outputs.** Motif and theme tables, topic streams across traditions and periods.

**Limits.** Motif categories are interpretive. Topic models are sensitive to preprocessing. Expert time is the bottleneck.

---

## R7. Long-context scripture benchmark

**Question.** Can question answering and cross-reference tasks over the whole corpus measure long-context reasoning without being confounded by memorization?

**Why.** Long-context and RAG evaluation is active, and this corpus offers verifiable ground truth through the R2 gold links.

**Data.** The corpus and gold links (R1, R2); perturbed and obscure-text variants as controls.

**Method.** Task design with answers checkable against the corpus; memorization controls built in from the start (perturbed verses, held-out or obscure texts, closed-book baselines).

**Evaluation.** Accuracy per task type and context length, with controls; documented annotation and contamination analysis.

**Outputs.** The benchmark, a data card and baseline results. Models used are free or local unless the owner approves otherwise.

**Limits.** Models have likely seen scripture. Without the controls, scores would measure recall, not reasoning.

---

## R8. How LLMs handle religious texts

**Question.** How do LLMs behave on religious texts across traditions: memorization versus reasoning, consistency across translations, and differences in treatment across traditions?

**Why.** Comparative evaluation across religions is interesting and publishable, and it is easy to do badly.

**Data.** Matched prompt sets across traditions and translations, built from the corpus and reviewed for fairness.

**Method.** A fixed, pre-registered protocol; matched tasks per tradition; consistency tests across translations; memorization probes.

**Evaluation.** Reported per tradition with confidence intervals; a fairness review of prompts and framing by someone outside the author team where possible.

**Outputs.** A descriptive study and its data.

**Limits.** The framing must stay descriptive. The study does not evaluate any tradition, only model behavior. Prompt wording effects are large and must be reported.

---

## R9. RAG scholarly research assistant

**Question.** Can a retrieval-augmented assistant answer questions about the corpus with exact verse and source citations, and can we measure how faithful its answers are?

**Why.** It gives the project a demo and a rigorous evaluation alongside the research.

**Data.** The corpus with verse-level IDs, the reuse links, and an evaluation question set.

**Method.** Retrieval over verse-level chunks with multilingual embeddings; answers that must cite verse IDs; refusal when the corpus does not support an answer.

**Evaluation.** Faithfulness (does each claim follow from the cited verses?), citation accuracy and answer coverage, compared with a no-retrieval baseline and with the memorization controls from R7.

**Outputs.** A working demo and the evaluation. Cost is capped; free or local models by default.

**Limits.** Retrieval errors and translation differences. The assistant is a research aid, not an authority, and shows its sources and uncertainty.
