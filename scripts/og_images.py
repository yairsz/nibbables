#!/usr/bin/env python3
"""Generate 1200x630 social/Pinterest share images (static/og/<slug>.png) from each
built page's own <title>. Text comes only from the page title; no new claims.
Run after build.py, then build again so pages pick up og:image. Needs Pillow."""
import re, html, pathlib
from PIL import Image, ImageDraw, ImageFont
ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE, OUT = ROOT / "site", ROOT / "static" / "og"
OUT.mkdir(parents=True, exist_ok=True)
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
INK, ACC, MUT, BG, BG2 = "#1d2433", "#9a4a12", "#5b6476", "#fafbfc", "#fbefe4"
def slug(p):
    rel = p.parent.relative_to(SITE).as_posix()
    return "home" if rel == "." else rel.replace("/", "-")
def wrap(d, text, font, w):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=font) <= w: cur = t
        else: lines.append(cur); cur = word
    return lines + [cur]
n = 0
for p in sorted(SITE.rglob("index.html")):
    if p.parent.relative_to(SITE).parts[:1] in (("nibbables",), ("static",)): continue
    m = re.search(r"<title>(.*?)</title>", p.read_text(), re.S)
    if not m: continue
    title = html.unescape(m.group(1)).replace(" | Nibbables", "").strip()
    im = Image.new("RGB", (1200, 630), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1200, 14], fill=ACC); d.rectangle([0, 560, 1200, 630], fill=BG2)
    lf = ImageFont.truetype(B, 44); d.text((70, 60), "Nibb", font=lf, fill=INK)
    d.text((70 + d.textlength("Nibb", font=lf), 60), "ables", font=lf, fill=ACC)
    for size in (68, 60, 52, 46, 40):
        f = ImageFont.truetype(B, size); lines = wrap(d, title, f, 1060)
        if len(lines) * size * 1.22 <= 380: break
    y = 150 + (380 - len(lines) * size * 1.22) / 2
    for ln in lines: d.text((70, y), ln, font=f, fill=INK); y += size * 1.22
    d.text((70, 578), "Dog chew claims quoted from each brand's own page  ·  nibbables.com",
           font=ImageFont.truetype(R, 26), fill=MUT)
    im.save(OUT / f"{slug(p)}.png", optimize=True); n += 1
print(f"og images: {n}")
