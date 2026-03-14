# sf-docs Final Architectural Recommendation

## Mandatory vs Optional

- `sf-docs` is a **mandatory core skill** in `sf-skills`
- qmd is an **optional external dependency** installed via the installer when the user opts in

## Runtime Behavior

Use a **sequential retrieval model** in v1:

1. detect qmd and local corpus availability
2. run qmd lookup first when available
3. evaluate result quality
4. fall back to Salesforce-aware retrieval when results are weak or missing
5. answer with grounded official sources

## Why This Architecture

This model gives the best balance of:

- correctness
- operational simplicity
- user choice
- compatibility with both qmd and non-qmd environments

## Local Storage

All downloaded/scraped Salesforce documentation artifacts stay **local to the user machine**:

- manifests
- raw PDFs
- raw HTML captures
- normalized markdown
- qmd index/embedding state

These artifacts should **not** be committed into the public Git repo.

## v1 Boundaries

Keep v1 intentionally limited:

- small pilot corpus
- one qmd collection
- targeted fallback retrieval
- no broad automatic crawling during normal queries
- no parallel qmd + scraping fusion by default

## Expansion Rule

Expand beyond the pilot corpus only after benchmark evidence shows that:

- qmd-first mode is reliable
- no-qmd mode is still materially useful
- fallback thresholds are well tuned
- answer grounding remains strong
