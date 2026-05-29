---
name: diverge
description: Generate genuinely diverse options for an OPEN-ENDED problem using the "diverge then focus" pattern (claude-adhd). Spawns N isolated ideation branches under different cognitive frames across cheap LLMs in parallel (no shared context = no anchoring), then runs a critic that clusters, flags seductive-but-broken "traps", and deepens the best. Use for design decisions, naming, API surface design, architecture options, debugging hypotheses, or any "give me a few good ways to X". NOT for convergent or execution work.
---

# diverge — diverge then focus

A native (no-plugin) implementation of the claude-adhd pattern, built on the
`~/.claude/bin/llm` multi-LLM harness. Cheap models do the wide divergence in
parallel; Opus does the smart focus.

## When to use
Open-ended, divergent problems where premature anchoring is the enemy:
- "What are a few ways to design / structure / name X?"
- Architecture or API-surface options, schema choices, tradeoff exploration
- Debugging: generate competing hypotheses for a bug before chasing one
- Any time the first idea shouldn't win by default

Do **not** use for convergent execution (writing the code, running a migration) —
that's the verification gate's job, not this.

## How to run it (preferred in-session flow: diverge cheap, focus on Opus)

1. Run Phase 1 only and capture the raw ideas:
   ```bash
   /Users/sashabogojevic/.claude/bin/diverge --raw --frames 6 --ideas 5 "<the problem>"
   ```
   This fans 6 isolated frames across different cheap model families (DeepSeek /
   GLM / Gemini / Kimi) in parallel. Each `🔶 EXTERNAL-LLM` banner is visible, and
   every call is logged to the cost ledger. It prints `{"problem","ideas":[...]}`.

2. **You (Opus) then do the FOCUS pass yourself** on the returned ideas — this is
   where the quality matters and where the trusted model belongs:
   - Cluster the ideas into distinct approaches.
   - Flag **traps**: ideas that look attractive but are broken/risky — say *why*.
   - Pick the top K and deepen each into: why it wins, risks, concrete first steps.
   - Present clusters → traps → deepened top picks.

## Fully autonomous mode (no Opus in the loop)
For scripts or when a cheap critic is acceptable, let the tool do both phases:
```bash
diverge "<problem>" --frames 6 --ideas 5 --top 3            # critic defaults to glm-4.6
diverge "<problem>" --critic kimi                            # choose the critic model
```

## Flags
- `--frames N`   how many cognitive frames (default 6, max 12)
- `--ideas N`    ideas per frame (default 5)
- `--top N`      how many to deepen in the focus pass (default 3)
- `--critic M`   critic model for autonomous mode (default glm-4.6)
- `--raw`        Phase 1 only → ideas JSON for Opus to focus on (preferred here)
- `--list-frames` show the cognitive frames

## Notes
- Isolation is the point: branches never see each other or the critic's view, so
  they don't converge early. Different model *families* add further diversity.
- Cost is tiny (cheap models, parallel) and fully tracked — check `llm ledger`.
- Edit the frame library or `DIVERGE_MODELS` directly in `~/.claude/bin/diverge`.
