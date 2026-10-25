# CJ pet advertisers vs. Nibbables catalog

Checked 2026-10-23, ~2:25 PM ET. Source list: /workspace/affiliate-library/cj-advertisers-2026-10-23.csv (category "Pets").
Our catalog: data/products.json (34 products, 12 brands: Campfire Treats, GREAT DOG CO., Best Bully Sticks, Jack&Pup,
Bow Wow Labs, Pawstruck, Nature Gnaws, Redbarn, Mighty Paw, Pupford, Raw Paws Pet Food, Earth Animal).
Method: public sites only, via curl. For Shopify stores I pulled the full public catalog (/products.json) and matched titles and
vendors against our brands and chew types (bully, pizzle, antler, yak, cheek, no-hide). For the .aspx pet-med stores I used sitemap.xml
(every product URL) plus on-site search for bully, antler, yak and redbarn. No sign-ins and no contact with anyone. CJ terms and
figures are copied from the CSV as exported (EPC = 3-month EPC).

## Apply

| Rank | Advertiser | CJ ID | Commission | EPC 3-mo | Approval odds | Nibbables products carried (evidence) |
|---|---|---|---|---|---|---|
| 1 | Raw Paws Pet Food | 7127091 | 10% | 19.16 USD | Manual review | It's one of our 12 brands, so the CJ program pays on its own store. It carries all 3 of our Raw Paws cards: Standard Bully Sticks 6" 10-ct https://www.rawpawspetfood.com/products/standard-bully-sticks-6-inch-10-ct (the catalog JSON showed this variant **unavailable** when checked); Himalayan Yak Chews Medium 3-ct https://www.rawpawspetfood.com/products/himalayan-yak-chews-dogs-medium-3-ct (available); Beef Cheek Rolls 6" 4-ct https://www.rawpawspetfood.com/products/beef-cheek-rolls-dogs-6-inch-4-ct (available). It also has other sizes we could add later (Thin/Jumbo bully sticks, Small/Large/XL yak chews, 10" cheek rolls, lamb pizzle). |

No other CJ Pets advertiser carries any of our 12 brands or any bully stick, antler, yak chew or beef cheek product.

## Skip

| Advertiser | CJ ID | Terms (CSV) | Why |
|---|---|---|---|
| Pet Care Supplies | 4247920 | 10%, EPC 50.70, manual | A pet-medication store. All 601 sitemap URLs checked: the only dog "chews" are VeggieDent dental chews and medicated chewables (Bravecto, NexGard and others). It has none of our brands. Its on-site search runs in JavaScript (Findify), so I couldn't check it with curl, but the sitemap covers every product URL. |
| Best Vet Care | 4247934 | 10%, EPC 37.48, auto | Same kind of store. Across 744 sitemap URLs, the only chews are VeggieDent. On-site search returned "No Result Found" for bully, antler, yak and redbarn. |
| Budget Pet Care | 4250177 | 10%, EPC 27.60, auto | Same kind of store. Across 730 sitemap URLs, the only chews are VeggieDent and Bravecto. Search for bully, yak and redbarn said it was "unable to find any results", and "antler" returned only unrelated fuzzy matches. |
| Canada Pet Care | 4247933 | 10%, EPC 80.56, auto | Same kind of store. Across 605 sitemap URLs, the only chews are VeggieDent, Sentinel, SeaFlex and Bravecto. |
| Revival Animal Health | 4579683 | 3%, EPC 54.49, manual | Full catalog checked (1,424 products, 267 vendors): none of our brands, and no bully sticks, antlers or yak chews. It does sell natural chews from Jones Natural Chews Co (e.g. https://revivalanimal.com/products/windees-beef-trachea), plus Nylabone and C.E.T. It's only worth applying if we add those brands or categories later. |
| UsaPetExpress (worldpetexpress.net) | 3435634 | 12%, EPC 80.14, manual | A pet-medication store. Its Treats category lists only the brands Addiction, Awesome Pawsome and Zeal, none of ours. On-site search couldn't be checked because the POST search was blocked by CloudFront (403), and its sitemap has only 6 URLs. |
| Maven Pet | 7651896 | no commission shown, EPC 168.23, manual | Sells a pet health-tracker smart collar (maven.pet), not chews. |
| JustFoodForDogs | 7015142 | 10%, EPC 74.48, manual | Full catalog checked (77 products): fresh dog food, no chews. |
| CUDDLY | 7646631 | 8%, EPC 5.14, manual | Full catalog checked (29 products): own-brand food, toys and apparel. No chews from our brands. |
| FunnyFuzzy | 6582116 | 10%, EPC 38.80, manual | Full catalog checked (330 products): its "chews" are chew toys and beds, not edible chews. |
| Ellevet Sciences | 5558840 | 15%, manual | Sells CBD and CBDA for pets (homepage title and meta). Its catalog JSON was blocked (403). |
| Petkit | 7454299 | 10%, manual | Sells litter boxes, feeders and fountains (homepage title). |
| Royal Canin | 6447582 | 8%, manual | Pet food. Site not fetched. |
| Support Pets | 5472210 | $30, manual | Sells ESA letters and training (homepage title). |
| Saltwaterfish.com | 2234018 | 2% | Aquarium supplies. Site not fetched. |
| EU/UK/PL stores: Kutyakajas.hu, PetCenter CZ/SK, Petissimo, Petkarma.pl, Reedog, Sape.hr, SUPERZOO.cz/.sk, Vetplanet PL, Furfable, Weenect, My Family Vets UK | various | various | Not US stores. Sites not checked. |
