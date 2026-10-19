# 3D map conversion playbook (instructions to myself)
Trigger: Max says e.g. "make Beginners Ground 3D". Goal: same standard as Bomb Town (v196). iPhone only. Short replies, one step at a time.

## 0. Golden rule - NEVER BREAK 2D
- The 2D art for a map must stay pixel-identical when 3D is off/failed. v184-v195 broke this (props were skipped in 2D and the shadow alpha lowered even when 3D was not running).
- Only ever skip 2D painting via `P3`, and `P3` is only true when `want3d(d)` (map has `v3d`, not `v3off`, not `v3fail`, THREE loaded). Never test `d.v3d` directly in paint code.
- Anything that changes how 2D paints must use `P3 ? new : original`.
- `repaintArt()` re-bakes the 2D pictures when 3D is toggled/fails. Call it after any code that flips `v3fail`/`v3off`.
- BEFORE EVERY PUSH: `python3 tests/parity2d.py` must print "OK - 2D art identical to baseline". Add the new map's id to the baseline only if it is deterministic (no Math.random in its paint code - seed it with dtRng or add to NONDET). Never run `--save` to hide a failure; only when 2D art was meant to change.
- Also take one screenshot of the map with 3D maps: off.

## 1. Setup per map
1. Add `v3d: true` to the map entry in MAPS (the renderer then draws it; 2D canvas stays as HUD overlay).
2. Find the map's coordinate offset (Bomb Town: `DT_OY=390`, world z = draft y + O; RECTS y include O; paint code uses `yq = q.y - O`). Note `WORLD`, `GS`.
3. Classify every RECTS/BLD entry: building wall, interior wall, fence, barricade, door, solid prop, low cover. Heights: walls ~ full, fences ~60, cover ~ 30-40, barricades short (shorter barriers were requested).
4. Make a list of tall/raised 2D props painted in `ground`/`bld` (cars, trees, benches, crates, hedges, furniture, toys, litter). Each gets (a) a 3D builder and (b) an `if (!P3) { ...2D paint... }` wrapper. Floor-level detail (cracks, stains, grass, paths) stays 2D, only baked shadows lower to 0.14 under P3 (`P3 ? 0.14 : 0.36`).
5. Interior furniture: record into `DT3` (via `frec` + overridden bed/table/chair/sofa under P3), build with `v3furn`.

## 2. 3D pieces to write (reuse the globals; parametrise any Bomb Town hard-coded numbers)
- `v3walls()` groups: brick, plaster, wood, leaf, metal, roof, dark from RECTS/BLD/shape tables. Boundary wall, roofs, house shells.
- Props: `v3prop` (match rects by size), `v3deco` (hard-coded Bomb Town coordinates - give it per-map data), litter scatter with seeded rng + rejection vs RECTS, `CARC` car table.
- Ground: `v3gdet('a'|'b')` + `v3gmat(map)` detail overlay; textures via `v3tex(kind)` (brick, plaster, wood, roof, leaf, metal, skin, cloth, denim, grit) with bump maps (`v3bump`, `V3BS`).
- Lighting: first-person maps are always night (moonlit); sun DirectionalLight with 2048 shadow map, ortho +-460 (scale to map), texel-snapped target; per-frame shadows (`V.rs`) with fallback when `V.ft` is slow.
- Sky/fog, lights (LIGHTS list), doors, windows, bats, pickups, perks, chests, coins, pets, zombies, players, guns are global and need nothing per map.
- Floor LOD / zombie extras LOD if the map is big.

## 3. Trimmed three.js limits
No SpotLight, no BackSide/RepeatWrapping constants (use numbers: RepeatWrapping=1000, BackSide=1, PCFShadowMap=1), no `Color.multiplyScalar`. Supported: MeshLambertMaterial (+bumpMap), onBeforeCompile, CylinderGeometry, Group, CanvasTexture, InstancedMesh, shadows. Avoid name collisions inside the IIFE (e.g. `V.pk` is barricade planks, `rec` is a function).

## 4. Gameplay rules in 3D
- 3D maps are capped at a steady 30 fps (loop gate `v3Active() ? 31 : 14` ms).
- Headshots are the crits: first-person bullet carries `h0, vh, vy`; hit above 78% of `zHeight(z)` = x2 damage, gold hit marker. The two-thumb "centred" crit is top-down only.
- Looking up/down, gun follows the view, no aim assist, auto-fire when crosshair is on a zombie (firing method still open with Max).

## 5. Test loop (harness in /tmp/zt, not in repo; recreate if gone)
- Copy index.html with `window.__ev = function(c){return eval(c)}` injected before the final `})();`; serve with `(setsid nohup python3 -m http.server 8765 &)` in the SAME command as the test; Playwright + swiftshader (software GL ~3-7 fps, so real performance is unmeasurable - ask Max for the FPS counter).
- Check: spawn at each corner, inside every building, top/bottom look, night + muzzle flash, zombies/pets/pickups, shadows, no console errors.
- Syntax check: extract largest `<script>` and `node --check`.
- Run `tests/parity2d.py` (see rule 0) and a 3D-off screenshot.

## 6. Ship
Bump `VERSION`, commit with the Co-Authored-By and Claude-Session trailers, `git push -q origin HEAD:main`, reply: what changed first, then link + version at the bottom. Notion logging on `log`/End Convo.
