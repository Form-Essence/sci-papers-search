#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v pm2 &> /dev/null; then
    echo "Error: PM2 is not installed. Please install it with: npm install -g pm2"
    exit 1
fi

APP="paper-search"
LEGACY_APPS=("paper-search-backend" "paper-search-frontend" "paper-search-mcp")

echo "Stopping paper-search..."
FAILED=0

if pm2 describe "$APP" > /dev/null 2>&1; then
    pm2 stop "$APP" || FAILED=1
else
    echo "  (skipping $APP — not registered with PM2)"
fi

# Clean up any legacy multi-process installs from before the unification.
for app in "${LEGACY_APPS[@]}"; do
    if pm2 describe "$app" > /dev/null 2>&1; then
        echo "  removing legacy app: $app"
        pm2 delete "$app" > /dev/null 2>&1 || true
    fi
done

if [ $FAILED -eq 0 ]; then
    echo "✓ paper-search stopped successfully!"
else
    echo "Warning: paper-search failed to stop cleanly"
    exit 1
fi
