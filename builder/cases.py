#!/usr/bin/env python3
"""Fetch one hero photo per Rabbit Hole case file (Wikimedia Commons API thumbnails, 960 px)."""
import json, os, re, sys, time, urllib.parse, urllib.request, urllib.error, io
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MYS = os.path.join(os.path.dirname(ROOT), "Mysteries")
UA = {"User-Agent": "LogPoseBuild/1.0 (personal dashboard; https://github.com/gomayoha)"}
stories = json.load(open(os.path.join(MYS, "data", "stories.json")))["stories"]
def fname(src):
    return urllib.parse.unquote(src.rsplit("/", 1)[-1])
names = {s["id"]: fname(s["hero"]["src"]) for s in stories}
titles = "|".join("File:" + n for n in set(names.values()))
q = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|extmetadata",
                            "iiurlwidth": 800, "titles": titles, "redirects": 1, "maxlag": 5})
def get(url):
    for wait in (20, 45, 90, 150, 240, 300):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print("wait", wait, url[:80], e, flush=True); time.sleep(wait)
    return None
res = json.loads(get("https://commons.wikimedia.org/w/api.php?" + q))
info = {}
norm = {n["from"]: n["to"] for n in res["query"].get("normalized", [])}
for p in res["query"]["pages"].values():
    if "imageinfo" in p:
        ii = p["imageinfo"][0]; md = ii.get("extmetadata", {})
        info[p["title"]] = {"url": ii.get("thumburl") or ii["url"],
                            "artist": re.sub("<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip(),
                            "licence": md.get("LicenseShortName", {}).get("value", "")}
out = {}
for s in stories:
    t = "File:" + names[s["id"]]; t = norm.get(t, t)
    if t not in info: print("missing", s["id"], t); continue
    p = os.path.join(ROOT, "src", "cases", s["id"] + ".jpg")
    if not os.path.exists(p):
        raw = get(info[t]["url"])
        if raw is None:
            print("gave up", s["id"]); continue
        im = Image.open(io.BytesIO(raw)).convert("RGB"); im.thumbnail((960, 960), Image.LANCZOS)
        im.save(p, "JPEG", quality=82)
        time.sleep(12)
    out[s["id"]] = {"artist": info[t]["artist"][:80], "licence": info[t]["licence"], "file": names[s["id"]]}
json.dump(out, open(os.path.join(ROOT, "src", "cases", "credits.json"), "w"), indent=1, ensure_ascii=False)
print(len(out), "photos")
