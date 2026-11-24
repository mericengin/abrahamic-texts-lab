# Roadmap

Rough, solo-scale estimates. Nothing below is built yet.

## Research spine

How is the Genesis and creation tradition reused and transformed across Jewish, Christian, Gnostic and Qur'anic texts? Each component below serves this question.

## Phases

**Phase 0: setup (this commit).** Manifest, fetch tooling, licensing record.

**Phase 1: corpus (6 to 8 weeks).** Fetch the `ready` sources. Normalize to one schema with stable verse-level IDs, text language, edition, translation and license per row. Search, a parallel reader, and a first reuse-detection baseline.

**Phase 2: analysis.** Reuse and parallel passages, stylometry (with bootstrap consensus and honest limits), concept tracking (light, spirit, wisdom, logos) using contextual embeddings and sense clustering, motif mining (demiurge, dualism, creation).

**Phase 3: Coptic tooling and gold set.** POS and lemma tagging for Coptic, adaptation of multilingual models, and an expert-validated gold set of parallels.

**Phase 4: LLM layer.** A long-context scripture benchmark, a descriptive study of how LLMs handle religious texts, and a RAG assistant with verse-level citations. Controls for memorization are required (perturbed verses, obscure texts, closed-book baselines).

## Visualizations (planned)

Cross-reference arc diagram, synoptic-style parallel reader, reuse Sankey or chord diagram, UMAP map of passages, stylometric dendrogram with bootstrap support, semantic-drift streams, LLM evaluation heatmaps, RAG view highlighting the cited verse.

## Known risks

- Small Coptic corpus: modest absolute numbers, stated openly.
- Diachronic embeddings with few time slices are weak; dates are scholarly ranges.
- Gold sets and annotation need a domain expert.
- LLM evaluations are confounded by memorization.
- License constraints: non-commercial, ShareAlike and verbatim-only (see SOURCES.md).

## Open decisions

1. Gospel of Judas: permission, own transcription, or defer.
2. English Qur'an translation with a clear license.
3. Whether to add German and Syriac layers.
4. Domain expert collaborator.
5. Target venue and timeline (computational humanities conference).
