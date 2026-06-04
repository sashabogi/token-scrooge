#!/usr/bin/env bash
# Token Scrooge test suite — hermetic, offline, no API keys required.
# Spins up a throwaway $SCROOGE_HOME with a synthetic ledger, exercises the CLI
# (lessons, watch project-filter, ledger, resilience) and the routing unit tests,
# then exits non-zero if anything failed. Run:  ./tests/run.sh
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SCROOGE="$REPO/bin/scrooge"
PY="$(command -v python3)"
PASS=0; FAIL=0
ok(){ if eval "$2"; then echo "  PASS  $1"; PASS=$((PASS+1)); else echo "  FAIL  $1"; FAIL=$((FAIL+1)); fi; }

echo "== compile =="
"$PY" -m py_compile "$REPO"/bin/scrooge "$REPO"/bin/scrooge-capabilities "$REPO"/hooks/scrooge-announce.py \
  && { echo "  PASS  scripts byte-compile"; PASS=$((PASS+1)); } \
  || { echo "  FAIL  scripts byte-compile"; FAIL=$((FAIL+1)); }

echo "== routing (hermetic unit tests) =="
"$PY" "$REPO/tests/test_routing.py"; [ $? -eq 0 ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

echo "== CLI (throwaway \$SCROOGE_HOME, synthetic ledger) =="
TMP="$(mktemp -d)"; export SCROOGE_HOME="$TMP"
cp "$REPO/registry.template.json" "$TMP/registry.json"
cp "$REPO/lessons.seed.json"      "$TMP/lessons.seed.json"      2>/dev/null
cp "$REPO/capabilities.seed.json" "$TMP/capabilities.seed.json" 2>/dev/null
cat > "$TMP/calls.jsonl" <<JSONL
{"ts":1700000000,"provider":"deepseek","model":"deepseek-v4-flash","task":"code","project":"alpha","cwd":"/x/alpha","tokens_in":100,"tokens_out":50,"cost_usd":0.00002,"duration_ms":1200,"ok":true,"prompt_preview":"draft alpha widget"}
{"ts":1700000001,"provider":"gemini","model":"gemini-2.5-flash-lite","task":"summarize","project":"beta","cwd":"/x/beta","tokens_in":900,"tokens_out":120,"cost_usd":0.00007,"duration_ms":600,"ok":true,"prompt_preview":"summarize beta notes"}
JSONL

A="$("$SCROOGE" watch --all --no-follow --project alpha 2>&1)"
ok "watch --project alpha shows alpha"   'echo "$A" | grep -q "draft alpha widget"'
ok "watch --project alpha excludes beta" '! echo "$A" | grep -q "summarize beta notes"'
L="$("$SCROOGE" ledger --since all --project beta 2>&1)"
ok "ledger --project beta scopes"        'echo "$L" | grep -q "project=beta" && echo "$L" | grep -q "(1 calls)"'

rm -f "$TMP/lessons.json"
"$SCROOGE" learn -m deepseek -t code "unit test lesson zzz" >/dev/null 2>&1
ok "learn then lessons shows it"         '"$SCROOGE" lessons -m deepseek 2>&1 | grep -q "unit test lesson zzz"'
ok "seed bootstrapped on first use"      '"$SCROOGE" lessons -m deepseek 2>&1 | grep -q "order-book bids/asks"'
IDX="$("$PY" -c "import json,os;d=json.load(open(os.environ['SCROOGE_HOME']+'/lessons.json'));print(d['deepseek-v4-flash']['code'].index('unit test lesson zzz'))")"
"$SCROOGE" forget -m deepseek -t code "$IDX" >/dev/null 2>&1
ok "forget removes it"                   '! "$SCROOGE" lessons -m deepseek 2>&1 | grep -q "unit test lesson zzz"'

echo "not json {{{" > "$TMP/lessons.json"
"$SCROOGE" lessons >/dev/null 2>&1; ok "corrupt lessons store does not crash" '[ $? -eq 0 ]'
rm -f "$TMP/lessons.json"
"$SCROOGE" lessons >/dev/null 2>&1; ok "missing lessons store does not crash" '[ $? -eq 0 ]'

rm -rf "$TMP"
echo ""
echo "RESULT: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
