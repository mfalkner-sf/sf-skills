---
name: sf-diagram-architecture
description: >
  Salesforce standards-compliant architecture diagrams using the sfdc-arch-mcp server.
  Generates presentation-quality SVG slides following official Salesforce Architects
  visual language from architect.salesforce.com.
  TRIGGER when: user says "architecture diagram", "solution architecture", "system landscape",
  "capability map", "process flow diagram", "data model", "ERD", "roadmap", or asks for
  Salesforce-branded diagrams, presentation slides, or customer-facing architecture artifacts.
  DO NOT TRIGGER when: user wants simple Mermaid text diagrams (use sf-diagram-mermaid),
  or wants non-Salesforce diagrams.
license: MIT
metadata:
  version: "1.0.0"
  author: "Michael Falkner"
  scoring: "100 points across 5 categories"
---

# sf-diagram-architecture: Salesforce Standards-Compliant Architecture Diagrams

Use this skill when the user needs **presentation-quality architecture diagrams** that follow the official Salesforce Architects visual standards. This skill produces SVG slides embedded in HTML, suitable for customer presentations, architecture reviews, and documentation.

## When This Skill Owns the Task

Use `sf-diagram-architecture` when the user wants:
- Solution Architecture diagrams (how systems integrate)
- System Landscape diagrams (big picture of all systems)
- Interaction Process Flow diagrams (step-by-step data/event flows)
- Business Capability Maps (what a solution does, not how)
- Technology Roadmaps (phased rollout plans)
- Data Model ERDs (entity relationships with crow's foot notation)
- Customer-facing architecture slides with Salesforce branding
- Any diagram that needs to follow Salesforce Architects standards

Delegate elsewhere when the user wants:
- Quick text-based Mermaid diagrams for docs/README → [sf-diagram-mermaid](../sf-diagram-mermaid/SKILL.md)
- Non-Salesforce system diagrams → use general diagramming
- Object discovery before building an ERD → [sf-metadata](../sf-metadata/SKILL.md) first

---

## MCP Server Reference

The `sfdc-arch-mcp` server at `/Users/michael.falkner/sfdc-arch-mcp` provides the `generate_architecture_diagram` tool. Use `get_sfdc_specs` with `category: 'diagram_standards'` to retrieve the full visual standards.

---

## 6 Diagram Types

| Type | Layout | When to Use |
|------|--------|-------------|
| `solution-architecture` | Center-stage: sources → platform → destinations | How systems integrate and communicate |
| `interaction-process-flow` | Left-to-right with numbered steps | Workflows, data flows, user journeys |
| `system-landscape` | Horizontal tiered layers | Big picture view of all systems |
| `business-capability-map` | Nested zones, NO connectors | What a solution can do (business capabilities) |
| `roadmap` | Gantt-style timeline grid | Time-based delivery planning |
| `data-model-erd` | Entity boxes with crow's foot notation | Object model and field relationships |

---

## Required Context to Gather First

Before generating a diagram, determine:
1. **Diagram type** — which of the 6 types best fits the need
2. **Systems involved** — Salesforce products, external systems, integration tools
3. **Relationships** — data flows, events, API calls between systems
4. **Scope** — what to include vs. exclude (keep diagrams focused)
5. **Audience** — technical deep-dive vs. executive summary

---

## Recommended Workflow

### 1. Choose the diagram type
Match the user's intent to one of the 6 types. If unclear, ask.

### 2. Design the layout with routing in mind
**This is the most critical step.** Position nodes in clear columns/rows with 60px+ gaps between them for connector routing channels.

**Solution Architecture layout:**
- Left column (x=24-184): Source systems, channels
- Center zone (x=250-670): Salesforce platform with nested product cards
- Right column (x=730-930): Downstream systems
- Bottom bar (full width): Integration layer (MuleSoft)
- Below: Data sources

**System Landscape layout:**
- 4 horizontal tiers: Channels → Core Platform → Integration → External
- Cards auto-center within zones
- Vertical connectors between tiers

**Process Flow layout:**
- 3-4 columns left to right
- Numbered step circles on connectors
- Bottom infrastructure zone

### 3. Define connections with routing awareness
- Set `style: 'sync'` for direct/synchronous calls
- Set `style: 'async'` for event-driven/asynchronous flows
- Set `style: 'bidirectional'` for request/response pairs
- Add `label` for pill text on connectors
- Add `stepNumber` for process flow numbered circles
- Connectors auto-route through gaps between columns — leave space

### 4. Generate and review
Call `generate_architecture_diagram` with the configuration. Review the output for:
- Connectors not crossing through cards
- Cards fitting within zones
- Text not bleeding outside cards
- Legend explaining all icon/line types used

---

## Visual Standards (mandatory)

All diagrams MUST follow these rules:

### Background & Header
- White `#FFFFFF` background — NO gradients, decorative elements, or mountain silhouettes
- Salesforce cloud logo at top-left
- Bold 22px navy title
- Gray 10px description (2-4 lines, max 50% width)
- Floating legend box at top-right with icon+label pairs

### Cards
- Optional circle icon inline-left of title
- Bold 11px navy title, gray 9px attribute list, footer icon row
- White background, 1px `#C9C9C9` border, 8px radius
- **NO colored top-bar. NO drop shadow.** Cards use `<clipPath>` to prevent content overflow.

### Connectors
- **Orthogonal elbow only** — 90° turns using H and V path commands. NO Bezier curves. NO diagonals.
- Solid 1.5px `#3E3E3C` for synchronous. Dashed 1.5px `#706E6B` for asynchronous.
- Pill labels: white bg, `#C9C9C9` border, centered on line
- Numbered step circles: 26px navy `#032D60` circle with white number

### Connector Routing (critical)
- Lines must NEVER pass through cards or zones
- Route through **routing channels** — the gaps between card columns or tier rows
- In 3-column layouts: vertical channels at midpoint of each gap
- In tiered layouts: horizontal channels between tier bottoms and next tier tops
- Fan out from card edges: 15-20px spacing when multiple lines leave same edge
- Parallel tracks: 8-12px offset for multiple lines in same channel

### Zones
- Solid 1.5px `#C9C9C9` border, 10px radius, `#F3F3F3` fill
- Icon + bold label at top-left inside zone
- Cards auto-center horizontally within zones

### Colors

| Token | Hex | Usage |
|-------|-----|-------|
| Navy | `#032D60` | Titles, primary text, step circles |
| Salesforce Blue | `#0176D3` | Core platform |
| Sales | `#0B827C` | Sales Cloud |
| Service | `#9E2A7D` | Service Cloud |
| Marketing | `#F49756` | Marketing Cloud |
| Commerce | `#43B02A` | Commerce Cloud |
| Data Cloud | `#1B96FF` | Data Cloud |
| MuleSoft | `#00A0DF` | Integration |
| Tableau | `#E97627` | Analytics |
| Slack | `#4A154B` | Collaboration |
| Gray | `#706E6B` | Secondary text, async connectors |
| Border | `#C9C9C9` | Card/zone borders |
| Zone fill | `#F3F3F3` | Zone backgrounds |

---

## Generation Guardrails

**BLOCK these anti-patterns:**
- Bezier curves or diagonal connector lines
- Colored top-bars on cards
- Mountain silhouettes or gradient backgrounds
- Dashed zone borders (except in ERD record types)
- Connectors routing through cards
- More than 15 nodes on a single slide (split into multiple diagrams)

**WARN on:**
- Missing legend/key when using multiple icon colors
- Missing description in header
- Capability maps with connectors (they should have none)
- Process flows without numbered steps

---

## Output Format

The tool outputs a complete HTML file with embedded SVG. The output can be:
- Opened directly in a browser
- Printed to PDF via `@page { size: letter landscape; margin: 0; }`
- Exported to PNG/PDF via the `export_to_image` MCP tool
- Saved to a file via the `outputPath` parameter

---

## Cross-Skill Integration

| Need | Delegate to | Reason |
|------|-------------|--------|
| Quick text-based diagram | [sf-diagram-mermaid](../sf-diagram-mermaid/SKILL.md) | Mermaid for docs/README |
| Object discovery for ERD | [sf-metadata](../sf-metadata/SKILL.md) | Get real schema before building ERD |
| Integration pattern guidance | [sf-integration](../sf-integration/SKILL.md) | Understand sync/async/event patterns |
| Agentforce architecture | [sf-ai-agentforce](../sf-ai-agentforce/SKILL.md) | Agent topology and behavior |
| Architecture review/scoring | `criticize_architecture` MCP tool | Well-Architected pillar assessment |
| Diagram validation | `validate_diagram` MCP tool | Pre-flight structural checks |

---

## Reference Map

### Standards & rules
- `/Users/michael.falkner/sfdc-arch-mcp/scraper/diagram_standards.json` — complete visual standards
- `/Users/michael.falkner/sfdc-arch-mcp/CLAUDE.md` — project documentation
- `/Users/michael.falkner/sfdc-arch-mcp/docs/PRESENTATION_DIAGRAMS.md` — full standards reference

### Component library
- `/Users/michael.falkner/sfdc-arch-mcp/src/components/svg-components.ts` — all reusable SVG components

### Templates
- `/Users/michael.falkner/sfdc-arch-mcp/context/templates/` — one HTML template per diagram type

### Visual references
- `/Users/michael.falkner/sfdc-arch-mcp/context/Architecture Diagram Components/` — 55+ official reference diagrams organized by type (Solution Architecture, Process Flow, System Landscape, Capability Map, Roadmap)

---

## Score Guide

| Category | Points | Criteria |
|----------|--------|----------|
| Correct diagram type | 15 | Type matches the use case |
| Visual standards compliance | 25 | White bg, orthogonal connectors, no top-bars |
| Connector routing quality | 25 | No lines through cards, proper channels, fan-out |
| Layout & spacing | 20 | Clear gaps, centered cards, no overflow |
| Documentation | 15 | Legend, description, proper labels |

| Score | Meaning |
|-------|---------|
| 90-100 | Presentation-ready, matches official Salesforce reference diagrams |
| 75-89 | Professional quality with minor polish needed |
| 60-74 | Functional but needs layout or routing improvements |
| 40-59 | Significant visual issues, needs rework |
| < 40 | Does not meet standards |
