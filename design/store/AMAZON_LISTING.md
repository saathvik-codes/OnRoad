# OnRoad on the Amazon Appstore: what to fill in

Images are in `design/store/out/`. To rebuild them, run `python design/store/make_store_assets.py`.
The Amazon APK is built with `./gradlew assembleAmazon`: package com.onroad.app, version 1.4.0 (code 14), minSdk 26, release-signed.

## 1. General information
| Field | Value |
|---|---|
| App title | OnRoad: On-Road Car Prices |
| App SKU | onroad-android |
| App category | Shopping. Pick an "Automotive" subcategory if the form offers one; otherwise use Lifestyle. |
| Customer support email | saathvikk202@gmail.com |
| Customer support phone | leave blank (optional) |
| Customer support website | https://onroad-frontend.onrender.com/support |

## 2. Availability & pricing
- Price: Free. No in-app purchases.
- Countries: India only, since prices, taxes and showrooms are Indian. Choose "Select countries" and tick India.
- Release date: as soon as possible.

## 3. Description
**Short description** (shown first, up to 1,200 characters):
> See the real on-road price of any new car or bike in India, worked out for your city. Every rupee is itemised: ex-showroom price, road tax, registration, insurance and charges. Then compare variants, check live offers from carmakers and get quotes from showrooms near you.

**Long description** (up to 4,000 characters):
> The brochure price is never what you pay. OnRoad shows the real on-road price of every new car and bike sold in India, for your city.
>
> REAL PRICES FOR YOUR CITY
> • Ex-showroom prices from each carmaker's official price list
> • Road tax and registration from your state transport department's rules
> • Insurance and other charges added, so the total is what you actually pay
>
> COMPARE AND DECIDE
> • Every variant side by side: price, engine, power, mileage, features
> • Spec sheet for each variant
> • EMI and loan calculator
> • Filters for budget, body type, fuel and transmission
>
> OFFERS AND ALERTS
> • Festive and consumer offers published by carmakers, updated daily
> • Set a target price on any car and we tell you once it drops there
> • Launch alerts for new models
>
> SHOWROOMS NEAR YOU
> • Official dealers sorted by distance, with directions and one-tap calling
> • Ratings from verified buyers
> • Ask showrooms for a quote. Your mobile number is never shared with them.
>
> OnRoad is independent and is not affiliated with any carmaker or showroom. Prices can change without notice, so confirm the final figure with the showroom before you pay.

**Product feature bullets** (3 to 5):
1. Real on-road price for your city: tax, registration and insurance included
2. Compare variants and full specs side by side
3. Live offers from carmakers, plus price-drop alerts
4. Showrooms near you, with directions and verified-buyer ratings
5. Request showroom quotes without sharing your number

**Keywords**: on road price, car price, new car, car prices india, ex showroom price, road tax, car insurance, car compare, car offers, bike price, showroom, emi calculator, maruti, tata, mahindra, hyundai

## 4. Images & multimedia
| Asset | File | Notes |
|---|---|---|
| Small icon 114×114 | out/icon-114.png | |
| Large icon 512×512 | out/icon-512.png | |
| Screenshots (3 to 10) | out/screenshot-1.png … screenshot-7.png | 1200×1920 portrait. Upload them in this order. |
| Promotional image 1024×500 | out/feature-1024x500.png | Optional, but it gets you featured placements |
| Video | skip | Optional |

## 5. Content rating
Answer **None** for every theme: violence, sexual content, profanity, drugs, alcohol, tobacco, gambling and horror.
- Advertisements: **Yes** (AdMob banner ads)
- Collects user information: **Yes** (email, phone if verified, city)
- Location-based services: **Yes** (only when the user taps "Showrooms near me")
- User-generated content shared publicly: **Yes** (showroom ratings)
- Account creation: **Yes**
- Privacy policy URL: **https://onroad-frontend.onrender.com/privacy**
- Kids (COPPA / for children under 13): **No**

## 6. App files (APK)
- Upload `onroad-amazon-1.4.0.apk` (built with `./gradlew assembleAmazon`; no self-update permission).
- Device support: **untick every Amazon Fire device**; keep only non-Amazon Android devices. Sign-in, notifications and ads use Google Play services, which Fire tablets don't have.
- Language: English.
- Export compliance: Yes. The app uses only standard HTTPS encryption.
- Apply Amazon DRM: **No**.

## 7. Before you submit: Google sign-in under Amazon's signature
Amazon re-signs the APK with its own key. Google sign-in and Firebase check that key's fingerprint, so they will fail for Amazon users until you add it:
1. After the upload, open **App files → Appstore Certificate Hashes** and copy the **SHA-1** and **SHA-256**.
2. In the Firebase console, open project onroad-6c950 → Project settings → the Android app com.onroad.app → **Add fingerprint**, and paste both hashes.
3. Keep the existing fingerprints. Your own release key's SHA-1 is 6b:f3:93:62:3d:3f:2e:37:c5:33:ca:99:db:9d:5d:4f:f2:5f:c1:04.

## 8. Notes for the review team
> No login is needed to browse prices, offers and showrooms. Signing in, with email or Google, is only needed to save cars, set price alerts and request quotes. Quote requests need a verified Indian mobile number (SMS code). Location access is optional and only used for "Showrooms near me".
