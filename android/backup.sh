#!/bin/bash
# Copies MeshChatX's data (identity, messages, Reticulum config) off an Android
# device into ./meshchatx-backup-<date>/. Contains your PRIVATE identity key -
# keep it safe and don't share it.
#   bash backup.sh [adb-serial]
# Copies file by file because "adb pull" of the whole folder stops at the first
# file it can't read.
set -e
S=${1:+-s $1}
D="/sdcard/Android/data/com.meshchatx/files"
OUT="$(pwd)/meshchatx-backup-$(date +%Y%m%d-%H%M%S)"
adb $S shell "[ -d $D ]" || { echo "No MeshChatX data at $D"; exit 1; }
mkdir -p "$OUT"
adb $S shell "cd $D && find . -type f" | tr -d '\r' > "$OUT/.filelist"
total=$(wc -l < "$OUT/.filelist"); n=0; bad=0
while IFS= read -r f; do
	mkdir -p "$OUT/files/$(dirname "$f")"
	if adb $S pull "$D/$f" "$OUT/files/$f" >/dev/null 2>&1; then n=$((n+1)); else bad=$((bad+1)); echo "could not copy: $f"; fi
done < "$OUT/.filelist"
echo "Copied $n of $total files to $OUT ($bad failed)"
