#!/usr/bin/env python3
"""Builds Log Pose's images and data from the Grand Archive repo.

Run from anywhere:  python3 log-pose/tools/build.py
Reads  ../grand-archive-voyage  (images + JSON) and the portrait uploads,
writes img/*.webp and data.json next to index.html.
Every image is re-encoded, so no photo metadata (EXIF/GPS) survives.
"""
import json, os, random, sys
from collections import Counter
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # log-pose/
REPOS_DIR = os.path.dirname(ROOT)
GA = os.path.join(REPOS_DIR, "grand-archive-voyage")
OUT = os.path.join(ROOT, "img")
UPLOADS = sys.argv[1] if len(sys.argv) > 1 else None
os.makedirs(OUT, exist_ok=True)

def J(name):
    return json.load(open(os.path.join(GA, "data", name + ".json")))

written = set()
def save(src, name, maxpx=720, q=70):
    """Resize + strip metadata. Returns the published path or None."""
    out = f"img/{name}.webp"
    if out in written:
        return out
    if not os.path.exists(src):
        return None
    im = Image.open(src)
    im = ImageOps.exif_transpose(im)
    alpha = im.mode in ("RGBA", "LA", "P") and "transparency" in im.info or im.mode in ("RGBA", "LA")
    im = im.convert("RGBA" if alpha else "RGB")
    im.thumbnail((maxpx, maxpx), Image.LANCZOS)
    im.save(os.path.join(ROOT, out), "WEBP", quality=q, method=6)
    written.add(out)
    return out

def art(i, maxpx=720):
    for d in ("t", "f"):
        p = os.path.join(GA, "assets", "img", d, i + ".webp")
        if os.path.exists(p):
            return save(p, i, maxpx)
    p = os.path.join(GA, "assets", "chars", i + ".webp")
    return save(p, i, maxpx) if os.path.exists(p) else None

media, chars, sh, shelf, tcg = J("media"), J("characters"), J("strawhats"), J("shelf"), J("tcg")
charinfo = {c["name"]: c for c in chars["characters"]}
crewinfo = {c["short"]: c for c in sh["crew"]}

PER = 8  # images per folder (cover + 7)
folders = []

def add_folder(fid, name, series, line, ids, cover=None, extra=None):
    ids = [i for i in ([cover] if cover else []) + ids if i]
    seen, pics = set(), []
    for i in ids:
        if i in seen:
            continue
        seen.add(i)
        p = art(i)
        if p:
            pics.append(p)
        if len(pics) >= PER:
            break
    if not pics:
        return
    f = {"id": fid, "name": name, "series": series, "line": line, "pics": pics}
    if extra:
        f.update(extra)
    folders.append(f)

def char_extra(name):
    c = charinfo.get(name, {})
    s = crewinfo.get(name, {})
    e = {}
    if c.get("word") or s.get("word"):
        e["word"] = c.get("word") or s.get("word")
    lesson = (c.get("changed") or [None])[0] or s.get("lesson")
    if lesson:
        e["lesson"] = lesson
    if s:
        e["bounty"] = s.get("bounty")
        e["tint"] = s.get("tint")
        e["role"] = s.get("role")
        e["dream"] = s.get("dream")
    elif c.get("image", {}).get("color"):
        e["tint"] = c["image"]["color"]
    return e

mchars = {c["home"]: c for c in media["characters"]}
mcrew = {c["name"]: c for c in media["crew"]}
mworld = {c["name"]: c for c in media["worlds"]}

# One Piece first, in crew order, then the rest of his favourites.
OP = [
    ("luffy", "Luffy", "Monkey D. Luffy"), ("zoro", "Zoro", "Roronoa Zoro"),
    ("nami", "Nami", "Nami"), ("usopp", "Usopp", "Usopp"), ("sanji", "Sanji", "Sanji"),
    ("chopper", "Chopper", "Tony Tony Chopper"), ("robin", "Robin", "Nico Robin"),
    ("franky", "Franky", "Franky"), ("brook", "Brook", "Brook"), ("jinbe", "Jinbe", "Jinbe"),
]
for fid, key, full in OP:
    c = mchars.get(key)
    k = mcrew.get(key)
    s = crewinfo.get(key, {})
    ids = []
    if c:
        ids += c["strip"] + c["all"]
    if k:
        ids += k["all"]
    cover = (c or {}).get("portrait") or (k or {}).get("cover") or s.get("art")
    line = (k or {}).get("line") or s.get("role", "")
    add_folder(fid, full, "One Piece", line, [s.get("art")] + ids, cover, char_extra(key))

for key, fid in [("Law", "law"), ("Yamato", "yamato"), ("Hancock", "hancock"), ("Garp", "garp"),
                 ("Kuma", "kuma"), ("Vivi", "vivi"), ("Straw Hats", "strawhats")]:
    k = mcrew[key]
    add_folder(fid, key if key != "Straw Hats" else "The Straw Hat Pirates", "One Piece",
               k["line"], k["all"], k["cover"])

OTHERS = [("Ayanokoji", "Classroom of the Elite"), ("Guts", "Berserk"), ("Subaru", "Re:Zero"),
          ("Violet", "Violet Evergarden"), ("Rudeus", "Mushoku Tensei"), ("All Might", "My Hero Academia")]
for key, series in OTHERS:
    c = mchars[key]
    full = {"Subaru": "Subaru Natsuki", "Violet": "Violet Evergarden"}.get(key, key)
    info = charinfo.get(full) or charinfo.get(key) or {}
    add_folder(key.lower().replace(" ", "-"), full, series, info.get("word", ""),
               c["strip"] + c["all"] + [info.get("image", {}).get("id")], c["portrait"],
               char_extra(full if full in charinfo else key))
jw = charinfo.get("Sung Jinwoo")
if jw:
    add_folder("jinwoo", "Sung Jinwoo", "Solo Leveling", jw.get("word", ""), [jw["image"]["id"]])
for key, fid in [("Rem", "rem"), ("Beatrice", "beatrice"), ("Reze", "reze"), ("Violet Evergarden", None)]:
    if fid:
        w = mworld[key]
        add_folder(fid, key, w["series"], "", w["all"], w["cover"])

# Straw Hat bounty strip
crew = []
for s in sh["crew"]:
    crew.append({"id": s["id"], "name": s["name"], "short": s["short"], "role": s["role"],
                 "bounty": s["bounty"], "tint": s["tint"], "word": s["word"],
                 "img": art(s["art"], 600), "dream": s["dream"]})

binder = []  # replaced by the full Card Vault below

# Watch stats from his shelf
cnt = lambda k: Counter(x.get("status") for x in shelf[k])
anime, manga = cnt("anime"), cnt("manga")
now = [{"t": x["t"], "p": x.get("progress") or x.get("s") or ""} for x in shelf["anime"] if x.get("status") == "watching"]
reading = [x["t"] for x in shelf["manga"] if x.get("status") == "reading"]
stats = {
    "updated": shelf.get("updated"),
    "animeDone": anime.get("completed", 0), "animeNow": anime.get("watching", 0),
    "mangaReading": manga.get("reading", 0), "mangaDone": manga.get("finished", 0),
    "tv": len(shelf["tv"]), "cards": len(tcg["cards"]),
    "watching": now, "reading": reading[:8],
    "top": [t["title"] for t in shelf["top10"]],
}

# Portraits (uploads), metadata stripped
me = {}
if UPLOADS:
    me["face"] = save(os.path.join(UPLOADS, "2ac764a7-image.jpg"), "me-face", 600, 78)
    me["full"] = save(os.path.join(UPLOADS, "b8211d3b-image.jpg"), "me-full", 900, 74)

# ---- Card Vault: every card he owns (official faces, his own DON photos), small + large
vault = []
for c in tcg["cards"]:
    sp = os.path.join(GA, "assets", "tcg", "s", c["id"] + ".webp")
    hp = os.path.join(GA, "assets", "tcg", "hd", c["id"] + ".webp")
    t = save(sp, "tcg-" + c["id"], 300, 70)
    l = save(hp if os.path.exists(hp) else sp, "tcgl-" + c["id"], 680, 78)
    if t:
        vault.append({"no": c["no"], "name": c["name"], "rarity": c.get("rarity"), "kind": c.get("kind"),
                      "colors": c.get("colors") or [], "cost": c.get("cost"), "power": c.get("power"),
                      "counter": c.get("counter"), "attr": c.get("attr"), "types": c.get("types"),
                      "effect": c.get("effect"), "set": c.get("set"), "crew": c.get("crew"), "t": t, "l": l})

# ---- Claude's editions: the four special rarities from the Special Card Lab
LAB = os.path.join(ROOT, "src", "lab")
lab = []
for key, name, sub, chip, move, no in [
    ("his", "Sanji", "Sun · Haki · Black Leg", "Conqueror · 1/1", "Hold it and the Haki charges until the screen cracks.", "0001"),
    ("g4", "Luffy", "Gear 4 · Boundman", "Red Manga", "Peel the corner back to find the full-colour original under the red ink.", "0137"),
    ("g5", "Nika", "The drums of liberation", "Sun God · 0.4%", "Pull it. It's rubber, and it has a heartbeat.", "—"),
    ("zoro", "Zoro", "Three-sword style", "Manga", "Draw on it to ink the pencils yourself.", "0211"),
]:
    p_ = save(os.path.join(LAB, key + ".jpg"), "lab-" + key, 760, 80)
    if p_:
        lab.append({"img": p_, "name": name, "sub": sub, "chip": chip, "move": move, "no": no})

# ---- The Rabbit Hole: case files and their photos
MYS = os.path.join(REPOS_DIR, "Mysteries")
cases = []
credits = {}
cp = os.path.join(ROOT, "src", "cases", "credits.json")
if os.path.exists(cp):
    credits = json.load(open(cp))
for st in json.load(open(os.path.join(MYS, "data", "stories.json")))["stories"]:
    ph = save(os.path.join(ROOT, "src", "cases", st["id"] + ".jpg"), "case-" + st["id"], 800, 72)
    cases.append({"id": st["id"], "no": st["caseNo"], "title": st["title"], "hook": st["hook"], "cat": st["category"],
                  "verdict": st["verdict"], "level": int(st["rabbitHoleLevel"]), "year": st["year"],
                  "where": (st.get("location") or {}).get("name", ""), "mins": st.get("readMinutes"),
                  "img": ph, "credit": credits.get(st["id"])})

# ---- Workshop cover: the R6 plan, rendered from the drawing
plan_img = save(os.path.join(ROOT, "src", "plan-r6.png"), "plan-r6", 900, 80)

# Pictures for the site cards, taken from the sites themselves
REPOS = REPOS_DIR
site_imgs = {}
for key, path, px in [
    ("archive", "grand-archive-voyage/assets/img/ui/share.jpg", 900),
    ("nika", "grand-archive-voyage/assets/img/ui/nika.webp", 320),
    ("story", "grand-archive-voyage/assets/cards/conqueror.webp", 720),
    ("behold", "Behold/icons/icon-512.png", 360),
    ("ilp", "ILP-Production-monthly-report/assets/img/logo-white.png", 300),
    ("betty", "shehansa-study/img/betty.jpg", 640),
    ("archive1", "my-grand-archive/media/luffy_poster.jpg", 900),
    ("watch", "my-grand-archive/media/zoro_poster.jpg", 900),
]:
    p = save(os.path.join(REPOS, path), "site-" + key, px, 74)
    if p:
        site_imgs[key] = p

# The opening wall: One Piece images from the folders, shuffled once per build.
random.seed(7)
pool = [p for f in folders if f["series"] == "One Piece" for p in f["pics"]]
random.shuffle(pool)
wall = pool[:36]

# ---- Pinterest boards (names and pins read from his public boards)
BOARDS = [("one-piece", "One Piece", "https://www.pinterest.com/yohandesilva54/one-piece/"),
          ("re-zero", "Re:Zero", "https://www.pinterest.com/yohandesilva54/re-zero/"),
          ("violet-evergarden", "Violet Evergarden", "https://www.pinterest.com/yohandesilva54/violet-evergarden/"),
          ("smoking-behind-the-supermarket-with-you", "Smoking Behind the Supermarket with You", "https://www.pinterest.com/yohandesilva54/smoking-behind-the-supermarket-with-you/"),
          ("omniscient-readers-viewpoint", "Omniscient Reader's Viewpoint", "https://www.pinterest.com/yohandesilva54/omniscient-readers-viewpoint/")]
boards = []
for slug, name, url in BOARDS:
    pics = [save(os.path.join(ROOT, "src", "pins", f"{slug}-{k}.jpg"), f"pin-{slug}-{k}", 600, 76) for k in range(6)]
    boards.append({"slug": slug, "name": name, "u": url, "pics": [x for x in pics if x]})

data = {"boards": boards, "vault": vault, "lab": lab, "cases": cases, "plan": plan_img, "sites": site_imgs, "folders": folders, "crew": crew, "binder": binder, "stats": stats, "me": me, "wall": wall,
        "finale": sh["finale"]["line"], "total": sh["total"]}
json.dump(data, open(os.path.join(ROOT, "data.json"), "w"), ensure_ascii=False, indent=1)

# App icon: his chosen picture (src/icon.png, 1024 square); PNG for the home screen, WebP for the page
_ic = os.path.join(ROOT, "src", "icon.png")
if os.path.exists(_ic):
    _im = Image.open(_ic).convert("RGB")
    for _px in (180, 512):
        _t = _im.resize((_px, _px), Image.LANCZOS); _t.save(os.path.join(OUT, f"icon-{_px}.png"), optimize=True)
        written.add(f"img/icon-{_px}.png")
    save(_ic, "icon", 256, 86)

# Remove images no longer referenced
for fn in os.listdir(OUT):
    if f"img/{fn}" not in written:
        os.remove(os.path.join(OUT, fn))
size = sum(os.path.getsize(os.path.join(ROOT, p)) for p in written)
print(f"{len(folders)} folders, {len(crew)} crew, {len(binder)} cards, {len(written)} images, {size/1e6:.1f} MB")
for f in folders:
    print(f"  {f['name']:<26} {len(f['pics'])}")

# Compose index.html from the page source with the data inlined
src = os.path.join(ROOT, "src", "page.html")
if os.path.exists(src):
    page = open(src, encoding="utf-8").read()
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(page.replace("__DATA__", blob))
    print("index.html written")
