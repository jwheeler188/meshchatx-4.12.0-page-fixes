# Micron in-page anchor links (`#section`) don't scroll: "unsupported url: #arts" (4.12.0)

**Version:** 4.12.0 (macOS, Android; shared frontend
`meshchatx/src/frontend/js/nomadCrashTabMain.js`)

## What happens

Micron links that point to an anchor on the same page don't work. For example,
the contents list on Retipedia articles uses `` `[Arts`#arts] ``. Clicking one
shows an "unsupported url: #arts" error, and the page doesn't move.

It doesn't look like a recent regression. The click handling below is the same
from at least v4.10.0 through v4.12.0. The micron parser is pinned to the same
commit across those versions, and pages were already in the sandboxed frame in
v4.9.3.

## How to reproduce

1. Open a Retipedia article with a contents list, from
   `ecb618b568d276fabbeed7355845cb91:/page/Retipedia/index.mu`.
2. Click an entry in the contents.
3. The error appears, and the page doesn't scroll to the section.

## Cause

The micron renderer turns `` `[label`#anchor] `` into a `.Mu-nl` element with
`data-action="openNode"` and `data-destination="#anchor"`. In the frame's
`onClick()`, the `[data-action="openNode"]` branch posts every destination to
the parent as `{type: "navigate", kind: "openNode", url}`. The parent can't
resolve a bare `#anchor` as a Nomad URL, so it reports it as unsupported. The
target element with that id is inside the frame's own document.

## Suggested fix

In `onClick()`, handle same-page anchors inside the frame before posting the
navigation:

```js
const node = t.closest('[data-action="openNode"]');
if (node) {
    const dest = (node.getAttribute("data-destination") || "").trim();
    if (dest.length > 1 && dest.charAt(0) === "#") {
        event.preventDefault();
        event.stopPropagation();
        let id = dest.slice(1);
        try { id = decodeURIComponent(id); } catch (e) {}
        let target = null;
        try { target = root.querySelector(`#${CSS.escape(id)}`); } catch (e) {}
        if (!target) target = document.getElementById(id);
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
    }
    // ... existing openNode handling ...
}
```

## Tested

I patched the built `nomad-crash-tab-*.js` along these lines and tested it on
macOS 4.12.0, an Android 14 tablet and an Android 10 phone. Retipedia's
contents links scroll to their sections, and links to other pages and nodes
behave as before.

The patch script and test instructions are at https://github.com/jwheeler188/meshchatx-4.12.0-page-fixes (`patches/patch_anchor.py`).
