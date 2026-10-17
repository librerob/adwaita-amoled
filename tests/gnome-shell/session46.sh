#!/usr/bin/env bash
set -euo pipefail
# Mutter 46's test runner forces its child backend to memory. Restore the
# isolated on-disk preferences prepared by the Python fixture.
export GSETTINGS_BACKEND=keyfile
exec gnome-shell --wayland --headless --no-x11 --virtual-monitor 1600x1200
