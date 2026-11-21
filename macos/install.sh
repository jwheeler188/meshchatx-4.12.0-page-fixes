#!/bin/bash
# Installs the MeshChatX 4.12.0 page fixes (anchor links + fit width) into the
# macOS app. Quit MeshChatX first.
#   bash install.sh                      # finds the app in /Applications
#   bash install.sh "/path/to/Some.app"  # or name it
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
PATCHES="$HERE/../patches"
APP="$1"
if [ -z "$APP" ]; then
	for a in "/Applications/Reticulum MeshChatX.app" "/Applications/meshchatx-desktop.app" "/Applications/MeshChatX.app" "$HOME/Applications/meshchatx-desktop.app"; do
		[ -d "$a/Contents/Resources/backend/public/assets" ] && { APP="$a"; break; }
	done
fi
[ -n "$APP" ] && [ -d "$APP/Contents/Resources/backend/public/assets" ] || { echo "MeshChatX app not found - run: bash install.sh \"/path/to/the.app\""; exit 1; }
ASSETS="$APP/Contents/Resources/backend/public/assets"
if pgrep -f "^$APP/Contents/" >/dev/null; then echo "MeshChatX is still running - quit it first (check Activity Monitor for a leftover ReticulumMeshChatX process)."; exit 1; fi
ver=$(defaults read "$APP/Contents/Info.plist" CFBundleShortVersionString)
[ "$ver" = "4.12.0" ] || { echo "These patches are for MeshChatX 4.12.0, found $ver - not installing."; exit 1; }
echo "Patching $APP"
set +e; python3 -I "$PATCHES/patch_anchor.py" "$ASSETS"; rc=$?; set -e
[ $rc -eq 0 ] || [ $rc -eq 3 ] || { echo "anchor-links patch failed ($rc)"; exit $rc; }
set +e; python3 -I "$PATCHES/patch_fitwidth.py" "$ASSETS"; rc=$?; set -e
[ $rc -eq 0 ] || [ $rc -eq 3 ] || { echo "fit-width patch failed ($rc)"; exit $rc; }
# Patching changes files inside the app, so give it a fresh local (ad-hoc) signature.
codesign --force --deep --sign - "$APP" 2>&1 | tail -1
codesign --verify --deep "$APP"
# The app caches its page scripts; move the cache aside so the patched one loads.
id=$(defaults read "$APP/Contents/Info.plist" CFBundleIdentifier 2>/dev/null || true)
C="$HOME/Library/Caches/$id/WebKit"
if [ -n "$id" ] && [ -d "$C" ]; then mv "$C" "$C.bak-pagefix-$(date +%Y%m%d%H%M%S)"; echo "Moved web cache aside: $C.bak-pagefix-*"; fi
echo "Installed. Start MeshChatX again."
