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
for b in scrooge scrooge-diverge scrooge-verify; do
  chmod +x "$SRC/bin/$b"
  ln -sf "$SRC/bin/$b" "$BIN_DIR/$b"   # symlink → `git pull` keeps tools current
done
cp "$SRC/registry.template.json" "$SCROOGE_HOME/registry.template.json"
[ -f "$SCROOGE_HOME/registry.json" ] || cp "$SRC/registry.template.json" "$SCROOGE_HOME/registry.json"

say "✓ Installed: scrooge, scrooge-diverge, scrooge-verify → $BIN_DIR"

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
