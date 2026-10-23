# NIGHTLY.md: add one new page to Nibbables each night

Goal: each night, publish **one** new page that is useful and 100% sourced. A page can be a new chew-type category, a brand-comparison guide, or a batch of new products added to an existing category. One accurate page beats three sloppy ones. If a page can't be verified well enough, skip it, note why in `published-log.md`, and take the next item in the queue.

## Ground rules (never break these)
1. **Never invent anything.** That covers ingredients, origins, sizes, prices, reviews and ratings. If the brand's page doesn't say it, write `Not stated, check with them`.
2. **Never call a chew "safe", never rate safety, never compare which chew is "safer".** The build refuses any page containing safe/safer/safest. Don't quote brand sentences that contain those words either. Pick a different sentence or use `Not stated, check with them`.
3. **No prices** (the build refuses `$12`-style text). **No reviews or star ratings.** Don't quote customer reviews from product pages.
4. Only use the **brand's own product page** as the source (not Amazon, Chewy, blogs or Reddit; those can only help you *find* products). Each product needs `source_url` and `last_checked` set to today (YYYY-MM-DD, America/New_York).
5. Claims are **verbatim quotes**. "Made in USA" etc. is always the brand's claim. If a page contradicts itself (for example two different source countries), quote one and record the other in `note`.
6. "Rawhide-free" only when the page literally says rawhide-free, no rawhide or made without rawhide. An "alternative to rawhide" line does not count.
7. **Amazon affiliate links (approved by Yair 2026-10-23, tag `nibbables-20`, `"affiliates_live": true`).** For every new product, look for the **exact same product** on Amazon.com: same brand, same product name, same size/variant wording (pack count may differ only if the brand page sells that chew in several counts; note it). Prefer listings under the brand's own store ("Visit the <Brand> Store" / "Brand: <Brand>"). Find candidates with `curl --compressed -A "<browser UA>" "https://www.amazon.com/s?k=<brand+product>"` or WebSearch, then fetch `https://www.amazon.com/dp/<ASIN>` and read the title, byline, seller and variation list. A search result showing the ASIN and title is acceptable evidence only if brand, product and variant clearly match. **Never guess an ASIN. If unsure, leave the product with no link.** Record every match *and* every miss (with the reason) in `research/amazon-matches.md`. Then set `"amazon_asin": "<ASIN>"` and `"affiliate_url": "https://www.amazon.com/dp/<ASIN>?tag=nibbables-20"` on the product (the build rejects any other format). The card shows a "Check on Amazon" button (rel="sponsored nofollow noopener", target="_blank") next to the brand-page link, and any page with an Amazon link gets "As an Amazon Associate I earn from qualifying purchases." above the first link (the build refuses a page without it). **Never show Amazon prices, ratings, stars or review counts**, and Amazon is never a *source* for card claims (rule 4). Never sign up for other programs, accept terms or create accounts. Publishing new pages to the existing GitHub Pages site is approved. Changing hosting, DNS, domains or repo settings is not.
8. Our own copy (intros, guide sections) should be factual and neutral: describe what the brands say, and point to the vet for health questions. No health or dental-benefit claims in our voice.

## Procedure
1. **Pick the page:** take the top unchecked item in `content-queue.md`.
2. **Research** (about 30–60 minutes of tool time):
   - Many chew brands run Shopify: `curl -s "https://<domain>/products.json?limit=250" -o research/raw/<domain>.json` (use curl's default user-agent; a browser user-agent gets 403). The product page is `https://<domain>/products/<handle>`.
   - Snapshot every product page you cite: `curl -sL https://<domain>/products/<handle> -o research/pages/<brand>-<handle>.html && python3 scripts/h2t.py research/pages/<brand>-<handle>.html > research/pages/<brand>-<handle>.txt`. If curl is blocked, use WebFetch and save its text output to the .txt.
   - `research/pages/` and `research/raw/` are gitignored. They live on the box for re-checking.
3. **Write the data:**
   - **New products:** append to `data/products.json` with the same shape: `brand, product, category, source_url, ingredients, made_in, sourced_from, rawhide_free, size_guidance, supervision, sizes[], note, last_checked`, plus `"snapshot": "research/pages/<brand>-<handle>.txt"`. `category` must be a slug in `data/categories.json`. Multiple quotes in one field are joined with ` · `.
   - **New category:** add an entry to `data/categories.json` (slug, name, h1, title, meta, intro) and at least 3 products for it.
   - **New guide:** create `data/guides/<slug>.json` with `slug, title, meta, h1, intro, sections[{h,p}], sources[{label,url}], product_ids[], last_checked`. Product ids are the card anchors (`id="..."`) on the category pages, i.e. the slug of "brand product". Every sentence in `sections` must be backed by a cited brand page.
   - **Amazon match:** per rule 7, check each new product for an exact Amazon match and log it in `research/amazon-matches.md`.
   - Title ≤ 65 characters where possible; meta description ≤ 160.
4. **Verify quotes:** `python3 scripts/verify_quotes.py` must print `quote check: OK` (every quoted segment must appear verbatim in its snapshot).
5. **Build:** `python3 build.py`. It fails on missing fields or sources, unknown categories, duplicate products, guides pointing at unknown products, the word safe/safer, or prices. Fix and rebuild. Sitemap and robots are regenerated automatically.
6. **Check:** `cd site && python3 -m http.server 8765`, then take screenshots at 390px and 1280px:
   `google-chrome --headless=new --no-sandbox --window-size=390,2400 --screenshot=/tmp/p.png http://localhost:8765/<path>/`
   Then spot-check 3 cards against the live brand pages.
7. **Log:** append a row to `published-log.md` (date, path, products added, sources checked, gaps).
8. **Update the queue:** tick the item in `content-queue.md` and add new ideas (keep about 30 queued).
9. **Re-verify** if time allows: re-fetch 3–5 of the oldest `last_checked` products. Update changed quotes and bump `last_checked`. If a page is gone (404), remove the product and log it.
10. **Commit & publish** (approved: GitHub Pages under `yairsz/nibbables`):
   ```
   cd /workspace/nibbable/site-src
   git pull --rebase
   git add data/ content-queue.md published-log.md NIGHTLY.md build.py static/ site.json scripts/ research/amazon-matches.md
   git commit -m "Add <page path> (<n> products, checked <YYYY-MM-DD>)"
   git push
   ./publish.sh          # builds and force-pushes site/ to gh-pages
   ```
11. **Confirm the deploy** (about 1–2 minutes):
   ```
   gh api repos/yairsz/nibbables/pages --jq .status                                   # expect: built
   curl -s -o /dev/null -w "%{http_code}\n" "https://yairsz.github.io/nibbables/<path>/?v=$(date +%s)"   # expect 200
   curl -s https://yairsz.github.io/nibbables/sitemap.xml | grep -c "<path>"           # expect 1
   ```
   (The custom domain is live: also check https://nibbables.com/<path>/ and, if the page has Amazon links, `curl -s https://nibbables.com/<path>/ | grep -c 'tag=nibbables-20'` and `grep -c 'As an Amazon Associate I earn from qualifying purchases.'`.) Record the result in `published-log.md`.

## Re-verification cadence
- Every product: re-check within 90 days of `last_checked`, or right away if someone reports a change.
