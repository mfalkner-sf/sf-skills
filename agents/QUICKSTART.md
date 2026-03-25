# Agent Team Quick Start Guide

Get started with the Prompt Wizard agent team in 5 minutes.

## Installation Status

### Global Agents (`~/.claude/agents/`)
- `orchestrator.md` - Workflow coordinator
- `frontend-developer.md` - UI/component specialist
- `backend-developer.md` - Server-side logic
- `salesforce-developer.md` - Platform operations
- `uiux-designer.md` - Design and accessibility
- `content-writer.md` - Copy and documentation
- `qa-engineer.md` - Testing and validation

### Project-Specific Agents (`./agents/`)
- `agentforce-orchestrator.md` - Task tool routing, wizard coordination
- `nextjs-frontend-developer.md` - React 19 + Zustand specialist
- `nextjs-backend-developer.md` - Compiler + store specialist
- `agentforce-salesforce-developer.md` - Agent Script DSL + metadata specialist
- `agentforce-uiux-designer.md` - Wizard UX + Tailwind specialist
- `agentforce-content-writer.md` - Wizard copy + terminology specialist
- `agentforce-qa-engineer.md` - Compiler tests + output validation specialist

### Supporting Files
- `workflows/` - 4 predefined workflows (feature, bug fix, design review, deployment)
- `templates/` - Agent and handoff templates
- `cursor-prompts/` - 7 Cursor-compatible prompts
- `generic-prompts/` - 7 generic AI platform prompts
- `CLAUDE.md` - Project configuration (root directory)

## Quick Test

Try these commands to test agent activation:

### 1. Test Orchestrator (Multi-Agent)
```
Me: "Help me plan a new wizard step for the Agent Script wizard"
  -> Orchestrator creates workflow plan and routes to specialists
```

### 2. Test Frontend Developer
```
Me: "Create a new wizard step component"
  -> Frontend Developer builds React component with Zustand + React Hook Form
```

### 3. Test Backend Developer
```
Me: "Add a new field to the Agent Script compiler"
  -> Backend Developer updates types, store, and compiler
```

### 4. Test QA Engineer
```
Me: "Write tests for the prompt template compiler"
  -> QA Engineer creates unit tests validating XML output
```

### 5. Test Content Writer
```
Me: "Update the help text for the Variables step"
  -> Content Writer writes clear, user-friendly copy
```

### 6. Test Agent Chaining
```
Me: "Build an account search component"
  -> Orchestrator analyzes
  -> Routes to UI/UX Designer -> Backend -> Frontend -> QA
  -> Reports completion
```

## Agent Reference

| Agent | subagent_type | Model | Use When |
|---|---|---|---|
| Orchestrator | `orchestrator` | opus | Planning, coordinating multi-step tasks |
| Frontend Developer | `frontend-developer` | sonnet | Building wizard steps, React components |
| Backend Developer | `backend-developer` | opus | Compilers, stores, types, business logic |
| Salesforce Developer | `salesforce-developer` | sonnet | Deploying, retrieving, org management |
| UI/UX Designer | `uiux-designer` | opus | Designing interfaces, accessibility audits |
| Content Writer | `content-writer` | sonnet | Writing copy, labels, documentation |
| QA Engineer | `qa-engineer` | opus | Testing, validation, bug tracking |

## Common Commands

### Check Installed Agents
```bash
ls -la ~/.claude/agents/
ls -la ./agents/
```

### Verify Project Config
```bash
cat ./CLAUDE.md
```

### Use in Cursor
1. Copy prompt from `./agents/cursor-prompts/cursor-orchestrator.md`
2. Add to `.cursorrules` file in project root
3. Cursor will follow agent guidelines

### Use in Generic AI Platform
1. Copy prompt from `./agents/generic-prompts/generic-orchestrator.txt`
2. Paste into system message or start of conversation
3. Reference agent by role ("As the Orchestrator, help me...")

## Routing Quick Reference

| You Say | Agent Invoked | What Happens |
|---|---|---|
| "Build a component" | Orchestrator -> multi-agent | Full workflow |
| "Fix this compiler bug" | Backend Developer | Direct fix |
| "Write tests" | QA Engineer | Test creation |
| "Update the help text" | Content Writer | Copy update |
| "Deploy to sandbox" | Salesforce Developer | Deployment |
| "Review accessibility" | UI/UX Designer | Accessibility audit |
| "Plan a new feature" | Orchestrator | Workflow planning |

## Troubleshooting

### Agent Not Activating
- Ensure request is clear and specific
- Mention agent role explicitly ("I need the Frontend Developer to...")
- Check file context (agents activate based on file patterns)

### Wrong Agent Activated
- Override: "Actually, I need the [Agent Name] for this"
- Orchestrator will adjust workflow

### Need Multiple Agents
- Request parallel work: "Have Frontend and Backend work together on this"
- Or: "I need all agents for a full feature implementation"

## Next Steps

1. **Read Full Documentation**: See `./agents/README.md`
2. **Review CLAUDE.md**: See `./CLAUDE.md` for project configuration
3. **Review Workflows**: Check `./agents/workflows/` for detailed processes
4. **Test Agent Chaining**: Try a multi-step workflow
5. **Customize**: Modify agents in `./agents/` for project-specific needs

---

**Version**: 2.0.0
**Last Updated**: 2026-02-10
**Ready to Use**: Yes - All agents installed and operational
