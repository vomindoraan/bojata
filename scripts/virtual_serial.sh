#!/usr/bin/env bash
set -euo pipefail

if ! command -v socat &>/dev/null; then
    echo "$0 requires socat to be installed"
    exit 1
fi

DELAY=${1:-0.33}
SYMLINK=${2:-/dev/ttyACM10}
SOCAT_LOG=$(mktemp)

# Create PTY (/dev/pts/N) and link to it
sudo socat -dd PTY,link="$SYMLINK",user="$USER",raw,echo=0 \
               PTY,user="$USER",raw,echo=0 2>"$SOCAT_LOG" &
SOCAT_PID=$!

cleanup() {
    echo "Shutting down..." >&2
    kill "$SOCAT_PID" || true
    rm -f "$SYMLINK" "$SOCAT_LOG"
}
trap cleanup EXIT INT TERM

# Poll the log file until socat prints both PTY paths
PTY=""
for _ in $(seq 20); do
    sleep 0.1
    match=$(grep -oP 'N PTY is \K/dev/pts/[0-9]+' "$SOCAT_LOG" | tail -1)
    if [[ -n "$match" ]]; then
        PTY="$match"
        break
    fi
done
if [[ -z "$PTY" ]]; then
    echo "Timed out waiting for socat PTY" >&2
    exit 2
fi

echo "Virtual serial port ready: $SYMLINK -> $PTY" >&2

while true; do
    r=$(( RANDOM % 256 ))
    g=$(( RANDOM % 256 ))
    b=$(( RANDOM % 256 ))
    printf "%d,%d,%d\r\n" "$r" "$g" "$b" > "$PTY"
    sleep "$DELAY"
done
