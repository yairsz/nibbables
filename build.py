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
from ytembed import embed as yt_embed, video_ld, VIDEOS
import privacy
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

META = {}  # path -> (title, description); feeds llms.txt
# path -> YYYY-MM-DD the page's content was last checked/changed. Filled in main() from the data
# (latest last_checked of what the page shows), never "today". Feeds WebPage dateModified, visible dates and sitemap lastmod.
MODIFIED = {}
ABOUT_UPDATED = "2026-10-24"     # bump when /about/ text changes
PRIVACY_UPDATED = "2026-10-23"   # matches privacy.EFFECTIVE

def cat_products(c, products):
    if c["slug"] == "rawhide-free":
        return [p for p in products if p["category"] == "rawhide-free"] + \
               [p for p in products if p["category"] != "rawhide-free" and p["rawhide_free"] != NS]
    return [p for p in products if p["category"] == c["slug"]]

def org_ld():
    return {"@type": "Organization", "@id": base_url() + "/#org", "name": CFG["site_name"], "url": base_url() + "/",
            "sameAs": [YT_CHANNEL]}

def webpage_ld(title, desc, path):
    if path not in MODIFIED:
        return None
    return {"@context": "https://schema.org", "@type": "AboutPage" if path == "/about/" else "WebPage",
            "@id": base_url() + path, "url": base_url() + path, "name": title, "description": desc,
            "dateModified": MODIFIED[path], "inLanguage": "en-US",
            "isPartOf": {"@type": "WebSite", "@id": base_url() + "/#website", "name": CFG["site_name"],
                         "url": base_url() + "/", "publisher": org_ld()},
            "publisher": {"@id": base_url() + "/#org"}}

# Hand-written complete meta descriptions for pages whose long description would otherwise be cut mid-sentence.
# Reworded only from the page's own description; no new facts. Keep <= 158 chars.
META_DESC = {'/rawhide-free/': "Dog chews whose brand says they're rawhide-free or made without rawhide, including Earth Animal No-Hide, quoted from each brand's page.", '/compare/': "Bully sticks, yak chews, beef cheek rolls, rawhide-free chews and antlers side by side, with each brand's ingredient and made-in claims quoted.", '/yak-cheese-chews/': 'Yak cheese dog chews from Mighty Paw, Pupford, Pawstruck, Raw Paws and Best Bully Sticks, with ingredients and origin claims quoted from each brand.', '/antlers/': 'Elk and deer antler chews from GREAT DOG, Redbarn, Mighty Paw, Nature Gnaws and Best Bully Sticks, with sourcing and size guidance quoted from each brand.', '/': "Bully sticks, yak cheese chews, beef cheek rolls, rawhide-free chews and antlers compared by each brand's own ingredient, made-in and sourcing claims.", '/bully-sticks/': 'Bully sticks from Campfire Treats, GREAT DOG, Best Bully Sticks, Redbarn, Jack&Pup, Mighty Paw and more, with ingredients, made-in claims and sizes quoted.'}

def fit_meta(title, desc, suffix=" | Nibbables"):
    """Keep SERP snippets readable: titles <= 70 chars (keep the brand suffix unless longer; drop the site-name suffix if needed),
    descriptions <= 158 chars (cut at the last full sentence, else the last word + ellipsis).
    Only shortens; never adds wording."""
    if suffix and title.endswith(suffix) and len(title) > 70:
        title = title[: -len(suffix)]
    if len(desc) > 158:
        cut = desc[:158]
        ends = [cut.rfind(p) for p in (". ", "? ", "! ")]
        end = max(ends)
        if end >= 90:
            desc = cut[: end + 1]
        else:
            desc = cut[: cut.rfind(" ")].rstrip(",;:-–—(") + "…"
    return title, desc

# Entity hub links (added 2026-10-25, from Dixon Jones / Advanced Web Ranking on entity hubs): each chew type has
# ONE authority page. The first plain-text mention of that chew type in a body paragraph links to its hub, unless
# the page is the hub or already links to it. Never touches quotes, links, headings, cards or tables.
HUB_TERMS = [("bully-sticks", r"(?<!Best )(?<!&quot; Beef )\bbully sticks?\b"), ("yak-cheese-chews", r"\b(?:yak|Himalayan)(?: cheese)? chews?\b"),
             ("beef-cheek-rolls", r"\bbeef cheek rolls?\b"), ("rawhide-free", r"\brawhide-free(?: chews?)?\b"),
             ("antlers", r"\b(?:(?:elk|deer) )?antler chews?\b")]
_SKIP_TAGS = ("a", "q", "blockquote", "cite", "code", "h1", "h2", "h3")

def link_hubs(body, path):
    for slug, pat in HUB_TERMS:
        hub = "/" + slug + "/"
        if path == hub or f'href="{U(hub)}"' in body: continue
        rx = re.compile(pat, re.I)
        def para(m):
            attrs = m.group(1) or ""
            if 'class="disclosure' in attrs: return m.group(0)
            parts = re.split(r"(<[^>]+>)", m.group(2)); depth = 0; done = False; inq = 0
            for i, t in enumerate(parts):
                if t.startswith("<"):
                    tag = re.match(r"</?([a-zA-Z0-9]+)", t)
                    if tag and tag.group(1).lower() in _SKIP_TAGS:
                        depth += -1 if t.startswith("</") else 1
                    continue
                # never link inside a quotation (“…”), which may span tags
                if depth == 0 and not done:
                    for mm in rx.finditer(t):
                        before = t[:mm.start()]
                        if (inq + before.count("“") - before.count("”")) > 0: continue
                        parts[i] = before + f'<a href="{U(hub)}">{mm.group(0)}</a>' + t[mm.end():]; done = True; break
                inq += t.count("“") - t.count("”")
            return f"<p{attrs}>" + "".join(parts) + "</p>"
        new = re.sub(r"<p(\s[^>]*)?>(.*?)</p>", para, body, flags=re.S)
        # keep only the first inserted link for this hub
        first = new.find(f'<a href="{U(hub)}">')
        if first != -1:
            head, tail = new[:first + 1], new[first + 1:]
            tail = re.sub(r'<a href="' + re.escape(U(hub)) + r'">([^<]*)</a>', r"\1", tail)
            body = head + tail
    return body

def page(title, desc, path, body, jsonld=None):
    body = link_hubs(body, path)
    desc = META_DESC.get(path, desc)
    title, desc = fit_meta(title, desc)
    url = base_url() + path
    META[path] = (title, desc)
    lds = [x for x in ((jsonld if isinstance(jsonld, list) else [jsonld]) + [video_ld(path), webpage_ld(title, desc, path)]) if x]
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x)}</script>' for x in lds)
    year = datetime.date.today().year
    nav = "".join(f'<a href="{U("/" + s + "/")}">{e(n)}</a>' for s, n in CAT_LABEL.items())
    return f"""<!doctype html>
<html lang="en"><head>{ga_tag()}
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="msvalidate.01" content="45CDFD465C8824EB2040D1A77F7E20CB" />
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
<footer><div class="wrap">© {year} {e(CFG['site_name'])}. We quote what each brand says on its own website and link the source. We don't test, rate or review products. Brand claims (including "Made in USA") are the brand's, not ours. Always supervise chewing, pick an appropriate size, and ask your vet. {AMAZON_DISCLOSURE} <a href="{U('/about/')}">How we verify &amp; affiliate disclosure</a>. <a href="{U('/privacy/')}">Privacy policy</a>. <a href="{YT_CHANNEL}" rel="noopener" target="_blank">Nibbables on YouTube</a>.</div></footer>
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

GUIDES = []  # filled in main(); used for contextual internal links (added 2026-10-24)

def related_guides_block(cat_slug, cat_name):
    """Contextual links from a chew-type page to guides tagged with that category (guide JSON "categories")."""
    gs = [g for g in GUIDES if cat_slug in g.get("categories", [])]
    if not gs: return ""
    return f'<h2>Guides about {e(cat_name.lower())}</h2><ul>' + "".join(
        f'<li><a href="{U("/" + g["slug"] + "/")}">{e(g["h1"])}</a></li>' for g in gs) + "</ul>"

def guide_related(g):
    """Guide footer: links to its chew-type page(s) and the other guides."""
    cl = [f'<a href="{U("/" + c + "/")}">all {e(CAT_LABEL[c].lower())} we list</a>' for c in g.get("categories", []) if c in CAT_LABEL]
    others = [x for x in GUIDES if x["slug"] != g["slug"]]
    out = "<h2>Related on Nibbables</h2><ul>"
    if cl: out += "<li>Browse " + " and ".join(cl) + ", with each brand's own ingredient and made-in wording.</li>"
    out += f'<li><a href="{U("/compare/")}">Compare all chews in one table</a></li>'
    out += "".join(f'<li><a href="{U("/" + x["slug"] + "/")}">{e(x["h1"])}</a></li>' for x in others)
    return out + "</ul>"

# Fan-out "Quick answers" on chew-type pages (added 2026-10-24). AI answers split a query into sub-questions
# (where is it made, which brands, rawhide-free?). Every answer is COUNTED from data/products.json, so it can't
# say anything the cards don't. No judgments, no safety wording.
PLACES = [("USA", r"\bUSA\b|\bU\.S\.|United States|\bUS\b|(?<!South )American"), ("Canada", r"Canada"),
          ("Brazil", r"Brazil"), ("Argentina", r"Argentina"), ("Paraguay", r"Paraguay"),
          ("Colombia", r"Colombi|Columbia"),  # one brand page writes "Columbia" for its country of origin
          ("Peru", r"Peru"), ("Mexico", r"Mexico"), ("South America", r"South America"), ("the Americas", r"The Americas"),
          ("Turkey", r"Turkey"), ("New Zealand", r"New Zealand"), ("Europe", r"Europe"), ("India", r"India"),
          ("Nepal", r"Nepal"), ("the Himalayas", r"Himalaya")]
FAQ_NOUN = {"antlers": "antler chews"}
# Wording that names a place but isn't about where the chew is made or sourced (e.g. a recipe's origin).
NOT_A_PLACE = re.compile(r"recipe that originates in [^.·]*", re.I)

def cat_faq(c, ps):
    noun = FAQ_NOUN.get(c["slug"], c["name"].lower())
    n = len(ps); last = max(p["last_checked"] for p in ps)
    stated = sum(1 for p in ps if p["made_in"] != NS)
    counts = []
    for place, rx in PLACES:
        k = sum(1 for p in ps if re.search(rx, NOT_A_PLACE.sub("", p["made_in"] + " " + p["sourced_from"])))
        if k: counts.append((k, place))
    counts.sort(key=lambda x: -x[0])
    places = ", ".join(f"{pl} ({k})" for k, pl in counts)
    qa = []
    qa.append((f"Where are {noun} made or sourced?",
        (f"All {n} {noun} product pages we list state where the chew is made. " if stated == n else
         f"{stated} of the {n} {noun} product pages we list state where the chew is made; the rest don't say. ")
        + (f"Places named in the brands' own made-in or sourcing wording, with the number of products: {places}. "
           "Some pages name several possible countries, so the counts can add up to more than the number of products. " if counts else "")
        + f"These are the brands' claims, not ours; each card below quotes the exact wording. Last checked {last}."))
    usa = [p for p in ps if mentions_usa(p)]
    if usa:
        qa.append((f"Which {noun} say they're made or sourced in the USA?",
            f"{len(usa)} of {n}: " + "; ".join(f"{p['brand']} {p['product']}" for p in usa)
            + ". The wording differs (for example sourced in the USA vs made in the USA), so read the quote on each card."))
    brands = {}
    for p in ps: brands[p["brand"]] = brands.get(p["brand"], 0) + 1
    qa.append((f"Which brands' {noun} are listed here?",
        f"{n} products from {len(brands)} brands: " + ", ".join(f"{b} ({k})" for b, k in brands.items())
        + ". Nibbables doesn't rank or rate them; each card links the brand's own product page."))
    if c["slug"] != "rawhide-free":
        rh = [p for p in ps if p["rawhide_free"] != NS]
        qa.append((f"Do brands say their {noun} are rawhide-free?",
            (f"{len(rh)} of {n} product pages literally say rawhide-free or made without rawhide: "
             + "; ".join(f"{p['brand']} {p['product']}" for p in rh) + ". " if rh else
             f"None of the {n} product pages we list use the words rawhide-free or made without rawhide. ")
            + ("The others don't say either way, which doesn't mean they contain rawhide; check with the brand." if rh else
               "That doesn't mean they contain rawhide; the pages just don't say. Check with the brand.")))
    html_ = '<section class="faq"><h2>Quick answers</h2>' + "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in qa) + "</section>"
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}
    return html_, ld

CATS = []  # filled in main()

def sibling_hubs_block(c, products):
    """Hub-to-hub links (entity hubs, 2026-10-25): every chew-type page links in-body to the other chew-type pages,
    with product counts computed from data/products.json."""
    items = [f'<li><a href="{U("/" + o["slug"] + "/")}">{e(o["name"])}</a> ({len(cat_products(o, products))} products)</li>'
             for o in CATS if o["slug"] != c["slug"]]
    return "<h2>Other chew types we list</h2><ul>" + "".join(items) + "</ul>" if items else ""

def category_page(c, products):
    set_page(f"/{c['slug']}/")
    ps = cat_products(c, products)
    assert ps, f"category {c['slug']} is empty"
    faq_html, faq_ld = cat_faq(c, ps)
    toc = "".join(f'<li><a href="#{e(p["id"])}">{e(p["brand"])}: {e(p["product"])}</a></li>' for p in ps)
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › {e(c['name'])}</p>
<h1>{e(c['h1'])}</h1><p class="lead">{e(c['intro'])}</p>
<p class="meta">{len(ps)} products · every claim is quoted from the brand's own page and linked · no prices (they change; check the brand) · page updated {e(MODIFIED.get(f"/{c['slug']}/", ""))} · <a href="{U('/compare/')}">compare all in one table</a></p>
{SAFETY}
{aff_disclosure(ps)}
<details class="toc"><summary>Products on this page</summary><ul>{toc}</ul></details>
{faq_html}
{yt_embed(f"/{c['slug']}/", YT_CHANNEL, 'Nibbables')}
{related_guides_block(c['slug'], c['name'])}
{sibling_hubs_block(c, products)}
{''.join(card(p) for p in ps)}"""
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": c["h1"],
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": f"{p['brand']} {p['product']}"} for i, p in enumerate(ps)]}
    return page(c["title"], c["meta"], f"/{c['slug']}/", body, [ld, faq_ld])

def mentions_usa(p):
    t = (p["made_in"] + " " + p["sourced_from"]) if True else ""
    return bool(re.search(r"\bUSA\b|\bU\.S\.|United States|\bUS\b|(?<!South )American", t))  # "South American cattle" is not USA (fixed 2026-10-24)

def compare_summary(products):
    """Answer-first summary (added 2026-10-24): counts computed from data/products.json only, no judgments."""
    rows, tot = "", {"n": 0, "made": 0, "usa": 0, "rh": 0}
    for slug, name in CAT_LABEL.items():
        ps = [p for p in products if p["category"] == slug]
        if not ps: continue
        n, b = len(ps), len({p["brand"] for p in ps})
        made = sum(1 for p in ps if p["made_in"] != NS); usa = sum(1 for p in ps if mentions_usa(p)); rh = sum(1 for p in ps if p["rawhide_free"] != NS)
        for k, v in (("n", n), ("made", made), ("usa", usa), ("rh", rh)): tot[k] += v
        rows += (f'<tr><td><a href="{U("/" + slug + "/")}">{e(name)}</a></td><td>{n}</td><td>{b}</td>'
                 f'<td>{made} of {n}</td><td>{usa} of {n}</td><td>{rh} of {n}</td></tr>')
    brands = len({p["brand"] for p in products})
    dates = sorted(p["last_checked"] for p in products)
    lead = (f"The short version: this page lists {tot['n']} long-lasting dog chews from {brands} brands. "
            f"{tot['made']} of the {tot['n']} product pages state where the chew is made, {tot['usa']} have made-in or sourcing wording that mentions the USA, "
            f"and {tot['rh']} literally say rawhide-free (or no rawhide). The rest don't say, so ask the brand. "
            + (f"Product pages were last checked on {dates[0]}. " if dates[0] == dates[-1] else f"Product pages were last checked between {dates[0]} and {dates[-1]}. ") + f"Nibbables doesn't rank chews or rate their safety.")
    return (f'<p>{e(lead)}</p><h2>At a glance: what the brand pages state, by chew type</h2>'
            f'<div class="tablewrap"><table class="cmp"><caption>Counts of products whose own page states each item. Computed from the full table below.</caption>'
            f'<thead><tr><th>Chew type</th><th>Products</th><th>Brands</th><th>Made-in claim stated</th><th>Made-in or sourcing claim mentions USA</th><th>Says rawhide-free</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')

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
{compare_summary(products)}
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
<p class="meta">Product pages last checked {e(MODIFIED.get('/', ''))}.</p>
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
    secs = "".join(f"<h2>{e(s['h'])}</h2>" + "".join(f"<p>{e(x)}</p>" for x in (s['p'] if isinstance(s['p'], list) else [s['p']])) for s in g["sections"])
    tbl = guide_table(g.get("table"))
    faq = g.get("faq") or []
    faq_html = "".join(f'<h2>{e(f["q"])}</h2><p>{e(f["a"])}</p>' for f in faq)  # question-style H2s + FAQPage JSON-LD
    srcs = "".join(f'<li><a href="{e(s["url"])}" rel="nofollow noopener" target="_blank">{e(s["label"])}</a></li>' for s in g["sources"])
    cards = aff_disclosure([byid[pid] for pid in g.get("product_ids", [])]) + "".join(card(byid[pid]) for pid in g.get("product_ids", []))
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › {e(g['h1'])}</p><h1>{e(g['h1'])}</h1><p class="lead">{e(g['intro'])}</p>
<p class="meta">Last checked {e(g['last_checked'])}{(" · page updated " + e(MODIFIED[f"/{g['slug']}/"])) if MODIFIED.get(f"/{g['slug']}/", g['last_checked']) != g['last_checked'] else ""}</p>{SAFETY}{tbl}{yt_embed(f"/{g['slug']}/", YT_CHANNEL, 'Nibbables')}{faq_html}{secs}{cards}<h2>Sources</h2><ul>{srcs}</ul>{guide_related(g)}"""
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]} if faq else None
    return page(g["title"], g["meta"], f"/{g['slug']}/", body, ld)

def guide_table(t):
    """Optional guide table: {"h", "caption", "head": [...], "rows": [{"cells": [...], "snapshot": path}]}.
    A cell is plain text (our neutral label, e.g. a brand name or "Not stated") or {"q": "verbatim quote"};
    quote cells are rendered in <q> and checked against the row's snapshot by scripts/verify_quotes.py."""
    if not t: return ""
    def cell(c):
        if isinstance(c, dict): return q(c["q"])
        return '<span class="ns">Not stated</span>' if c == "Not stated" else e(c)
    head = "".join(f"<th>{e(h)}</th>" for h in t["head"])
    rows = "".join("<tr>" + "".join(f"<td>{cell(c)}</td>" for c in r["cells"]) + "</tr>" for r in t["rows"])
    cap = f"<caption>{e(t['caption'])}</caption>" if t.get("caption") else ""
    h = f"<h2>{e(t['h'])}</h2>" if t.get("h") else ""
    return f'{h}<div class="tablewrap"><table class="cmp">{cap}<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


def about(products, cats, guides):
    set_page("/about/")
    brands = {p["brand"] for p in products}
    dates = sorted(p["last_checked"] for p in products)
    fields = ("ingredients", "made_in", "sourced_from", "rawhide_free", "size_guidance", "supervision")
    nns = sum(1 for p in products for k in fields if str(p.get(k) or NS).strip().startswith(NS))
    namz = sum(1 for p in products if has_aff(p))
    nums = f"""<h2>By the numbers</h2>
<ul>
<li>{len(products)} products from {len(brands)} brands, in {len(cats)} chew-type pages, plus {len(guides)} guides and a <a href="{U('/compare/')}">compare table</a>.</li>
<li>Each product cites 1 brand product page ({len({p['source_url'] for p in products})} distinct pages in total). Product pages were last checked {("on " + e(dates[0])) if dates[0] == dates[-1] else ("between " + e(dates[0]) + " and " + e(dates[-1]))}.</li>
<li>{nns} product fields say <span class="ns">{e(NS)}</span> because the brand's page doesn't state them. We don't fill those in with guesses.</li>
<li>{namz} of {len(products)} products have a "Check on Amazon" link, added only where we found the exact same product on Amazon.</li>
</ul>
<p class="meta">These counts are computed from the site's data each time it's built. This page was last updated {e(ABOUT_UPDATED)}.</p>"""
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
<p>This site uses Google Analytics to collect aggregate traffic statistics, such as page views and how visitors found us. It doesn't collect your name or email, though Google may set cookies to tell visits apart. Details are in our <a href="{U('/privacy/')}">privacy policy</a>.</p>
<h2>Corrections</h2>
<p>Brands update their pages. If a card is out of date, let us know and we'll re-check it against the brand's page and update the date.</p>""" + nums
    return page("About Nibbables: how we verify & affiliate disclosure",
                "How Nibbables quotes each dog chew brand's own claims, what we don't do (no safety ratings, prices or reviews), and our affiliate disclosure.", "/about/", body)

def privacy_page():
    set_page("/privacy/")
    vids = [(VIDEOS[k].get("heading", k).split(" (")[0], U(k)) for k in sorted(VIDEOS)]
    tag = e(CFG.get("amazon_tag", ""))
    aff = f"""<h2>Amazon affiliate links</h2>
<p>Nibbables is a participant in the Amazon Services LLC Associates Program, an affiliate advertising program designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.com. {AMAZON_DISCLOSURE}</p>
<ul>
<li>The "Check on Amazon" buttons on product cards are affiliate links to amazon.com that include our Associates tag (<code>{tag}</code>). They're the only affiliate links on the site. "Brand's product page" links are ordinary links.</li>
<li>Nibbables doesn't load any Amazon scripts, images or widgets, and our pages don't set Amazon cookies. Nothing is sent to Amazon unless you click one of those links.</li>
<li>When you click one, you leave Nibbables for amazon.com. Amazon may set or read cookies on your device to record that you came from our link and to credit qualifying purchases, as described in the <a href="https://www.amazon.com/gp/help/customer/display.html?nodeId=GX7NJQ4ZB8MHFRNJ" rel="noopener" target="_blank">Amazon.com Privacy Notice</a> (which links to Amazon's Cookies Notice).</li>
<li>Amazon gives us aggregate reports, such as the number of clicks and which items were ordered, so we can be paid. Those reports don't tell us who you are.</li>
</ul>"""
    body = privacy.body(CFG["site_name"], "nibbables.com", CFG.get("ga_measurement_id", "").strip(), vids, aff,
                        "The compare page has a chew-type menu, checkboxes and a search box for narrowing the table.")
    return page("Privacy policy | Nibbables",
                "What Nibbables collects (Google Analytics, click-to-play YouTube videos, GitHub Pages hosting logs), how its Amazon affiliate links work, and how to opt out.",
                "/privacy/", body)

def check_links(out):
    """Fail the build if any internal href/src in the generated site points at a file that doesn't exist."""
    import posixpath
    from urllib.parse import unquote
    sub = urlparse(base_url()).path.rstrip("/")
    bad = []
    for f in out.rglob("*.html"):
        r = str(f.parent.relative_to(out)); rel_dir = "/" + ("" if r == "." else r)
        for u in re.findall(r'(?:href|src)="([^"]+)"', f.read_text()):
            u = html.unescape(u)
            if re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", u, re.I): continue
            path = unquote(u.split("#")[0].split("?")[0])
            if not path: continue
            if path.startswith("/"):
                if sub and path.startswith(sub + "/"): path = path[len(sub):]
                tgt = posixpath.normpath(path)
            else:
                tgt = posixpath.normpath(posixpath.join(rel_dir, path))
            t = out / tgt.lstrip("/")
            if not (t.is_file() or (t / "index.html").is_file()):
                bad.append(f"{f.relative_to(out)} -> {u}")
    if bad:
        sys.exit("Build refused: broken internal links:\n" + "\n".join(bad))

LLMS_SUMMARY = (CFG["tagline"] + " A directory of long-lasting dog chews (bully sticks, yak cheese chews, beef cheek rolls, "
                "rawhide-free chews and antlers) that quotes each brand's own product page.")
LLMS_NOTES = ["Each product card quotes the brand's own page word for word (ingredients, made-in and sourcing wording, size "
              "guidance, supervision notes), links that page and shows the date it was checked. Made-in and sourcing statements "
              f'are the brands\' claims, not independently verified. Missing facts are marked "{NS}". Nibbables shows no prices, '
              "reviews, star ratings or safety ratings, and it is not veterinary advice. Some product cards have Amazon "
              "affiliate links; see the About page for the disclosure."]
LLMS_SECTIONS = [("Chew types", lambda p: p.strip("/") in CAT_LABEL),
                 ("Guides", lambda p: p not in ("/", "/compare/", "/about/", "/privacy/") and p.strip("/") not in CAT_LABEL),
                 ("Compare, about and privacy", lambda p: p in ("/", "/compare/", "/about/", "/privacy/"))]

# Search and AI-answer crawlers we explicitly welcome (one robots.txt group, RFC 9309).
# The catch-all group below allows everyone else too; this list just makes intent explicit.
ALLOWED_BOTS = ["Googlebot", "Bingbot", "Applebot", "DuckDuckBot", "DuckAssistBot", "OAI-SearchBot", "ChatGPT-User",
                "PerplexityBot", "Perplexity-User", "Claude-SearchBot", "Claude-User", "ClaudeBot", "YandexBot",
                "SeznamBot", "Yeti", "MojeekBot", "GPTBot", "Google-Extended", "Applebot-Extended",
                "Amazonbot", "meta-externalagent", "CCBot"]
def robots_txt(base):
    group = "".join(f"User-agent: {b}\n" for b in ALLOWED_BOTS)
    return (f"# {CFG['site_name']}: search engines and AI answer engines are welcome.\n"
            f"{group}Allow: /\n\nUser-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n")

def llms_txt(base, pages):
    """/llms.txt (llmstxt.org format) built only from the site's own page titles and meta descriptions."""
    def item(path):
        t, d = META[path]
        return f"- [{t}]({base}{path}): {d}"
    out = [f"# {CFG['site_name']}", "", f"> {LLMS_SUMMARY}", ""] + LLMS_NOTES + [""]
    for heading, test in LLMS_SECTIONS:
        items = [item(p) for p in pages if test(p)]
        if items: out += [f"## {heading}", ""] + items + [""]
    out += ["## Optional", "", f"- [Sitemap]({base}/sitemap.xml): every page with a lastmod date", ""]
    return "\n".join(out)


def main():
    products = json.loads((ROOT / "data/products.json").read_text())
    cats = json.loads((ROOT / "data/categories.json").read_text())
    guides = [json.loads(p.read_text()) for p in sorted((ROOT / "data/guides").glob("*.json"))] if (ROOT / "data/guides").exists() else []
    for c in cats: CAT_LABEL[c["slug"]] = c["name"]
    CATS[:] = cats
    GUIDES[:] = guides
    for g in guides:
        for c in g.get("categories", []): assert c in CAT_LABEL, f"guide {g['slug']}: unknown category {c}"
    validate(products, cats)
    products.sort(key=lambda p: (p["brand"].lower(), p["product"].lower()))
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")
    latest = max(p["last_checked"] for p in products)
    byid0 = {p["id"]: p for p in products}
    MODIFIED.update({"/": latest, "/compare/": latest, "/about/": ABOUT_UPDATED, "/privacy/": PRIVACY_UPDATED})
    for c in cats: MODIFIED[f"/{c['slug']}/"] = max(p["last_checked"] for p in cat_products(c, products))
    for g in guides:
        MODIFIED[f"/{g['slug']}/"] = max([g["last_checked"]] + [byid0[i]["last_checked"] for i in g.get("product_ids", []) if i in byid0])
    pages = {"/": home(products, cats, guides), "/compare/": compare(products), "/about/": about(products, cats, guides), "/privacy/": privacy_page()}
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
    urls = "".join(f"<url><loc>{base}{p}</loc><lastmod>{MODIFIED.get(p, latest)}</lastmod></url>" for p in pages)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    if CFG.get("indexnow_key"):  # IndexNow (Bing/Yandex) key file must sit at the site root
        (OUT / f"{CFG['indexnow_key']}.txt").write_text(CFG["indexnow_key"])
    (OUT / "robots.txt").write_text(robots_txt(base))
    (OUT / "llms.txt").write_text(llms_txt(base, pages))
    if (ROOT / "BingSiteAuth.xml").exists():  # Bing Webmaster Tools verification file, must sit at the site root
        shutil.copyfile(ROOT / "BingSiteAuth.xml", OUT / "BingSiteAuth.xml")
    if CFG.get("cname"):
        (OUT / "CNAME").write_text(CFG["cname"].strip() + "\n")
    check_links(OUT)
    print(f"Built {len(pages)} pages (internal links OK), {len(products)} products -> {OUT}")

if __name__ == "__main__":
    main()
