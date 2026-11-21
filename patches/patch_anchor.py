# Makes micron in-page links like `[Arts`#arts] (Retipedia contents) scroll to
# their anchor inside the Nomad page sandbox frame, instead of being sent to the
# parent as a navigation ("unsupported url: #arts"). MeshChatX 4.12.0.
# Usage: python3 patch_anchor.py <assets dir>   (exit 0 patched, 3 already, 2 not found)
import sys, os, re, shutil
assets = sys.argv[1]
MARK = "/*anchor-links*/"
OLD = 'const o=e.closest(\'[data-action="openNode"]\');if(o){'
SCROLL = ('let w,h=q.slice(1);try{h=decodeURIComponent(h)}catch(x){}'
          'try{w=r.querySelector(`#${CSS.escape(h)}`)}catch(x){w=document.getElementById(h)}'
          'w||(w=document.getElementById(h));'
          'return void(w&&w.scrollIntoView({behavior:"smooth",block:"start"}))')
# start from the pristine file if an earlier version of this patch was applied
for f in os.listdir(assets):
    if f.startswith("nomad-crash-tab-") and f.endswith(".js.orig"):
        shutil.copy2(os.path.join(assets, f), os.path.join(assets, f[:-5]))
hits = []
for f in os.listdir(assets):
    if f.startswith("nomad-crash-tab-") and f.endswith(".js"):
        p = os.path.join(assets, f); s = open(p, encoding="utf-8").read()
        if MARK in s and "data-destination\")||\"\").trim();" in s: print("Already patched:", f); sys.exit(3)
        if s.count(OLD) == 1: hits.append((p, s))
if len(hits) != 1: print(f"frame link handler not found ({len(hits)} files)"); sys.exit(2)
p, s = hits[0]
NEW = (OLD + MARK + '{const q=(o.getAttribute("data-destination")||"").trim();'
       'if("#"===q.charAt(0)&&q.length>1){t.preventDefault(),t.stopPropagation();' + SCROLL + '}}')
if not os.path.exists(p + ".orig"): shutil.copy2(p, p + ".orig")
open(p, "w", encoding="utf-8").write(s.replace(OLD, NEW, 1))
print("Patched:", os.path.basename(p))
