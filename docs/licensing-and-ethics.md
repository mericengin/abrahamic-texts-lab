# Licensing and ethics

This is a record of how the project handles licenses and sensitive material. It is not legal advice. When a license matters for a decision, re-read the primary page.

## Licensing

**Our own work.** Code and original documentation are MIT ([LICENSE](../LICENSE)). Our derived data layers will be released under a license compatible with their inputs; the choice is recorded here once made.

**Third-party texts are never committed.** `data/raw/` is git-ignored. The fetch script retrieves from the original source and writes a provenance record (URL, time, license, checksum or commit).

### Rules by license type

| Type | Examples here | What it means |
|---|---|---|
| Public domain | WLC text, WEB, Luther 1912, Charles's Enoch and Jubilees | Free to use and redistribute. WEB: if you change the text you may not call it "World English Bible". |
| Attribution (CC BY) | morphhb annotations, UD Coptic, most Coptic SCRIPTORIUM | Credit the source. |
| ShareAlike (CC BY-SA) | MorphGNT morphology, First1KGreek | Derived data carries the same license. Combining with other share-alike data is fine; mixing with incompatible licenses needs care. |
| Non-commercial (CC BY-NC) | ETCBC Dead Sea Scrolls, Tanzil translations | Allowed for this non-profit use; the project must never be monetized. |
| Verbatim only | Tanzil Arabic text | No modification. The notice, credit and a link to tanzil.net must travel with every copy or derived file. Keep annotations in separate layers. |
| Unresolved | Gospel of Judas, SBLGNT text (EULA unread), Sahidica NT | Not fetched or published until resolved. |

### Procedure for a new source

1. Read the license on the primary page and quote the key sentences in the manifest.
2. Note any conflict between sources and keep the entry at `verify`.
3. Record the date checked.
4. Ask the owner before fetching anything.

### Known conflicts and gaps

- **SBLGNT text:** the Faithlife repository says CC BY 4.0; the MorphGNT README says the text falls under the SBLGNT EULA, which could not be read. Resolve before publishing the text.
- **Gospel of Judas:** no open Coptic edition; the free English translation found names no translator and sits on a site with an "all rights reserved" footer. Options: ask for permission, transcribe from published images, or defer.
- **Nag Hammadi English translations** (Robinson, Meyer) are copyrighted and will not be used. Our own translations from Coptic are an option.
- **Tanzil translations:** each belongs to its translator and is non-commercial; the project does not bundle them.
- **Rahlfs Septuagint:** avoided because of a reported TLG-derived license.

## Ethics

### Descriptive, not evaluative

The project describes how texts relate and how language and ideas move between them. It does not judge, rank or argue for any tradition, and it avoids framing one tradition's texts as derivative of another's as a value claim. When a result shows a directional relationship ("text A reworks text B"), the evidence and the scholarly debate are shown beside it.

### Terminology

Use neutral, widely understood terms: "Hebrew Bible", "New Testament", "Qur'an", "Dead Sea Scrolls", "Apocrypha and Pseudepigrapha". Avoid loaded labels. Where a term is contested (for example "Gnostic"), say so in the docs and the interface.

### Respect and sensitivity

- Sacred texts are treated respectfully in the interface: no jokes, memes or decorative misuse.
- The Qur'an text is shown verbatim and is not edited, truncated mid-verse or recombined.
- No content is presented as a ruling, a prediction or religious guidance.

### Scholarly honesty

- Automated output is a lead, not a verdict. Every link, date and label carries a confidence or an "unvalidated" flag.
- Dates are ranges. Disputed authorship and dating are reported with the scholarly positions.
- Gold sets and annotations are reviewed by a domain expert before any claim is made about them.
- Negative and weak results are reported as plainly as strong ones.
- No citation is used without verifying that it exists.

### LLM studies (R7 to R9)

- Memorization controls are required before any claim about reasoning.
- Prompts are matched across traditions and reviewed for fairness and framing; results are reported per tradition with uncertainty.
- The framing is about model behavior, never about the traditions.
- Free or local models by default; paid use needs approval and a cost cap.

### Privacy

No personal data is collected or published. The web app should not track visitors. Contributor credit is by choice.

### Community

Corrections from scholars and readers are welcome and should be easy to submit. Errors in texts, licenses or attributions are fixed and recorded in the changelog.
