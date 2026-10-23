// Typed client for the OnRoad API (proxied at /api by next.config rewrites; session is an httpOnly cookie).

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    credentials: "same-origin",
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
  });
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const b = await res.json();
      msg = typeof b.detail === "string" ? b.detail : Array.isArray(b.detail) ? b.detail.map((d: { msg: string }) => d.msg).join(", ") : msg;
    } catch { /* not json */ }
    throw new ApiError(res.status, msg);
  }
  return res.json() as Promise<T>;
}
export const fetcher = <T,>(p: string) => api<T>(p);

export type Brand = { slug: string; name: string; segment: "mass" | "premium" | "luxury"; vehicle_type?: string | null; website: string; logo: string | null;
  models: number; from_inr: number | null; dealers_here: number; offers: number; last_refresh: string | null; refresh_note?: string | null };

export type Line = { label: string; amount_inr: number | null; basis: string; source: string | null; verified: boolean; optional: boolean; refundable: boolean };
export type Breakdown = { state: string; state_name: string; coverage: string; refundable_inr: number;
  ex_showroom_inr: number; lines: Line[]; optional: Line[]; total_inr: number; complete: boolean;
  as_of: string | null; notes: string[]; price_city?: string; price_as_of?: string; price_source?: string };

export type Variant = { id: string; model_id: string; name: string; fuel: string | null; transmission: string | null; engine_cc: number | null;
  battery_kwh: number | null; seats: number | null; ex_showroom_inr: number | null; price_city: string | null; price_as_of: string | null;
  price_source: string | null; onroad?: Breakdown; image_url?: string | null };

export type Offer = { id: number; brand_slug: string; model_name: string | null; title: string; amount_inr: number | null; details: string;
  valid_until: string | null; city: string | null; source: "brand_site" | "dealer"; source_url: string | null; fetched_at: string; dealer_id: string | null;
  kind?: string | null; conditions?: string | null; variant?: string | null; days_left?: number | null; brand_name?: string; model_id?: string | null; model_image?: string | null };

export type Dealer = { id: string; brand_slug: string; name: string; address: string; city: string; state: string; pincode: string | null;
  phone: string | null; email: string | null; lat: number | null; lng: number | null; kind: string; website: string | null;
  source_url: string; distance_km?: number | null; claimed_by: number | null };

export type ModelSummary = { id: string; name: string; slug: string; brand_slug: string; brand: string; segment?: string; body_type: string | null;
  image_url: string | null; from_inr: number | null; to_inr: number | null; fuels: string | null; transmissions: string | null; variants?: number; offers: number; logo?: string | null;
  vehicle_type?: string | null; sales_rank?: number | null; six_month_units?: number | null };

export type DummyInjuryZone = { status: string; color: string; desc: string };

export type SafetyData = {
  tested: boolean;
  agency: string;
  stars: number;
  category: string;
  protocol: string;
  adult_score: string;
  child_score: string;
  bodyshell: string;
  test_speed_kmh: number;
  braking_distance_100_0?: string;
  video_url: string;
  video_title: string;
  video_duration: string;
  video_timestamps: { time: string; label: string }[];
  dummy_injury: Record<string, DummyInjuryZone>;
  active_safety_features: string[];
  videos?: VideoItem[];
};

export type VideoItem = {
  id: string;
  category: string;
  category_slug: string;
  title: string;
  badge: string;
  duration: string;
  resolution: string;
  thumbnail: string;
  video_url: string;
  timestamps: { time: string; label: string }[];
  highlights?: string[];
  telemetry?: { label: string; value: string; status?: "good" | "adequate" | "warning" }[];
};

export type PPFStudio = {
  name: string;
  location: string;
  rating: number;
  reviews_count: number;
  phone: string;
  specialty: string;
  packages: Record<string, string>;
};

export type ShowroomWatchout = {
  id: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM";
  badge: string;
  title: string;
  description: string;
  action_tip: string;
};

export type ShowroomInsights = {
  city: string;
  showroom_watchouts: ShowroomWatchout[];
  service_center_health: {
    avg_periodic_turnaround: string;
    off_the_shelf_spare_availability: string;
    customer_satisfaction_index: string;
    free_pickup_drop: string;
  };
  detailing_and_ppf: {
    title: string;
    description: string;
    studios: PPFStudio[];
    ppf_vs_ceramic_comparison: {
      type: string;
      thickness: string;
      stone_chip_protection: string;
      scratch_repair: string;
      durability: string;
      approx_cost: string;
      verdict: string;
    }[];
  };
};

export type ModelDetail = { id: string; name: string; slug: string; brand_slug: string; brand_name: string; body_type: string | null;
  url: string | null; image_url: string | null; logo: string | null; variants: Variant[]; dealers: Dealer[]; offers: Offer[];
  price_history: { variant_id: string; city: string; ex_showroom_inr: number; fetched_at: string }[];
  recent_dealer_quotes: { on_road_inr: number; discount_inr: number; created: string; dealer: string; variant: string }[];
  vehicle_type?: string;
  crash_tests?: CrashTest[];
  gallery?: { url: string; label: string; kind: "model" | "variant" | "feature" }[] };

export type CrashTest = { brand: string; model: string; variant_tested?: string | null; agency: string; protocol: string;
  test_date?: string | null; adult_stars?: number | null; child_stars?: number | null; adult_score?: number | null; adult_max?: number | null;
  child_score?: number | null; child_max?: number | null; airbags_tested?: string | null; notes?: string | null; source_url: string; video_url?: string | null; rating_published?: string | null };

export type Account = { id: number; email: string; name: string; phone: string | null; role: "buyer" | "dealer" | "admin" };

export type Meta = { rules_as_of: string | null; states_with_rules: string[]; last_refresh: string | null;
  counts: { brands: number; models: number; variants: number; dealers: number; offers: number } };
