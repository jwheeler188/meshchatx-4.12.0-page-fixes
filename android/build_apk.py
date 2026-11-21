# Builds a MeshChatX APK with the page fixes (anchor links + fit width) (unsigned, unaligned).
#   python3 build_apk.py <official.apk> <out-unsigned.apk>
# Then: zipalign -p -f 4 out-unsigned.apk out-aligned.apk && apksigner sign ...
# (build.sh does all of it.)
#
# The page frame script lives inside the Chaquopy Python bundle
# assets/chaquopy/app.imy (a zip) at meshchatx/public/assets/nomad-crash-tab-*.js.
# We patch it with ../patch_anchor.py, rewrite app.imy, update its SHA-1 in
# assets/chaquopy/build.json (Chaquopy uses it to decide re-extraction), and
# copy every other APK entry unchanged except the old signature files.
import sys, os, io, json, hashlib, shutil, subprocess, tempfile, zipfile

src_apk, out_apk = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
patcher = os.path.join(here, "..", "patches", "patch_anchor.py")
IMY = "assets/chaquopy/app.imy"
BUILD = "assets/chaquopy/build.json"

def is_sig(name):
    if not name.startswith("META-INF/"): return False
    base = name[len("META-INF/"):]
    if "/" in base: return False
    return base == "MANIFEST.MF" or base.upper().endswith((".SF", ".RSA", ".DSA", ".EC"))

with zipfile.ZipFile(src_apk) as apk:
    imy_bytes = apk.read(IMY)

# --- patch the frame script inside app.imy
with tempfile.TemporaryDirectory() as td:
    with zipfile.ZipFile(io.BytesIO(imy_bytes)) as imy:
        targets = [n for n in imy.namelist()
                   if n.startswith("meshchatx/public/assets/nomad-crash-tab-") and n.endswith(".js")]
        if len(targets) != 1: sys.exit(f"frame script not found in app.imy ({targets})")
        target = targets[0]
        with open(os.path.join(td, os.path.basename(target)), "wb") as f:
            f.write(imy.read(target))
    rc = subprocess.run([sys.executable, "-I", patcher, td]).returncode
    if rc != 0: sys.exit(f"patch_anchor.py failed ({rc})")
    rc = subprocess.run([sys.executable, "-I", os.path.join(here, "..", "patches", "patch_fitwidth.py"), td]).returncode
    if rc != 0: sys.exit(f"patch_fitwidth.py failed ({rc})")
    with open(os.path.join(td, os.path.basename(target)), "rb") as f:
        patched_js = f.read()

# The app serves assets as "immutable" (1-year cache) and the service worker
# precaches them by URL, so an in-place update (adb install -r) would keep
# showing the old script. Give the patched script a new name and point every
# reference (nomad-crash-tab.html, service-worker.js) at it.
old_base = os.path.basename(target)
new_base = old_base[:-3] + "-fix" + hashlib.sha1(patched_js).hexdigest()[:8] + ".js"
new_target = target[:-len(old_base)] + new_base
TEXT_EXT = (".html", ".js", ".mjs", ".json", ".webmanifest", ".css")
renamed_refs = []

new_imy = io.BytesIO()
with zipfile.ZipFile(io.BytesIO(imy_bytes)) as imy, zipfile.ZipFile(new_imy, "w") as out:
    for info in imy.infolist():
        name = info.filename
        if name == target:
            data, name = patched_js, new_target
        else:
            data = imy.read(info)
            if name.startswith("meshchatx/public/") and name.endswith(TEXT_EXT) and old_base.encode() in data:
                data = data.replace(old_base.encode(), new_base.encode()); renamed_refs.append(name)
        zi = zipfile.ZipInfo(name, info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        zi.create_system = info.create_system
        out.writestr(zi, data)
new_imy = new_imy.getvalue()
sha1 = hashlib.sha1(new_imy).hexdigest()

# --- rebuild the APK
with zipfile.ZipFile(src_apk) as apk, zipfile.ZipFile(out_apk, "w") as out:
    for info in apk.infolist():
        if is_sig(info.filename): continue
        if info.filename == IMY:
            data = new_imy
        elif info.filename == BUILD:
            b = json.loads(apk.read(info))
            if "app.imy" not in b.get("assets", {}): sys.exit("build.json has no app.imy hash")
            b["assets"]["app.imy"] = sha1
            data = json.dumps(b, indent=4).encode()
        else:
            data = apk.read(info)
        zi = zipfile.ZipInfo(info.filename, info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        out.writestr(zi, data)
if not renamed_refs: sys.exit("no references to the frame script found - layout changed?")
print(f"built {out_apk}: patched {target} -> {new_base}, refs updated in {renamed_refs}, app.imy sha1 {sha1}")
