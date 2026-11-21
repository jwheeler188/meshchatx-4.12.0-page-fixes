# MeshChatX 4.12.0 "fit wide pages" fix for the Nomad page frame script
# (the page display mode toggled by the <-> button; "fit" is the default).
#
# Bug: fit measured every element's scrollWidth, including content that is
# clipped and never shown -- the screen-reader-only .Mu-sr text copies (one
# unwrapped copy of every line) and `-` divider lines (2400px of box chars in
# an overflow:hidden div). Any page with long prose lines or dividers was scaled
# to ~15%. Meanwhile ANSI/box-drawing art lines wrap (so were never measured)
# and break apart on narrow phones.
#
# New fit:
#  1. Art blocks (runs of consecutive leaf divs, not separators, that hold
#     3+ box/block chars U+2500-U+259F, or figlet-style ASCII art: <25% of the
#     non-space chars are letters/digits) wider than the screen get CSS zoom so the
#     whole block fits on one line per row. Text stays full size.
#  2. Then, if any *visible* block-level thing is still wider than the screen
#     (rect widths; scrollWidth only where overflow is visible; .Mu-sr and
#     clipped elements skipped), scale the page by screen/width (min 0.3) and
#     widen #root by 1/scale so prose still wraps to the full screen width.
# Switching mode clears the zoom/width again.
#
#   python3 patch_fitwidth.py <dir containing nomad-crash-tab-*.js>
# Exit: 0 patched, 3 already patched, 2 pattern not found.
# Run AFTER patch_anchor.py (which restores the pristine .orig first and keeps
# the only backup); install.sh and android/build_apk.py do both in order.
import sys, os, glob
MARK = "/*fit-v4*/"
START = 'const e=document.documentElement.clientWidth;let n=function(){'
END = 'r.style.marginBottom=-(1-a)*r.scrollHeight+"px"}'
RESET_OLD = 'r.style.width="",delete r.dataset.fitScale,'
RESET_NEW = ('r.style.width="",delete r.dataset.fitScale,r.style.maxWidth="",'
             'r.querySelectorAll("[data-fit-zoom]").forEach(t=>{t.style.zoom="",delete t.dataset.fitZoom}),')
NEW = (MARK +
 'const e=document.documentElement.clientWidth;if(e<=0)return;'
 # 1. art runs
 'const A=[...r.querySelectorAll("div")].filter(t=>!t.querySelector("div")&&"separator"!==t.getAttribute("role")&&(x=>{if(/[─-▟]{3}/.test(x))return!0;const n=x.replace(/\\s/g,"");return n.length>0&&(n.match(/[\\p{L}\\p{N}]/gu)||[]).length<.25*n.length})(t.textContent||""));'
 'const G=[];let p=null;for(const t of A){p&&t.previousElementSibling===p?G[G.length-1].push(t):G.push([t]);p=t}'
 'for(const g of G){let m=0;for(const t of g){const o=t.style.width;t.style.width="max-content";const w=t.getBoundingClientRect().width;t.style.width=o;w>m&&(m=w)}'
  'if(m>e+1){const z=Math.max(.2,(e-2)/m);for(const t of g)t.dataset.fitZoom=String(z),t.style.zoom=String(z)}}'
 # 2. remaining wide content
 'const C=/^(hidden|clip)$/;let n=0;'
 'for(const t of r.querySelectorAll("*")){if(t.closest(".Mu-sr,[data-fit-zoom]"))continue;'
  'const c=getComputedStyle(t);if("inline"===c.display||"absolute"===c.position&&C.test(c.overflowX))continue;'
  'const w=t.getBoundingClientRect().width;w>n&&(n=w);'
  'if(!C.test(c.overflowX)){const s=t.scrollWidth;s>n&&(n=s)}}'
 'if(n<=e+1)return;'
 'const a=Math.max(.3,e/n);r.dataset.fitScale=String(a);r.style.transformOrigin="0 0";'
 'r.style.maxWidth="none";r.style.width=100/a+"%";r.style.transform=`scale(${a})`;'
 'r.style.marginBottom=-(1-a)*r.scrollHeight+"px"}')
files = glob.glob(os.path.join(sys.argv[1], "nomad-crash-tab-*.js"))
if len(files) != 1: print("frame script not found"); sys.exit(2)
f = files[0]; s = open(f, encoding="utf-8").read()
if MARK in s: print("Already patched:", f); sys.exit(3)
i = s.find(START); j = s.find(END, i)
if i < 0 or j < 0 or s.count(START) != 1: print("fit code not found"); sys.exit(2)
s = s[:i] + NEW + s[j + len(END):]
if s.count(RESET_OLD) != 1: print("reset code not found"); sys.exit(2)
s = s.replace(RESET_OLD, RESET_NEW)
open(f, "w", encoding="utf-8").write(s)
print("Patched fit-width:", os.path.basename(f))
