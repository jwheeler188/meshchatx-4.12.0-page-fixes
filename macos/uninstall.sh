#!/bin/bash
# Removes the page fixes: restores the original MeshChatX page script.
# Quit MeshChatX first.   bash uninstall.sh ["/path/to/the.app"]
set -e
APP="$1"
if [ -z "$APP" ]; then
	for a in "/Applications/Reticulum MeshChatX.app" "/Applications/meshchatx-desktop.app" "/Applications/MeshChatX.app" "$HOME/Applications/meshchatx-desktop.app"; do
		[ -d "$a/Contents/Resources/backend/public/assets" ] && { APP="$a"; break; }
	done
fi
[ -n "$APP" ] && [ -d "$APP/Contents/Resources/backend/public/assets" ] || { echo "MeshChatX app not found - run: bash uninstall.sh \"/path/to/the.app\""; exit 1; }
ASSETS="$APP/Contents/Resources/backend/public/assets"
if pgrep -f "^$APP/Contents/" >/dev/null; then echo "MeshChatX is still running - quit it first."; exit 1; fi
n=0; for o in "$ASSETS"/nomad-crash-tab-*.js.orig; do [ -f "$o" ] || continue; mv "$o" "${o%.orig}"; n=$((n+1)); done
[ $n -gt 0 ] || { echo "No backup found - patches not installed?"; exit 1; }
codesign --force --deep --sign - "$APP" 2>&1 | tail -1
id=$(defaults read "$APP/Contents/Info.plist" CFBundleIdentifier 2>/dev/null || true)
C="$HOME/Library/Caches/$id/WebKit"
if [ -n "$id" ] && [ -d "$C" ]; then mv "$C" "$C.bak-unpatch-$(date +%Y%m%d%H%M%S)"; fi
echo "Original restored. Start MeshChatX again."
