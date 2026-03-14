# sf-docs Local Corpus Layout

`sf-docs` stores retrieved Salesforce documentation **locally on the user's machine**. Nothing in this layout should be committed into the public `sf-skills` repository.

## Default Root

```text
~/.sf-docs/
```

## Recommended Layout

```text
~/.sf-docs/
├── manifest/
│   ├── guides.json            # discovered guide roots and metadata
│   └── fetch-status.json      # optional fetch/index status
├── raw/
│   ├── pdf/                   # downloaded official PDFs
│   └── html/                  # optional raw HTML captures
├── normalized/
│   └── md/                    # canonical markdown corpus for qmd indexing
│       ├── apexcode/
│       ├── api_rest/
│       ├── lwc/
│       └── ...
├── qmd/
│   ├── qmd.yml                # optional qmd config
│   └── notes.txt              # setup notes / operator hints
└── logs/
    └── fetch.log              # optional operational logs
```

## Canonical Content Rules

- **Markdown is the canonical indexed format**
- PDFs may be retained in `raw/pdf/` for provenance and reprocessing
- Page-level markdown should be preferred when available and clean
- Each normalized markdown document should preserve:
  - title
  - source URL
  - guide/book id when known
  - doc family (`atlas`, `platform`, `help`, `pdf`)
  - fetch timestamp

## Runtime Detection Rules

When `sf-docs` runs, determine mode in this order:

1. Is the `qmd` CLI available on `PATH`?
2. Does a local Salesforce docs corpus exist under `~/.sf-docs/` (or configured equivalent)?
3. If qmd exists but the corpus/index is missing or empty, treat the environment as **no-qmd for retrieval purposes**
4. If qmd exists and the corpus is populated, use **qmd-first mode**
5. Otherwise, use **Salesforce-aware scraping mode**

## Operational Guidance

- Use a **single local root** so future sync/index commands are predictable
- Keep official downloaded content **outside the git repo**
- Avoid storing transient browser shell output as canonical docs
- Prefer guide-organized paths so qmd path/context signals remain useful
