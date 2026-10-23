#!/usr/bin/env python3
"""Nibbables static site builder (stdlib only).
Usage: python3 build.py   -> writes ./site/
Data:  data/products.json   (one record per product; every claim is a verbatim quote from the brand's own page)
       data/categories.json (category pages)
       data/guides/*.json   (optional extra pages added by the nightly routine)
The build REFUSES to run if a product is missing a field or a source, or if the generated
pages contain forbidden wording ("safe"/"safer"/"safest") or a price ("$12.99")."""
import json, html, shutil, datetime, re, os, sys
from pathlib import Path
from urllib.parse import urlparse
from ytembed import embed as yt_embed, video_ld
YT_CHANNEL = "https://www.youtube.com/@Nibbables"

ROOT = Path(__file__).parent
OUT = ROOT / "site"
CFG = json.loads((ROOT / "site.json").read_text())
NS = "Not stated, check with them"
REQUIRED = ["brand", "product", "category", "source_url", "ingredients", "made_in", "sourced_from",
            "rawhide_free", "size_guidance", "supervision", "sizes", "last_checked"]
QUOTED = ["ingredients", "made_in", "sourced_from", "rawhide_free", "size_guidance", "supervision"]
AMAZON_DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."
AMAZON_URL = re.compile(r"https://www\.amazon\.com/dp/[A-Z0-9]{10}\?tag=" + re.escape(CFG.get("amazon_tag", "nibbables-20")))
FORBIDDEN = [(re.compile(r"\bsafe(r|st|ly)?\b", re.I), "the word 'safe' (never call a chew safe)"),
             (re.compile(r"[$€£]\s?\d"), "a price")]

e = lambda s: html.escape(str(s), quote=True)
PREFIX = ""
def set_page(path):
    global PREFIX
    PREFIX = "../" * len([p for p in path.strip("/").split("/") if p])
def U(target):
    return (PREFIX + target.lstrip("/")) or "./"
def base_url():
    return os.environ.get("SITE_BASE_URL", CFG["base_url"]).rstrip("/")
def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def q(s):
    """Render a brand quote, or the not-stated marker."""
    if s == NS:
        return f'<span class="ns">{NS}</span>'
    return "<q>" + "</q> · <q>".join(e(x) for x in s.split(" · ")) + "</q>"

def validate(products, cats):
    slugs = {c["slug"] for c in cats}
    ids = set()
    for p in products:
        name = f"{p.get('brand')} / {p.get('product')}"
        for k in REQUIRED:
            assert k in p and p[k] not in (None, "", []), f"{name}: missing field '{k}'"
        for k in QUOTED:
            assert isinstance(p[k], str) and p[k].strip(), f"{name}: '{k}' must be a quote or '{NS}'"
        u = urlparse(p["source_url"])
        assert u.scheme == "https" and u.netloc, f"{name}: bad source_url"
        assert p["category"] in slugs, f"{name}: unknown category {p['category']}"
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", p["last_checked"]), f"{name}: bad last_checked"
        assert not p.get("affiliate_url") or CFG.get("affiliates_live"), f"{name}: affiliate_url set but affiliates_live is off"
        if p.get("affiliate_url"):
            # Only exact Amazon /dp/<ASIN>?tag=<our tag> links, matching the recorded ASIN (see research/amazon-matches.md).
            assert AMAZON_URL.fullmatch(p["affiliate_url"]), f"{name}: affiliate_url must be https://www.amazon.com/dp/<ASIN>?tag={CFG.get('amazon_tag')}"
            assert p.get("amazon_asin") and f"/dp/{p['amazon_asin']}?" in p["affiliate_url"], f"{name}: amazon_asin missing or doesn't match affiliate_url"
        p["id"] = slugify(p["brand"] + " " + p["product"])[:80]
        assert p["id"] not in ids, f"duplicate product {p['id']}"
        ids.add(p["id"])

CAT_LABEL = {}
def ga_tag():
    gid = CFG.get("ga_measurement_id", "").strip()
    if not gid: return ""
    assert re.fullmatch(r"G-[A-Z0-9]+", gid), f"bad ga_measurement_id {gid}"
    return f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{gid}');
</script>"""

def page(title, desc, path, body, jsonld=None):
    url = base_url() + path
    lds = [x for x in (jsonld, video_ld(path)) if x]
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x)}</script>' for x in lds)
    year = datetime.date.today().year
    nav = "".join(f'<a href="{U("/" + s + "/")}">{e(n)}</a>' for s, n in CAT_LABEL.items())
    return f"""<!doctype html>
<html lang="en"><head>{ga_tag()}
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{e(url)}">
<link rel="stylesheet" href="{U('/static/style.css')}">{ld}
</head><body>
<header class="site"><div class="wrap"><a class="logo" href="{U('/')}">Nibb<span>ables</span></a>
<nav>{nav}<a href="{U('/compare/')}">Compare all</a><a href="{U('/about/')}">How we verify</a></nav></div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">© {year} {e(CFG['site_name'])}. We quote what each brand says on its own website and link the source. We don't test, rate or review products. Brand claims (including "Made in USA") are the brand's, not ours. Always supervise chewing, pick an appropriate size, and ask your vet. {AMAZON_DISCLOSURE} <a href="{U('/about/')}">How we verify &amp; affiliate disclosure</a>. <a href="{YT_CHANNEL}" rel="noopener" target="_blank">Nibbables on YouTube</a>.</div></footer>
</body></html>"""

SAFETY = """<aside class="note"><strong>Before you give any chew:</strong> supervise your dog while it chews, choose a size and hardness that suits your dog (follow the brand's size guidance), take away small or broken pieces, keep fresh water available, and ask your vet if a chew is right for your dog, especially for puppies, seniors, dogs with dental work or dogs on special diets. Nibbables does not rate safety. Each card shows what the brand itself says.</aside>"""

def has_aff(p):
    return bool(p.get("affiliate_url") and CFG.get("affiliates_live"))

def affiliate_slot(p):
    # Amazon Associates (tag in site.json "amazon_tag"). Only set affiliate_url for an exact Amazon match of the
    # same brand, product and size wording, recorded in research/amazon-matches.md. Never show Amazon prices,
    # ratings or review counts.
    if has_aff(p):
        return f'<a class="aff" href="{e(p["affiliate_url"])}" rel="sponsored nofollow noopener" target="_blank">Check on Amazon</a>'
    return f"<!-- AFFILIATE_SLOT:{e(p['id'])} (no exact Amazon match) -->"

def aff_disclosure(ps):
    return f'<p class="disclosure meta">{AMAZON_DISCLOSURE} <a href="{U("/about/")}">Affiliate disclosure</a>.</p>' if any(has_aff(p) for p in ps) else ""

def card(p):
    sizes = "".join(f"<li>{e(s)}</li>" for s in p["sizes"])
    note = f"<dt>Note</dt><dd>{e(p['note'])}</dd>" if p.get("note") else ""
    return f"""<article class="card" id="{e(p['id'])}">
<span class="badge">{e(CAT_LABEL[p['category']])}</span><h3>{e(p['brand'])}: {e(p['product'])}</h3>
<dl><dt>Ingredients (as listed)</dt><dd>{q(p['ingredients'])}</dd>
<dt>Made-in claim</dt><dd>{q(p['made_in'])}</dd>
<dt>Sourced-from claim</dt><dd>{q(p['sourced_from'])}</dd>
<dt>Rawhide-free?</dt><dd>{q(p['rawhide_free'])}</dd>
<dt>Size / dog guidance</dt><dd>{q(p['size_guidance'])}</dd>
<dt>Supervision note</dt><dd>{q(p['supervision'])}</dd>
<dt>Options on the page</dt><dd><ul class="items">{sizes}</ul></dd>{note}
<dt>Source</dt><dd><a href="{e(p['source_url'])}" rel="nofollow noopener" target="_blank">Brand's product page</a> · checked {e(p['last_checked'])}</dd></dl>
{affiliate_slot(p)}</article>"""

def category_page(c, products):
    set_page(f"/{c['slug']}/")
    if c["slug"] == "rawhide-free":
        ps = [p for p in products if p["category"] == "rawhide-free"] + \
             [p for p in products if p["category"] != "rawhide-free" and p["rawhide_free"] != NS]
    else:
        ps = [p for p in products if p["category"] == c["slug"]]
    assert ps, f"category {c['slug']} is empty"
    toc = "".join(f'<li><a href="#{e(p["id"])}">{e(p["brand"])}: {e(p["product"])}</a></li>' for p in ps)
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › {e(c['name'])}</p>
<h1>{e(c['h1'])}</h1><p class="lead">{e(c['intro'])}</p>
<p class="meta">{len(ps)} products · every claim is quoted from the brand's own page and linked · no prices (they change; check the brand) · <a href="{U('/compare/')}">compare all in one table</a></p>
{SAFETY}
{aff_disclosure(ps)}
<details class="toc"><summary>Products on this page</summary><ul>{toc}</ul></details>
{''.join(card(p) for p in ps)}"""
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": c["h1"],
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": f"{p['brand']} {p['product']}"} for i, p in enumerate(ps)]}
    return page(c["title"], c["meta"], f"/{c['slug']}/", body, ld)

def mentions_usa(p):
    t = (p["made_in"] + " " + p["sourced_from"]) if True else ""
    return bool(re.search(r"\bUSA\b|\bU\.S\.|United States|\bUS\b|American", t))

def compare(products):
    set_page("/compare/")
    opts = "".join(f'<option value="{e(s)}">{e(n)}</option>' for s, n in CAT_LABEL.items())
    def cell(s): return '<span class="ns">Not stated</span>' if s == NS else e(s)
    rows = ""
    for p in products:
        rows += (f'<tr data-cat="{e(p["category"])}" data-made="{int(p["made_in"] != NS)}" data-rh="{int(p["rawhide_free"] != NS)}" '
                 f'data-usa="{int(mentions_usa(p))}" data-s="{e((p["brand"] + " " + p["product"] + " " + p["ingredients"]).lower())}">'
                 f'<td><a href="{U("/" + p["category"] + "/")}#{e(p["id"])}">{e(p["brand"])}</a><br><span class="meta">{e(p["product"])}</span></td>'
                 f'<td>{e(CAT_LABEL[p["category"]])}</td><td>{cell(p["ingredients"])}</td><td>{cell(p["made_in"])}</td>'
                 f'<td>{cell(p["sourced_from"])}</td><td>{cell(p["rawhide_free"])}</td>'
                 f'<td><a href="{e(p["source_url"])}" rel="nofollow noopener" target="_blank">Source</a><br><span class="meta">{e(p["last_checked"])}</span></td></tr>')
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › Compare</p>
<h1>Compare long-lasting dog chews</h1>
<p class="lead">All {len(products)} products in one table. Every cell is the brand's own wording from its product page. "Not stated" means we couldn't find it on that page, so check with the brand.</p>
{SAFETY}
{yt_embed('/compare/', YT_CHANNEL, 'Nibbables')}
<div class="filters"><select id="fc" aria-label="Chew type"><option value="">All chew types</option>{opts}</select>
<label><input type="checkbox" id="fm"> Made-in claim stated</label>
<label><input type="checkbox" id="fu"> Claim mentions USA</label>
<label><input type="checkbox" id="fr"> Says rawhide-free</label>
<input id="fq" type="search" placeholder="Search brand or ingredient…" aria-label="Search"></div>
<p class="meta" id="cnt"></p>
<div class="tablewrap"><table class="cmp"><thead><tr><th>Brand / product</th><th>Type</th><th>Ingredients (as listed)</th><th>Made-in claim</th><th>Sourced-from claim</th><th>Rawhide-free (as stated)</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="meta">"Claim mentions USA" only means the brand's made-in or sourcing wording mentions the USA or the U.S. It may be partial, for example "Made in USA with globally sourced ingredients". Read the exact wording.</p>
<script>
(function(){{var c=document.getElementById('fc'),m=document.getElementById('fm'),u=document.getElementById('fu'),r=document.getElementById('fr'),q=document.getElementById('fq'),n=document.getElementById('cnt');
function f(){{var k=0,qv=q.value.toLowerCase().trim();document.querySelectorAll('table.cmp tbody tr').forEach(function(t){{
var ok=(!c.value||t.dataset.cat===c.value)&&(!m.checked||t.dataset.made==='1')&&(!u.checked||t.dataset.usa==='1')&&(!r.checked||t.dataset.rh==='1')&&(!qv||t.dataset.s.indexOf(qv)>-1);
t.style.display=ok?'':'none';if(ok)k++;}});n.textContent=k+' of {len(products)} products shown';}}
[c,m,u,r].forEach(function(x){{x.addEventListener('change',f)}});q.addEventListener('input',f);f();}})();
</script>"""
    return page("Compare dog chews: ingredients, made-in & sourcing claims side by side | Nibbables",
                "Side-by-side table of bully sticks, yak chews, beef cheek rolls, rawhide-free chews and antlers, with each brand's ingredient, made-in and sourcing claims quoted and linked.",
                "/compare/", body)

def home(products, cats, guides):
    set_page("/")
    def count(s):
        if s == "rawhide-free": return sum(1 for p in products if p["category"] == s or p["rawhide_free"] != NS)
        return sum(1 for p in products if p["category"] == s)
    cl = "".join(f'<a href="{U("/" + c["slug"] + "/")}">{e(c["name"])}<br><span class="meta">{count(c["slug"])} products</span></a>' for c in cats)
    gl = ""
    if guides:
        gl = "<h2>Guides</h2><ul>" + "".join(f'<li><a href="{U("/" + g["slug"] + "/")}">{e(g["h1"])}</a></li>' for g in guides) + "</ul>"
    brands = sorted({p["brand"] for p in products}, key=str.lower)
    body = f"""<h1>Long-lasting dog chews, compared by what the brands actually say</h1>
<p class="lead">{e(CFG['tagline'])} For {len(products)} bully sticks, yak cheese chews, beef cheek rolls, rawhide-free chews and antlers from {len(brands)} brands, we quote each brand's own product page: the ingredient list, where it says the chew is made and sourced, its size guidance and its supervision note. Every card links its source and shows the date we checked it.</p>
<h2>Browse by chew type</h2><div class="cities">{cl}<a href="{U('/compare/')}">Compare all<br><span class="meta">filterable table</span></a></div>
{SAFETY}
{gl}
<h2>What we don't do</h2>
<ul><li>We don't rate or vouch for the safety of any chew. Only you and your vet can judge what suits your dog.</li>
<li>We don't show prices, because they change. Check the brand's page.</li>
<li>We don't publish reviews or star ratings.</li>
<li>"Made in USA" and similar wording is the brand's claim, shown in quotes.</li></ul>
<h2>Brands covered</h2><p>{e(', '.join(brands))}</p>
<p><a href="{U('/about/')}">How we verify &amp; how this site makes money →</a></p>"""
    return page(f"{CFG['site_name']}: long-lasting dog chews compared (ingredients, made-in claims, sizes)",
                "Bully sticks, yak cheese chews, beef cheek rolls, rawhide-free chews and antlers compared using each brand's own ingredient, made-in and sourcing claims, quoted and linked.", "/", body)

def guide_page(g, products):
    set_page(f"/{g['slug']}/")
    for k in ("slug", "title", "meta", "h1", "intro", "sections", "sources", "last_checked"):
        assert g.get(k), f"guide {g.get('slug')}: missing {k}"
    byid = {p["id"]: p for p in products}
    for pid in g.get("product_ids", []):
        assert pid in byid, f"guide {g['slug']} references unknown product {pid}"
    secs = "".join(f"<h2>{e(s['h'])}</h2><p>{e(s['p'])}</p>" for s in g["sections"])
    srcs = "".join(f'<li><a href="{e(s["url"])}" rel="nofollow noopener" target="_blank">{e(s["label"])}</a></li>' for s in g["sources"])
    cards = aff_disclosure([byid[pid] for pid in g.get("product_ids", [])]) + "".join(card(byid[pid]) for pid in g.get("product_ids", []))
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › {e(g['h1'])}</p><h1>{e(g['h1'])}</h1><p class="lead">{e(g['intro'])}</p>
<p class="meta">Last checked {e(g['last_checked'])}</p>{SAFETY}{secs}{cards}<h2>Sources</h2><ul>{srcs}</ul>"""
    return page(g["title"], g["meta"], f"/{g['slug']}/", body)

def about():
    set_page("/about/")
    body = f"""<h1>About Nibbables: how we verify, and our affiliate disclosure</h1>
<h2>How we verify</h2>
<ul>
<li>Every product comes from the brand's <strong>own</strong> website, never a reseller or review site. Each card links the exact product page we read and shows the date we checked it.</li>
<li>Claims are <strong>quoted word for word</strong> in quotation marks: ingredients, "made in" and "sourced from" wording, rawhide-free statements, size guidance and supervision notes. We don't reword them into our own claims.</li>
<li>If the page doesn't state something, the card says <span class="ns">{NS}</span>. We never guess or fill gaps from other sources.</li>
<li>"Rawhide-free" is shown only when the brand's page says so explicitly ("rawhide-free", "made without rawhide" and similar). Many other chews here may also contain no rawhide. Their pages just don't say it in those words.</li>
<li>"Made in USA", "Sourced and made in the USA", "Country of Origin" and similar statements are <strong>the brand's claims</strong>. We haven't independently verified where any product is made or sourced. Where a page contradicts itself, the card notes it.</li>
<li>We show no prices, because they change. We show no reviews, star ratings or safety ratings.</li>
<li>Our build checks every listing for a source and every required field, and refuses to publish a listing that is missing one.</li>
</ul>
<h2>Chewing and your dog</h2>
{SAFETY}
<p>Nibbables is an information directory, not veterinary advice. No chew is right for every dog. Supervise chewing, choose an appropriate size, and talk to your vet, especially for puppies, seniors, dogs with dental problems or dogs on special diets.</p>
<h2>Affiliate disclosure</h2>
<p>Nibbables is free to use. <strong>Some links on this site are Amazon affiliate links</strong>: the "Check on Amazon" buttons on product cards. {AMAZON_DISCLOSURE} If you buy through one of those links, Nibbables earns a commission at no extra cost to you.</p>
<p>Affiliate links don't affect which products are listed or what we say about them. Every card quotes the brand's own product page, and we add an Amazon link only when we can find the same product (same brand, product name and size) on Amazon. Products without an exact match simply have no Amazon link. A brand can't pay to change what its card says. We don't show Amazon prices, ratings or review counts. The "Brand's product page" links are ordinary links and don't earn anything.</p>
<h2>Analytics</h2>
<p>This site uses Google Analytics to collect aggregate traffic statistics, such as page views and how visitors found us. It doesn't collect your name or email, though Google may set cookies to tell visits apart.</p>
<h2>Corrections</h2>
<p>Brands update their pages. If a card is out of date, let us know and we'll re-check it against the brand's page and update the date.</p>"""
    return page("About Nibbables: how we verify & affiliate disclosure",
                "How Nibbables quotes each dog chew brand's own claims, what we don't do (no safety ratings, prices or reviews), and our affiliate disclosure.", "/about/", body)

def main():
    products = json.loads((ROOT / "data/products.json").read_text())
    cats = json.loads((ROOT / "data/categories.json").read_text())
    guides = [json.loads(p.read_text()) for p in sorted((ROOT / "data/guides").glob("*.json"))] if (ROOT / "data/guides").exists() else []
    for c in cats: CAT_LABEL[c["slug"]] = c["name"]
    validate(products, cats)
    products.sort(key=lambda p: (p["brand"].lower(), p["product"].lower()))
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")
    pages = {"/": home(products, cats, guides), "/compare/": compare(products), "/about/": about()}
    for c in cats: pages[f"/{c['slug']}/"] = category_page(c, products)
    for g in guides:
        assert f"/{g['slug']}/" not in pages, f"guide slug clash {g['slug']}"
        pages[f"/{g['slug']}/"] = guide_page(g, products)
    global PREFIX
    PREFIX = urlparse(base_url()).path.rstrip("/") + "/"
    notfound = page("Page not found | Nibbables", "Page not found.", "/404.html", f'<h1>Page not found</h1><p><a href="{U("/")}">Go to the home page</a></p>')
    problems = []
    for path, h in list(pages.items()) + [("/404.html", notfound)]:
        text = re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h))
        text = text.replace("SafeFit", "")  # brand product name, not a claim
        # Tags (and so href values like ...?tag=nibbables-20) are stripped before this scan, so affiliate URLs are
        # never flagged; visible text is still checked for prices exactly as before.
        for rx, what in FORBIDDEN:
            for m in rx.finditer(text):
                problems.append(f"{path}: contains {what}: ...{text[max(0, m.start()-40):m.end()+40]}...")
        if "amazon.com/dp/" in h:
            for u in re.findall(r'href="(https://www\.amazon\.com/[^"]+)"', h):
                if not AMAZON_URL.fullmatch(html.unescape(u)): problems.append(f"{path}: bad Amazon link {u}")
            top = h.split('class="aff"', 1)[0]
            if AMAZON_DISCLOSURE not in re.sub(r"<[^>]+>", "", top):
                problems.append(f"{path}: has Amazon links but no disclosure above the first one")
    if problems:
        print("\n".join(problems)); sys.exit("Build refused: forbidden wording found.")
    for path, h in pages.items():
        d = OUT / path.strip("/"); d.mkdir(parents=True, exist_ok=True); (d / "index.html").write_text(h)
    (OUT / "404.html").write_text(notfound)
    base = base_url()
    latest = max(p["last_checked"] for p in products)
    urls = "".join(f"<url><loc>{base}{p}</loc><lastmod>{latest}</lastmod></url>" for p in pages)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    if CFG.get("indexnow_key"):  # IndexNow (Bing/Yandex) key file must sit at the site root
        (OUT / f"{CFG['indexnow_key']}.txt").write_text(CFG["indexnow_key"])
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    if CFG.get("cname"):
        (OUT / "CNAME").write_text(CFG["cname"].strip() + "\n")
    print(f"Built {len(pages)} pages, {len(products)} products -> {OUT}")

if __name__ == "__main__":
    main()
