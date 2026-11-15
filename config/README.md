# Gecko Hub content (remote config)

The app reads these files from https://qliclover.github.io/geckohub/config/v1/ at launch, in the background.
New content takes effect the **next** time the app opens. Offline, or if a file fails its checks, the app keeps
its last good copy (or the one built into the app).

| File | What it holds | Changes allowed |
|---|---|---|
| `species.json` | Species, temperature and humidity targets, feeding interval, diet, misting | Edit values, add species. Never remove a species or rename an `id`. |
| `careguide.json` | Wikipedia article per species, care sheet links, the "more care sheets" link | Edit or add links (https only). |
| `copy.json` | A short list of lines in English, Simplified and Traditional Chinese | Reword existing keys only. New keys need an app update. |
| `flags.json` | Switches for existing features (`careGuideLive`, `wikipediaSummaries`, `iNaturalistPhotos`) | Turn an existing feature off or back on. Never for unreleased features. |

## How to change something

1. Edit the file in `config/v1/` (on github.com you can use the pencil icon).
2. In `manifest.json`, add 1 to that file's `version` (e.g. `"species.json": { "version": 2 }`).
   Without this the app won't download it.
3. Check it: `python3 tools/validate_config.py` (needs a copy of the repo on your Mac).
4. Commit and push. GitHub Pages updates in about a minute; phones pick it up next launch.

To undo: put the old content back and add 1 to the version again (versions only go up).

## App Store rules

Content only: no code, and nothing that changes what the app does beyond the values above.
Don't use this to switch on features that weren't in the reviewed version (guideline 2.3.1 / 2.5.2).
Changes to species targets only affect new animals' starting routines and the care guide;
existing animals keep their saved targets and routines.
