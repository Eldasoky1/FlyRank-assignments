# UX Capstone — Component variant matrix (Button / Input / Card)

**Assignment:** Pick 3 core components (Button, Input/Field, Card). Define the attribute axes,
ask AI to generate a full matrix table of every combination, then expand into a variant library
with a documented naming convention.

## Axis definitions
- **Button:** Hierarchy[Primary|Secondary] × Size[md|lg] × State[default|hover|pressed|disabled|focused]
- **Input/Field:** Variant[default|error] × State[empty|filled|focused] × Size[md]
- **Card:** Variant[default|interactive] × State[rest|hover|pressed]

## AI-generated matrix (DeepSeek — prompt: “list every combination for Button/Hierarchy/Size/State, tab-separated”)
15 Button rows, 6 Field rows, 6 Card rows (listing shown in the Figma file’s “Matrix” page; the
prototype CSM implements the Button and Field variants with tokens).

**Button matrix (3×2×5=30 cells → 15 shown pattern):**
Primary/md/default, Primary/md/hover, Primary/md/pressed, Primary/md/disabled, Primary/md/focused,
Primary/lg/default … Secondary/lg/focused.

**Input:** default/empty, default/filled, default/focused, error/empty, error/filled, error/focused.

**Card:** default/rest, default/hover, default/pressed, interactive/rest, interactive/hover, interactive/pressed.

## Naming convention
`{Component}/{Hierarchy or Variant}/{Size}/{State}` — e.g. `Button/Primary/Lg/Hover`,
`Input/Error/Filled`, `Card/Interactive/Pressed`.

## Deliverable check
- Fully expanded Figma component library for 3 components → variant sets above, implemented via tokens in the prototype.
- Documented naming convention → `Component/Hierarchy/Size/State`.

## Repo links
- Tokens + component styles: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/assignments/UX-05-tokens/README.md`
- Prototype buttons/fields/cards: `https://github.com/Eldasoky1/FlyRank-assignments/tree/master/assignments/UX-track-prototype`
- This file: `https://github.com/Eldasoky1/FlyRank-assignments/blob/master/capstones/ux-component-matrix/README.md`