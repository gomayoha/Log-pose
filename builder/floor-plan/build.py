#!/usr/bin/env python3
"""Builds the Building 05 · Layout R6 artifact page from the R6 drawing source.
Inputs: src/svg_R6_illus.svg (from Drive: ILP NEW FLOOR PLAN/.layout-source), page.html.
Output: index.html (sheets/*.webp are published beside it)."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
svg = open(os.path.join(HERE, "src", "svg_R6_illus.svg"), encoding="utf-8").read()

# The material route: the first polyline (starts at the north main door, x 21.6 y -2.2)
svg = svg.replace('<polyline points="21.600,-2.200', '<polyline id="flow" points="21.600,-2.200', 1)
assert 'id="flow"' in svg
# Numbered step badges: orange circles r=0.7, each followed by its number
n = 0
def tag(m):
    global n
    n += 1
    return m.group(0).replace("<circle ", f'<circle class="badge" data-step="{n}" ', 1)
svg = re.sub(r'<circle cx="[\d.]+" cy="[-\d.]+" r="0\.7" fill="#DD4A16"[^>]*>', tag, svg)
assert n == 13, n
# badge numbers: text right after a badge circle
svg = re.sub(r'(<circle class="badge" data-step="(\d+)"[^>]*>\s*)<text ', r'\1<text class="badge-n" data-step="\2" ', svg)
svg = svg.replace('<svg class="plan"', '<svg class="plan" id="plan" role="img" aria-label="Building 05 layout R6: machines, storage, offices and the 13-step material route"', 1)

page = open(os.path.join(HERE, "page.html"), encoding="utf-8").read()
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(page.replace("__PLAN__", svg))
print("index.html", os.path.getsize(os.path.join(HERE, "index.html")))
