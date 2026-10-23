"""City -> (state, lat, lng) for dealer locators that search by coordinates (as their Google-Places box does).
City-centre coordinates only; not brand data. Not a brand adapter (no ADAPTER)."""

CITY_GEO = {
    "hyderabad": ("Telangana", 17.385044, 78.486671),
    "secunderabad": ("Telangana", 17.439930, 78.498276),
    "bengaluru": ("Karnataka", 12.971599, 77.594566),
    "bangalore": ("Karnataka", 12.971599, 77.594566),
    "mumbai": ("Maharashtra", 19.076090, 72.877426),
    "pune": ("Maharashtra", 18.520430, 73.856743),
    "chennai": ("Tamil Nadu", 13.082680, 80.270721),
    "kolkata": ("West Bengal", 22.572645, 88.363892),
    "delhi": ("Delhi", 28.613939, 77.209023),
    "new delhi": ("Delhi", 28.613939, 77.209023),
    "ahmedabad": ("Gujarat", 23.022505, 72.571365),
    "jaipur": ("Rajasthan", 26.912434, 75.787270),
    "lucknow": ("Uttar Pradesh", 26.846694, 80.946166),
    "kochi": ("Kerala", 9.931233, 76.267304),
    "visakhapatnam": ("Andhra Pradesh", 17.686815, 83.218483),
    "vijayawada": ("Andhra Pradesh", 16.506174, 80.648015),
    "chandigarh": ("Chandigarh", 30.733315, 76.779419),
    "gurugram": ("Haryana", 28.459497, 77.026638),
    "noida": ("Uttar Pradesh", 28.535517, 77.391029),
    "indore": ("Madhya Pradesh", 22.719568, 75.857727),
    "nagpur": ("Maharashtra", 21.145800, 79.088158),
    "coimbatore": ("Tamil Nadu", 11.016844, 76.955833),
}


def geo(city: str):
    return CITY_GEO.get((city or "").strip().lower())


# ---- sanity check for dealer coordinates published by brand locators ---------------------------------------------
# India Post PIN prefixes -> state (first 3 digits override the 2-digit ones), and rough state bounding boxes.
_PIN3 = {"403": "Goa", "160": "Chandigarh", "737": "Sikkim", "744": "Andaman and Nicobar Islands", "605": "Puducherry",
         **{p: "Uttarakhand" for p in ("244", "246", "247", "248", "249", "262", "263")},
         **{p: "Jharkhand" for p in ("814", "815", "816", "822", "825", "826", "827", "828", "829", "831", "832", "833", "834", "835")}}
_PIN2 = {"11": "Delhi", "12": "Haryana", "13": "Haryana", "14": "Punjab", "15": "Punjab", "16": "Punjab", "17": "Himachal Pradesh",
         "18": "Jammu and Kashmir", "19": "Jammu and Kashmir", **{str(p): "Uttar Pradesh" for p in range(20, 29)},
         **{str(p): "Rajasthan" for p in range(30, 35)}, **{str(p): "Gujarat" for p in range(36, 40)},
         **{str(p): "Maharashtra" for p in range(40, 45)}, **{str(p): "Madhya Pradesh" for p in range(45, 49)}, "49": "Chhattisgarh",
         "50": "Telangana", "51": "Andhra Pradesh", "52": "Andhra Pradesh", "53": "Andhra Pradesh",
         **{str(p): "Karnataka" for p in range(56, 60)}, **{str(p): "Tamil Nadu" for p in range(60, 65)},
         **{str(p): "Kerala" for p in range(67, 70)}, **{str(p): "West Bengal" for p in range(70, 75)},
         **{str(p): "Odisha" for p in range(75, 78)}, "78": "Assam", **{str(p): "Bihar" for p in range(80, 86)}}
_BOX = {"Andhra Pradesh": (12.6, 19.9, 76.7, 84.8), "Telangana": (15.8, 19.95, 77.2, 81.4), "Karnataka": (11.5, 18.5, 74.0, 78.6),
        "Tamil Nadu": (8.0, 13.6, 76.2, 80.4), "Kerala": (8.2, 12.8, 74.8, 77.5), "Maharashtra": (15.6, 22.1, 72.6, 80.9),
        "Gujarat": (20.1, 24.7, 68.1, 74.5), "Rajasthan": (23.0, 30.2, 69.4, 78.3), "Madhya Pradesh": (21.0, 26.9, 74.0, 82.9),
        "Chhattisgarh": (17.7, 24.1, 80.2, 84.4), "Uttar Pradesh": (23.8, 30.5, 77.0, 84.7), "Uttarakhand": (28.7, 31.5, 77.5, 81.1),
        "Bihar": (24.3, 27.6, 83.3, 88.3), "Jharkhand": (21.9, 25.4, 83.3, 87.9), "West Bengal": (21.5, 27.3, 85.8, 89.9),
        "Odisha": (17.8, 22.6, 81.3, 87.5), "Assam": (24.1, 28.0, 89.7, 96.1), "Punjab": (29.5, 32.6, 73.8, 77.0),
        "Haryana": (27.6, 31.0, 74.4, 77.6), "Delhi": (28.4, 28.9, 76.8, 77.4), "Himachal Pradesh": (30.3, 33.3, 75.5, 79.0),
        "Jammu and Kashmir": (32.2, 37.1, 73.2, 80.3), "Goa": (14.8, 15.9, 73.6, 74.4), "Chandigarh": (30.6, 30.8, 76.6, 76.9)}


def pin_state(pin: str | None) -> str | None:
    p = (pin or "").strip()
    if len(p) != 6 or not p.isdigit():
        return None
    return _PIN3.get(p[:3]) or _PIN2.get(p[:2])


def coords_ok(pin: str | None, lat: float | None, lng: float | None) -> bool:
    """False when a dealer's published coordinates fall outside the state its PIN code belongs to (a data-entry slip
    on the brand's site); True when they fit or the state can't be checked."""
    if lat is None or lng is None:
        return False
    box = _BOX.get(pin_state(pin) or "")
    if not box:
        return 6 <= lat <= 37.5 and 68 <= lng <= 97.5
    a, b, c, d = box
    return a - 0.3 <= lat <= b + 0.3 and c - 0.3 <= lng <= d + 0.3
