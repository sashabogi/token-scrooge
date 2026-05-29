#!/usr/bin/env python3
"""
verify-done-gate.py  --  Layer 2: Programmatic enforcement of "done" claims.

Registered on Stop and SubagentStop. Reads the hook JSON from stdin
({transcript_path, stop_hook_active, ...}), scans the RECENT tail of the
transcript for a completion claim ("done", "it works", "complete", etc.) made
by the assistant, then checks whether that claim is CORROBORATED by machine
evidence in the SAME recent window:

  - a build/test/run command was actually executed via Bash, AND
  - its tool_result did not error (is_error != true, no obvious failure text).

Optionally it also wants proof that code was written (Edit/Write/MultiEdit) when
the claim implies implementation.

If a clear completion claim has NO corroborating execution evidence, the hook
emits {"decision":"block","reason":"..."} so the model must keep working and
paste real evidence. Otherwise it exits 0 (allow stop).

Design rules:
  * stop_hook_active guard -> never loop forever (allow on second pass).
  * Conservative: only block UNAMBIGUOUS, UNSUBSTANTIATED claims.
  * Never crash the stop pipeline: any internal error -> exit 0 (fail-open).
  * Composes with other Stop hooks (it only reads; touches nothing else).
"""

import sys, os, json, re

# ----- knobs -------------------------------------------------------------
TAIL_MESSAGES = 60          # how many trailing transcript lines to consider
EVIDENCE_LOOKBACK = 80      # how far back to hunt for build/test/run evidence
BYPASS_ENV = "VERIFY_DONE_GATE_OFF"   # set to "1" to disable entirely
# -------------------------------------------------------------------------

# Strong completion-claim phrases. Anchored to reduce false positives on words
# like "complete the form" -> we require claim-like contexts.
CLAIM_PATTERNS = [
    r"\b(it|this|everything|the (?:feature|fix|change|app|build|tests?))\s+(?:is\s+)?(?:now\s+)?(?:work(?:s|ing)|fixed|done|complete[d]?)\b",
    r"\ball\s+(?:tests?\s+)?(?:pass(?:ing|ed)?|green|working)\b",
    r"\b(?:successfully|now)\s+(?:implemented|working|complete[d]?|fixed|tested|verified)\b",
    r"\b(?:i(?:'ve| have)?\s+)?(?:fully\s+)?(?:implemented|completed|finished)\s+(?:the|all|this)\b",
    r"\b(?:task|implementation|migration|refactor)\s+(?:is\s+)?(?:complete[d]?|done|finished)\b",
    r"\bready\s+(?:to\s+(?:ship|merge|deploy)|for\s+review)\b",
    r"\b(?:done|complete)[.!]?\s*$",
    r"\bverified\s+(?:it\s+)?works?\b",
    r"\bconfirmed\s+working\b",
]

# Phrases that indicate the assistant is NOT claiming done (suppress blocking).
NEGATION_PATTERNS = [
    r"\bnot\s+(?:yet\s+)?(?:done|complete|working|finished|tested|verified)\b",
    r"\bstill\s+(?:need|have to|broken|failing|not)\b",
    r"\b(?:fail(?:s|ed|ing)|error|broke[n]?|does(?:n't| not)\s+work)\b",
    r"\bwould\s+(?:complete|finish|implement)\b",   # describing a plan, not a claim
    r"\bto\s+(?:complete|finish|verify|test)\b",
    r"\bonce\s+(?:i|we|you)\b",
    r"\bcouldn't\s+(?:verify|test|run|build)\b",
    r"\bunable\s+to\s+(?:verify|test|run|build)\b",
]

# Commands that count as real build/test/run execution.
EVIDENCE_CMD = re.compile(
    r"(?<![\w-])("
    r"npm\s+(?:run\s+)?(?:test|build|lint|type-check)"
    r"|npm\s+t\b"
    r"|pnpm\s+(?:run\s+)?(?:test|build|lint)"
    r"|yarn\s+(?:test|build|lint)"
    r"|npx\s+(?:tsc|jest|vitest|playwright|next\s+build|next\s+lint|eslint|tsx)"
    r"|tsc\b"
    r"|jest\b|vitest\b|playwright\b"
    r"|pytest\b|python\s+-m\s+pytest|unittest\b"
    r"|cargo\s+(?:test|build|run|check|clippy)"
    r"|go\s+(?:test|build|run|vet)"
    r"|make\s+(?:test|build|check)"
    r"|gradle\s+(?:test|build)|mvn\s+(?:test|verify|package)"
    r"|dotnet\s+(?:test|build|run)"
    r"|rspec\b|phpunit\b"
    r"|curl\b"                       # hitting a running server = observed behavior
    r"|playwright\s+test"
    r"|agent-browser\s+(?:open|screenshot|snapshot)"  # observed UI behavior
    r")",
    re.IGNORECASE,
)

# Failure signatures in a tool_result that DISQUALIFY it as success evidence.
FAILURE_SIG = re.compile(
    r"(?:^|\n)\s*(?:error|fail(?:ed|ure)?|exception|traceback|"
    r"\d+\s+failing|tests?\s+failed|exit\s+code\s*[1-9]|"
    r"npm\s+err!|cannot\s+find|not\s+found|undefined\s+reference|"
    r"segmentation\s+fault|panicked|assertion\s+failed)",
    re.IGNORECASE,
)

WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", "create_file", "str_replace"}


def log(msg):
    # Goes to stderr -> visible in hook debug, never to the model unless we block.
    sys.stderr.write("[verify-done-gate] " + msg + "\n")


def load_transcript(path):
    rows = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except Exception as e:
        log("cannot read transcript: %s" % e)
    return rows


def result_text(content):
    """tool_result.content may be a str or a list of {type:text,text:..} blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                parts.append(str(c.get("text", "")))
            else:
                parts.append(str(c))
        return "\n".join(parts)
    return str(content) if content is not None else ""


def main():
    raw = sys.stdin.read() or "{}"
    try:
        hook = json.loads(raw)
    except Exception:
        hook = {}

    if os.environ.get(BYPASS_ENV) == "1":
        sys.exit(0)

    # Loop guard: if we already blocked once this stop-cycle, allow now.
    if hook.get("stop_hook_active"):
        log("stop_hook_active -> allowing stop (loop guard)")
        sys.exit(0)

    tpath = hook.get("transcript_path")
    if not tpath or not os.path.exists(tpath):
        sys.exit(0)  # fail-open

    rows = load_transcript(tpath)
    if not rows:
        sys.exit(0)

    tail = rows[-TAIL_MESSAGES:]

    # 1) Find the most recent assistant TEXT and test for a claim.
    claim_text = None
    for o in reversed(tail):
        if o.get("type") != "assistant":
            continue
        m = o.get("message", {})
        if not isinstance(m, dict):
            continue
        chunk = []
        for c in (m.get("content") or []):
            if isinstance(c, dict) and c.get("type") == "text":
                chunk.append(c.get("text", ""))
        if chunk:
            claim_text = "\n".join(chunk)
            break

    if not claim_text:
        sys.exit(0)

    low = claim_text.lower()

    # Negation / hedging present -> assistant isn't actually claiming done.
    for np in NEGATION_PATTERNS:
        if re.search(np, low):
            log("negation/hedge found -> allow")
            sys.exit(0)

    matched = next((p for p in CLAIM_PATTERNS if re.search(p, low)), None)
    if not matched:
        sys.exit(0)  # no completion claim -> nothing to enforce

    # 2) Hunt for corroborating execution evidence in the recent window.
    window = rows[-EVIDENCE_LOOKBACK:]
    ran_cmds = []          # commands that look like build/test/run
    success_evidence = []  # (cmd, ok) where ok means result not errored
    wrote_code = False
    # map tool_use_id -> command string, so we can pair with its result
    pending = {}

    for o in window:
        m = o.get("message", {})
        if not isinstance(m, dict):
            continue
        content = m.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict):
                continue
            ct = c.get("type")
            if ct == "tool_use":
                name = c.get("name", "")
                if name in WRITE_TOOLS:
                    wrote_code = True
                inp = c.get("input") or {}
                cmd = inp.get("command") if isinstance(inp, dict) else None
                if name in ("Bash", "shell") and isinstance(cmd, str) and EVIDENCE_CMD.search(cmd):
                    ran_cmds.append(cmd)
                    tuid = c.get("id")
                    if tuid:
                        pending[tuid] = cmd
            elif ct == "tool_result":
                tuid = c.get("tool_use_id")
                if tuid in pending:
                    txt = result_text(c.get("content"))
                    errored = bool(c.get("is_error")) or bool(FAILURE_SIG.search(txt or ""))
                    success_evidence.append((pending[tuid], not errored))

    has_run = len(ran_cmds) > 0
    has_success = any(ok for _, ok in success_evidence)
    has_failed = any((not ok) for _, ok in success_evidence)

    # Non-code turn: no code written AND nothing built/tested/run in the window.
    # This is almost certainly analysis / research / explanation (e.g. a read-only
    # Explore subagent) — NOT a "I shipped working code" claim. Don't gate it; the
    # gate is for code sessions that skipped verification, not for not-coding.
    if not wrote_code and not has_run:
        log("no writes and no build/test in window -> non-code turn -> allow")
        sys.exit(0)

    # 3) Decide.
    # Strongest case: ran something and at least one run succeeded -> ALLOW.
    if has_run and has_success and not has_failed:
        log("claim corroborated by passing build/test/run -> allow")
        sys.exit(0)

    # Ran tests but the latest evidence shows failures -> BLOCK (claim is false).
    if has_run and has_failed and not has_success:
        block(
            "You claimed completion, but the most recent build/test/run in this "
            "session ERRORED. Do not report done while the evidence shows failure.\n\n"
            "Required before claiming done:\n"
            "  1. Fix the failure.\n"
            "  2. Re-run the failing command and confirm a clean exit (exit code 0).\n"
            "  3. Paste the actual command and the tail of its output as evidence.\n\n"
            "Detected commands: " + "; ".join(_short(c) for c in ran_cmds[:4])
        )

    # Mixed (some pass some fail) but no clean all-green: be conservative, nudge.
    if has_run and has_success and has_failed:
        block(
            "You claimed completion, but among the build/test/run commands in this "
            "session at least one ERRORED. Re-run everything that touched the change "
            "and confirm a fully clean result, then paste the commands + output tails "
            "as evidence before claiming done."
        )

    # No build/test/run evidence at all behind the claim -> BLOCK.
    extra = ""
    if not wrote_code:
        extra = ("\nNote: I also see no Edit/Write tool calls recently, so it is "
                 "unclear that any code was actually written. ")
    block(
        "You appear to be reporting this as DONE / WORKING, but I find NO evidence in "
        "this session that you actually built, tested, or ran anything to verify it.\n"
        + extra +
        "\n'I tested it and it works' is not acceptable on its own — evidence must be "
        "machine-checkable artifacts.\n\n"
        "Before you may report done, do ALL of the following and show the output:\n"
        "  1. Run the project's build/typecheck (e.g. npm run build / tsc / cargo build).\n"
        "  2. Run the tests (e.g. npm test / pytest / cargo test) — exit code 0.\n"
        "  3. For runtime/UI behavior, actually launch it and observe it "
        "(use /run or /verify, or agent-browser, or curl the endpoint).\n"
        "  4. Paste the exact commands and the tail of their real output here.\n\n"
        "If a component genuinely cannot be run, say so explicitly and explain why — "
        "do not claim it 'works'."
    )


def _short(cmd):
    cmd = " ".join(cmd.split())
    return cmd[:70] + ("…" if len(cmd) > 70 else "")


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Never break the user's stop pipeline.
        log("internal error, failing open: %s" % e)
        sys.exit(0)
