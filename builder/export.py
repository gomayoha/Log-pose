#!/usr/bin/env python3
"""Turn the built page into the GitHub Pages web app (../log-pose-app).
Wraps index.html in a full document, adds the app manifest, the offline service worker,
the floor plan page and copies the images. Run after tools/build.py."""
import os, re, shutil, json, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(os.path.dirname(ROOT), "log-pose-app")
FLOOR = os.path.join(os.path.dirname(ROOT), "floor-r6")
os.makedirs(APP, exist_ok=True)

page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
cut = page.index('<header class="bar"')
head, body = page[:cut], page[cut:]
head = head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
head = head.replace('<meta name="apple-mobile-web-app-capable" content="yes">',
    '<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="mobile-web-app-capable" content="yes">\n<link rel="manifest" href="manifest.webmanifest">')
doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       '<meta name="description" content="Yohan\'s Log Pose: every site, board, card and case file in one place.">\n'
       + head + '</head>\n<body>\n' + body +
       '\n<script>if("serviceWorker" in navigator){addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}))}</script>\n</body>\n</html>\n')
open(os.path.join(APP, "index.html"), "w", encoding="utf-8").write(doc)

# images
dst = os.path.join(APP, "img")
if os.path.isdir(dst): shutil.rmtree(dst)
shutil.copytree(os.path.join(ROOT, "img"), dst)

# floor plan page (built in ../floor-r6), with a way back to the app
fp = open(os.path.join(FLOOR, "index.html"), encoding="utf-8").read()
fp = fp.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
back = ('<div style="max-width:1280px;margin:0 auto;padding:14px max(16px,env(safe-area-inset-left,0px)) 0"><a href="../" '
        'style="display:inline-block;font:600 13px \'IBM Plex Mono\',ui-monospace,monospace;color:#fff;border:1px solid rgba(255,255,255,.35);'
        'padding:7px 12px;text-decoration:none">← Log Pose</a></div>\n')
cutf = fp.index('<header class="tb">')
fdoc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<meta name="theme-color" content="#16324f">\n<link rel="apple-touch-icon" href="../img/icon-180.png">\n'
        '<style>body{margin:0}[hidden]{display:none!important}:root{padding-top:env(safe-area-inset-top,0px)}</style>\n'
        + fp[:cutf] + '</head>\n<body>\n' + fp[cutf:].replace('<header class="tb">', '<header class="tb">' + back, 1) + '\n</body>\n</html>\n')
fdir = os.path.join(APP, "floor-plan")
if os.path.isdir(fdir): shutil.rmtree(fdir)
os.makedirs(fdir)
open(os.path.join(fdir, "index.html"), "w", encoding="utf-8").write(fdoc)
shutil.copytree(os.path.join(FLOOR, "sheets"), os.path.join(fdir, "sheets"))

# app manifest
json.dump({
  "name": "Yohan's Log Pose", "short_name": "Log Pose", "start_url": "./", "scope": "./", "display": "standalone",
  "background_color": "#000000", "theme_color": "#000000", "orientation": "any",
  "icons": [{"src": "img/icon-180.png", "sizes": "180x180", "type": "image/png"},
            {"src": "img/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}],
}, open(os.path.join(APP, "manifest.webmanifest"), "w"), indent=1)

# service worker: pages network-first, images cache-first
ver = hashlib.sha1(doc.encode()).hexdigest()[:10]
open(os.path.join(APP, "sw.js"), "w").write(f'''// Log Pose offline cache. The version changes on every build.
const V = "logpose-{ver}";
const CORE = ["./", "index.html", "manifest.webmanifest", "img/icon-180.png", "img/icon-512.png", "img/icon.webp"];
self.addEventListener("install", e => {{ e.waitUntil(caches.open(V).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); }});
self.addEventListener("activate", e => {{ e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())); }});
self.addEventListener("fetch", e => {{
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return;
  if (e.request.mode === "navigate" || u.pathname.endsWith(".html") || u.pathname.endsWith("/")) {{
    e.respondWith(fetch(e.request).then(r => {{ const c = r.clone(); caches.open(V).then(x => x.put(e.request, c)); return r; }}).catch(() => caches.match(e.request).then(r => r || caches.match("index.html"))));
    return;
  }}
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(res => {{ const c = res.clone(); caches.open(V).then(x => x.put(e.request, c)); return res; }})));
}});
''')
open(os.path.join(APP, ".nojekyll"), "w").write("")
n = sum(len(f) for _, _, f in os.walk(APP))
print("app written:", APP, n, "files")
