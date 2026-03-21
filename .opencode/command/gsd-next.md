---
description: Automatically advance to the next logical step in the GSD workflow
tools:
  read: true
  bash: true
  grep: true
  glob: true
  skill: true
---
<objective>
Detect the current project state and automatically invoke the next logical GSD workflow step.
No arguments needed — reads STATE.md, ROADMAP.md, and phase directories to determine what comes next.

Designed for rapid multi-project workflows where remembering which phase/step you're on is overhead.
</objective>

<execution_context>
@/home/diego/Documentos/projetos/data-products/sliceinsights/.opencode/get-shit-done/workflows/next.md
</execution_context>

<process>
Execute the next workflow from @/home/diego/Documentos/projetos/data-products/sliceinsights/.opencode/get-shit-done/workflows/next.md end-to-end.
</process>
