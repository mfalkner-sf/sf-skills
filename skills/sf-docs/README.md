# sf-docs

Official Salesforce documentation retrieval skill for `sf-skills`.

## Contract

`sf-docs` is a **core skill** in the suite.

- mandatory with `sf-skills`
- uses **qmd first** when available and the local corpus is ready
- falls back to **Salesforce-aware retrieval** when qmd is missing or weak
- keeps downloaded/scraped docs **local-only**, not in the public repo

## Runtime Modes

### qmd-enabled

- detect qmd
- detect local corpus readiness
- run qmd query first
- accept results only when they are strong enough
- otherwise fall back to targeted official HTML/PDF retrieval

### no-qmd

- classify likely doc family first
- target likely official guide/article roots
- prefer official URLs and PDFs over third-party summaries
- avoid broad crawling during normal question answering

## Key References

- [SKILL.md](./SKILL.md)
- [references/local-corpus-layout.md](./references/local-corpus-layout.md)
- [references/discovery-manifest.md](./references/discovery-manifest.md)
- [references/qmd-integration.md](./references/qmd-integration.md)
- [references/runtime-workflow.md](./references/runtime-workflow.md)
- [references/ingestion-workflow.md](./references/ingestion-workflow.md)
- [references/salesforce-scraper-techniques.md](./references/salesforce-scraper-techniques.md)
- [references/pilot-scope.md](./references/pilot-scope.md)
- [references/benchmark-protocol.md](./references/benchmark-protocol.md)
- [references/cli-workflow.md](./references/cli-workflow.md)

## Unified CLI

Use the wrapper CLI for the common end-to-end workflow:

### Discover / enrich the manifest

```bash
python3 skills/sf-docs/scripts/cli.py discover \
  --output ~/.sf-docs/manifest/guides.json \
  --pretty
```

### Sync a local corpus from the manifest

```bash
python3 skills/sf-docs/scripts/cli.py sync \
  --manifest ~/.sf-docs/manifest/guides.json \
  --download-pdf \
  --download-html \
  --browser-scrape \
  --normalize
```

### Bootstrap qmd for the local corpus

```bash
python3 skills/sf-docs/scripts/cli.py bootstrap-qmd --embed
```

### Check qmd/corpus status

```bash
python3 skills/sf-docs/scripts/cli.py status
```

### Diagnose runtime lookup behavior

```bash
python3 skills/sf-docs/scripts/cli.py diagnose \
  --query "Find official Salesforce REST API authentication docs"
```

### Run end-to-end retrieval

```bash
python3 skills/sf-docs/scripts/cli.py retrieve \
  --query "Find official Salesforce REST API authentication docs" \
  --mode qmd_first
```

### Execute the benchmark and write results

```bash
python3 skills/sf-docs/scripts/cli.py run-benchmark \
  --results skills/sf-docs/assets/retrieval-benchmark.results-template.json
```

### Score retrieval benchmark results

```bash
python3 skills/sf-docs/scripts/cli.py score-benchmark \
  --results skills/sf-docs/assets/retrieval-benchmark.results-template.json
```

> See [references/cli-workflow.md](./references/cli-workflow.md) for the recommended operator sequence.
