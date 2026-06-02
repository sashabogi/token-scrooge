<p align="center">
  <img src="assets/header.png" alt="Token Scrooge — make the cheap models do the grunt work" width="100%">
</p>

<h1 align="center">Token Scrooge</h1>

<p align="center">
  <b>Make the cheap models do the grunt work.</b><br>
  Your orchestrator stays in charge — routine, disconnected tasks get delegated to cheap LLMs you already pay for,<br>
  with a live cost ledger and a verification gate so the savings never cost you quality.
</p>

---

Frontier models (Claude Opus, GPT, Gemini Pro, …) are the best *orchestrators* — and the most expensive tokens you'll spend. But most of what an agent actually *does* — drafting a function, summarizing a file, extracting data, judging whether a test covers a claim — doesn't need a frontier model. **Token Scrooge** routes that work to DeepSeek / Kimi / GLM / Gemini / OpenRouter / OpenAI / xAI — typically **30–100× cheaper** — while your smart model keeps doing the part only it's good at: orchestrating.

It's **orchestrator-agnostic**: drive with Claude, GPT, Gemini, Grok — or, if you're truly thrifty, a cheap flagship like DeepSeek or Kimi.

## Quickstart

```bash
git clone https://github.com/sashabogi/token-scrooge && cd token-scrooge
./install.sh          # symlinks the CLIs, then launches the setup wizard
```

The **setup wizard** asks two things and writes everything for you — no hand-editing JSON:

1. **Your orchestrator** — pick from 11 frontier *and* budget options; sets the ledger's savings baseline.
2. **API keys** — auto-detects any already in your environment, prompts (masked) for the rest, then **live-tests each one** and offers to re-enter any that fail. Keys go to `~/.token-scrooge/.env` (chmod 600) — never your shell profile, never the repo.

```bash
scrooge list                                   # what's live
scrooge "draft a regex for E.164 phone numbers"
scrooge --task summarize < bigfile.md          # cheapest capable model for the task
scrooge --model kimi --json "extract the prices as JSON"
scrooge ledger                                 # spend + savings vs your orchestrator
scrooge-drift                                  # is the registry still current? (run weekly)
```

Every call prints a loud banner, so an external model never runs silently:

```
🪙 scrooge ▸ deepseek/deepseek-v4-flash  [task: summarize]
🪙 scrooge ✓ deepseek/deepseek-v4-flash · 1240→830 tok · ~$0.00041 · 1.4s · ledger#23
```

## What's inside

| Command | What it does |
|---|---|
| **`scrooge`** | Routes one task to the cheapest capable model (`--task` or `--model`), prints a transparency banner, logs cost. `scrooge ledger` shows spend + savings; `scrooge list` / `scrooge models <provider>` introspect; `scrooge setup` re-runs the wizard. |
| **`scrooge-diverge`** | "Diverge → focus" idea generator. Fans N isolated cognitive frames across *different* cheap model families in parallel (no shared context = no anchoring), then a critic clusters and flags seductive-but-broken ideas. Great for design/naming/architecture calls. *(Inspired by [claude-adhd](https://github.com/UditAkhourii/adhd).)* |
| **`scrooge-verify`** | A real verification gate. Detects your toolchain, runs build/typecheck/test (free, ground truth — a non-zero exit is an objective FAIL), then asks a cheap model whether the evidence actually supports a `--claim` (catching "green tests that don't exercise the change"). |
| **`scrooge-drift`** | Keeps the registry honest. Diffs each provider's *live* model list against what the registry routes to: **DEAD** = registry points at a retired model (calls will fail — fix now), **NEW** = a current-gen model you haven't adopted yet. Exit 1 on drift; run it weekly via cron so the registry never silently rots. |
| **Claude Code gate** *(opt-in)* | A `diverge` skill, an `adversarial-verifier` agent, and a `Stop`/`SubagentStop` hook that **blocks "done" claims with no build/test evidence**. Offered during `scrooge setup`. |

## How it works

- **One OpenAI-compatible code path** covers every provider; the router is dependency-free Python (stdlib only).
- **A capability registry** (`~/.token-scrooge/registry.json`) maps each model → provider, env var, base URL, **cost per 1M tokens**, speed, and `good_for` tags. Fully editable; `scrooge models <provider>` discovers live IDs, and `scrooge-drift` flags when the registry has fallen behind what providers actually serve (retired IDs that would fail, or newer models worth adopting) — run it weekly via cron so routing never silently rots.
- **A cost ledger** (`~/.token-scrooge/calls.jsonl`) records every call; `scrooge ledger` totals spend and savings against *your* orchestrator's price.
- **Bring your own keys.** Nothing is bundled. Works with whatever subset you have — even one provider.

### Orchestrators (savings baseline)

Frontier: Claude Opus · Claude Sonnet · OpenAI GPT · Gemini Pro · xAI Grok · Mistral Large.
Budget (cheap enough to orchestrate on): DeepSeek V4 · Kimi K2 · Qwen Max · Zhipu GLM-5.

### Optional: route through a proxy

Running an OpenAI-compatible LLM proxy (LiteLLM, or a cheap-routing gateway)? Point a provider's `base_url` at it in `registry.json` and set its key — Token Scrooge routes through it transparently. `SCROOGE_ENV_FILE=/path/to/.env` loads keys from an existing proxy env file.

## Why it's good for AI-coding developers

- **Cost** — frontier tokens are for thinking, not busywork; the ledger proves the savings.
- **Rate limits** — cheap providers carry the volume, so you stop burning premium quota on grunt work.
- **Speed** — `scrooge-diverge` and parallel delegation run many cheap workers at once.
- **Better output, not just cheaper** — the verification gate means nothing is "done" until it's built, tested, and observed. Cheap labor *with* receipts.

## Install as a Claude Code plugin

The repo ships a plugin manifest (`.claude-plugin/plugin.json`) bundling the `diverge` skill and `adversarial-verifier` agent. The CLIs and the Stop-hook are installed by `install.sh` / `scrooge setup`.

## Caveats

- Bring your own API keys (one or more of DeepSeek / Kimi / ZAI / Gemini / OpenAI / OpenRouter / xAI).
- macOS / Linux (bash + python3 ≥ 3.8). Windows via WSL.
- Model IDs and prices drift — the registry is yours to edit.
- The verification hook only fires on code sessions (code written or build/test attempted); `VERIFY_DONE_GATE_OFF=1` bypasses a block.

## Credits

The `diverge` "isolated frames → focus" pattern is a native reimplementation of the idea behind [**claude-adhd / adhd** by Udit Akhourii](https://github.com/UditAkhourii/adhd). Logo and header generated with `gemini-3-pro-image`.

## License

MIT © sashabogi
