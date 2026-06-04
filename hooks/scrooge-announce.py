#!/usr/bin/env python3
"""
scrooge-announce — Claude Code PreToolUse(Bash) hook.

Surfaces an inline, user-visible marker whenever the orchestrator shells out to
`scrooge`, so it's obvious a cheap model is being delegated to — and nudges you to
open a `scrooge watch` pane for the live per-call feed.

Why a hook AND `scrooge watch`? A PreToolUse hook fires once per Bash tool call, so
it can mark that a delegation is *starting* (even a big background batch), but it
cannot emit a line per individual scrooge call — that's what `scrooge watch` (which
tails the ledger) is for. This hook is the "something's happening, go look" signal.

Behaviour: never blocks (always exit 0, fail-open). Throttled so a burst of calls
doesn't spam the transcript. Emits a Claude Code `systemMessage` (shown to the user).
"""
import sys, os, json, time, re, shlex

THROTTLE_SECONDS = 180
STAMP = os.path.join(os.environ.get("SCROOGE_HOME", os.path.expanduser("~/.token-scrooge")),
                     ".announce-stamp")

def _recently_announced():
    try:
        return (time.time() - os.path.getmtime(STAMP)) < THROTTLE_SECONDS
    except OSError:
        return False

def _touch_stamp():
    try:
        os.makedirs(os.path.dirname(STAMP), exist_ok=True)
        open(STAMP, "w").write(str(int(time.time())))
    except OSError:
        pass

def _invokes_scrooge(cmd):
    # Match the `scrooge` executable as a token (start of line/pipe/;/&&/path), not
    # substrings like "scrooge-verify" config text or "scrooge watch" itself.
    if "scrooge" not in cmd:
        return False
    if re.search(r"scrooge\s+watch\b", cmd):   # don't announce the watcher itself
        return False
    return bool(re.search(r"(^|[|&;]|\s|/)scrooge(\s|$)", cmd))

def _model_task(cmd):
    """Best-effort: pull -m/--model and -t/--task off the command for a richer marker."""
    model = task = None
    try:
        toks = shlex.split(cmd)
    except ValueError:
        toks = cmd.split()
    for i, t in enumerate(toks):
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if t in ("-m", "--model") and nxt:
            model = nxt
        elif t.startswith("--model="):
            model = t.split("=", 1)[1]
        elif t in ("-t", "--task") and nxt:
            task = nxt
        elif t.startswith("--task="):
            task = t.split("=", 1)[1]
    return model, task

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    cmd = (payload.get("tool_input") or {}).get("command", "") or ""
    if not _invokes_scrooge(cmd) or _recently_announced():
        return 0
    _touch_stamp()
    model, task = _model_task(cmd)
    detail = []
    if model: detail.append("model=%s" % model)
    if task:  detail.append("task=%s" % task)
    suffix = (" (%s)" % ", ".join(detail)) if detail else ""
    msg = ("🪙 Token Scrooge is delegating to a cheap model%s. "
           "Run `scrooge watch` in a side pane for the live per-call feed "
           "(model · task · cost), or `scrooge ledger` for the running total." % suffix)
    try:
        print(json.dumps({"systemMessage": msg}))
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
