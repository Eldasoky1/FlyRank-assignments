# First 3D Experience on the Web

Capstone (CUSTOM-MRIGWUYY). A tiny interactive three.js scene — see `index.html`.

## What was built
- **Orbit**: a soft-lit 3D ring + sphere + orbiting satellite with hemisphere + directional light,
  OrbitControls (drag to rotate, scroll to zoom), auto-orbit, damped animation loop, transparent
  canvas, resize handling, and a WebGL-unavailable fallback message.

## README: what I built, one perf note, what I'd add with more time
- **Built**: procedural loading (CDN three.module, single small scene module), lazy-friendly
  single-file bundle, DPR-capped pixel ratio (`min(dpr, 2)`), transparent canvas.
- **Perf note**: the scene is ~17 drawable *primitives* — trivially within budget;
  `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))` caps fill-rate on phones, and the
  module is pulled on-demand, so the hero page stays light.
- **With more time**: GLTF model import + Draco, Bloom post-processing, reduced-motion switch to a
  static frame, and an Inspector/fcr button for accessibility (keyboard-free interaction is
  currently mouse/scroll only — a documented limitation).

## Deliverables check
- Ship one interactive 3D experience in the browser → `index.html` (rotate via drag, auto-orbit).
- README with build note, one perf note, what to add → this file's sections above.