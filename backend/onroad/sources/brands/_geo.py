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
