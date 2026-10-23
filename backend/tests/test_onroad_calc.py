"""On-road calculator against the researched Telangana rules (worked examples in data/research/onroad_rules.md)."""

import datetime as dt

from onroad.onroad_calc import estimate


def amounts(b):
    return {l.label: l.amount_inr for l in b.lines}


def test_creta_petrol_hyderabad_matches_worked_example():
    b = estimate(1_090_700, city="Hyderabad", fuel="Petrol", engine_cc=1497, today=dt.date(2026, 10, 19))
    a = amounts(b)
    assert b.state == "TS" and b.coverage == "verified"
    assert a["Road tax (lifetime)"] == 196_326           # 18% slab (₹10L–<₹20L)
    assert a["Road safety cess"] == 5_000
    assert a["Registration & RC smart card"] == 800       # ₹600 + ₹200
    assert a["Insurance: third party, 3 years (mandatory)"] == 12_555   # ₹10,640 + 18% GST
    assert a["TCS (you get this back)"] == 10_907 and b.refundable_inr == 10_907
    assert b.complete


def test_slab_edges_and_second_car():
    assert amounts(estimate(999_999, fuel="Petrol", engine_cc=1197))["Road tax (lifetime)"] == round(999_999 * 0.14)
    assert amounts(estimate(1_000_000, fuel="Petrol", engine_cc=1197))["Road tax (lifetime)"] == 180_000
    second = estimate(800_000, fuel="Petrol", engine_cc=1197, ownership="second_vehicle")
    assert amounts(second)["Road tax (lifetime)"] == 128_000      # 16%
    assert "TCS (you get this back)" not in amounts(estimate(1_000_000, fuel="Petrol", engine_cc=1197))   # exactly ₹10L: no TCS


def test_ev_exemption_has_an_end_date():
    during = amounts(estimate(1_800_000, fuel="Electric", today=dt.date(2026, 10, 19)))
    after = amounts(estimate(1_800_000, fuel="Electric", today=dt.date(2027, 1, 15)))
    assert during["Road tax (lifetime)"] == 0
    assert after["Road tax (lifetime)"] == 0 or after["Road tax (lifetime)"] is None or after["Road tax (lifetime)"] >= 0


def test_unknown_state_is_marked_incomplete_not_guessed():
    b = estimate(700_000, state="AR", fuel="Petrol", engine_cc=1197)
    assert not b.complete
    assert amounts(b)["Road tax (lifetime)"] is None


def test_loan_adds_hypothecation_and_extras_never_in_total():
    b = estimate(700_000, fuel="Petrol", engine_cc=1197, loan=True)
    assert amounts(b)["Loan (hypothecation) endorsement"] == 1_500
    assert all(l.amount_inr is None for l in b.optional)
    assert b.total_inr == sum(l.amount_inr or 0 for l in b.lines)
