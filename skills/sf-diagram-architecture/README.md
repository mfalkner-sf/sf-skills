# sf-diagram-architecture

Generates presentation-quality Salesforce architecture diagrams following the official Salesforce Architects visual standards from architect.salesforce.com.

## What it does

Produces SVG slide diagrams using the `generate_architecture_diagram` MCP tool from the `sfdc-arch-mcp` server. Supports 6 diagram types: Solution Architecture, Interaction Process Flow, System Landscape, Business Capability Map, Roadmap, and Data Model ERD.

## Key features

- Standards-compliant SVG output (white bg, orthogonal connectors, circle icons)
- Channel-based connector routing that avoids crossing through cards
- 2,700+ icons including verified Salesforce product SVGs and Kit of Parts assets
- Reusable SVG component library for pixel-exact output
- PDF export via headless Chrome

## When to use

Use this skill for customer-facing architecture artifacts, presentation slides, and any diagram that needs to match official Salesforce visual language. For quick text-based diagrams in docs/README, use `sf-diagram-mermaid` instead.

## MCP server

Requires the `sfdc-arch-mcp` MCP server at `/Users/michael.falkner/sfdc-arch-mcp`.
