# Prompt Wizard - Agent Team

This directory contains specialized AI agents designed to improve development efficiency and code quality for the Prompt Wizard project.

## Overview

The agent team consists of **7 specialized roles** coordinated by an orchestrator that routes requests using Claude Code's `Task` tool with the appropriate `subagent_type`.

| # | Agent | subagent_type | Model | Role |
|---|---|---|---|---|
| 1 | **Orchestrator** | `orchestrator` | opus | Workflow coordinator, agent routing |
| 2 | **UI/UX Designer** | `uiux-designer` | opus | Wizard UX, Tailwind, accessibility |
| 3 | **Backend Developer** | `backend-developer` | opus | Compilers, Zustand stores, types |
| 4 | **Frontend Developer** | `frontend-developer` | sonnet | React components, wizard steps |
| 5 | **Content Writer** | `content-writer` | sonnet | Labels, help text, error messages |
| 6 | **QA Engineer** | `qa-engineer` | opus | Tests, validation, coverage |
| 7 | **Salesforce Developer** | `salesforce-developer` | sonnet | Deployments, metadata, org ops |

## Agent Locations

### Global Agents (Reusable Across All Projects)
Located in `~/.claude/agents/`:
- `orchestrator.md`
- `frontend-developer.md`
- `backend-developer.md`
- `salesforce-developer.md`
- `uiux-designer.md`
- `content-writer.md`
- `qa-engineer.md`

### Project-Specific Agents (Prompt Wizard)
Located in `./agents/` - extend global agents with project context:

| File | Extends | Specialization |
|---|---|---|
| `agentforce-orchestrator.md` | `orchestrator.md` | Task tool routing, multi-agent workflows, wizard coordination |
| `nextjs-frontend-developer.md` | `frontend-developer.md` | React 19, Zustand, React Hook Form, wizard step components |
| `nextjs-backend-developer.md` | `backend-developer.md` | Compilers, Zustand stores, TypeScript types, Zod schemas |
| `agentforce-salesforce-developer.md` | `salesforce-developer.md` | Agent Script DSL, GenAiPromptTemplate XML, schema validation |
| `agentforce-uiux-designer.md` | `uiux-designer.md` | Wizard UX, Tailwind CSS 4, progressive disclosure, form design |
| `agentforce-content-writer.md` | `content-writer.md` | Wizard microcopy, Agentforce terminology, step descriptions |
| `agentforce-qa-engineer.md` | `qa-engineer.md` | Compiler tests, store tests, output format validation |

## How to Use

### Automatic Activation (Preferred)
Agents automatically activate based on your request and file context:

```
You: "Build an account search component"
  -> Orchestrator analyzes -> Routes to UI/UX Designer -> Backend Developer -> Frontend Developer -> QA Engineer
```

```
You: "Fix the compiler for prompt templates"
  -> Routes directly to Backend Developer
```

```
You: "Deploy changes to my org"
  -> Routes directly to Salesforce Developer
```

### Manual Invocation
You can explicitly request an agent:

```
You: "I need the Frontend Developer agent to build a new wizard step"
You: "Have the QA Engineer write tests for the compiler"
You: "Route this to the Content Writer for help text"
```

### Agent Chaining
Agents automatically suggest the next agent in the workflow:

```
UI/UX Designer completes -> Suggests Backend Developer for types/stores
Backend Developer completes -> Suggests Frontend Developer for components
Frontend Developer completes -> Suggests Content Writer for copy
Content Writer completes -> Suggests QA Engineer for testing
QA Engineer completes -> Suggests Salesforce Developer for deployment
```

## Workflows

### Feature Development Workflow
See `./workflows/feature-development.md`:

1. **UI/UX Designer** -> Design spec, wireframes, accessibility requirements
2. **Backend Developer** -> Types, Zustand store, compiler logic
3. **Frontend Developer** -> React wizard step components
4. **Content Writer** -> Labels, help text, error messages
5. **QA Engineer** -> Unit tests, component tests, output validation
6. **Salesforce Developer** -> Deploy to sandbox (if applicable)
7. **QA Engineer** -> Post-deployment validation

### Bug Fix Workflow
See `./workflows/bug-fix.md`:

1. **Backend/Frontend Developer** -> Analyze and fix
2. **QA Engineer** -> Regression test, validate fix
3. **Salesforce Developer** -> Deploy to appropriate environment

### Design Review Workflow
See `./workflows/design-review.md`:

1. **UI/UX Designer** -> Accessibility audit, design critique
2. **Frontend Developer** -> Implement recommended fixes
3. **QA Engineer** -> Validate accessibility compliance
4. **Content Writer** -> Review copy for clarity

### Deployment Workflow
See `./workflows/deployment.md`:

1. **QA Engineer** -> Pre-deployment validation
2. **Salesforce Developer** -> Execute deployment
3. **QA Engineer** -> Post-deployment smoke tests

## Task Tool Integration

The orchestrator coordinates agents using Claude Code's `Task` tool:

### Sequential Execution
```
Task(subagent_type: "uiux-designer", prompt: "Design wizard step...")
  -> wait for result ->
Task(subagent_type: "backend-developer", prompt: "Create types based on design...")
  -> wait for result ->
Task(subagent_type: "frontend-developer", prompt: "Build component using types...")
```

### Parallel Execution
When agents don't depend on each other, they run simultaneously:
```
// Both launched at once
Task(subagent_type: "backend-developer", prompt: "Create types and store...")
Task(subagent_type: "content-writer", prompt: "Draft field labels...")
```

## Cross-Platform Support

### Claude Code (This Project)
Agents are designed for Claude Code and automatically activate via Task tool routing.

### Cursor
Cursor-compatible prompts available in `./cursor-prompts/`:
- Copy prompts to `.cursorrules` file

### Generic AI Platforms (ChatGPT, Claude Web, etc.)
Generic system prompts available in `./generic-prompts/`:
- Copy prompts to system message or paste at start of conversation

## Agent Features

### Hybrid Development Support
Agents automatically detect and adapt to:
- **Next.js Mode**: `.ts`, `.tsx`, `src/app/`, `src/components/`
- **Salesforce Mode**: `.agent`, `.prompt`, Metadata XML
- **Both**: Wizard generates Salesforce output from Next.js UI

### Model Selection
- **Opus**: Complex decision-making (Orchestrator, Backend, UI/UX, QA)
- **Sonnet**: Execution-focused tasks (Frontend, Salesforce, Content)

### Safety-First Design
- All agents validate before destructive actions
- Deployment/delete operations require confirmation
- Rollback plans documented
- Error handling with pause-investigate-fix pattern

### Integration with Project Rules
Agents reference global and project-specific rules:
- `~/.claude/rules/custom-general-Apex-rules.md`
- `~/.claude/rules/custom-general-Lwc-Html-rules.md`
- `~/.claude/rules/custom-general-Lwc-Js-rules.md`
- `~/.claude/rules/custom-general-ApexScript-rules.md`
- `~/.claude/rules/custom-general-MetaFiles-rules.md`
- `~/.claude/rules/versioningRules.md`
- `./CLAUDE.md` (project-specific)

## Troubleshooting

### Agent Not Activating
- Ensure your request is clear and specific
- Mention the agent role explicitly ("I need the Frontend Developer to...")
- Check file context (agents activate based on file patterns)

### Agent Suggests Wrong Next Agent
- You can override: "Actually, hand this to the [Agent Name] instead"
- Orchestrator will adjust workflow

### Need to Skip Agent
- Explicitly state: "Skip the [Agent Name], go directly to [Next Agent]"

### Multiple Agents Needed Simultaneously
- Request parallel work: "Have Frontend and Backend Developers work on this together"

## Contributing

To create a new agent:
1. Use template in `./templates/agent-template.md`
2. Define responsibilities, workflow, validation checklist
3. Add project-specific agent in `./agents/` extending a global agent
4. Update this README and the orchestrator routing

---

**Version**: 2.0.0
**Last Updated**: 2026-02-10
**Maintained By**: Prompt Wizard Team
