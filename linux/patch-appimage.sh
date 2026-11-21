#!/bin/bash
# Makes a patched copy of the MeshChatX 4.12.0 AppImage.
#   bash patch-appimage.sh ReticulumMeshChatX-v4.12.0-linux-x64.AppImage
# Run it on a Linux machine of the same architecture as the AppImage.
# Result:
#  - with appimagetool on PATH: <name>-pagefix.AppImage next to the original
#  - without it: a patched folder <name>-pagefix/; start MeshChatX with
#    <name>-pagefix/AppRun
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
IMG="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
[ -f "$IMG" ] || { echo "usage: bash patch-appimage.sh <MeshChatX .AppImage>"; exit 2; }
NAME="$(basename "$IMG" .AppImage)-pagefix"
OUTDIR="$(dirname "$IMG")"
WORK="$(mktemp -d)"
chmod +x "$IMG"
( cd "$WORK" && "$IMG" --appimage-extract >/dev/null )
python3 "$HERE/install.py" --dir "$WORK/squashfs-root"
if command -v appimagetool >/dev/null; then
	ARCH=$(uname -m) appimagetool "$WORK/squashfs-root" "$OUTDIR/$NAME.AppImage" >/dev/null
	rm -rf "$WORK"
	echo "Built $OUTDIR/$NAME.AppImage"
else
	rm -rf "$OUTDIR/$NAME"; mv "$WORK/squashfs-root" "$OUTDIR/$NAME"; rmdir "$WORK"
	echo "appimagetool not found, so the patched app is a folder:"
	echo "  start it with: $OUTDIR/$NAME/AppRun"
fi
