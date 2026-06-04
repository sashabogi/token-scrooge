#!/usr/bin/env python3
"""Hermetic unit tests for the capability-weighted router (no network, no keys).

Loads bin/scrooge as a module against the committed registry.template.json and
capabilities.seed.json, then asserts routing behaviour. Run via tests/run.sh, or
directly:  python3 tests/test_routing.py   (exit 0 = all pass, 1 = a failure).
"""
import importlib.machinery, importlib.util, os, sys, json, tempfile, collections

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# Point at an empty SCROOGE_HOME *before* import so load_caps() falls back to the
# committed seed (not whatever is in the developer's ~/.token-scrooge).
os.environ["SCROOGE_HOME"] = tempfile.mkdtemp()

ld = importlib.machinery.SourceFileLoader("scrooge", os.path.join(REPO, "bin", "scrooge"))
m = importlib.util.module_from_spec(importlib.util.spec_from_loader("scrooge", ld))
ld.exec_module(m)

reg = json.load(open(os.path.join(REPO, "registry.template.json")))
caps = m.load_caps()
m.provider_key = lambda reg, prov: "x"   # pretend every provider has a live key

P = F = 0
def ok(desc, cond):
    global P, F
    if cond:
        P += 1; print("  PASS", desc)
    else:
        F += 1; print("  FAIL", desc)

ok("capability seed loaded (>=13 models)", len([k for k in caps if not k.startswith("_")]) >= 13)
ok("code/easy -> cheapest capable (deepseek-v4-flash)",
   m.route_task(reg, caps, "code", "easy", "x")[0] == "deepseek-v4-flash")
hard = m.route_task(reg, caps, "code", "hard", "x")[0]
ok("code/hard escalates off the floor model", hard != "deepseek-v4-flash")
ok("code/hard picks a higher-coding model", caps[hard]["coding"] > caps["deepseek-v4-flash"]["coding"])
ok("reason task uses the reasoning metric", m.route_task(reg, caps, "reason", "hard", "x")[2]["metric"] == "reasoning")
ok("difficulty inference: code default = medium", m.infer_difficulty("code", "short") == "medium")
ok("difficulty inference: summarize default = easy", m.infer_difficulty("summarize", "short") == "easy")
ok("difficulty inference: long prompt bumps up", m.infer_difficulty("code", "x" * 9000) == "hard")

dist = collections.Counter(m.route_task(reg, caps, "code", "medium", "item %d" % i, spread=3)[0] for i in range(60))
ok("--spread 3 uses >=3 distinct models over a batch", len(dist) >= 3)
ok("--spread is deterministic for a fixed prompt",
   m.route_task(reg, caps, "code", "medium", "fixed", spread=3)[0]
   == m.route_task(reg, caps, "code", "medium", "fixed", spread=3)[0])

first = reg["tasks"]["code"][0]
ok("no capability data -> registry cheapest-first fallback",
   m.route_task(reg, {}, "code", None, "x")[0] == first)

try:
    m.route_task(reg, caps, "does-not-exist", None, "x"); ok("unknown task raises SystemExit", False)
except SystemExit:
    ok("unknown task raises SystemExit", True)

print("ROUTING: %d passed, %d failed" % (P, F))
sys.exit(1 if F else 0)
