# Workflows + Token Scrooge

Claude Code's **`Workflow`** tool (and the plain **`Agent`** tool) spawn **Claude** subagents.
By default an `agent()` call **inherits the session model**, so an Opus-driven workflow runs
*every* subagent on Opus — including dumb fan-out scans. Scrooge can't fix this automatically:
the two systems are separate (Workflows spawn Claude; Scrooge is a CLI that calls external cheap
models). Integration is a **convention you apply when authoring the workflow**, not a global
switch.

There are two levers. Use both.

## Lever 1 — tier the Claude model per phase

`agent()` and `Agent` take a `model` option (`'haiku' | 'sonnet' | 'opus'`). Set it by what the
phase actually needs:

```js
const hits = await parallel(repos.map(r => () =>
  agent(`Scan ${r} for X`, { model: 'haiku' })));          // cheap fan-out workers
const mid  = await agent(`Analyze the hits`, { model: 'sonnet' });
const out  = await agent(`Synthesize:\n${hits}`, { model: 'opus' });  // Opus only where it earns it
```

Never leave `model` unset on a wide fan-out — that *is* the expensive Opus default you're trying
to avoid.

## Lever 2 — push pure grunt all the way out to Scrooge (30–100× cheaper)

A Workflow script can't run Bash directly, but an `agent()` can — so wrap Scrooge in a cheap
**courier** agent. The courier (Haiku) just runs one command and relays stdout; the real LLM work
runs on an external model (DeepSeek/Kimi/GLM…) and shows up in `scrooge watch` + the ledger:

```js
const summary = await agent(
  `Run exactly: scrooge -t summarize -d easy < ${file}\nReturn only its stdout.`,
  { model: 'haiku' });
```

Best for pure execution grunt inside a big fan-out: extraction, classification, drafting,
first-pass judging. Pass an honest `--difficulty` (`easy` for trivial work — cheap is correct),
and `--spread N` for large batches so they fan across models for throughput.

## Reference

[`cheap-fanout.workflow.js`](./cheap-fanout.workflow.js) is a runnable end-to-end example:
Haiku couriers → Scrooge to scan a work-list, then **one** Opus pass to synthesize. Run it with:

```js
Workflow({ scriptPath: "<repo>/docs/workflows/cheap-fanout.workflow.js", args: ["a.md", "b.md"] })
```

## Watching it

- **Claude side:** `/workflows` shows live phase/agent progress.
- **Scrooge side:** keep `scrooge watch` open (or `scrooge watch --here`) to see every external
  call stream by — model · task · cost · what it's doing.

## Why it isn't automatic

There's no hook that rewrites a workflow's per-agent model or reroutes `agent()` to an external
model — the model choice lives inside the (opaque) workflow script. So the durable fix is the
**authoring rule** (encoded in `~/.claude/CLAUDE.md`): tier `agent()` models by phase and delegate
execution grunt to `scrooge`. A workflow already running won't pick up a CLAUDE.md change until the
session restarts — to fix one mid-flight, just tell that session: *"re-run the fan-out phases with
`model: 'haiku'` and use `scrooge` for the grunt."*
