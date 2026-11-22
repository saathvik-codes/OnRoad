import datetime as dt
import json

from onroad import resale


def _page(cars):
    items = [{"@type": "Car", "name": f"2020 Hyundai {n}", "vehicleModelDate": y, "offers": {"@type": "Offer", "price": p},
              "mileageFromOdometer": {"value": 40000}} for n, y, p in cars]
    return f'<script type="application/ld+json">{json.dumps({"@type": "ItemList", "itemListElement": items})}</script>'


def test_parse_keeps_only_this_model_and_sane_prices():
    html = _page([("Creta SX", 2021, 1200000), ("Venue S", 2021, 800000), ("Creta E", 2019, 5)])
    assert resale.parse_listings(html, "Creta") == [{"year": 2021, "km": 40000, "price": 1200000}]


def test_curve_falls_every_year_and_starts_below_new_price():
    today = dt.date(2026, 11, 22)
    listings = [{"year": 2025, "price": 1500000}, {"year": 2022, "price": 1150000}, {"year": 2019, "price": 850000}]
    c = resale.fit_curve(listings, 1700000, today)
    keep = [c["keep"][k] for k in ("1", "2", "3", "4", "5", "7")]
    assert keep == sorted(keep, reverse=True) and keep[0] < 0.92
    assert 3 < c["per_year_loss_pct"] < 20


def test_single_model_year_is_not_enough():
    assert resale.fit_curve([{"year": 2022, "price": 900000}] * 5, 1200000) is None
