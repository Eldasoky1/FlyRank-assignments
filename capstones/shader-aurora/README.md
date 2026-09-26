# Fragment shader hero — aurora

Capstone (CUSTOM-MRIH2B7J). A fullscreen WebGL1 fragment shader hero — see `index.html`.

## What was built
- **Interactive aurora hero**: `index.html` runs a raw WebGL1 fragment shader (no libraries) with:
  - `uv/time/mouse` mental model — mouse influence makes the flow field gently lean toward the
    cursor (`m.x` injected into band elevation);
  - value-noise aurora bands in blue/pink/teal with an additive glow;
  - a **grain pass** on top (hash-based dither);
  - title = name + one-line intro over it (contrast-treated, text-shadow).
- **Reduced-motion**: `matchMedia('(prefers-reduced-motion: reduce)')` freezes `u_time` so
  reduced-motion users get the same palette as a static gradient.
- **Every line is mine**: remixed from the session's aurora-gradient playground, palette swapped
  (blue/pink/teal), mouse influence + grain added, and every line in the shader is explained below.

## Shader line-by-line (what I kept / changed / why)
- `noise`/`hash` — playground's value noise, kept (required for believable bands).
- `warp` term — added: fractures the band centerline so it doesn't look like stacked ellipses.
- `bands` loop — changed packing from 3 to 4 bands and injected `m.x` and per-band phase so the
  field tilts toward the cursor.
- `grain` — added: `hash(gl_FragCoord + time)` ±0.06 keeps it film-like, never static-band visible.
- `reduced` guard — added at the JS level (not in-shader) so frozen frames still render.

## Deliverables check
- Fragment shader shipped as a fullscreen hero on a real page → `index.html`.
- Understand uv/time/mouse well enough to modify on request → line-by-line above; try changing
  `palette a/b/c` or the `34.0` band width.
- Text stays readable (contrast as design) → `.hero h1/p` + text-shadow; `no-webgl` fallback.