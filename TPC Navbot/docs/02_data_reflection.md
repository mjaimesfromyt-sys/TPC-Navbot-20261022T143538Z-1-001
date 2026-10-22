# Data preparation and reflection

The repository contains 30 generated sample `.txt` files, not a collected official directory. Consistent headings made parsing easy, but plausible room numbers and confident "official" language could be mistaken for verified facts. A document title does not establish authority.

The pipeline removes decorative divider lines, normalizes line endings/whitespace, and expands common abbreviations. `TextPreprocessor` retains building label, location ID, source filename, and chunk ID. It creates bounded overlapping character chunks: default 400 characters with up to 50 characters of overlap. This is not a model-token chunk budget.

An actual local run on 22 October 2026 produced:

```text
Before (CRLF line endings):
===
Bldg   Name: Admin
Rm 203    Dept Office
===

After:
Building Name: Administration
Room 203 Department Office

Lexical tokens (casefold + Unicode \w+):
building, name, administration, room, 203, department, office
```

That run processed 30 files into **114 chunks**, with maximum chunk length **399 characters** and **0 verified chunks**. This describes this corpus/configuration snapshot, not retrieval accuracy. The offline backend was signed SHA-256 unigram hashing into 384 dimensions, followed by unit normalization. It is a lexical feature vector, not a pretrained semantic model.

After an explicit model download, a separate local run used Sentence Transformers with `all-MiniLM-L6-v2`, producing actual 384-dimensional semantic vectors; its results are retained in `data/evaluation/semantic_metrics.json`. The model weights are ignored by Git and must be provisioned explicitly elsewhere. The lexical and semantic results remain separately labelled. Application startup itself avoids an implicit model download.

Provenance now comes from the source registry. Missing reviews, unsupported source types, malformed dates, changed content, and absent official references fail closed. Chunks inherit reviewed metadata only when the file hash and review match. Generated files remain unverified even if their text claims authority.

The key lesson is that cleaning and vectors do not make source claims true. Similarity measures representation overlap; it cannot approve an office location or certify a safe route. The [metric report](04_distance_metric_report.md) records examples where lexical top results were wrong. Real campus validation and broader multilingual evaluation remain future work.
