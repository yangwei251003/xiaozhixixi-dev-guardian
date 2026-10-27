---
name: guard-xiaozhixixi-development
description: Enforce research-first, skill-aware, test-gated development for the 小智析析 project. Use before every stage or implementation task, when selecting tools from research/skills-map.md, when recording stage completion, and when preparing a Progress.md handoff after each pair of stages.
---

# Guard 小智析析 Development

Keep every development step traceable to current research, an appropriate installed Skill or plugin, and an explicit verification result.

## Before every task

1. Locate the project root containing `SPEC.md`.
2. Read `research/skills-map.md` and the current stage research note.
3. Run:

```powershell
python scripts/guardian.py preflight --project-root <root> --stage <0-7> --task "<task>"
```

4. Load and announce every relevant Skill returned by the preflight. If none matches, select the closest installed tool and add the mapping before implementation.
5. Confirm the task has a test or observable acceptance check. For behavior changes, follow Superpowers TDD.

Do not begin implementation while preflight reports missing research or tool mapping.

## Before every stage

Research current official documentation, strong open-source implementations, and relevant competition-winning product patterns. Write `research/stage-<N>-research.md` with dated links, reusable ideas, license constraints, and concrete decisions. Prefer primary sources and never copy GPL/AGPL code.

For stage 0, use `research/调研报告.md` as the research artifact.

## Record progress

After a stage passes its acceptance checks, run:

```powershell
python scripts/guardian.py record-stage --project-root <root> --stage <N> --summary "<verified result>" --tests "<commands and results>" --next "<next work>"
```

Record only evidence that was actually observed.

## Handoff every two stages

After stages `0-1`, `2-3`, `4-5`, or `6-7`, run:

```powershell
python scripts/guardian.py handoff --project-root <root> --completed <pair> --next-stage <N>
```

Review and enrich the generated `Progress.md` with key decisions, known risks, exact commands, and unresolved work. End the current task and tell the user to open a new window. In the new window, provide `SPEC.md`, `Progress.md`, `research/skills-map.md`, the next stage research note, and the repository path. Never include `.env` values in a handoff.

Use [handoff-schema.md](references/handoff-schema.md) when checking handoff completeness.
