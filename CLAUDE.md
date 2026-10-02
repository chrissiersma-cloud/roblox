# Project notes for Claude

Roblox game (Wrangler Camp hub, lasso, zoo, areas: Forest, Dark Woods, Frost Peak). Models are built from
Parts by Python scripts in `tools/` and written to `.rbxm` with `tools/rbxm-writer`. READMEs in `models/` are
written in Dutch; reply to the user in the language they write in.

## Animal part budgets (set by the user)

| Rarity | Parts |
|---|---|
| Secret | about 800 |
| Mythic | about 500 |
| Legendary and lower | keep the quality they have now (roughly 100 to 300); do not inflate them |

Mythic and Secret animals get real detail for those parts (feathers, scales, armour, fur layers, props) and
cool effects that fit the animal, plus their own idle actions in `tools/animal-models/AnimalFX.lua`. Use the
built-in Roblox particle textures (fire, fire sparks, explosion core/shockwave/implosion, forcefield
glow/vortex, sparkles, smoke) so nothing has to be uploaded.

## Conventions

- Animals face -Z, +X is their right side, y = 0 is the ground.
- Invisible effect holders (transparency 1) count toward the hitbox size, so keep them within the animal's
  normal bounds.
- `AnimalFX.lua` is embedded in every animal `.rbxm`. After changing it, rebuild all of them:
  `build_dark_woods.py`, `build_horses.py`, `build_mountain.py`, `build_mounts.py` and `build_phoenix.py`
  (each with `--rbxm`, see the READMEs for the output paths).
- Check Luau with the luau-analyze/luau-compile tools before committing script changes.
- Develop on the branch the session names, commit with clear messages, and only open pull requests when asked.
