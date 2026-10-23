# Nibbables

A static directory of long-lasting dog chews (bully sticks, yak cheese chews, beef cheek rolls, rawhide-free chews, antlers). Every claim on a card is quoted word for word from the brand's own product page, with a link and the date it was checked.

- Live: https://yairsz.github.io/nibbables/ (https://nibbables.com once DNS is set; see DOMAIN.md)
- Build: `python3 build.py` (stdlib only) → `site/`
- Publish: `./publish.sh` (builds, then force-pushes `site/` to the `gh-pages` branch)
- Check quotes against saved snapshots: `python3 scripts/verify_quotes.py`

## Rules baked into the build
- Every product must have: brand, product, category, source_url, ingredients, made_in, sourced_from, rawhide_free, size_guidance, supervision, sizes, last_checked. Use `Not stated, check with them` for anything the brand's page doesn't say.
- The build refuses to publish if any page contains the word "safe"/"safer"/"safest" or a price.
- No reviews, no ratings, no prices. "Made in USA" is always shown as the brand's quoted claim.
- Affiliate slots stay empty (`affiliate_url` is rejected unless `site.json` has `"affiliates_live": true`, which needs Yair's approval).

## Files
- `data/products.json`: products. `data/categories.json`: category pages. `data/guides/*.json`: extra pages (see NIGHTLY.md).
- `scripts/make_data.py`: the v1 curation script that generated products.json. `scripts/verify_quotes.py`: quote checker. `scripts/extract.py`: Shopify feed → candidate quotes. `scripts/h2t.py`: HTML → text.
- `NIGHTLY.md`, `content-queue.md`, `published-log.md`: nightly routine. `DOMAIN.md`: DNS and redirect steps.
