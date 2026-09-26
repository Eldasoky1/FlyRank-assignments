# AI Fluency — Week 3 · Identity kit (Decide Once)

**Deliverable:** a two-line style note (fonts, hex codes, one sentence on the mood), added to the
Claude Project so the build stays consistent.

## The style note (2 lines)
```
FONTS: system-ui sans (body) + JetBrains Mono (labels/data)  ·  HEX: bg #f7f7f5, ink #0f172a, muted #64748b, accent #07f49e (CTA-only), danger #dc2626
MOOD: "Calm and confident — a white lab coat with one green button; only the action gets colour."
```

## Added to the Claude Project
This exact block lives in the `fl-cap` Claude Project's custom instructions (appended to the proof
statement + tutor role), so every generated asset, wireframe and copy decision inherits the same
tokens and mood. (`fl-cap` = Claude Project `f4d401b2-…`.)

## The kit in practice
- The deployed site (`assignments/PF-04-personal-website/site/index.html`) uses these exact hexes;
  the accent `#07f49e` appears only on link/action elements.
- Consistency check: no new color has been introduced anywhere without a reason (see
  AI-fluency-decide-look for the rejections).

## Deliverable check
- Two-line style note (fonts, hex, mood) → the block above.
- Added to the Claude Project → custom-instructions snippet lives in `fl-cap`.

## Repo link
`https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/AI-fluency-identity-kit/README.md`