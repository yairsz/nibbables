#!/usr/bin/env python3
"""Pull candidate quotes from brand Shopify product JSON (research/raw/<domain>.json).
Outputs research/candidates.json for manual review. Quotes are verbatim sentences from the brand's own product description."""
import json, re, html, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent / "research"
PICKS = json.loads((R / "picks.json").read_text())

def text_of(body):
    t = re.sub(r'<(br|/p|/li|/h\d|/div|/dt|/dd|/tr)[^>]*>', '\n', body, flags=re.I)
    t = re.sub(r'<li[^>]*>', '\n• ', t, flags=re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = html.unescape(t).replace('\xa0', ' ')
    lines = [re.sub(r'[ \t]+', ' ', l).strip(' •') for l in t.split('\n')]
    return [l for l in lines if l]

def sentences(lines):
    out = []
    for l in lines:
        for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', l):
            s = s.strip()
            if s: out.append(s)
    return out

PAT = {
 "ingredients": r'ingredient|made (from|with) (only|just|100%)|single[- ]ingredient|100% (beef|natural|yak)|composition',
 "made": r'made in|crafted in|baked in|produced in|manufactured|handcrafted in|kitchen|facility',
 "sourced": r'sourced|source[sd]? from|origin|raised|free[- ]range|grass[- ]fed|himalaya|nepal|brazil|argentina|colombia|naturally shed|shed antler|wild|ranch',
 "rawhide": r'rawhide|hide[- ]free|no[- ]hide',
 "guidance": r'\blbs?\b|pound|dog size|for (small|medium|large|giant|all)|chewer|puppies|puppy|breed|months|weigh',
 "supervision": r'supervis|discard|swallow|choking|choke|fresh water|small enough|remove|unattended|vet',
}
res = []
for p in PICKS:
    d = json.loads((R / "raw" / f"{p['domain']}.json").read_text())["products"]
    prod = next((x for x in d if x["handle"] == p["handle"]), None)
    if not prod:
        print("MISSING", p, file=sys.stderr); continue
    lines = text_of(prod["body_html"] or "")
    ss = sentences(lines)
    c = {k: [s for s in ss if re.search(v, s, re.I)][:8] for k, v in PAT.items()}
    opts = [{"name": o["name"], "values": o["values"]} for o in prod.get("options", [])]
    res.append({**p, "title": prod["title"], "vendor": prod.get("vendor"), "options": opts,
                "url": f"https://{p['domain']}/products/{prod['handle']}", "cand": c, "alltext": lines})
(R / "candidates.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(len(res), "products")
