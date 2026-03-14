# sf-docs Implementation Order

Recommended implementation order for v1:

1. Define the `sf-docs` skill contract and make it a core skill
2. Define qmd-first / scrape-fallback runtime behavior
3. Add `sf-docs` to `README.md` and `skills-registry.json`
4. Add installer support for optional qmd installation
5. Define local corpus layout and runtime detection rules
6. Build the discovery manifest and seed guide set
7. Define targeted HTML/PDF normalization policy
8. Define qmd collection/context strategy
9. Define no-qmd Salesforce-aware retrieval instructions
10. Validate both runtime modes against real failing queries

## Notes

- qmd remains an optional external dependency
- `sf-docs` remains mandatory as part of the skill suite
- the pilot corpus should be kept intentionally small until benchmark results are healthy
- broad crawling and parallel retrieval are deferred until after v1 validation
