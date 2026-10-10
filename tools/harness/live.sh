#!/bin/bash
# Interactive headless control of Augustus.
#   live.sh start DATA_DIR WORK_DIR [BINARY]   start the game in the background
#   live.sh do WORK_DIR "cmd args" ...         send commands (click X Y, drag ..., key SC SYM, text S, move X Y)
#   live.sh shot WORK_DIR NAME [WAIT_MS]       wait, take a screenshot -> WORK_DIR/NAME.png
#   live.sh stop WORK_DIR
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -f "$HERE/shim.so" ] || gcc -shared -fPIC -O2 -o "$HERE/shim.so" "$HERE/shim.c" -ldl
case "$1" in
start)
    DATA="$2"; WORK="$3"; BIN="${4:-/usr/games/augustus-game}"
    mkdir -p "$WORK/xdg"; : > "$WORK/cmds"; rm -f "$WORK"/*.ppm
    env -u DISPLAY -u WAYLAND_DISPLAY XDG_DATA_HOME="$WORK/xdg" \
        SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy SDL_RENDER_DRIVER=software \
        AUG_CMDFILE="$WORK/cmds" AUG_SHOTDIR="$WORK" LD_PRELOAD="$HERE/shim.so" \
        nohup "$BIN" --windowed "$DATA" </dev/null >"$WORK/stdout.txt" 2>&1 &
    echo $! > "$WORK/pid"
    sleep 2; echo "started pid $(cat "$WORK/pid")";;
do)
    WORK="$2"; shift 2
    for c in "$@"; do echo "$c" >> "$WORK/cmds"; sleep 0.35; done;;
shot)
    WORK="$2"; NAME="$3"; WAIT="${4:-300}"
    sleep "$(echo "$WAIT/1000" | bc -l)"
    rm -f "$WORK/$NAME.ppm" "$WORK/$NAME.png"
    echo "shot $NAME" >> "$WORK/cmds"
    for i in $(seq 1 50); do [ -s "$WORK/$NAME.ppm" ] && break; sleep 0.1; done
    sleep 0.2
    python3 -c "import sys; from PIL import Image; Image.open(sys.argv[1]).save(sys.argv[2])" "$WORK/$NAME.ppm" "$WORK/$NAME.png" && rm "$WORK/$NAME.ppm"
    kill -0 "$(cat "$WORK/pid")" 2>/dev/null || echo "GAME NOT RUNNING"
    echo "$WORK/$NAME.png";;
stop)
    kill "$(cat "$2/pid")" 2>/dev/null; sleep 1; kill -9 "$(cat "$2/pid")" 2>/dev/null; echo stopped;;
esac
