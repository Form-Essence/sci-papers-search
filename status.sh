#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v pm2 &> /dev/null; then
    echo "Error: PM2 is not installed. Please install it with: npm install -g pm2"
    exit 1
fi

APP="paper-search"

echo "PM2 Status:"
echo "==========="
pm2 status

echo ""
echo "Details: $APP"
echo "=================="
if pm2 describe "$APP" > /dev/null 2>&1; then
    pm2 describe "$APP"
else
    echo "  (not registered with PM2)"
fi
