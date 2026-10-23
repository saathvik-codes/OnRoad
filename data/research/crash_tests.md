# Crash-test dataset (crash_tests.json)

Read on: 2026-10-22. I used official sources only: bncap.in and globalncap.org. Crawling followed robots.txt, kept TLS verification on and made about 1 request per second.

## Coverage
- **Bharat NCAP: 38 records covering 37 result pages.** These are all the vehicles on https://www.bncap.in/vehicle-safety-ratings/, cross-checked against the site's vehicle sitemap (37 pages each). The Safari/Harrier page has one shared rating and is split into two records. Stars come from each page's rating widgets ("Rated X out of 5"). Scores come from the page header. `variant_tested` comes from the "Tested Vehicle Model & Variant" field.
- **Global NCAP: 28 records from 25 fact sheets.** These are all results from the 2022+ "Safer Cars for India" protocol listed on https://www.globalncap.org/indiaresults, where the adult maximum is 34. Scores, bodyshell and footwell ratings come from the official fact-sheet PDFs, which are the `source_url` for these records. Stars are images in the PDFs, so I counted them from the rendered fact sheets and checked each one by eye. There are 3 shared ratings: Safari/Harrier, Taigun/Kushaq and Virtus/Slavia. Each is split into one record per model.
- Models tested by both agencies have one record per agency: Nexon, Safari, Harrier, Dzire and Victoris. Some models have several records, and the `notes` field tells them apart: Baleno 2 and 6 airbags, Celerio 2 and 6 airbags, Kia Carens and Nissan Magnite by VIN range, old and new Dzire, and Punch EV 2024 and 2026.
- `video_url` (youtube-nocookie embed) is set only where the official page links that model's crash-test video. That is 64 of 66 records. The Bharat NCAP Safari/Harrier page has no model video. I ignored the YouTube link that appears on every bncap.in page because it is a site-wide channel link, not a model video.

## Gaps and caveats
- **Skipped: old-protocol Global NCAP results** (adult maximum 17), including 8 published in 2022: Kia Carens 2022, Toyota Urban Cruiser, Hyundai i20, Hyundai Creta, Honda City (4th gen), Honda Jazz, Nissan Magnite 2022 and Renault Kiger.
- **`test_date` is null everywhere.** Neither site states a crash-test date. Bharat NCAP shows only a "rating applicable from" month (stored as `rating_published`, YYYY-MM) and variant-assessment months. Global NCAP shows only the year of publication (stored as `rating_published`).
- **`airbags_tested` is filled only when the official page states it** (Baleno and Celerio). Global NCAP records have no `variant_tested`, because the fact sheets state only the model.
- **VinFast VF6 and VF7 use brand "VinFast",** which is not in OnRoad's brand list.
- **Nissan Tekton's Bharat NCAP rating comes from a Renault Duster test** (corporate twin), as stated on the page.
- **Model names that differ from the source:** Mahindra "XUV400" is listed as "XUV 400 EV", and Global NCAP's "Scorpio-N" is recorded as "Scorpio N".
