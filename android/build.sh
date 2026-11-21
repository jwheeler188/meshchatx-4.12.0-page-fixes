#!/bin/bash
# Builds a MeshChatX APK with the page fixes and signs it with YOUR OWN key.
#   bash build.sh <official ReticulumMeshChatX-v4.12.0-android-universal.apk>
# Output: <name>-pagefix.apk next to this script.
#
# Needs: python3, openssl, Java keytool, Android SDK build-tools (zipalign,
# apksigner). Set ANDROID_HOME if the SDK is not in a standard place.
#
# The signing key (meshchatx-local.keystore + keystore.pass) is created on the
# first run. KEEP IT and keep it private: later builds must use the same key or
# Android refuses to install them over the earlier one.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$1"; [ -f "$SRC" ] || { echo "usage: bash build.sh <MeshChatX.apk>"; exit 2; }
for SDK in "$ANDROID_HOME" "$ANDROID_SDK_ROOT" "$HOME/Library/Android/sdk" "$HOME/Android/Sdk"; do
	[ -n "$SDK" ] && [ -d "$SDK/build-tools" ] && break; SDK=""
done
[ -n "$SDK" ] || { echo "Android SDK build-tools not found - set ANDROID_HOME"; exit 2; }
BT="$(ls -d "$SDK/build-tools/"* | sort -V | tail -1)"
KS="$HERE/meshchatx-local.keystore"; PW="$HERE/keystore.pass"
if [ ! -f "$KS" ]; then
	umask 077
	openssl rand -base64 24 | tr -d '\n' > "$PW"
	keytool -genkeypair -keystore "$KS" -storepass:file "$PW" -keypass:file "$PW" \
		-alias local -keyalg RSA -keysize 3072 -validity 18250 \
		-dname "CN=MeshChatX local build" >/dev/null
	echo "Created signing key $KS (keep it and keystore.pass private)."
fi
NAME="$(basename "$SRC" .apk)-pagefix"
TMP="$(mktemp -d)"
python3 -I "$HERE/build_apk.py" "$SRC" "$TMP/unsigned.apk"
"$BT/zipalign" -p -f 4 "$TMP/unsigned.apk" "$TMP/aligned.apk"
"$BT/apksigner" sign --ks "$KS" --ks-pass "file:$PW" --ks-key-alias local --out "$HERE/$NAME.apk" "$TMP/aligned.apk"
"$BT/apksigner" verify --print-certs "$HERE/$NAME.apk" | grep -E 'Signer #1 certificate (DN|SHA-256)'
rm -f "$TMP/unsigned.apk" "$TMP/aligned.apk" "$HERE/$NAME.apk.idsig"; rmdir "$TMP"
echo "Built $HERE/$NAME.apk"
