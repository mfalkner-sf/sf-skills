# sf-docs qmd Integration

This document defines how `sf-docs` should use qmd when it is available.

## First-Version Policy

Use **one qmd collection** for the normalized Salesforce docs corpus.

Recommended root:

```text
~/.sf-docs/normalized/md/
```

## Why One Collection First

A single collection keeps setup and operations simple:

- one place to index
- one place to re-embed
- one query target for `sf-docs`
- easier debugging during initial rollout

If benchmark results later show quality issues, split collections by family or product.

## Context Strategy

Use qmd context aggressively.

### Global Context

```text
Official Salesforce public documentation corpus used by sf-docs. Prefer this source over third-party blogs for platform guidance, API references, setup documentation, and release-sensitive behavior.
```

### Family-Level Context

Examples:

- `atlas/` — Legacy official Salesforce guides and references
- `platform/` — Modern developer.salesforce.com platform guides
- `help/` — Salesforce Help and setup documentation
- `pdf/` — Official guide PDFs normalized for local search

### Guide-Level Context

Examples:

- `apexcode/` — Apex Developer Guide
- `api_rest/` — REST API Developer Guide
- `object_reference/` — Object Reference for Salesforce Platform
- `agentforce/` — Agentforce and AI platform documentation

## Retrieval Expectations

When qmd is available, `sf-docs` should:

1. search qmd first
2. evaluate whether results are good enough
3. answer from local docs when confidence is high
4. fall back to Salesforce-aware scraping when local results are weak

## Weak Result Indicators

Treat qmd results as weak when:

- no results are returned
- only unrelated guides are returned
- the exact API/term/error is missing
- snippets are too fragmentary to support a grounded answer
- the request is release-sensitive and the local corpus appears stale

## Suggested Collection Setup

Example qmd commands once a local corpus exists:

```bash
qmd collection add ~/.sf-docs/normalized/md --name sf-docs
qmd context add qmd://sf-docs "Official Salesforce public documentation corpus used by sf-docs"
qmd context add qmd://sf-docs/atlas "Legacy official Salesforce guide and reference docs"
qmd context add qmd://sf-docs/platform "Modern developer.salesforce.com platform guides"
qmd context add qmd://sf-docs/help "Salesforce Help and setup documentation"
qmd context add qmd://sf-docs/pdf "Official Salesforce guide PDFs normalized for local search"
qmd embed
```

## Future Expansion

Only split into multiple collections if benchmarks justify it, for example:

- `sf-docs-platform`
- `sf-docs-help`
- `sf-docs-pdf`

Start simple; optimize later.
