#!/usr/bin/env python3
# MeshChatX 4.12.0 page fixes (anchor links + fit width) for Linux.
#
#   python3 install.py                     patch installed copies it can find
#                                          (.deb/.rpm backend, pip/pipx package)
#   python3 install.py --dir <folder>      patch a specific folder, e.g. an
#                                          extracted AppImage (squashfs-root)
#   python3 install.py --pyz in.pyz out.pyz  write a patched copy of a .pyz
#   python3 install.py --uninstall [--dir <folder>]   undo
#
# Quit MeshChatX first. System-wide installs (/usr/...) need sudo.
#
# How: the page viewer script public/assets/nomad-crash-tab-<hash>.js is
# patched and saved under a NEW name (…-fix<sha8>.js), and nomad-crash-tab.html
# and service-worker.js are pointed at it. The new name means no web or
# service-worker cache can keep serving the old script. The original files are
# kept in public/.pagefix-backup/ for --uninstall.
import sys, os, glob, shutil, hashlib, subprocess, tempfile, zipfile, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
PATCHES = [os.path.join(HERE, "..", "patches", "patch_anchor.py"),
           os.path.join(HERE, "..", "patches", "patch_fitwidth.py")]
BACKUP = ".pagefix-backup"
REF_FILES = ("nomad-crash-tab.html", "service-worker.js")

def patch_js(src_bytes, name):
    """Run both patchers on a copy of the script; return patched bytes."""
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, name)
        open(p, "wb").write(src_bytes)
        for patcher in PATCHES:
            rc = subprocess.run([sys.executable, "-I", patcher, td]).returncode
            if rc not in (0, 3):
                sys.exit(f"{os.path.basename(patcher)} failed ({rc}) - is this MeshChatX 4.12.0?")
        return open(p, "rb").read()

def new_name(orig_name, data):
    return orig_name[:-3] + "-fix" + hashlib.sha1(data).hexdigest()[:8] + ".js"

def find_public_dirs():
    found = []
    for pat in ("/usr/local/lib/reticulum-meshchatx/backend/**/public",
                "/usr/lib/reticulum-meshchatx/backend/**/public",
                "/opt/**/reticulum-meshchatx/**/public",
                os.path.expanduser("~/.local/share/pipx/venvs/*/lib/python*/site-packages/meshchatx/public"),
                os.path.expanduser("~/.local/lib/python*/site-packages/meshchatx/public"),
                "/usr/local/lib/python*/dist-packages/meshchatx/public",
                "/usr/lib/python*/site-packages/meshchatx/public"):
        found += glob.glob(pat, recursive=True)
    try:
        import importlib.util
        spec = importlib.util.find_spec("meshchatx")
        if spec and spec.submodule_search_locations:
            for loc in spec.submodule_search_locations:
                found.append(os.path.join(loc, "public"))
    except Exception:
        pass
    out = []
    for d in found:
        d = os.path.realpath(d)
        if d not in out and os.path.isfile(os.path.join(d, "nomad-crash-tab.html")):
            out.append(d)
    return out

def public_dirs_under(root):
    return sorted({os.path.dirname(h) for h in
                   glob.glob(os.path.join(root, "**", "nomad-crash-tab.html"), recursive=True)
                   if os.path.isdir(os.path.join(os.path.dirname(h), "assets"))})

def restore(pub):
    """Put the pristine files back (from the backup) and drop our patched script."""
    bk = os.path.join(pub, BACKUP)
    if not os.path.isdir(bk):
        return False
    for f in os.listdir(bk):
        dst = os.path.join(pub, "assets", f) if f.endswith(".js") and f.startswith("nomad-crash-tab-") else os.path.join(pub, f)
        shutil.copy2(os.path.join(bk, f), dst)
    for f in glob.glob(os.path.join(pub, "assets", "nomad-crash-tab-*-fix????????.js")):
        os.remove(f)
    return True

def install_dir(pub):
    assets = os.path.join(pub, "assets")
    restore(pub)  # start from pristine if patched before
    js = [f for f in glob.glob(os.path.join(assets, "nomad-crash-tab-*.js")) if "-fix" not in os.path.basename(f)]
    if len(js) != 1:
        print(f"  skip {pub}: page script not found"); return False
    js = js[0]; base = os.path.basename(js)
    patched = patch_js(open(js, "rb").read(), base)
    nn = new_name(base, patched)
    bk = os.path.join(pub, BACKUP)
    os.makedirs(bk, exist_ok=True)
    if not os.path.exists(os.path.join(bk, base)):
        shutil.copy2(js, os.path.join(bk, base))
    for r in REF_FILES:
        p = os.path.join(pub, r)
        if os.path.isfile(p) and not os.path.exists(os.path.join(bk, r)):
            shutil.copy2(p, os.path.join(bk, r))
    open(os.path.join(assets, nn), "wb").write(patched)
    n = 0
    for r in REF_FILES:
        p = os.path.join(pub, r)
        if os.path.isfile(p):
            s = open(p, "rb").read()
            if base.encode() in s:
                open(p, "wb").write(s.replace(base.encode(), nn.encode())); n += 1
    if n == 0:
        restore(pub); print(f"  skip {pub}: nothing references {base}"); return False
    print(f"  patched {pub}\n    {base} -> {nn}")
    return True

def patch_pyz(src, dst):
    raw = open(src, "rb").read()
    with zipfile.ZipFile(src) as z:
        infos = z.infolist()
        # a .pyz is "#!shebang\n" + zip; keep the prefix
        first = min(i.header_offset for i in infos)
        prefix = raw[:first]
        names = z.namelist()
        js = [n for n in names if "/public/assets/nomad-crash-tab-" in n and n.endswith(".js")]
        if len(js) != 1: sys.exit("page script not found in the .pyz")
        js = js[0]; base = os.path.basename(js)
        patched = patch_js(z.read(js), base)
        nn = new_name(base, patched)
        pubdir = js[:js.index("/assets/")]
        tmp = dst + ".tmp"
        with open(tmp, "wb") as out:
            out.write(prefix)
            with zipfile.ZipFile(out, "a") as zo:
                for i in infos:
                    data = z.read(i); name = i.filename
                    if name == js:
                        data, name = patched, name[:-len(base)] + nn
                    elif name in (f"{pubdir}/{r}" for r in REF_FILES):
                        data = data.replace(base.encode(), nn.encode())
                    zi = zipfile.ZipInfo(name, i.date_time)
                    zi.compress_type = i.compress_type; zi.external_attr = i.external_attr
                    zo.writestr(zi, data)
        os.replace(tmp, dst); os.chmod(dst, os.stat(src).st_mode)
    print(f"Wrote {dst} ({base} -> {nn})")

def main():
    ap = argparse.ArgumentParser(description="MeshChatX 4.12.0 page fixes for Linux")
    ap.add_argument("--dir", help="patch MeshChatX files under this folder (e.g. squashfs-root)")
    ap.add_argument("--pyz", nargs=2, metavar=("IN", "OUT"), help="write a patched copy of a .pyz")
    ap.add_argument("--uninstall", action="store_true")
    a = ap.parse_args()
    if a.pyz:
        patch_pyz(*a.pyz); return
    pubs = public_dirs_under(a.dir) if a.dir else find_public_dirs()
    if not pubs:
        sys.exit("No MeshChatX install found. Use --dir <folder> (e.g. an extracted AppImage) or --pyz.")
    ok = 0
    for pub in pubs:
        try:
            if a.uninstall:
                if restore(pub):
                    shutil.rmtree(os.path.join(pub, BACKUP)); print(f"  restored {pub}"); ok += 1
            elif install_dir(pub):
                ok += 1
        except PermissionError:
            print(f"  {pub}: permission denied - run with sudo")
    if not ok: sys.exit(1)
    print("Done. Start MeshChatX again.")

if __name__ == "__main__":
    main()
