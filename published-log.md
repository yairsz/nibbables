# Published log

| Date (ET) | Path(s) | Products | Sources checked | Gaps / notes | Deploy |
|---|---|---|---|---|---|
| 2026-10-23 | v1: /, /bully-sticks/, /yak-cheese-chews/, /beef-cheek-rolls/, /rawhide-free/, /antlers/, /compare/, /about/ | 34 (12 brands) | 34 brand product pages, all HTTP 200 on 2026-10-23; every quote checked with scripts/verify_quotes.py | Dropped 3 picks with too little stated (Jack&Pup yak chews, Pupford split elk antlers, Raw Paws alternative soft bully sticks: no rawhide statement). Feeds blocked: Himalayan Pet Supply, Cheesy100, Barkworthies. See "Data gaps" below. | gh-pages main@86d5145: Pages status built; 8 pages + sitemap/robots curl 200 |
| 2026-10-23 | all pages | n/a | live curl: homepage + 7 pages 200, each contains G-MXKFFSYRQB twice | Added GA4 gtag.js (site.json ga_measurement_id) and Analytics paragraph on /about/ | gh-pages main@344b611, Pages built |

## Data gaps at v1 (2026-10-23)
- Made-in claim not stated (9): Best Bully Sticks 6" thin bully, yak cheese and split elk antler; Jack&Pup bully; Bow Wow Labs bully (sourcing countries given, and the FAQ says "packaged in the US"); Nature Gnaws bully and antlers; Mighty Paw bully and antlers (sourcing given, plus hand-inspection in Rochester, NY).
- Sourced-from not stated (6): Best Bully Sticks 6" and 12" bully; Pupford bully (says "made in the USA"); Mighty Paw yak; Redbarn bully and beef cheek (country of origin only).
- Supervision note not stated (6): Bow Wow Labs bully, Mighty Paw bully and antlers, Pupford bully and yak, Best Bully Sticks yak.
- Size guidance not stated (2): Pupford bully and yak.
- Rawhide-free stated by only 7 of 34 (4 Earth Animal No-Hide, GREAT DOG jumbo bully, Nature Gnaws bully, Best Bully Sticks yak). The others are "Not stated" even if they say "alternative to rawhide".
- Mighty Paw bully page names both Colombia and Brazil (noted on the card). Jack&Pup bully says Brazil and "South American" (noted).
