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

Every call prints a loud banner **to stderr**, so an external model never runs silently:

```
🪙 scrooge ▸ deepseek/deepseek-v4-flash  [task: summarize]
🪙 scrooge ✓ deepseek/deepseek-v4-flash · 1240→830 tok · ~$0.00041 · 1.4s · ledger#23
```

In a terminal you see this directly. When an **agent** drives scrooge, the banner lands
in that subprocess's captured output — easy to miss, and invisible for background or
subagent calls. So for live visibility regardless of who's calling, keep a
**`scrooge watch`** pane open — it tails the ledger and streams *every* call as it
happens (model · task · tokens · cost · what it's doing) with a rolling savings line:

```
🪙 scrooge watch  following ~/.token-scrooge/calls.jsonl  ·  Ctrl-C to stop
14:22:31 ✓ deepseek/deepseek-v4-flash [code]      70→35 tok  $0.00002  1.3s  · draft a retry wrapper
14:22:33 ✓ gemini/gemini-2.5-flash-lite [summarize] 980→120 tok $0.00007 0.6s · summarize: changelog.md
  ── 12 calls · $0.0041 cheap · ~$1.40 on Claude Opus · saved ~$1.39 (99%) ──
```

## What's inside

| Command | What it does |
|---|---|
| **`scrooge`** | Routes one task to the cheapest capable model (`--task` or `--model`), prints a transparency banner, logs cost. `scrooge ledger` shows spend + savings; `scrooge list` / `scrooge models <provider>` introspect; `scrooge setup` re-runs the wizard. |
| **`scrooge watch`** | **Live feed of every cheap-model call** as it lands in the ledger — model · task · tokens · cost · prompt preview, with a rolling savings line. Catches foreground, background, *and* subagent calls (they all log). Keep it open in a side pane to literally watch the orchestrator delegate in real time. `--all` replays history; `--tail N` backfills recent context. |
| **`scrooge-diverge`** | "Diverge → focus" idea generator. Fans N isolated cognitive frames across *different* cheap model families in parallel (no shared context = no anchoring), then a critic clusters and flags seductive-but-broken ideas. Great for design/naming/architecture calls. *(Inspired by [claude-adhd](https://github.com/UditAkhourii/adhd).)* |
| **`scrooge-verify`** | A real verification gate. Detects your toolchain, runs build/typecheck/test (free, ground truth — a non-zero exit is an objective FAIL), then asks a cheap model whether the evidence actually supports a `--claim` (catching "green tests that don't exercise the change"). |
| **`scrooge-drift`** | Keeps the registry honest. Diffs each provider's *live* model list against what the registry routes to: **DEAD** = registry points at a retired model (calls will fail — fix now), **NEW** = a current-gen model you haven't adopted yet. Exit 1 on drift; run it weekly via cron so the registry never silently rots. |
| **`scrooge learn` / `lessons` / `forget`** | **Live training.** Accumulates short, per-model corrective guardrails learned from observed failures and auto-injects the relevant ones into the model's system prompt at routing time — so recurring cheap-model bugs are preempted, not re-fixed (and re-paid for) on every call. See [Live training](#live-training-per-model-lessons) below. |
| **Claude Code gate** *(opt-in)* | A `diverge` skill, an `adversarial-verifier` agent, a `Stop`/`SubagentStop` hook that **blocks "done" claims with no build/test evidence**, and a `PreToolUse` hook (`scrooge-announce.py`) that drops an inline marker whenever the agent delegates to scrooge (nudging you to open `scrooge watch`). Offered during `scrooge setup`. |

## How it works

- **One OpenAI-compatible code path** covers every provider; the router is dependency-free Python (stdlib only).
- **A capability registry** (`~/.token-scrooge/registry.json`) maps each model → provider, env var, base URL, **cost per 1M tokens**, speed, and `good_for` tags. Fully editable; `scrooge models <provider>` discovers live IDs, and `scrooge-drift` flags when the registry has fallen behind what providers actually serve (retired IDs that would fail, or newer models worth adopting) — run it weekly via cron so routing never silently rots.
- **No hardcoded default model.** A bare `scrooge "prompt"` (no `--model`/`--task`) routes to the **cheapest model you currently have a key for**, verified against the provider's *live* `/models` list (cached ~10 min in `models-cache.json`). If the registry's id has drifted out of what the provider actually serves, Scrooge falls back to a live-discovered id rather than failing on a stale string; `--latest` forces a fresh liveness check. So the default tracks reality as models come and go — nothing to pin or update by hand.
- **A cost ledger** (`~/.token-scrooge/calls.jsonl`) records every call; `scrooge ledger` totals spend and savings against *your* orchestrator's price.
- **Bring your own keys.** Nothing is bundled. Works with whatever subset you have — even one provider.

### Orchestrators (savings baseline)

Frontier: Claude Opus · Claude Sonnet · OpenAI GPT · Gemini Pro · xAI Grok · Mistral Large.
Budget (cheap enough to orchestrate on): DeepSeek V4 · Kimi K2 · Qwen Max · Zhipu GLM-5.

### Optional: route through a proxy

Running an OpenAI-compatible LLM proxy (LiteLLM, or a cheap-routing gateway)? Point a provider's `base_url` at it in `registry.json` and set its key — Token Scrooge routes through it transparently. `SCROOGE_ENV_FILE=/path/to/.env` loads keys from an existing proxy env file.

## Live training (per-model lessons)

Cheap models tend to make the *same classes* of mistake over and over — and if your
orchestrator fixes each one by hand, you pay frontier tokens to re-discover a known bug.
**Live training** preempts that. Scrooge accumulates short, per-model (and per-task)
**lessons** — one-line corrective guardrails learned from observed failures — and
**auto-injects the relevant ones into the model's system prompt at routing time**. This is
"training" by prompt augmentation: cheap, immediate, and fully transparent (the guardrails
are visible in the call, not baked into opaque weights).

```bash
# capture a lesson the moment you fix a recurring bug (the "training signal")
scrooge learn -m deepseek -t code "Sort bids/asks explicitly; never assume API ordering."
scrooge learn -m deepseek "Return only what was asked — no prose preamble."   # -t omitted ⇒ all tasks ("*")

scrooge lessons                      # show the whole store
scrooge lessons -m deepseek -t code  # filtered (also shows the universal "*" lessons that apply)

scrooge forget -m deepseek -t code 0 # remove one by its 0-based index (from `scrooge lessons`)
scrooge forget -m deepseek --all     # wipe every lesson for a model
```

**Injection.** On each routed call, Scrooge gathers the lessons for the resolved model
(its full id **and** any alias), for the active `--task` **and** the `"*"` (all-tasks)
bucket, plus a top-level `"*"` model bucket of universal guardrails. It composes them into
a terse block:

```
Known pitfalls to avoid:
- Never assume API array ordering — sort order-book bids/asks explicitly by price.
- Use 0.0 (or the schema default) for absent numeric values, not None.
```

…and prepends it to the system prompt (if you passed `--system`, *your* text leads and the
guardrails follow). The transparency banner reports it:

```
🪙 scrooge ▸ deepseek/deepseek-v4-flash [task: code] +3 lessons
```

- **Bounded.** ≤ 8 lessons per (model, task) and a total injected-char cap (~1200) — lessons
  are one-liners, so prompt bloat never erodes the savings Scrooge exists for.
- **`--no-lessons`** bypasses injection entirely (handy for A/B comparison).
- **Per-model, not global** — a weakness of one cheap model isn't forced onto the others.
  (The top-level `"*"` bucket only ever reaches cheap *execution* models, since that's all
  Scrooge routes.)

**User-local, with a shipped seed.** Your lessons live in `~/.token-scrooge/lessons.json`
(honoring `$SCROOGE_HOME`) — **gitignored, never committed**. The repo ships a small vetted
starter set in **`lessons.seed.json`** (committed); it's copied into your store on first use,
and `scrooge learn --seed` re-merges any new seed lessons without clobbering your edits. A
missing or malformed store is treated as empty — Scrooge never crashes on it, it just injects
nothing.

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
