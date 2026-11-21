#!/bin/bash
# Puts a backup made by backup.sh back after installing the patched APK.
#   bash restore.sh <meshchatx-backup-folder> [adb-serial]
# Order matters: install the APK, open MeshChatX once (so Android creates its
# data folder - don't create it yourself), then run this. It stops the app,
# copies the files back and starts the app again.
set -e
B="$1"; [ -d "$B/files" ] || { echo "usage: bash restore.sh <meshchatx-backup-folder> [adb-serial]"; exit 2; }
S=${2:+-s $2}
D="/sdcard/Android/data/com.meshchatx/files"
adb $S shell "[ -d $D ]" || { echo "Open MeshChatX once first so it creates $D, then re-run."; exit 1; }
adb $S shell am force-stop com.meshchatx
adb $S push "$B/files/." "$D/"
adb $S shell monkey -p com.meshchatx -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
echo "Restored. MeshChatX is starting - the first start can take a minute."
