# sf-docs Runtime Workflow

This document defines the first-version runtime behavior for `sf-docs`.

## Query-Time Flow

Use this sequence in order:

1. **Detect qmd**
   - check whether `qmd` is available on `PATH`
   - check whether the local Salesforce docs corpus exists and is populated

2. **qmd lookup if available**
   - search the local normalized corpus first
   - prefer exact API names, CLI commands, error strings, and quoted terms for lexical matching

3. **Evaluate hit quality**
   - if results are strong, answer from local docs
   - if results are weak, incomplete, or unrelated, fall back

4. **Salesforce-aware fallback retrieval**
   - identify likely doc family first (`platform`, `atlas`, `help`, `pdf`)
   - try the most likely official guide/article root
   - for JS-heavy pages, prefer Salesforce-aware browser scraping with Shadow DOM and legacy container heuristics
   - use targeted fallback, not broad crawling
   - prefer official PDFs when HTML retrieval is shell-rendered or unstable

5. **Answer with source grounding**
   - cite the exact official source URL
   - identify whether the source came from local qmd, HTML retrieval, or PDF fallback
   - call out uncertainty when the retrieval was partial or indirect

## Weak Result Rules

Fall back when:

- no qmd results are returned
- returned guides are clearly unrelated
- the exact requested concept/identifier does not appear
- snippets are too fragmentary to support a reliable answer
- the query is release-sensitive and the local corpus seems stale

## No-qmd Special Instructions

When qmd is not installed or not usable:

- do **not** rely on naive generic `web_fetch` expectations for Salesforce docs
- identify the likely official guide family first
- prefer official URLs over blog summaries
- try `help.salesforce.com` article views carefully because shell content is common
- try official PDFs when guide HTML is unstable

## Keep Fallback Targeted

During normal query-time retrieval:

- do **not** crawl the entire Salesforce docs universe
- do **not** launch a broad sync automatically
- target likely guide roots, exact official pages, and candidate PDFs first

Broad crawling belongs in explicit sync/index workflows, not in routine question answering.

## Separate Sync / Index Workflow

For qmd-backed setups, keep query-time retrieval separate from corpus maintenance.

Recommended operator workflow:

1. `discover` — build/update the guide manifest
2. `fetch` — retrieve targeted HTML/PDF sources
3. `normalize` — convert sources into markdown with provenance
4. `index` — add/update qmd collection and embeddings
5. `refresh` — re-run discovery/fetch for changed or missing guides

## Persistence Policy

Useful fetched assets may be stored locally for future indexing:

- official PDFs in `~/.sf-docs/raw/pdf/`
- normalized markdown in `~/.sf-docs/normalized/md/`
- manifest/status files in `~/.sf-docs/manifest/`

However:

- query-time fallback should not trigger uncontrolled large-scale fetches
- persisted content stays local to the user machine
- fetched Salesforce docs content should not be committed into the public repo

## Repo Hygiene & Legal Constraints

Keep the public repo limited to:

- skill definitions
- installer logic
- helper scripts
- schemas, templates, and examples

Keep Salesforce documentation artifacts local-only:

- downloaded PDFs
- scraped HTML captures
- normalized markdown corpus
- qmd indexes and embeddings
