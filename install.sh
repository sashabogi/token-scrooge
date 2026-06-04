#!/usr/bin/env bash
# Token Scrooge installer — make the cheap models do the grunt work.
# Usage:
#   git clone https://github.com/sashabogi/token-scrooge && cd token-scrooge && ./install.sh
#   curl -fsSL https://raw.githubusercontent.com/sashabogi/token-scrooge/main/install.sh | bash
set -euo pipefail

REPO_URL="${SCROOGE_REPO_URL:-https://github.com/sashabogi/token-scrooge}"
BIN_DIR="${SCROOGE_BIN_DIR:-$HOME/.local/bin}"
SCROOGE_HOME="${SCROOGE_HOME:-$HOME/.token-scrooge}"

say() { printf '%s\n' "$*"; }

# --- prerequisites -------------------------------------------------------
command -v python3 >/dev/null 2>&1 || { say "✗ python3 is required (3.8+)."; exit 1; }

# --- locate the repo (clone if piped via curl) ---------------------------
SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [ -z "${SRC:-}" ] || [ ! -f "$SRC/bin/scrooge" ]; then
  command -v git >/dev/null 2>&1 || { say "✗ git is required to bootstrap (or run ./install.sh from a clone)."; exit 1; }
  SRC="$SCROOGE_HOME/repo"
  say "▸ Fetching Token Scrooge into $SRC ..."
  if [ -d "$SRC/.git" ]; then git -C "$SRC" pull --ff-only --quiet; else git clone --depth 1 "$REPO_URL" "$SRC" --quiet; fi
fi

# --- install -------------------------------------------------------------
mkdir -p "$BIN_DIR" "$SCROOGE_HOME"
for b in scrooge scrooge-diverge scrooge-verify scrooge-drift; do
  chmod +x "$SRC/bin/$b"
  ln -sf "$SRC/bin/$b" "$BIN_DIR/$b"   # symlink → `git pull` keeps tools current
done
# --- registry: refresh untouched copies, never clobber local edits ----------
# We keep the last-shipped template at $SCROOGE_HOME/registry.template.json as a
# baseline. If your live registry.json is byte-identical to that baseline you
# never edited it, so it's safe to roll forward to the new template. If it
# differs, you (or a manual sync) changed it — we preserve it and just flag that
# a newer template exists.
NEW_TPL="$SRC/registry.template.json"
OLD_TPL="$SCROOGE_HOME/registry.template.json"
REG="$SCROOGE_HOME/registry.json"
if [ ! -f "$REG" ]; then
  cp "$NEW_TPL" "$REG"                                   # fresh install
  say "✓ Registry installed."
elif cmp -s "$REG" "$NEW_TPL"; then
  : # already current — nothing to do
elif [ -f "$OLD_TPL" ] && cmp -s "$REG" "$OLD_TPL"; then
  cp "$NEW_TPL" "$REG"                                   # untouched copy → roll forward
  say "✓ Registry auto-refreshed to the latest models (no local edits detected)."
else
  say "⚠ A newer registry template is available, but your registry.json has local"
  say "  edits — leaving it untouched. Compare with:"
  say "      diff \"$REG\" \"$NEW_TPL\"     (or run: scrooge-drift)"
fi
cp "$NEW_TPL" "$OLD_TPL"                                 # update baseline for next run

# --- live-training seed: keep a current copy in $SCROOGE_HOME ----------------
# The committed seed (lessons.seed.json) ships starter guardrails. The user-local
# lessons.json (gitignored) is created from it on first use and never clobbered.
if [ -f "$SRC/lessons.seed.json" ]; then
  cp "$SRC/lessons.seed.json" "$SCROOGE_HOME/lessons.seed.json"
fi

say "✓ Installed: scrooge, scrooge-diverge, scrooge-verify, scrooge-drift → $BIN_DIR"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) say "⚠ $BIN_DIR is not on your PATH. Add it:"
     say "    echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.zshrc && source ~/.zshrc" ;;
esac

# --- first-run setup -----------------------------------------------------
if [ "${1:-}" = "--no-setup" ] || [ ! -t 0 ]; then
  say ""
  say "Next: run the setup wizard to pick your orchestrator and add API keys:"
  say "    scrooge setup"
else
  say ""
  "$SRC/bin/scrooge" setup
fi
