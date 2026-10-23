# OnRoad: On-road price rules for India (as of 19 Oct 2026)

The machine-readable version is `onroad_rules.json`, which sits in this folder. Every figure below is tagged with its source:
- **[OFFICIAL]** means I read it on a government website or in a gazette.
- **[SECONDARY]** means it comes from news or an aggregator and is not verified against an official document.
- **null** means I could not verify it. No numbers were made up.

---

## Part 1: Telangana (main focus)

### 1.1 Lifetime (life) tax on new private four-wheelers [OFFICIAL]

The rates below come from **G.O.Ms.No.53**, TR&B (Tr.I) Dept, dated 13-08-2025, in force from **14-08-2025**. This order replaced the Third, Sixth and Seventh Schedules of the Telangana Motor Vehicles Taxation Act, 1963. Source: <https://www.transport.telangana.gov.in/html/taxes-life-time-tax.html> (the G.O. is posted as images; read 19-10-2026). It replaced the 2022 rates in G.O.Ms.No.22 (13/14/17/18%), which some aggregators still quote.

| Cost of vehicle | Individual, 1st vehicle (Sixth Sch.) | Individual, 2nd or later vehicle (Sixth + 2%) | Company / institution / society (Seventh Sch.) |
|---|---|---|---|
| Below ₹5 L | **13%** | 15% | 15% |
| ₹5 L to below ₹10 L | **14%** | 16% | 16% |
| ₹10 L to below ₹20 L | **18%** | 20% | 20% |
| ₹20 L to below ₹50 L | **20%** | 22% | 22% |
| Above ₹50 L | **21%** | 23% | 25% |

- **Tax base:** the tax is charged on the "cost of the vehicle". That means the invoice price **including GST and other levies**, with **no deduction for cash or trade discounts**, and never less than the manufacturer's ex-showroom price. This definition is s.2(aa), added by TS MVT (Amendment) Act No.6 of 2023 with effect from 13-04-2023 ([LegitQuest](https://www.legitquest.com/act/the-telangana-motor-vehicles-taxation-amendment-act-2023/E031)) [SECONDARY text of statute]. TS High Court rulings say the tax follows the invoice cost including taxes.
- **Fuel:** there is no difference by fuel. Petrol, diesel, CNG and hybrid cars all pay the same slab. I found **no hybrid concession**.
- **Second vehicle:** the extra 2% applies to the second or later personal vehicle owned by an individual, and only at new registration [OFFICIAL].
  - The Telangana HC held that it cannot be charged if the first vehicle was sold before the new one was permanently registered ([LiveLaw](https://www.livelaw.in/tax-cases/2-additional-tax-for-acquiring-second-vehicle-cannot-be-levied-first-vehicle-sold-before-permanent-registration-of-new-vehicle-telangana-hc-277287)).
  - **Pending waiver:** news reports dated 22-02-2026 say the CM approved scrapping this 2% ([Swipe](https://getswipe.in/blog/article/telangana-govt-to-scrap-additional-life-tax-on-second-vehicle-purchase)). I **found no G.O.**, and the official page still shows the surcharge, so the waiver status is **null**.
  - **Calculator:** charge the 2% by default and show the user a note about the pending waiver.
- **Slab edge:** the G.O. says "20 lakh or above and below 50 lakh" and "above 50 lakh", so it leaves exactly ₹50,00,000 unassigned. The JSON puts it in the 20–50 L slab.

### 1.2 Road Safety Cess (new from 1 March 2026)
- **Amount:** **₹5,000 one-time** on a new non-transport light motor vehicle (car) at first registration.
- **Legal basis:** s.3-C and the Ninth Schedule, added by L.A. Bill No.5 of 2026 (Telangana Gazette, 02-01-2026) [OFFICIAL: <https://prsindia.org/files/bills_acts/bills_states/telangana/2026/Bill5of2026TG.pdf>].
- **Commencement:** 01-03-2026 under G.O.Ms.No.10 dated 25-02-2026 [SECONDARY: [The South First](https://thesouthfirst.com/telangana/telangana-to-levy-one-time-road-safety-cess-on-new-vehicles-from-1-march/)].
- **EVs:** whether EVs are exempt from this cess is **null** (not verified).

### 1.3 Electric vehicle exemption
- **Exemption:** 100% life tax plus 100% registration fee waived under **G.O.Ms.No.41** dated 16-11-2024 (Telangana EV Policy).
- **Validity:** about 18-11-2024 to **31-12-2026**.
- **Conditions:** the EV must be bought and registered in Telangana. There is no cap on the number of vehicles. It covers 2W, private 4W, taxis, autos, LGVs and buses.
- **Sources:** [SECONDARY: [Deccan Herald](https://www.deccanherald.com/india/telangana/telangana-announces-100-exemption-on-road-tax-registration-fees-for-electric-vehicles-3280328); [ETV Bharat, Aug 2026](https://www.etvbharat.com/en/state/incentives-fuel-transition-to-electric-vehicles-in-telangana-enn26081904371)]. The G.O. text itself was not retrieved.
- **After 2026:** no extension has been announced as of 19-10-2026. The calculator must switch EVs to the normal slabs for registrations from 01-01-2027 unless a new G.O. is issued.
- **Central rule:** battery-operated vehicles are also exempt nationally from RC and registration-mark fees under MoRTH G.S.R. 525(E) of 02-08-2021.

### 1.4 Registration, RTO and other charges

| Item | ₹ | Status / source |
|---|---|---|
| New registration, LMV non-transport | 600 | [OFFICIAL] CMVR Rule 81, [TS fees page](https://www.transport.telangana.gov.in/html/fees-registration.html) |
| Smart-card RC (Form 23A) | 200 | [OFFICIAL] same page, Note 1 |
| Hypothecation (loan) endorsement, LMV | 1,500 | [OFFICIAL] same page, item 9 (only if financed) |
| HSRP number plates | 0 extra | [OFFICIAL rule] HSRP Order 2018: the cost is inside the vehicle price and dealers may not itemise it |
| Temporary registration fee | null | Not published. A TR must be issued via Vahan before delivery |
| Postal / speed-post fee for RC | null | Since Jan 2026, TS registers at the dealer and posts the RC ([South First](https://thesouthfirst.com/telangana/no-more-rta-visits-telangana-permits-vehicle-registration-at-dealerships-rcs-delivered-by-post/)). No fee is published |
| Service / user charges | null | The user-charges tables on the TS site are commented out of the page, so not verified |
| Green tax | 0 | Only applies to non-transport vehicles over 15 years old (G.O.Ms.No.23, 2022) |

### 1.5 Hyderabad (GHMC) vs the rest of Telangana
- **Taxes and fees:** I found **no difference** in life tax, cess or registration fees. They are the same across the state.
- **Insurance:** Hyderabad is in **Zone A** of the old India Motor Tariff, so the reference own-damage (OD) rate is slightly higher there. The rest of Telangana is Zone B (see 3.3).

---

## Part 2: GST context (affects ex-showroom, and through it the life tax)

From **22-09-2025** (GST 2.0, 56th GST Council) [SECONDARY: [India Briefing](https://www.india-briefing.com/news/gst-cess-removal-india-2025-business-benefits-39879.html/), [CarDekho](https://www.cardekho.com/india-car-news/gst-rate-cut-for-cars-cess-removed-all-cars-to-get-cheaper-34975.htm)]:
- Small cars pay **18%**: petrol ≤1200 cc or diesel ≤1500 cc, and length ≤4 m.
- All other cars and SUVs pay **40%**.
- EVs pay **5%**.
- The compensation cess on cars was abolished.

Ex-showroom prices already include GST. Telangana charges life tax on top of that GST-inclusive price, so this is a tax on tax, which the courts have upheld.

---

## Part 3: Insurance

### 3.1 Third-party (TP) insurance: mandatory 3-year cover for a new car
- **Rule:** Motor Vehicles (Third Party Insurance Base Premium and Liability) Rules, 2022 (MoRTH with IRDAI), notified 25-05-2022 and **effective 01-06-2022**. The G.S.R. number is not verified.
- **Still current:** this is the **latest notified revision as of 19-10-2026**. Hikes of 10–25% were proposed in 2025–26 but have not been gazetted.
- **Sources:** [SECONDARY: [Moneylife](https://mas360.moneylife.in/article/government-notifies-increase-in-motor-third-party-insurance-premium-from-1st-june/4048.html), [SCC Online](https://www.scconline.com/blog/post/2022/05/26/base-premium-for-third-party-insurance-for-unlimited-liability-revised-vide-motor-vehicles-third-party-insurance-base-premium-and-liability-rules-2022/)]. The e-Gazette PDF would not download.

| Private car | 3-yr TP (new car) | 1-yr TP |
|---|---|---|
| ≤1000 cc | ₹6,521 | ₹2,094 |
| 1000–1500 cc | ₹10,640 | ₹3,416 |
| >1500 cc | ₹24,596 | ₹7,897 |

| Private EV car (motor kW) | 3-yr TP |
|---|---|
| ≤30 kW | ₹5,543 |
| 30–65 kW | ₹9,044 |
| >65 kW | ₹20,907 |

- **GST:** 18% GST is added on top of these premiums.
- **EV/hybrid discount:** one summary says the 2022 rules allow a 7.5% discount for EVs and hybrids. Other outlets conflict, so the examples **do not apply** it.

### 3.2 Compulsory personal accident (CPA) cover
- **Cover:** the owner-driver must have **₹15 lakh** cover (IRDAI 2018).
- **Premium:** set by each insurer, so `pa_cover_inr` = **null**.
- **Exception:** the cover can be skipped if the owner already has a PA policy of ₹15 lakh or more, or holds no driving licence.

### 3.3 Own-damage (OD) premium: **estimate only**
OD premiums have been set freely by insurers since 2007. Use this method:
1. **IDV** = ex-showroom × (1 − 5%). The 5% is depreciation for a car aged 6 months or less.
2. **Reference OD** = IDV × the rate in the table below.
3. Add **18% GST**.
4. **NCB = 0** for a new car, unless an NCB is transferred from an old car.

| Old India Motor Tariff rate, age ≤5 yrs | ≤1000 cc | 1000–1500 cc | >1500 cc |
|---|---|---|---|
| Zone A (incl. **Hyderabad**) | 3.127% | 3.283% | 3.440% |
| Zone B (rest of Telangana) | 3.039% | 3.191% | 3.343% |

- **Sources:** [SECONDARY: [Shriram GI](https://www.shriramgi.com/article/why-car-insurance-premiums-vary-across-regions), [Bajaj Allianz](https://bajajallianz.com/blog/motor-insurance-articles/why-vehicle-insurance-premiums-vary-from-city-to-city.html)].
- **Upper reference only:** real quotes are usually discounted from these rates. The typical discount range is **null** (not verified). Add-ons such as zero-dep, RSA and engine protect are optional.
- **EVs:** there is no official OD reference by kW. Using the >1500 cc band is an assumption.

---

## Part 4: TCS (tax collected at source)
- **Rule:** 1% when the sale value of the vehicle **exceeds ₹10,00,000**. At exactly ₹10 L, no TCS applies.
- **Law:** s.206C(1F) of the IT Act 1961 applied up to 31-03-2026. From **01-04-2026** it is s.394 of the **Income-tax Act 2025**, with the rate and threshold unchanged. Secondary sources cite the sub-section and table entry inconsistently.
- **Base:** the **whole** sale consideration, not just the part above ₹10 L. It is usually applied to the GST-inclusive dealer invoice. Road tax, registration and insurance are not part of the dealer's sale consideration. This is my interpretation and should be verified.
- **Not a real cost:** TCS is credited to the buyer's PAN (Form 26AS / AIS) and can be set off against income tax or refunded through the ITR. The calculator should show it **separately as refundable**.
- **Sources:** [SECONDARY: [TaxGuru 2026-27 chart](https://taxguru.in/income-tax/tcs-rate-chart-tax-year-2026-27-income-tax-act-2025.html), [TAXAJ](https://www.taxaj.com/learn/tcs-on-sale-of-motor-vehicle-above-10-lakh-seller-compliance/)].

## Part 5: FASTag and dealer add-ons
- **FASTag (car, VC4):** about ₹100 issuance fee (often waived) plus a **₹200 refundable deposit** plus any opening balance. The JSON uses **₹300** [SECONDARY: [BankBazaar](https://www.bankbazaar.com/driving-licence/fastag-charges.html); not verified on IHMCL]. FASTag is mandatory on new 4W. The ₹3,000 annual pass (from 15-08-2025) is optional and not part of the on-road price.
- **Not allowed / not statutory:**
  - **Handling, logistics, delivery, documentation or PDI charges:** a Telangana statewide dealer crackdown was reported on 01-07-2026, threatening refunds, trade-certificate suspension and prosecution ([NewsMeter](https://newsmeter.in/regional/telangana/telangana-cracks-down-on-vehicle-dealers-over-illegal-charges-missing-temporary-registration-770903)). The circular number was not found. Delhi, Kerala and Telangana also issued earlier notices ([Deccan Chronicle](https://www.deccanchronicle.com/nation/current-affairs/240216/benagluru-auto-dealers-continue-to-levy-handling-charges.html)).
  - **Separate HSRP charge:** not allowed, because the plate cost is included in the vehicle price.
- **Optional (dealers cannot make them compulsory):**
  - Extended warranty.
  - Accessory packs, "essential kits", coating and anti-rust.
  - Dealer-arranged insurance. You can buy from any insurer.

---

## Part 6: Worked examples (Hyderabad, individual, first vehicle, registered Oct 2026)

**Assumptions:**
- No dealer discount.
- Telangana tax = rate × ex-showroom (the GST-inclusive invoice).
- OD uses the Zone A tariff as an *upper reference*.
- CPA and add-ons are excluded because their premiums are null.
- Hypothecation (₹1,500) is added only if the car is financed.
- FASTag is ₹300.

### A. Hyundai Creta E 1.5 Petrol MT: ex-showroom ₹10,90,700 (input)
The price is from Hyundai India's Hyderabad price page (<https://www.hyundai.com/in/en/find-a-car/creta/price-in-hyderabad>) and Bajaj Finserv (Aug 2026). The engine is 1497 cc and the car is >4 m, so GST is 40%.

| Line | ₹ |
|---|---|
| Ex-showroom | 10,90,700 |
| Life tax 18% (₹10–20 L slab) | 1,96,326 |
| Road Safety Cess | 5,000 |
| Registration ₹600 + smart card ₹200 | 800 |
| HSRP | 0 (in price) |
| TP 3-yr (1000–1500 cc) ₹10,640 + 18% GST | 12,555 |
| **Statutory on-road (without OD)** | **13,05,381** |
| OD 1-yr estimate: IDV ₹10,36,165 × 3.283% = ₹34,017 + GST | ~40,140 (estimate, likely lower in real quotes) |
| FASTag | 300 |
| **On-road incl. OD estimate + FASTag** | **~13,45,821** |
| TCS 1% (refundable, collected by dealer) | 10,907 → cash outflow ~13,56,728 |
| + Hypothecation, if financed | 1,500 |

A second car in the same name pays 20%, which is ₹2,18,140, or +₹21,814. A company-owned car also pays 20%.

### B. ₹6 lakh hatchback (assumed 1197 cc petrol, ≤4 m)

| Line | ₹ |
|---|---|
| Ex-showroom | 6,00,000 |
| Life tax 14% | 84,000 |
| Road Safety Cess | 5,000 |
| Registration + smart card | 800 |
| TP 3-yr (1000–1500 cc) + GST | 12,555 |
| **Statutory on-road** | **7,02,355** |
| OD estimate (IDV ₹5,70,000 × 3.283% + GST) | ~22,081 |
| FASTag | 300 |
| **Total incl. OD estimate** | **~7,24,736** (no TCS: ≤ ₹10 L) |

### C. ₹25 lakh SUV (>1500 cc)

| Line | ₹ |
|---|---|
| Ex-showroom | 25,00,000 |
| Life tax 20% (₹20–50 L slab) | 5,00,000 |
| Road Safety Cess | 5,000 |
| Registration + smart card | 800 |
| TP 3-yr (>1500 cc) ₹24,596 + GST | 29,023 |
| **Statutory on-road** | **30,34,823** |
| OD estimate (IDV ₹23,75,000 × 3.440% + GST) | ~96,406 |
| FASTag | 300 |
| **Total incl. OD estimate** | **~31,31,529** |
| TCS 1% (refundable) | 25,000 |

### D. EV: ₹18 lakh, motor >65 kW (illustrative input), registered on or before 31-12-2026

| Line | ₹ |
|---|---|
| Ex-showroom (GST 5%) | 18,00,000 |
| Life tax | 0 (G.O.Ms.No.41) |
| Registration fee | 0 (G.O.41 / G.S.R. 525(E)) |
| Smart card | 200 (exemption not confirmed) |
| Road Safety Cess | 5,000 (applies unless exempt; exemption **null**) |
| TP 3-yr EV (>65 kW) ₹20,907 + GST | 24,670 |
| **Statutory on-road** | **18,29,870** |
| OD estimate (IDV ₹17,10,000 × 3.44% + GST) | ~69,412 |
| FASTag | 300 |
| **Total incl. OD estimate** | **~18,99,582** |
| TCS 1% (refundable) | 18,000 |

If the same EV is registered from 01-01-2027 and the exemption is not extended, it would pay 18%, which is ₹3,24,000, plus the ₹600 registration fee.

---

## Part 7: Other states and UTs (expansion table)

**Central rules that apply in every state** [OFFICIAL]:
- CMVR Rule 81: LMV registration ₹600, smart card ₹200, hypothecation ₹1,500.
- HSRP cost is included in the vehicle price.
- EVs are exempt from RC fees (G.S.R. 525(E)).

**State rules:** state service, postal and user charges are not verified for any state. Rates below are **[SECONDARY]** unless marked otherwise. Aggregators used: [motomotar (upd. 05-08-2026)](https://motomotar.com/car-buying-guide/rto-road-tax-by-state/) and [mycarhelpline (27-09-2026)](https://www.mycarhelpline.com/index.php?option=com_easyblog&view=entry&id=155&Itemid=91). The two often conflict with each other.

| State | Private car road tax (summary) | EV policy | Key sources |
|---|---|---|---|
| Karnataka | 13% (<5 L) / 14% (5–10 L) / 17% (10–20 L) / 18% (>20 L), + **11% cess on tax**, + **₹1,000 welfare cess** [OFFICIAL gazette, Karnataka Act 3 of 2025] | EV 4W now taxed: 5% ≤10 L, 8% 10–25 L, 10% >25 L from 01-04-2026; e-2W exempt | [KA schedule index](https://transport.karnataka.gov.in/36/motor-vehicles-taxation-schedule/en), [cess gazette](https://transport.karnataka.gov.in/storage/pdf-files/additionalcess.pdf), [Spinny](https://www.spinny.com/blog/road-tax-in-karnataka-applicability-calculation-payment-more/), [EVFY 06-04-2026](https://www.evfy.in/news/karnataka-ends-ev-tax-exemption--new-road-tax-slabs-explained-2026) |
| Tamil Nadu | 12% / 13% / 18% / 20% (bands <5 L, 5–10 L, 10–20 L, >20 L), from 09-11-2023 | 100% exemption extended 01-01-2026 to **31-12-2027** (order dt 29-12-2025) | [Taxscan](https://www.taxscan.in/tamil-nadu-implements-fresh-life-tax-rates-for-vehicles-from-november-9-2023/341232), [Business Today](https://www.businesstoday.in/personal-finance/news/story/breather-for-ev-buyers-full-road-tax-exemption-for-evs-in-tamil-nadu-extended-by-two-years-509022-2026-01-01) |
| Maharashtra | Petrol 11/12/13%, diesel 13/14/15%, CNG 8/9/10% (bands <10 L, 10–20 L, >20 L); company and imports 20% flat; cap ₹30 L; from 01-07-2025 | 100% exemption (to ~03-2030, EV Policy 2025); proposed 6% on >₹30 L EVs dropped | [Autocar](https://www.autocarindia.com/industry/new-car-prices-in-maharashtra-to-increase-with-amendments-to-motor-vehicles-tax-act-435960) |
| Delhi | Petrol/CNG 4/7/10% (≤6 L, 6–10 L, >10 L); diesel +25% [OFFICIAL note] = 5/8.75/12.5% | EV Policy 2026: 100% road tax + registration waiver for EVs ≤₹30 L, 01-07-2026 to 31-03-2030 | [Delhi transport](https://transport.delhi.gov.in/transport/tax-rate), [Business Standard](https://www.business-standard.com/amp/india-news/delhi-ev-policy-july-1-tax-waiver-subsidies-ev-only-rules-126062900692_1.html) |
| Andhra Pradesh | 12% ≤10 L / 14% >10 L (conflicting), + **10% Road Safety Cess on life tax** from 13-01-2026 [OFFICIAL] | 100% exemption reported to Dec 2029 | [AP Bill 14 of 2026](https://prsindia.org/files/bills_acts/bills_states/andhra-pradesh/2026/Bill14of2026AP.pdf) |
| Gujarat | 6% flat (reportedly on the pre-GST price); company rate unverified | 1% EV rate 18-04-2025 to 31-03-2026; status after that **null** | [News On AIR](https://www.newsonair.gov.in/gujarat-slashes-ev-motor-vehicle-tax-to-1-to-boost-green-mobility/) |
| Kerala | 10/13/15/17/22% by price (conflicting) | EV 5% ≤15 L, 8% 15–20 L, 10% >20 L (Budget Feb 2025) | [Business Standard](https://www.business-standard.com/industry/auto/kerala-shocks-electric-vehicle-buyers-raises-taxes-up-to-10-based-on-cost-125020701572_1.html) |
| West Bengal | ~10% lifetime, min ₹40,000 (conflicting with flat amounts by cc) | Exempt reported; validity **null** | [mycarhelpline](https://www.mycarhelpline.com/index.php?option=com_easyblog&view=entry&id=155&Itemid=91) |
| Uttar Pradesh | Conflicting (8%/10% vs 9%/11%), so set to **null** | 100% road tax + registration 14-10-2022 to 13-10-2027; from 14-10-2025 **only EVs made in UP** qualify | [The Statesman](https://www.thestatesman.com/business/up-grants-100-exemption-on-registration-fees-road-tax-for-electric-vehicle-purchases-till-october-2027-1503508414.html) |

The remaining states and UTs come from aggregators only. Their slabs are stored in the JSON as text notes, with `road_tax: null`:

| State / UT | Unverified summary |
|---|---|
| Assam | 4–14% plus 1% road safety cess. EV waiver under the 2021 policy, status unknown |
| Bihar | 8–12%. EV exempt |
| Chhattisgarh | 5–10%. EV figures conflict |
| Goa | 9/12/15% plus infra cess above ₹10 L. EV 100% |
| Haryana | 5/8/10%. EV figures conflict |
| Himachal Pradesh | 6% (≤15 L) / 7% (>15 L) plus 1% cess. EV exempt |
| Jharkhand | Conflicting, on pre-GST price. EV 100% to Oct 2027 |
| Madhya Pradesh | Petrol 8–14%, diesel 10–16%. EV conflicting |
| Manipur | 3–8% |
| Meghalaya | 4–10%. EV waiver lapsed |
| Mizoram | Flat amounts |
| Nagaland | 6% |
| Odisha | 6–12%. EV exempt |
| Punjab | ~10–13% plus ₹1,000 cow cess. EV 100% |
| Rajasthan | Engine-cc based, plus 12.5% surcharge. EV 100% to Aug 2027 |
| Sikkim | Low rates; the source table is malformed |
| Tripura | Flat amounts |
| Uttarakhand | 6–10% plus green tax. EV exempt |
| Chandigarh | Punjab-like rates. EVs and strong/plug-in hybrids exempt 18-03-2023 to 17-03-2028 ([Tribune](https://www.tribuneindia.com/news/chandigarh/no-road-tax-for-electric-hybrid-vehicles-in-city-511342/amp)) |
| Puducherry | 4/7/8% on pre-GST price |
| J&K | 9% from a J&K dealer, 12% from an outside dealer |
| Ladakh | 6% / 9% |
| Andaman & Nicobar | 6–8% |
| Dadra & Nagar Haveli and Daman & Diu | ~2.5–3% |
| Lakshadweep | 5.5% |
| Arunachal Pradesh | Nothing found |

### Coverage

| Coverage | States / UTs |
|---|---|
| **Verified (official)** | Telangana |
| **Partial** (some official items, or several consistent secondary sources) | Karnataka, Tamil Nadu, Maharashtra, Delhi, Andhra Pradesh, Gujarat, Kerala, West Bengal, Uttar Pradesh (UP road tax itself is null) |
| **Secondary only** (aggregator, unverified) | Assam, Bihar, Chhattisgarh, Goa, Haryana, Himachal Pradesh, Jharkhand, Madhya Pradesh, Manipur, Meghalaya, Mizoram, Nagaland, Odisha, Punjab, Rajasthan, Sikkim, Tripura, Uttarakhand, Chandigarh, Puducherry, J&K, Ladakh, Andaman & Nicobar, DNH & DD, Lakshadweep |
| **Not found** | Arunachal Pradesh |

## Part 8: Not verified / open items
1. **Telangana:**
   - Whether the 2% second-vehicle surcharge has been abolished (approved Feb 2026, no G.O. found).
   - Whether the EV exemption will be extended beyond 31-12-2026.
   - Whether EVs are exempt from the ₹5,000 Road Safety Cess.
   - The temporary registration fee, postal fee and service/user charges.
   - The text of G.O.Ms.No.41 and G.O.Ms.No.10 (both secondary).
2. **TP premiums:**
   - The G.S.R. number of the 2022 rules (e-Gazette PDF unreachable).
   - Whether the 7.5% EV/hybrid discount applies.
   - The 1-year TP premium for EVs.
3. **CPA:** there is no single premium figure.
4. **OD:** only tariff-era reference rates are available. Real discount levels are not verified.
5. **TCS:** whether the base includes GST is based on common practice, not a CBDT text I read. The exact s.394 sub-section is unconfirmed.
6. **FASTag:** fees are not confirmed on IHMCL/NHAI.
7. **GST 2.0 rates:** from secondary sources; the official notification was not read.
8. **Other states:** almost all state-level slabs are secondary, and most company and second-vehicle rates are unknown.
