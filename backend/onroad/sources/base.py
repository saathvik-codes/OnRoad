"""
Contract every brand data source implements.

A brand adapter reads ONLY the manufacturer's own public website / public JSON endpoints (never aggregators such as
CarDekho, CarWale, ZigWheels, V3Cars, Autocar, whose terms forbid scraping). Each record keeps its source URL and the
time it was read, so every number shown to a buyer can be traced.

Adapters live in onroad/sources/brands/<brand_slug>.py and expose a module-level ADAPTER = <subclass of BrandAdapter>().
Each method may raise NotSupported when the brand's site does not publish that data.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field

import httpx

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36 "
              "OnRoadBot/0.1 (+price research; low frequency)")


class NotSupported(Exception):
    """The brand's own site does not publish this data (say so instead of guessing)."""


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


@dataclass
class Variant:
    model: str                      # "Creta"
    variant: str                    # "SX(O) 1.5 Turbo DCT"
    fuel: str                       # Petrol | Diesel | CNG | Electric | Hybrid | Strong Hybrid
    transmission: str               # Manual | Automatic | AMT | DCT | CVT | iMT
    ex_showroom_inr: int            # rupees, as published for `city`
    city: str                       # city the price applies to ("Hyderabad", or "Delhi" if the site has one national list)
    source_url: str
    fetched_at: str = field(default_factory=now)
    body_type: str | None = None    # Hatchback | Sedan | SUV | MUV | Pickup | Coupe | Convertible
    engine_cc: int | None = None
    battery_kwh: float | None = None
    seats: int | None = None
    model_url: str | None = None
    image_url: str | None = None


@dataclass
class Dealer:
    name: str
    address: str
    city: str
    state: str
    pincode: str | None
    phone: str | None
    email: str | None
    lat: float | None
    lng: float | None
    kind: str                       # sales | service | sales+service
    source_url: str
    website: str | None = None
    fetched_at: str = field(default_factory=now)


@dataclass
class Offer:
    model: str
    title: str                      # "Cash discount" / "Exchange bonus" / "Corporate offer"
    amount_inr: int | None          # None when the site states a benefit without a number
    details: str
    valid_until: str | None
    city: str | None
    source_url: str
    fetched_at: str = field(default_factory=now)
    # cash | exchange | scrappage | corporate | loyalty | finance | accessories | insurance | warranty | other
    kind: str | None = None
    conditions: str | None = None   # eligibility / terms exactly as the brand states them (e.g. "on exchange of any car")
    valid_from: str | None = None   # ISO date when the brand states a start date
    variant: str | None = None      # when the offer applies to specific variants only


# Canonical equipment keys (the web app has an explanatory illustration for each). Use these exact keys.
FEATURE_KEYS = {
    # safety
    "airbags_2", "airbags_6", "esc", "hill_hold", "tpms", "isofix", "rear_parking_sensors", "front_parking_sensors", "rear_camera",
    "camera_360", "adas", "blind_spot_monitor", "rear_disc_brakes", "auto_headlamps", "rain_sensing_wipers", "electric_parking_brake",
    # tech
    "touchscreen", "digital_cluster", "android_auto_carplay", "wireless_android_auto_carplay", "connected_car", "wireless_charger",
    "premium_audio", "hud", "cruise_control", "keyless_entry", "push_button_start", "remote_start",
    # comfort
    "auto_climate", "rear_ac_vents", "ventilated_seats", "powered_driver_seat", "sunroof", "panoramic_sunroof", "ambient_lighting",
    "cooled_glovebox", "rear_armrest", "height_adjustable_seat",
    # styling
    "led_headlamps", "led_drl", "alloy_wheels", "fog_lamps", "roof_rails",
    # two-wheelers
    "abs_dual", "abs_single", "cbs", "front_disc", "tft_display", "bluetooth_console", "usb_charging", "traction_control",
    "ride_modes", "slipper_clutch", "led_lamps_2w",
}


@dataclass
class Spec:
    """One published specification value for one variant, e.g. ("Engine", "max_power", "Max power", "113 bhp @ 6300 rpm")."""
    model: str
    variant: str
    fuel: str | None
    transmission: str | None
    group: str                      # Engine | Performance | Dimensions | Capacity | Efficiency | Battery | Chassis
    key: str                        # max_power | max_torque | mileage_arai | range | fuel_tank | boot_space | length | ...
    label: str                      # as shown to buyers
    value: str                      # exactly as the manufacturer states it (units included)
    source_url: str
    fetched_at: str = field(default_factory=now)


@dataclass
class Feature:
    """A piece of equipment the manufacturer lists as standard on one variant."""
    model: str
    variant: str
    fuel: str | None
    transmission: str | None
    key: str                        # one of FEATURE_KEYS, or "other"
    label: str                      # the manufacturer's own wording
    source_url: str
    fetched_at: str = field(default_factory=now)


class BrandAdapter:
    brand: str = ""                 # "Hyundai"
    slug: str = ""                  # "hyundai"
    website: str = ""

    def client(self) -> httpx.Client:
        return httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-IN"})

    def models(self) -> list[dict]:
        """[{name, url, body_type, image_url}] currently on sale in India."""
        raise NotSupported

    def prices(self, city: str = "Hyderabad") -> list[Variant]:
        """Every variant's ex-showroom price for `city` (or the single national list, with city set accordingly)."""
        raise NotSupported

    def dealers(self, city: str = "Hyderabad") -> list[Dealer]:
        """Sales outlets from the brand's official dealer locator."""
        raise NotSupported

    def offers(self, city: str = "Hyderabad") -> list[Offer]:
        """Current offers published on the brand's own site."""
        raise NotSupported

    def specs(self) -> tuple[list[Spec], list[Feature]]:
        """Specifications and standard equipment per variant, from the brand's own spec sheets / brochures / spec APIs."""
        raise NotSupported


def as_dicts(items) -> list[dict]:
    return [asdict(i) for i in items]
