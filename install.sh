#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
    echo 'Python 3.11 or newer is required. No compiler or sudo is needed.' >&2
    exit 1
fi
exec python3 "$ROOT/tools/install.py" "$@"
