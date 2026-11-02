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
- GA4 tag is rendered in every page <head> from `site.json` `ga_measurement_id` (remove the field to disable).
- Amazon Associates is live (`site.json` `"affiliates_live": true`, tag `nibbables-20`). Products with an exact Amazon match carry `amazon_asin` + `affiliate_url`; see `research/amazon-matches.md` and NIGHTLY.md rule 7.

## Files
- `data/products.json`: products. `data/categories.json`: category pages. `data/guides/*.json`: extra pages (see NIGHTLY.md).
- `scripts/make_data.py`: the v1 curation script that generated products.json. `scripts/verify_quotes.py`: quote checker. `scripts/extract.py`: Shopify feed → candidate quotes. `scripts/h2t.py`: HTML → text.
- `NIGHTLY.md`, `content-queue.md`, `published-log.md`: nightly routine. `DOMAIN.md`: DNS and redirect steps.

## Microsoft Clarity (added 2026-11-02)
- Clarity tag is rendered in every page <head> right after the GA4 tag by `clarity_tag()` in build.py, from `site.json` `clarity_project_id` (remove the field to disable; privacy page section also keys off it).
- Project IDs: ByeBulky `z7gso98mvr`, Nibbables `z7gtb12n7l`. Account: malteado001@gmail.com. Dashboard: https://clarity.microsoft.com
- AI-assistant referral data: Clarity puts sessions from ChatGPT, Copilot, Gemini, Claude and Perplexity (standalone sites only; Google AI Overviews are not separated) in the **AIPlatform** / **PaidAIPlatform** channel groups. Per https://learn.microsoft.com/en-us/clarity/insights/ai-channel-group: project Dashboard > Referrer card (the doc also calls it the Traffic card) > **Channels** tab > select AIPlatform. Hidden referrers show as Direct. Include it in traffic reports alongside GA4.

## Pinterest (added 2026-11-02)
- `p:domain_verify` meta rendered in every page <head> by `pinterest_tag()` from `site.json` `pinterest_domain_verify`.
