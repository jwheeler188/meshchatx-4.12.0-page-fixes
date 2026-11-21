# Nomad page "fit" mode shrinks pages with long text or `-` dividers to ~15% (4.12.0)

**Version:** 4.12.0 (Android, macOS, and the Linux AppImage/wheel builds; they share
`meshchatx/src/frontend/js/nomadCrashTabMain.js`)

## What happens

The default page display mode, "Fit wide pages to the screen", makes many
ordinary pages unreadably small. On a phone the page shows as a narrow strip of
tiny text, about 15% of normal size. Desktop windows narrower than about
2,600 px show the same effect, less strongly.

It happens with any page that has a long paragraph line or a `-` divider, even
when nothing on the page is actually wider than the screen.

## How to reproduce

1. On Android (or any narrow window), open a micron page that has a long line of
   prose (200+ characters) and/or a `-` divider. For example:
   `a6eaa98af0f97579edcfc83c39a72f0c:/page/index.mu`
2. Leave the display mode on "fit", the default.
3. The whole page is scaled to about 0.14. On a 360 px wide screen,
   `#root[data-fit-scale]` is `0.1446…`.

## Cause

`widestContentWidth()` takes the maximum `scrollWidth` and rect width over
every element under `#root`. Two kinds of element report a large
`scrollWidth` that is never shown on screen:

- **The hidden screen-reader copy of each line,** `span.Mu-sr`. It uses
  `position: absolute; width: 1px; overflow: hidden; clip: rect(0,0,0,0);
  white-space: nowrap`, so its `scrollWidth` is the full unwrapped line. On the
  test page it measures 2,592 px, for a line that wraps fine on screen.
- **Divider lines** (`<div role="separator" style="width:100%; white-space:nowrap;
  overflow:hidden">` filled with `─`). Their `scrollWidth` is 2,400 px, but the
  overflow is meant to be cut off.

So `natural` comes out at about 2,600 px. At 360 px, `avail / natural` gives a
scale of about 0.14. The page itself, `#root.scrollWidth`, is only 360 px wide.

A related problem: wide ASCII or box-drawing art (figlet headers, block
banners) is made of inline segments, so it wraps instead of overflowing. Its
`scrollWidth` is never larger than the screen, so fit doesn't help it. On
phones it breaks into a jumble, for example Retipedia's header at
`ecb618b568d276fabbeed7355845cb91:/page/Retipedia/index.mu`.

## Suggested fix

In `widestContentWidth()`, skip content that is clipped on purpose:

```js
function widestContentWidth() {
    let w = 0;
    for (const el of root.querySelectorAll("*")) {
        if (el.closest(".Mu-sr, [data-fit-zoom]")) continue;      // screen-reader copies, zoomed art
        const cs = getComputedStyle(el);
        if (cs.display === "inline") continue;                    // wrapped inline boxes
        const clipped = /^(hidden|clip)$/.test(cs.overflowX);     // e.g. dividers
        if (cs.position === "absolute" && clipped) continue;
        w = Math.max(w, el.getBoundingClientRect().width);
        if (!clipped) w = Math.max(w, el.scrollWidth);
    }
    return w;
}
```

Optionally, fit art blocks on their own instead of scaling the whole page. In
`applyDisplayMode()` for fit mode:

1. Find runs of consecutive leaf `div` lines, not separators, that are art. A
   line counts as art if it has 3+ box or block characters (U+2500–U+259F), or
   if fewer than 25% of its non-space characters are letters or digits
   (figlet).
2. Measure each run's natural width with `width: max-content`.
3. If a run is wider than the screen, set `zoom: avail / width` on each of its
   lines.

Text then stays full size and wraps, and banners stay whole. Clear the zoom in
`resetDisplayModeStyles()`.

Also, when fit does scale the page, `.nodeContainer { max-width: 100% }` keeps
`#root` at screen width, so prose wraps at screen width and then shrinks. Set
`root.style.maxWidth = "none"` and `root.style.width = 100 / scale + "%"`, so
the scaled page still fills the screen.

## Tested

I patched the built `nomad-crash-tab-*.js` along these lines and tested it on
Android 10, Android 14 (tablet) and macOS 4.12.0.

- **Before:** the test pages rendered at scale 0.14.
- **After:**
  - No page scaling.
  - Text is full size.
  - The block-art banner is zoomed to 0.55 and the Retipedia figlet header to
    0.62, each staying whole.
  - Switching between fit and scroll mode still works.
  - At 1,000 px wide, nothing is zoomed.

The patch scripts and test instructions are at https://github.com/jwheeler188/meshchatx-4.12.0-page-fixes (`patches/patch_fitwidth.py`).
