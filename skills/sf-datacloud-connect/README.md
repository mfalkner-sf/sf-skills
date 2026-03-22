# sf-datacloud-connect

Connection and connector workflows for Salesforce Data Cloud.

## Use this skill for

- listing available connector types
- inspecting configured connections
- testing a connection
- browsing source objects, databases, and fields
- preparing for stream creation

## Key reminders

- `connection list` requires `--connector-type`
- start with inspection before mutation
- use `2>/dev/null` to suppress linked-plugin warning noise
- some credential setup remains outside the CLI runtime

## Example requests

```text
"Show me which Data Cloud connections already exist in this org"
"Test my Redshift Data Cloud connection"
"What source objects are available on this Salesforce connector?"
"Help me set up a new Data Cloud source connection"
```

## Common commands

```bash
sf data360 connection connector-list -o myorg 2>/dev/null
sf data360 connection list -o myorg --connector-type SalesforceDotCom 2>/dev/null
sf data360 connection get -o myorg --name SalesforceDotCom_Home 2>/dev/null
sf data360 connection test -o myorg --name SalesforceDotCom_Home 2>/dev/null
```

## References

- [SKILL.md](SKILL.md)
- [../sf-datacloud/references/plugin-setup.md](../sf-datacloud/references/plugin-setup.md)
- [CREDITS.md](CREDITS.md)

## License

MIT License - See [LICENSE](LICENSE).
