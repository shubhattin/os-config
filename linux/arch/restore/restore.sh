#!/usr/bin/env bash
# Launcher for restore.py: works on a bare archinstall system (installs python + rich if missing).
# Usage (from the Backup/ folder on the pen drive):   bash restore.sh [--dry-run|--list|--only ID,…]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$(id -u)" -eq 0 ]; then
  echo "Run as your normal user, not root (the script uses sudo itself)." >&2; exit 1
fi
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import rich' 2>/dev/null; then
  echo "[restore.sh] installing python + python-rich (sudo asks once here) …"
  sudo pacman -Sy --needed --noconfirm python python-rich
fi
exec python3 "$HERE/restore.py" "$@"
