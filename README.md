<p align="center">
  <img src="assets/header.png" alt="Token Scrooge — make the cheap models do the grunt work" width="100%">
</p>

<h1 align="center">Token Scrooge</h1>

<p align="center">
  <b>Your $75-per-million-tokens genius shouldn't be summarizing changelogs.</b><br>
  Token Scrooge fires your frontier model from the grunt work, hands it to cheap LLMs that do it
  <b>30–100× cheaper</b>, and shows you every delegation live — with receipts.
</p>

---

You pay frontier prices (Claude Opus, GPT, Gemini Pro) for the one thing those models are uniquely great at: **orchestrating**. But most of what an agent actually *does* all day — draft a function, summarize a file, extract JSON, label 4,000 rows, judge whether a test covers a claim — is **grunt work a model costing 30–100× less does just as well.** Token Scrooge is a zero-dependency CLI (Python stdlib only) that routes that work to DeepSeek / Kimi / GLM / Gemini / OpenAI / xAI / OpenRouter while your expensive model stays in charge.

In one real session that meant **218 delegated calls for \$0.15** — the same tokens on Opus would've cost **~\$20. A 99% cut**, with a live ledger to prove it.

And it's not naïve "always grab the cheapest." Token Scrooge:

- **🎯 Routes by capability, not just price** — weighs each model's *benchmarked skill for the task* against cost, escalating **hard** work to a stronger model while keeping **easy** work cheap. (Backed by live [Artificial Analysis](https://artificialanalysis.ai/) scores, refreshed weekly.)
- **📺 Shows its work live** — `scrooge watch` streams every cheap-model call as it happens (model · task · cost · *what it's doing*), filterable per project.
- **🧠 Learns from its mistakes** — when a cheap model repeats a bug, capture a one-line lesson and it's auto-injected into that model's prompt from then on.
- **🔄 Keeps itself current** — weekly refreshers pull live model lists, prices, and quality benchmarks so routing never silently rots.
- **🧾 Never runs silently** — a loud banner + a cost ledger on every call. Nothing happens behind your back, and the savings are always provable.

It's **orchestrator-agnostic**: drive with Claude, GPT, Gemini, or Grok — or, if you're truly thrifty, a cheap flagship like DeepSeek or Kimi. **Bring your own keys** (any subset — even one provider).

## Quickstart

```bash
git clone https://github.com/sashabogi/token-scrooge && cd token-scrooge
./install.sh          # symlinks the CLIs, then launches the setup wizard
```

The **setup wizard** asks two things and writes everything for you — no hand-editing JSON:

1. **Your orchestrator** — pick from 11 frontier *and* budget options; sets the ledger's savings baseline.
2. **API keys** — auto-detects any already in your environment, prompts (masked) for the rest, then **live-tests each one** and offers to re-enter any that fail. Keys go to `~/.token-scrooge/.env` (chmod 600) — never your shell profile, never the repo.

```bash
scrooge list                                   # what's live (with capability scores)
scrooge "draft a regex for E.164 phone numbers"
scrooge -t summarize < bigfile.md              # best-value model for the task
scrooge -t code -d hard "design a lock-free queue"   # hard → escalates to a stronger model
scrooge -t code --spread 3 < batch.txt         # fan a batch across the top-3 capable models
scrooge --model kimi --json "extract the prices as JSON"
scrooge watch --here                           # live feed of this project's delegations
scrooge ledger                                 # spend + savings vs your orchestrator
```

The installer also schedules two **weekly self-maintenance** jobs (macOS LaunchAgent / Linux cron):
`scrooge-capabilities` (refresh model quality scores) and you can add `scrooge-drift` (flag retired/new models) the same way — so routing tracks reality with zero babysitting.

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
🪙 scrooge watch  all projects  ·  following ~/.token-scrooge/calls.jsonl  ·  Ctrl-C to stop
my-api         14:22:31 ✓ deepseek/deepseek-v4-flash [code]       70→35 tok  $0.00002 1.3s · draft a retry wrapper
docs-site      14:22:33 ✓ gemini/gemini-2.5-flash-lite [summarize] 980→120 tok $0.00007 0.6s · summarize: changelog.md
  ── 12 calls · $0.0041 cheap · ~$1.40 on Claude Opus · saved ~$1.39 (99%) ──
```

Running many projects at once? Each line is tagged with its project. To watch just the
one you're working on, run this **in that project's terminal**:

```
scrooge watch --here     # only this repo's calls (auto-detected from the git root / dir)
```

## What's inside

| Command | What it does |
|---|---|
| **`scrooge`** | Routes one task to the **best-value** model — weighing benchmarked capability for the task against cost, gated by difficulty (`--task` + `--difficulty`, or `--model` to force one). `--spread N` fans a batch across models. Prints a transparency banner, logs cost. `scrooge ledger` shows spend + savings; `scrooge list` / `scrooge models <provider>` introspect; `scrooge setup` re-runs the wizard. |
| **`scrooge watch`** | **Live feed of every cheap-model call** as it lands in the ledger — model · task · tokens · cost · prompt preview, with a rolling savings line. Catches foreground, background, *and* subagent calls (they all log). Keep it open in a side pane to literally watch the orchestrator delegate in real time. **Many projects share one ledger**, so each call is stamped with its project (git-repo / dir name, or `$SCROOGE_PROJECT`): run `scrooge watch --here` in a project's terminal to see **only that project**, `--project <name>` to pick one, or plain `scrooge watch` to see all (each line tagged). `--all` replays history; `--tail N` backfills. (`scrooge ledger --here` totals savings for one project.) |
| **`scrooge-diverge`** | "Diverge → focus" idea generator. Fans N isolated cognitive frames across *different* cheap model families in parallel (no shared context = no anchoring), then a critic clusters and flags seductive-but-broken ideas. Great for design/naming/architecture calls. *(Inspired by [claude-adhd](https://github.com/UditAkhourii/adhd).)* |
| **`scrooge-verify`** | A real verification gate. Detects your toolchain, runs build/typecheck/test (free, ground truth — a non-zero exit is an objective FAIL), then asks a cheap model whether the evidence actually supports a `--claim` (catching "green tests that don't exercise the change"). |
| **`scrooge-drift`** | Keeps the registry honest. Diffs each provider's *live* model list against what the registry routes to: **DEAD** = registry points at a retired model (calls will fail — fix now), **NEW** = a current-gen model you haven't adopted yet. Exit 1 on drift; run it weekly via cron so the registry never silently rots. |
| **`scrooge-capabilities`** | Refreshes per-model **quality scores** (Artificial Analysis Intelligence/Coding/Math indices + GPQA + speed, plus OpenRouter context/modality) into `capabilities.json`, which powers capability-aware routing (below). The installer schedules it weekly. **Optional** — routing already works from the shipped seed; this keeps scores current and wants a *free* [Artificial Analysis](https://artificialanalysis.ai/) key (`$AA_API_KEY`). |
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

## Capability-aware routing (not just cheapest)

A `--task` doesn't just grab the cheapest model — it **weighs each candidate's quality
*for that task* against its price, gated by difficulty**, so easy work stays cheap and hard
work escalates to a stronger (but still sub-orchestrator) model instead of always hitting
the floor.

```bash
scrooge -t code "draft a getter"              # easy/medium → cheapest capable (e.g. deepseek-v4-flash)
scrooge -t code -d hard "design a lock-free queue"   # hard → escalates (e.g. deepseek-v4-pro)
scrooge -t code --spread 3 < batch_of_calls   # fan a swarm across the top-3 capable models (rate limits/throughput)
scrooge -t code --no-weigh "…"                # opt out → registry cheapest-first order
```

How it works:

- **Quality data** lives in `~/.token-scrooge/capabilities.json` — per model: `intelligence`,
  `coding`, `math`, `reasoning` (GPQA), `speed_tps`. Seeded from the committed
  `capabilities.seed.json` (real [Artificial Analysis](https://artificialanalysis.ai/) numbers) so it works out of the box,
  and refreshed weekly by **`scrooge-capabilities`** (AA + OpenRouter).
- **The weigher** maps the task to a metric (`code`→coding, `reason`/`verify`→reasoning, else
  the general intelligence index), applies a **difficulty floor** (a percentile of the
  candidate pool: `easy`=none, `medium`≈median, `hard`≈top-fifth), then ranks survivors by
  `quality^1.5 / cost^0.5`. The banner shows the call: `[task: code · hard]`.
- **Difficulty** comes from `--difficulty/-d easy|medium|hard`, or is **inferred** when omitted
  (code/reasoning tasks default to `medium`, long prompts bump a notch).
- **`--spread N`** distributes a batch deterministically (by prompt hash) across the top-N
  capable models — no central lock, so parallel workers self-balance.
- Weights and difficulty floors are tunable under a `"routing"` key in `registry.json`. With no
  capability data present, routing falls back to the registry's cheapest-first task order.

> Reality check: capability routing won't spread *easy* work across many models — for a uniform
> easy batch (e.g. classification), one cheap model is genuinely the right answer. The payoff is
> **escalation** on hard tasks and **throughput** via `--spread`.

### The Artificial Analysis key — optional, free, and where to put it

Capability routing **works the moment you install** — the repo ships `capabilities.seed.json`
with real benchmark scores, so nothing extra is required to get smart routing. The only thing
the [Artificial Analysis](https://artificialanalysis.ai/) key adds is the **weekly auto-refresh**
that keeps those scores current as models change (new releases, retired ids, shifting quality).

- **Why bother:** models move fast. Without a refresh, routing decisions slowly drift from
  reality. With it, `scrooge-capabilities` pulls fresh Intelligence/Coding/Math/GPQA/speed numbers
  every week, no babysitting.
- **It's free:** create an account at [artificialanalysis.ai](https://artificialanalysis.ai/),
  open the API/Insights section, and generate a key (their free tier covers this; attribution to
  artificialanalysis.ai is requested).
- **Where it goes:** the **`scrooge setup`** wizard prompts for it (Enter to skip), or add it
  yourself any time:
  ```bash
  echo 'AA_API_KEY=aa_xxxxxxxx' >> ~/.token-scrooge/.env   # chmod 600, gitignored, never committed
  scrooge-capabilities                                      # refresh now (otherwise it runs weekly)
  ```
- **Skip it entirely** and everything still works — you just keep the shipped seed scores until you
  edit them by hand. (`scrooge-capabilities` also pulls OpenRouter context/modality with *no* AA key.)

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

## Tests

Hermetic, offline, no API keys — they spin up a throwaway `$SCROOGE_HOME` and assert the
real behaviour (capability routing & difficulty escalation, `--spread` distribution,
per-project `watch`/`ledger` filtering, the lessons round-trip, and corrupt/missing-store
resilience):

```bash
./tests/run.sh        # byte-compile + routing unit tests + CLI checks; exit 0 = all green
```

Run it after any change — a red line means a regression before you ship.

## Caveats

- Bring your own API keys (one or more of DeepSeek / Kimi / ZAI / Gemini / OpenAI / OpenRouter / xAI).
- macOS / Linux (bash + python3 ≥ 3.8). Windows via WSL.
- Model IDs and prices drift — the registry is yours to edit.
- The verification hook only fires on code sessions (code written or build/test attempted); `VERIFY_DONE_GATE_OFF=1` bypasses a block.

## Credits

The `diverge` "isolated frames → focus" pattern is a native reimplementation of the idea behind [**claude-adhd / adhd** by Udit Akhourii](https://github.com/UditAkhourii/adhd). Logo and header generated with `gemini-3-pro-image`.

## License

MIT © sashabogi
