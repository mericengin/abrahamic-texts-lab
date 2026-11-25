# Data readiness (Phase 1)

The nine Phase 1 layers, what each has, and how far it can be trusted. Metadata only: no texts. The checks are in [data-verification.md](data-verification.md) and the files in [data-inventory.md](data-inventory.md).

"Ready" here means: every verse is present, provenance and license are recorded, there is a Markdown copy and a PDF, the layer is mapped to the others, and its quality is **measured and stated**. Two layers are ready only with flags, because they are reconstructed from scans.

| # | Layer | Source | Verses | Markdown / PDF | Quality | Ready? |
|---|---|---|---|---|---|---|
| 1 | Hebrew Bible, Hebrew | WLC (morphhb), CC BY 4.0 | 23,213 | yes / generated | equals the raw OSIS word for word | **Ready** |
| 2 | Hebrew Bible, English | WEB, public domain | 23,145 OT verses (38,029 with NT and Deuterocanon) | yes / official PDF | equals independent extraction | **Ready** |
| 3 | Hebrew Bible, German | Luther 1912, public domain | 23,145 OT verses (31,102 with NT) | yes / official PDF | same checks as WEB | **Ready** |
| 4 | New Testament, Greek | SBLGNT, CC BY 4.0 | 7,939 | yes / generated | equals the edition's XML | **Ready** |
| 5 | New Testament, English | WEB | 7,957 | yes / official PDF | as above | **Ready** |
| 6 | New Testament, German | Luther 1912 | 7,957 | yes / official PDF | as above | **Ready** |
| 7 | Qur'an, Arabic | Tanzil Uthmani, CC BY 3.0, verbatim | 6,236 | yes / generated | text kept verbatim; counts agree with an independent source | **Ready** |
| 8 | Qur'an, English | Pickthall 1930, rebuilt from four scans | 6,236 | yes / generated | about 99% decided by agreement between scans; 126 verses read against page images; 5,931 of 6,236 verses equal a separately typed digital text apart from its known revisions; 83 verses rest on a vote only (79 of them equal that text) | **Ready with flags** |
| 9 | Qur'an, German | Henning 1901, OCR of a Fraktur scan with a repair pass | 6,236 (mapped 6,211) | yes / generated | about 1.0% token errors on a fresh random sample of 10 pages (25 in 2,500 words; 0.6% without stray header and junk tokens); 34 of 622 pages read against the scan | **Ready with flags** |

## Extra local layers (not published)

Two clean modern translations from Tanzil were downloaded on 2026-11-25 for analysis and comparison only: German Bubenheim and Elyas (`german-quran-tanzil-bubenheim`) and English Saheeh International (`english-quran-tanzil-saheeh`). Each has 6,236 verses in the standard numbering, the same verse set as the Arabic layer, and no empty verse, so they need no verse mapping. They stay in the git-ignored data folder; Tanzil allows non-commercial use only, forbids redistribution, and the translations are copyrighted. They appear in no PDF, Markdown copy or the app unless the rights holders grant permission.

## Mapping between layers

- Hebrew to English to German: complete except Nehemiah 7:68, which the Hebrew text lacks.
- Greek to English and German: 16 verses exist only in English, 20 only in German, 2 only in Greek; these need an expert-confirmed link.
- Qur'an: standard numbering to the number printed in Pickthall's 1930 book (483 verses differ) and to Henning's own numbering (6,211 of 6,236 verses; Henning does not number sura 1). The Henning mapping is a draft built from a typed copy of another edition.

## What "flags" means in the app and any output

Every view of layers 8 and 9 must say that the text is reconstructed or machine-read, show its measured error rate, and link the source scan. Verses that rest on a vote only (layer 8) are marked. Do not quote either layer without checking the scan.

## What would move layers 8 and 9 to fully verified

- Layer 8: reading the roughly 300 verses where the typed comparison text differs (a seeded sample of 20 gave 3 slips of ours), plus an expert review.
- Layer 9: a further round of page reading (34 of 622 pages read so far; errors are spread over about 540 pages, so reading the worst pages alone removes only about a tenth of them), an expert review of the verse mapping, and a decision on whether a typed edition with a suitable license can replace the OCR.

Domain-expert review has not happened for any layer (CLAUDE.md rule 8).
