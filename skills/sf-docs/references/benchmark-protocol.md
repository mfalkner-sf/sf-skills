# sf-docs Benchmark Protocol

This document defines how to validate `sf-docs` in both runtime modes.

## Modes to Validate

1. **qmd-first mode**
   - local qmd lookup first
   - Salesforce-aware fallback on weak/missing results

2. **no-qmd mode**
   - Salesforce-aware retrieval only
   - no local indexed corpus available

## Benchmark Asset

Use:

- [assets/retrieval-benchmark.json](../assets/retrieval-benchmark.json)

Use the companion results template:

- [assets/retrieval-benchmark.results-template.json](../assets/retrieval-benchmark.results-template.json)

Score results with:

- [scripts/score_retrieval_benchmark.py](../scripts/score_retrieval_benchmark.py)

## What Counts as a Pass

A benchmark case passes when:

- the retrieval outcome is marked `pass`
- the answer is grounded on an official Salesforce source
- the source family matches the benchmark expectation
- the guide matches the expected guide when a guide is specified

## Suggested Status Values

- `pass`
- `fail`
- `partial`
- `pending`

## qmd-first Validation

For each case, verify:

1. qmd was used when available
2. local hits were accepted only when they were strong enough
3. fallback was used on weak/missing hits
4. the final answer was grounded
5. the result family/guide was appropriate

## no-qmd Validation

For each case, verify:

1. retrieval did not assume qmd availability
2. Salesforce-aware lookup patterns were followed
3. help.salesforce.com shell/noise issues were avoided when possible
4. official PDF fallback was used when HTML was unstable
5. the final answer was grounded

## Fallback Threshold Refinement

Use benchmark failures to refine fallback rules.

Examples:

- If qmd returns irrelevant guides too often, tighten acceptance rules
- If qmd misses exact references, bias toward lexical lookups and exact identifiers
- If no-qmd mode keeps landing on shell pages, increase preference for guide roots or PDF candidates
- If fallback is too slow, narrow guide targeting instead of broadening crawl behavior

## v1 Non-Goals

Do **not** block v1 on these advanced features:

- parallel qmd + scraping fusion
- whole-site automatic crawling during routine lookup
- highly automated refresh of all public Salesforce docs
- multi-collection qmd tuning before benchmark evidence exists

## Recommendation

Get the pilot corpus and benchmark healthy first.

Only after both qmd-first and no-qmd modes perform well on the benchmark should `sf-docs` expand to broader documentation coverage.
