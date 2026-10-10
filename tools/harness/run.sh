#!/bin/bash
# Run Augustus headless (no window on the desktop) with scripted input.
# usage: run.sh DATA_DIR SCRIPT_FILE SHOT_DIR [TIMEOUT_SECONDS] [BINARY]
HERE="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$1"
SCRIPT="$2"
SHOTDIR="$3"
TIMEOUT="${4:-20}"
BIN="${5:-/usr/games/augustus-game}"
mkdir -p "$SHOTDIR" "$SHOTDIR/xdg"
rm -f "$SHOTDIR"/*.ppm
env -u DISPLAY -u WAYLAND_DISPLAY \
    XDG_DATA_HOME="$SHOTDIR/xdg" \
    SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy SDL_RENDER_DRIVER=software \
    AUG_SCRIPT="$SCRIPT" AUG_SHOTDIR="$SHOTDIR" \
    LD_PRELOAD="$HERE/shim.so" \
    timeout -s KILL "$TIMEOUT" "$BIN" --windowed "$DATA_DIR" </dev/null >"$SHOTDIR/stdout.txt" 2>&1
echo "exit code: $?"
for f in "$SHOTDIR"/*.ppm; do
    [ -e "$f" ] && python3 -c "import sys; from PIL import Image; Image.open(sys.argv[1]).save(sys.argv[1][:-4] + '.png')" "$f" && rm "$f"
done
ls "$SHOTDIR"
