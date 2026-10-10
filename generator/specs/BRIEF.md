# Brief: specifying replacement data for Augustus (Caesar III re-implementation)

We are creating **original, procedurally generated** replacement data files so that the
open-source game Augustus 4.0.0 can run without the proprietary Caesar III data. We do NOT
have and must NOT use any original Caesar III files. Our generator needs a precise
*specification* of what the engine expects, derived only from the Augustus source code.

Augustus v4.0.0 source (read-only reference):
`/tmp/claude-1000/-home-johane-projects-AUGUSTUS/0e95c5fb-1911-433f-87c2-374708527e22/scratchpad/src`
(C sources under `src/`). Augustus' own extra PNG assets + XML live in
`/usr/share/augustus-game/assets/Graphics/*.xml`; those XML files sometimes reference original
images as `<layer group="G" image="N"/>` (G = numeric group id, N = offset inside the group) —
treat such references as additional usages that must exist.

## Graphics file model (c3.sg2 index + c3.555 pixels)

* The main graphics file holds 10000 image slots. A table maps each **group id**
  (see `src/core/image_group.h`, `GROUP_*`, max 300) to the index of the group's first image.
  Code accesses images as `image_group(GROUP_X) + offset`. **We decide the absolute layout**;
  you only specify, per group, how many images it needs (max offset used + 1) and what each
  offset must look like.
* Image kinds:
  * `iso` — isometric tile/building (type 30). Size in tiles `n` is derived from width:
    `n = (width + 2) / 60`, so widths are 58, 118, 178, 238, 298, ... The diamond footprint is
    30*n px tall. A building may also have a `top` part rising above the diamond. Spec field
    `top` = pixels the artwork rises above the diamond's top vertex (0 = flat tile).
  * `sprite` — transparent (RLE-compressed) image of w x h px. Used for walkers/figures,
    animation frames, icons, cursors-in-UI, etc.
  * `opaque` — uncompressed w x h px (backgrounds, panels). May contain transparent key colour
    but is normally a full rectangle.
  * Large images (roughly > 400x400, e.g. full-screen backgrounds, the empire map) are stored
    "external"; mark them with `"external": true`.
* Animation metadata (`img->animation`: num_sprites, sprite_offset_x/y, can_reverse, speed_id)
  exists on an image only if num_sprites > 0.
  * Buildings: the *base* iso image carries the metadata; frames are the following images
    `base + 1 .. base + num_sprites` (sprites). See `draw_animation` in
    `src/widget/city_without_overlay.c` and `src/building/animation.c`.
  * Figures: `src/widget/city_figure.c adjust_pixel_offset` subtracts the image's
    sprite_offset_x/y, so we will give every figure sprite an anchor (feet position). You
    don't need to compute anchors, just say "figure" sprites and approximate size.
* Fonts are images in GROUP_FONT (see `src/graphics/font.c`).

## What to produce

Write a JSON file (path given in your task) shaped like:

```json
{
  "GROUP_TERRAIN_GRASS_1": {
    "id": 10,
    "count": 120,
    "entries": [
      {"from": 0, "to": 55, "kind": "iso", "tiles": 1, "top": 0,
       "desc": "plain grass variants picked at random"},
      {"from": 56, "to": 59, "kind": "iso", "tiles": 2, "top": 0, "desc": "2x2 grass"},
      {"from": 60, "to": 60, "kind": "iso", "tiles": 3, "top": 80,
       "anim": {"num_sprites": 10, "can_reverse": 0, "speed_id": 1},
       "desc": "workshop base image, frames follow at 61..70"},
      {"from": 61, "to": 70, "kind": "sprite", "w": 40, "h": 30, "desc": "workshop smoke frames"},
      {"from": 71, "to": 71, "kind": "opaque", "w": 640, "h": 480, "external": true, "desc": "..."}
    ],
    "evidence": ["src/map/tiles.c:123 image_group(GROUP_TERRAIN_GRASS_1) + (random & 7)"],
    "notes": "anything non-obvious"
  }
}
```

Rules:
* Every offset 0..count-1 must be covered by exactly one entry (contiguous ranges).
* `count` must be >= (largest offset the code or the asset XML can ever use) + 1. Be careful
  with computed offsets (direction*8 + frame, `% n`, lookup tables, climate, orientation
  4 rotations, etc.). If unsure, round up and explain in `notes`.
* `desc` should be concrete enough for an artist (what object, state, direction/frame
  numbering, colour hints such as "red roof", "water", "grass"), because our generator will
  paint from it. For figure animations state the frame/direction formula, e.g.
  "walk: offset = direction(0..7) + 8*frame(0..11); death frames 96..103".
* Sizes: pick sizes that fit how the code uses the image (UI widgets have strict sizes
  dictated by layout code — find them; buildings need the right tile count; figures roughly
  25-45 px tall; terrain is 58x30).
* Also report (in a top-level `"_absolute_ids"` list) any code that uses absolute image ids
  or relies on relationships between groups (e.g. `image_group(A) + 200` reaching into group
  B, `image_id >= 6145`, comparisons of image ids against group starts, etc.).
* Be thorough: grep for every `GROUP_...` name in your scope across `src/` and in the asset
  XML (numeric ids). Don't invent groups that the code never uses; but include unused-but-
  defined groups in your scope with count 1 so the layout has them.
