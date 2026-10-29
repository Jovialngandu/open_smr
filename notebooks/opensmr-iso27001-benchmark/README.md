# OpenSMR ISO 27001 Retrieval Benchmark

**Version:** 0.1.0  
**Status:** Initial seed — annotations still require expert review  
**Language:** French  
**Cases:** 50

## Purpose

This dataset is a seed benchmark for evaluating how well OpenSMR retrieves ISO/IEC 27001:2022 Annex A controls for a risk or task description.

## Files

- `retrieval/benchmark_v1.json`: canonical machine-readable dataset.
- `retrieval/benchmark_v1.csv`: spreadsheet-friendly view; `relevance_json` contains a JSON object.
- `schemas/benchmark_case.schema.json`: structural schema for validating each case.
- `metadata.json`: dataset metadata and annotation notes.

## Record format

Each case contains:
- `id`: stable identifier.
- `query`: French risk/task description.
- `relevance`: map of ISO control IDs to relevance grades.

Grades:
- `1`: low but relevant
- `2`: relevant
- `3`: highly relevant

## Evaluation cautions

1. This is an initial seed dataset, not yet a verified gold standard.
2. Review each control ID and relevance grade against the official ISO/IEC 27001:2022 control catalogue and your intended retrieval use case.
3. A control missing from a case must not automatically be interpreted as irrelevant unless the annotation protocol says so.
4. Recall@K is meaningful only when the relevant controls for each query have been judged sufficiently completely.
5. Do not edit annotations merely to improve model scores. Record justified changes and bump the dataset version.
6. Use the same fixed cases and labels when comparing BM25, vector search, and hybrid retrieval.

## Suggested versioning

- `0.1.0`: initial conversion of the existing 50 cases.
- `0.2.0`: after annotation review and documented corrections.
- `1.0.0`: when the annotation protocol and coverage are stable enough for a formal baseline.

## Citation / provenance

Created from an existing OpenSMR benchmark list supplied for evaluation. It has not been independently certified as an authoritative ISO mapping.
