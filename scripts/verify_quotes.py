"""Check every quoted field in data/products.json appears verbatim on the saved snapshot
of the brand's page (research/pages/NN.txt + Shopify body text). Run before publishing."""
import json, re, sys
NS = "Not stated, check with them"
FIELDS = ["ingredients","made_in","sourced_from","rawhide_free","size_guidance","supervision"]
def norm(s): return re.sub(r"\s+"," ",s.replace("\u00a0"," ")).strip().lower()
try:
    cands = json.load(open("research/candidates.json"))
except FileNotFoundError:
    sys.exit("research/ snapshots not present on this machine; cannot verify quotes")
bad = 0
for p in json.load(open("data/products.json")):
    i = p.get("snapshot")
    if isinstance(i, int):   # v1 products: research/pages/NN.txt + Shopify body text from candidates.json
        hay = norm(open(f"research/pages/{i:02d}.txt").read().replace("\n"," ") + " " + " ".join(cands[i].get("alltext") or []))
        assert cands[i]["url"] == p["source_url"], (i, p["source_url"])
    elif isinstance(i, str):  # later products: path to a text snapshot, e.g. research/pages/brand-handle.txt
        hay = norm(open(i).read().replace("\n"," "))
    else:
        bad += 1; print(f"NO SNAPSHOT [{p['brand']} / {p['product']}]"); continue
    for f in FIELDS:
        v = p[f]
        if v == NS: continue
        for seg in v.split(" · "):
            if norm(seg) not in hay:
                bad += 1; print(f"NOT FOUND [{p['brand']} / {p['product']}] {f}: {seg}")
print("quote check:", "OK" if not bad else f"{bad} problems"); sys.exit(1 if bad else 0)
