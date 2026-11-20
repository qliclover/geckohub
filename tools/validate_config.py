#!/usr/bin/env python3
"""Checks config/v1 the same way the app does, before you push.

    python3 tools/validate_config.py

Exit code 0 = safe to publish. Any problem is printed and the exit code is 1.
The app runs the same checks and ignores a file that fails, keeping its last good copy.
"""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "config" / "v1"
FILES = ["species.json", "careguide.json", "copy.json", "flags.json", "winter-guide.json"]
# Species the app shipped with: a download may add species but never drop these.
SHIPPED_SPECIES = {"crested", "leopard", "gargoyle", "fat_tailed", "day_gecko", "tokay", "leachianus"}
# The only lines copy.json may change (the keys bundled in the app).
COPY_KEYS = {"careGuide.disclaimer", "careGuide.targetsNote", "schedule.empty", "schedule.footer", "records.empty"}
FLAGS = {"careGuideLive", "wikipediaSummaries", "iNaturalistPhotos", "winterGuide"}
# Builds from before Winter care refuse a flags.json that names winterGuide and keep their built-in switches.

problems = []
def bad(msg): problems.append(msg)

def load(name):
    try:
        return json.loads((ROOT / name).read_text(encoding="utf-8"))
    except Exception as e:
        bad(f"{name}: not valid JSON ({e})")
        return None

def rng(v, lo, hi):
    return isinstance(v, list) and len(v) == 2 and all(isinstance(x, int) for x in v) and lo <= v[0] <= v[1] <= hi

manifest = load("manifest.json")
if manifest:
    if not isinstance(manifest.get("version"), int): bad("manifest.json: version must be a whole number")
    for f in FILES:
        v = manifest.get("files", {}).get(f, {}).get("version")
        if not isinstance(v, int) or v < 1: bad(f"manifest.json: {f} needs a version of 1 or more")

sp = load("species.json")
if sp:
    species = sp.get("species", [])
    ids = [s.get("id") for s in species]
    if len(ids) != len(set(ids)): bad("species.json: duplicate species id")
    missing = SHIPPED_SPECIES - set(ids)
    if missing: bad(f"species.json: these species can't be removed: {sorted(missing)}")
    for s in species:
        sid = s.get("id", "?")
        for key in ["id", "name", "latin", "env", "scene", "active", "uvb"]:
            if not isinstance(s.get(key), str) or not s.get(key): bad(f"species.json/{sid}: '{key}' is missing")
        if not rng(s.get("hotSpotF"), 50, 115): bad(f"species.json/{sid}: hotSpotF must be [low, high] °F between 50 and 115")
        if not rng(s.get("ambientF"), 50, 110): bad(f"species.json/{sid}: ambientF must be [low, high] °F between 50 and 110")
        if not rng(s.get("humidity"), 0, 100): bad(f"species.json/{sid}: humidity must be [low, high] % between 0 and 100")
        if not (isinstance(s.get("feedEveryDays"), int) and 1 <= s["feedEveryDays"] <= 60): bad(f"species.json/{sid}: feedEveryDays must be 1–60")
        if not s.get("diet"): bad(f"species.json/{sid}: diet can't be empty")
        if not isinstance(s.get("mist"), bool): bad(f"species.json/{sid}: mist must be true or false")
        if not isinstance(s.get("shedAreas"), list): bad(f"species.json/{sid}: shedAreas must be a list")

cg = load("careguide.json")
if cg:
    if not cg.get("wikipedia"): bad("careguide.json: wikipedia can't be empty")
    urls = [cg.get("allCareSheets", "")]
    for sid, links in cg.get("careSheets", {}).items():
        for l in links:
            if not l.get("title") or not l.get("site"): bad(f"careguide.json/{sid}: every link needs a title and a site")
            urls.append(l.get("url", ""))
    if "winter" in cg: bad("careguide.json: the winter links moved to winter-guide.json; remove the 'winter' block")
    for u in urls:
        if not str(u).startswith("https://"): bad(f"careguide.json: link must start with https:// ({u})")

cp = load("copy.json")
if cp:
    for key, langs in cp.get("strings", {}).items():
        if key not in COPY_KEYS: bad(f"copy.json: '{key}' isn't a line the app lets you change")
        if not langs.get("en"): bad(f"copy.json/{key}: needs English ('en')")
        for lang, text in langs.items():
            if len(text) >= 600: bad(f"copy.json/{key}/{lang}: too long")

wg = load("winter-guide.json")
if wg:
    def en(t, where):
        if not isinstance(t, dict) or not t.get("en"): bad(f"winter-guide.json/{where}: needs English ('en')")
    page = wg.get("page", {})
    for k in ["title", "intro", "footer"]: en(page.get(k), f"page/{k}")
    import re
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(page.get("checked", ""))): bad("winter-guide.json/page/checked: a date like 2026-11-20")
    sources = wg.get("sources", {})
    for sid, src in sources.items():
        if not src.get("name") or not src.get("title"): bad(f"winter-guide.json/sources/{sid}: needs a name and a title")
        if not str(src.get("url", "")).startswith("https://"): bad(f"winter-guide.json/sources/{sid}: link must start with https://")
    def point(p, where):
        en(p.get("lead"), f"{where}/lead")
        for s_ in p.get("sources", []):
            if s_ not in sources: bad(f"winter-guide.json/{where}: source '{s_}' isn't listed under sources")
    topics = wg.get("topics", [])
    if not topics: bad("winter-guide.json: needs at least one topic")
    for t in topics:
        tid = t.get("id", "?")
        en(t.get("title"), f"{tid}/title")
        if not t.get("points"): bad(f"winter-guide.json/{tid}: needs at least one point")
        for i, p in enumerate(t.get("points", [])):
            if "disagree" in p:
                d = p["disagree"]
                en(d.get("title"), f"{tid}/{i}/disagree")
                if not d.get("sides"): bad(f"winter-guide.json/{tid}/{i}: a disagreement needs its sides")
                for j, side in enumerate(d.get("sides", [])):
                    en(side.get("label"), f"{tid}/{i}/side{j}/label"); en(side.get("text"), f"{tid}/{i}/side{j}/text")
                    for s_ in side.get("sources", []):
                        if s_ not in sources: bad(f"winter-guide.json/{tid}/{i}: source '{s_}' isn't listed under sources")
            elif "lead" in p:
                point(p, f"{tid}/{i}")
    for sid, block in wg.get("species", {}).items():
        en(block.get("title"), f"species/{sid}/title")
        if not block.get("points"): bad(f"winter-guide.json/species/{sid}: needs at least one point")
        for i, p in enumerate(block.get("points", [])): point(p, f"species/{sid}/{i}")

fl = load("flags.json")
if fl is not None:
    for k, v in fl.items():
        if k not in FLAGS: bad(f"flags.json: unknown switch '{k}' (switches can only turn existing features off)")
        if not isinstance(v, bool): bad(f"flags.json: '{k}' must be true or false")

if problems:
    print("Not safe to publish:")
    for p in problems: print("  -", p)
    sys.exit(1)
print("All config files pass. Bump the file's version in manifest.json, then commit and push.")
