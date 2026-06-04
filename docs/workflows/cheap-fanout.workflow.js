// cheap-fanout.workflow.js — reference pattern for the Claude Code `Workflow` tool.
//
// THE PROBLEM this solves: Workflow `agent()` calls inherit the session model, so an
// Opus-driven workflow runs EVERY subagent on Opus — including dumb fan-out scans. That's
// the single biggest avoidable cost in multi-agent work.
//
// THE PATTERN: tier the work by what each phase actually needs.
//   • Fan-out / grunt  -> a HAIKU agent that is just a courier: it shells out to `scrooge`,
//     so the real work runs on an EXTERNAL model 30-100x cheaper than Opus (and shows up
//     live in `scrooge watch` + the cost ledger).
//   • Synthesis / judgment -> OPUS, once, over the cheap findings. The only place it earns it.
//
// COST SHAPE (illustrative, 20 items): 20 Opus scans + 1 Opus synth  ≈  expensive.
//   vs  20 Haiku couriers (≈free) + 20 scrooge calls (~$0.001 ea) + 1 Opus synth  ≈  ~99% less.
//
// RUN IT: pass the items to process as `args`, e.g. via the Workflow tool:
//   Workflow({ scriptPath: ".../cheap-fanout.workflow.js", args: ["a.md", "b.md", "c.md"] })
// Requires `scrooge` on PATH (token-scrooge installed) for the courier step.

export const meta = {
  name: 'cheap-fanout-synthesis',
  description: 'Fan grunt work across cheap models (Haiku courier → Scrooge), synthesize on Opus',
  phases: [
    { title: 'Scan', detail: 'one Haiku courier per item; each shells out to scrooge', model: 'haiku' },
    { title: 'Synthesize', detail: 'Opus combines the cheap findings', model: 'opus' },
  ],
}

// `args` is the work-list (file paths, repo names, URLs…). Fallback keeps the script runnable.
const items = Array.isArray(args) && args.length ? args : ['README.md', 'package.json']
log(`cheap-fanout over ${items.length} item(s) — Haiku+scrooge to scan, Opus to synthesize`)

phase('Scan')
// Each worker is a HAIKU agent acting as a courier: it runs ONE scrooge command and returns
// its stdout. The grunt LLM work happens on an external cheap model, not on Claude at all.
// Difficulty is `easy` here because summarizing a file is easy — be honest so the weigher
// keeps it on the cheapest capable model. (For real code/reasoning grunt, use -d medium/hard.)
const findings = await parallel(items.map((item, i) => () =>
  agent(
    [
      `Run EXACTLY this shell command and return ONLY its stdout — no preamble, no fences:`,
      `  scrooge -t summarize -d easy < ${JSON.stringify(item)}`,
      `If the command errors (e.g. file missing), return the single line: MISSING ${item}`,
    ].join('\n'),
    { model: 'haiku', label: `scan:${item}`, phase: 'Scan' }
  ).catch(() => `ERROR ${item}`)
))

// For many items you'd add `--spread N` so the batch fans across models for throughput:
//   scrooge -t summarize -d easy --spread 3 < file

phase('Synthesize')
// The ONE part that benefits from a frontier model: reconcile the cheap findings into a brief.
const report = await agent(
  [
    `You are given ${findings.length} short summaries produced by cheap models.`,
    `Synthesize them into one coherent brief: the key themes, anything important, and any`,
    `contradictions between sources. Be concise.`,
    ``,
    ...findings.map((f, i) => `### ${items[i]}\n${f}`),
  ].join('\n'),
  { model: 'opus', label: 'synthesize', phase: 'Synthesize' }
)

return report
