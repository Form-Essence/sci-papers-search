#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v pm2 &> /dev/null; then
    echo "Error: PM2 is not installed. Please install it with: npm install -g pm2"
    exit 1
fi

usage() {
    cat <<EOF
Usage: ./log.sh [--error|-e] [--out|-o] [--lines|-n <number>]

Flags:
  --error, -e           show only error logs
  --out,   -o           show only stdout logs
  --lines, -n <number>  show last N lines (non-streaming, default 50)
EOF
}

MODE=""
LINES=""

while [ $# -gt 0 ]; do
    case "$1" in
        --error|-e)  MODE="err"; shift ;;
        --out|-o)    MODE="out"; shift ;;
        --lines|-n)  LINES="${2:-50}"; shift 2 ;;
        -h|--help)   usage; exit 0 ;;
        *) echo "Unknown argument: $1"; usage; exit 1 ;;
    esac
done

TARGET="paper-search"
CMD=(pm2 logs "$TARGET")
[ "$MODE" = "err" ] && CMD+=(--err)
[ "$MODE" = "out" ] && CMD+=(--out)
if [ -n "$LINES" ]; then
    CMD+=(--lines "$LINES" --nostream)
    echo "Showing last $LINES lines of logs for $TARGET..."
else
    echo "Showing logs for $TARGET (Ctrl+C to exit)..."
    echo ""
fi

exec "${CMD[@]}"
