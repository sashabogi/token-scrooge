# Feature: Live training — per-model failure-pattern lessons

**Status:** proposed (2026-06-04)
**Motivation source:** dogfood run on the `polymarket-playground` project — cheap models
produced the *same classes* of bug repeatedly; the orchestrator fixed them by hand each time
and paid frontier tokens to do so. We should preempt known per-model failure patterns instead
of re-discovering and re-fixing them on every call.

## The idea

Scrooge accumulates **per-model (and per-task) "lessons"** — short corrective guardrails learned
from observed failures — and **auto-injects** the relevant ones into that model's system prompt at
routing time. So the next time the same model is routed the same kind of task, it already carries
the guardrails that previously had to be fixed by hand.

This is "live training" by **prompt augmentation**, not weight training: cheap, immediate, and
fully transparent (the injected guardrails are visible in the call).

## Why (concrete dogfood evidence)

In the 2026-06-04 polymarket dogfood, `deepseek-v4-flash` on `-t code/draft` tasks repeatedly:

1. **Assumed API array ordering** — read "best bid/ask" without sorting an order book's
   `bids`/`asks`, when the source doesn't guarantee order.
2. **Used `None` for empty numeric fields** where `0.0` (or the schema default) was required,
   breaking downstream arithmetic.
3. **Guessed JSON key names** instead of using the exact keys from the provided schema/example.

Each was caught and fixed by the (frontier) orchestrator — costing exactly the tokens Scrooge
exists to save. These are *stable, model-specific* patterns: ideal candidates to preempt.

## Design

### 1. Lessons store
`~/.token-scrooge/lessons.json` (gitignored, like `calls.jsonl`):

```json
{
  "deepseek-v4-flash": {
    "code":  ["Never assume array ordering from an API — sort bids/asks explicitly by price.",
              "Use 0.0 (or the schema default) for absent numeric fields, not None.",
              "Use the EXACT key names from the provided schema/example; never invent fields."],
    "*":     ["Return only what was asked; no prose preamble."]
  }
}
```

Keys: model id (full id and/or alias — resolve both), then task (`code`, `draft`, …) plus a `"*"`
bucket that applies to every task for that model. A top-level `"*"` model bucket can hold
universal lessons.

### 2. Injection at routing time
In `bin/scrooge`, after `resolve_model(...)` (≈ line 141) and before building messages (≈ line 158):

- Look up lessons for the resolved model id + alias, for the active `--task` and for `"*"`.
- Compose them into a short guardrail block and **prepend to the system message** (create one if
  `--system` was not passed; otherwise merge so the user's `--system` still leads).
- Keep it terse (lessons are one-liners) to avoid bloating the prompt / cost.
- A `--no-lessons` flag bypasses injection for A/B comparison.

### 3. `scrooge learn` — capture
```
scrooge learn -m deepseek -t code "Sort bids/asks explicitly; never assume API ordering."
scrooge lessons [-m deepseek] [-t code]      # list
scrooge forget  -m deepseek -t code <index>  # remove
```
`learn` appends (dedup on exact text); store is per-model/per-task. The orchestrator (Claude Code,
or any caller) runs `scrooge learn` the moment it fixes a recurring bug in a model's output — that
is the "training signal".

### 4. (Optional, later) assisted capture
A `scrooge-verify`-style pass, or a hook, could *suggest* a lesson when it detects a model's output
failed a check — surfaced for one-tap `scrooge learn`. Start manual; automate only if patterns are
frequent enough to be worth it.

## Guardrails on the guardrails
- **Terse + capped.** Cap lessons per (model,task) (e.g. 8) and total injected chars; lessons are
  one-liners. Prompt bloat would erode the cost savings Scrooge exists for.
- **Transparent.** Injected lessons appear in the call; `scrooge lessons` shows the store; a
  `--no-lessons` escape hatch exists.
- **Per-model, not global.** A weakness of deepseek isn't necessarily one of gemini — keep scopes
  separate so we don't over-constrain capable models.
- **Still not proof.** Lessons reduce *recurring* bugs; they do NOT make scrooge output verifiable.
  The build/test Definition-of-Done contract is unchanged.
- **Drift-aware.** When a model is retired (see `scrooge-drift`), prune its lessons.

## Seed lessons (from this session)
Ship these preloaded for `deepseek-v4-flash` (and review whether they generalize to other cheap
code models):
- `code`: "Never assume API array ordering — sort order-book bids/asks explicitly by price."
- `code`: "Use 0.0 (or the schema default) for absent numeric values, not None."
- `code`: "Use the exact key names from the provided schema/example; do not invent fields."

## Implementation notes
- Pure stdlib + a JSON file — consistent with Scrooge's zero-dep design.
- Touch points: `bin/scrooge` `resolve_model` / message build (≈ L141–L160); new `learn`/`lessons`/
  `forget` subcommands alongside `list`/`ledger`; `.gitignore` add `lessons.json`.
- Keep `registry.template.json` for *capabilities/pricing*; lessons are a separate, mutable,
  user-local store (not shipped in the template).

## Open questions
- Alias vs full-id keying — resolve both, store under full id, also match by alias.
- Should lessons be shareable/exportable (a curated `lessons.seed.json` shipped in the repo for new
  installs)? Probably yes for a small, vetted starter set; user-local store overrides/extends it.
