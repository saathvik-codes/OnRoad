"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import useSWR from "swr";
import { 
  ChevronRight, 
  Flame, 
  MapPin, 
  Tag, 
  Car, 
  Bike, 
  Layers, 
  SlidersHorizontal, 
  Filter, 
  CheckCircle2, 
  Search
} from "lucide-react";
import { fetcher, type Brand, type ModelSummary } from "@/lib/api";
import { lakh, range } from "@/lib/format";
import { BodyRow, BrandGrid } from "@/components/browse";
import { BIKE_BODY_TYPES, BODY_TYPES, BodyIcon } from "@/components/body-icons";
import { CarImage } from "@/components/car-image";
import { useCity, withCity } from "@/components/city";
import { Button, cn, Empty, Select, Skeleton } from "@/components/ui";
import { AdBanner } from "@/components/ad-banner";
import { RecommendationsModal } from "@/components/recommendations-modal";

type Model = ModelSummary & { sales_rank?: number | null; variants?: number; band?: string | null; vehicle_type?: string | null };
type Band = { id: string; label: string; hint: string };

const CAR_CATEGORIES = ["Hatchback", "Sedan", "SUV", "MUV", "Pickup", "Coupe", "Convertible"];
const BIKE_CATEGORIES = ["Commuter", "Scooter", "Cruiser", "Sports", "Adventure"];
const FUELS = ["Petrol", "Diesel", "CNG", "Electric", "Hybrid"];

const BIKE_BANDS = [
  { id: "commuter_bike", label: "Commuter", hint: "Under ₹1 Lakh" },
  { id: "daily_bike", label: "Premium Commuter", hint: "₹1–1.5 Lakh" },
  { id: "sport_bike", label: "Performance", hint: "₹1.5–2.5 Lakh" },
  { id: "cruiser_bike", label: "Touring & Cruiser", hint: "₹2.5–4 Lakh" },
  { id: "superbike", label: "Superbike", hint: "Above ₹4 Lakh" },
];

function useQueryState() {
  const sp = useSearchParams();
  const router = useRouter();
  
  // If user navigated here for bikes, immediately route to dedicated /bikes page
  if (typeof window !== "undefined" && sp.get("vehicle_type") === "bike") {
    router.replace("/bikes");
  }

  const set = (k: string, v: string) => {
    const n = new URLSearchParams(sp.toString());
    if (v) n.set(k, v); else n.delete(k);
    router.replace(`/cars${n.toString() ? `?${n}` : ""}`, { scroll: false });
  };
  return { sp, set };
}

function CarsHeaderControls({ onOpenAdvisor }: { onOpenAdvisor: () => void }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-4">
      <div>
        <h1 className="font-[family-name:var(--font-display)] text-3xl sm:text-5xl font-bold text-ink">
          Explore Cars in India
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-mute">
          Official manufacturer ex-showroom prices and authentic Indian state road tax calculations.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={onOpenAdvisor}
          className="border-line bg-panel-soft text-ink hover:border-accent hover:text-accent gap-2 h-10 px-4 text-xs sm:text-sm font-medium shadow-xs"
        >
          <SlidersHorizontal className="h-4 w-4 text-accent" />
          <span>Vehicle Match Finder</span>
        </Button>
      </div>
    </div>
  );
}

function BrandFilterStrip({ 
  selectedBrand, 
  onSelectBrand, 
  vehicleType 
}: { 
  selectedBrand: string; 
  onSelectBrand: (b: string) => void; 
  vehicleType: string;
}) {
  const { city } = useCity();
  const url = withCity(`/brands${vehicleType ? `?vehicle_type=${encodeURIComponent(vehicleType)}` : ""}`, city);
  const { data: brands } = useSWR<Brand[]>(url, fetcher);
  const activeBrands = (brands ?? []).filter((b) => b.models > 0);

  if (!brands || brands.length === 0) return null;

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-mute">
          Filter by Manufacturer ({activeBrands.length})
        </span>
        {selectedBrand && (
          <button 
            onClick={() => onSelectBrand("")}
            className="text-xs text-accent hover:underline"
          >
            Clear brand filter
          </button>
        )}
      </div>
      <div className="flex items-center gap-2 overflow-x-auto pb-1.5 no-scrollbar">
        <button
          onClick={() => onSelectBrand("")}
          className={cn(
            "flex shrink-0 items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-medium transition",
            !selectedBrand ? "border-accent bg-accent text-white" : "border-white/10 bg-panel text-mute hover:text-white"
          )}
        >
          All Brands
        </button>
        {activeBrands.map((b) => {
          const isSelected = selectedBrand === b.slug;
          return (
            <button
              key={b.slug}
              onClick={() => onSelectBrand(b.slug)}
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-medium transition cursor-pointer",
                isSelected 
                  ? "border-accent bg-accent/15 text-ink shadow-xs font-semibold" 
                  : "border-line bg-panel text-mute hover:border-line/80 hover:text-ink"
              )}
            >
              {b.logo && (
                <span className="grid h-4 w-6 place-items-center rounded bg-white p-0.5 border border-line">
                  <img src={b.logo} alt="" className="max-h-3 w-auto object-contain" />
                </span>
              )}
              <span>{b.name}</span>
              <span className="opacity-60 text-[10px]">({b.models})</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Crumbs({ brand }: { brand?: Brand }) {
  return (
    <nav className="flex items-center gap-1.5 text-xs sm:text-sm text-mute">
      <Link href="/cars" className="hover:text-ink transition">Catalogue</Link>
      {brand && (
        <>
          <ChevronRight className="h-3.5 w-3.5" />
          <span className="text-ink font-medium">{brand.name}</span>
        </>
      )}
    </nav>
  );
}

function ModelCard({ m, showBrand }: { m: Model; showBrand?: boolean }) {
  return (
    <Link 
      href={`/cars/${m.id}`} 
      className="group flex flex-col justify-between overflow-hidden rounded-3xl border border-line bg-panel transition hover:-translate-y-1 hover:border-accent/40 hover:shadow-xl"
    >
      <div>
        <div className="relative aspect-[16/10] bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.08),transparent_70%)] overflow-hidden">
          <CarImage src={m.image_url} alt={`${m.brand} ${m.name}`} bodyType={m.body_type} />
          {m.sales_rank && m.sales_rank <= 25 && (
            <span className="absolute right-3 top-3 inline-flex items-center gap-1 rounded-full bg-accent/90 px-2 py-0.5 text-[11px] font-semibold text-white shadow-sm">
              <Flame className="h-3 w-3" />#{m.sales_rank} in India
            </span>
          )}
        </div>
        <div className="p-4 sm:p-5">
          {showBrand && <p className="text-xs font-medium text-mute">{m.brand}</p>}
          <p className="font-[family-name:var(--font-display)] text-lg sm:text-xl font-bold text-ink group-hover:text-accent transition">
            {m.name}
          </p>
          <p className="mt-1 font-mono text-sm sm:text-base font-semibold text-ink">
            {range(m.from_inr, m.to_inr)}
          </p>
          <div className="mt-3 flex flex-wrap gap-1.5 text-xs text-mute">
            {m.body_type && (
              <span className="rounded-full bg-panel-soft border border-line px-2 py-0.5 text-[11px] text-ink">{m.body_type}</span>
            )}
            {m.variants ? (
              <span className="rounded-full bg-panel-soft border border-line px-2 py-0.5 text-[11px] text-ink">{m.variants} variants</span>
            ) : null}
            {(m.fuels ?? "").split(",").filter(Boolean).map((f) => (
              <span key={f} className="rounded-full bg-panel-soft border border-line px-2 py-0.5 text-[11px] text-ink">{f}</span>
            ))}
            {m.offers > 0 && (
              <span className="inline-flex items-center gap-1 rounded-full bg-good/10 px-2 py-0.5 text-[11px] font-medium text-good">
                <Tag className="h-3 w-3" />{m.offers} offer{m.offers > 1 ? "s" : ""}
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="px-4 sm:px-5 pb-4 pt-1 border-t border-line flex items-center justify-between text-xs text-mute">
        <span>Official ex-showroom prices</span>
        <span className="font-semibold text-accent group-hover:underline">View On-Road &rarr;</span>
      </div>
    </Link>
  );
}

/** Step 1: Pick a brand with shortcuts by vehicle type, budget, and body type. */
function ChooseBrand({ onOpenAdvisor }: { onOpenAdvisor: () => void }) {
  const { sp, set } = useQueryState();
  const vt = "car";
  const { data: bands } = useSWR<Band[]>("/bands", fetcher);

  return (
    <main className="mx-auto max-w-7xl px-4 sm:px-6 pb-24 pt-24 sm:pt-28">
      <Crumbs />

      {/* Top Header & Car Advisor */}
      <div className="mt-4">
        <CarsHeaderControls onOpenAdvisor={onOpenAdvisor} />
      </div>

      <div className="mt-8">
        <BrandGrid vehicleType="car" />
      </div>

      {/* Budget Shortcuts */}
      <h2 className="mt-14 font-[family-name:var(--font-display)] text-xl sm:text-2xl font-bold text-ink">
        Shop Cars by Budget
      </h2>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {(bands ?? []).map((b) => (
          <Link 
            key={b.id} 
            href={`/cars?band=${b.id}`} 
            className="rounded-2xl border border-line bg-panel p-4 transition hover:border-accent/60 shadow-sm"
          >
            <p className="font-semibold text-ink text-sm">{b.label}</p>
            <p className="text-xs text-mute mt-0.5">{b.hint}</p>
          </Link>
        ))}
      </div>

      <div className="mt-10">
        <AdBanner />
      </div>

      {/* Body Type Shortcuts */}
      <h2 className="mt-12 mb-4 font-[family-name:var(--font-display)] text-xl sm:text-2xl font-bold text-ink">
        Shop Cars by Body Style
      </h2>
      <BodyRow vehicleType="car" />
    </main>
  );
}

/** Step 2: One brand's line-up, grouped by category. */
function BrandLineup({ slug, onOpenAdvisor }: { slug: string; onOpenAdvisor: () => void }) {
  const { sp, set } = useQueryState();
  const cat = sp.get("body") ?? "";
  const vt = sp.get("vehicle_type") ?? "";
  const { city } = useCity();
  const { data: brands } = useSWR<Brand[]>(withCity("/brands", city), fetcher);
  const { data } = useSWR<Model[]>(withCity(`/explore?brand=${slug}&sort=popular`, city), fetcher);
  
  const brand = brands?.find((b) => b.slug === slug || b.slug.replace(/_/g, "-") === slug || b.slug === slug.replace(/-/g, "_"));
  const isBikeBrand = brand?.vehicle_type === "bike";
  const categoryOrder = isBikeBrand ? BIKE_CATEGORIES : CAR_CATEGORIES;

  const groups = useMemo(() => {
    const g = new Map<string, Model[]>();
    for (const m of data ?? []) {
      const k = m.body_type ?? "Standard";
      g.set(k, [...(g.get(k) ?? []), m]);
    }
    const rank = (k: string) => (categoryOrder.includes(k) ? categoryOrder.indexOf(k) : 99);
    return [...g.entries()].sort((a, b) => rank(a[0]) - rank(b[0]));
  }, [data, categoryOrder]);

  const shown = cat ? groups.filter(([k]) => k === cat) : groups;
  const priced = (data ?? []).map((m) => m.from_inr).filter(Boolean) as number[];
  const tops = (data ?? []).map((m) => m.to_inr).filter(Boolean) as number[];

  return (
    <main className="mx-auto max-w-7xl px-4 sm:px-6 pb-24 pt-24 sm:pt-28">
      <Crumbs brand={brand} />

      {/* Brand Header */}
      <div className="mt-5 flex flex-wrap items-center gap-5 sm:gap-6">
        <span className="grid h-20 w-28 sm:h-24 sm:w-32 place-items-center rounded-3xl bg-white p-3 shadow-md">
          {brand?.logo ? (
            <img src={brand.logo} alt={brand.name} className="max-h-12 sm:max-h-14 w-auto object-contain" />
          ) : (
            <span className="font-semibold text-black text-sm">{brand?.name}</span>
          )}
        </span>
        <div>
          <h1 className="font-[family-name:var(--font-display)] text-3xl sm:text-5xl lg:text-6xl font-bold text-ink">
            {brand?.name ?? "..."}
          </h1>
          <p className="mt-1.5 text-xs sm:text-sm text-mute">
            {data ? `${data.length} models listed` : "..."}
            {priced.length ? ` · ${lakh(Math.min(...priced))} – ${lakh(Math.max(...tops, ...priced)).replace("₹", "")}` : ""}
            {brand?.dealers_here ? (
              <> · <MapPin className="inline h-3.5 w-3.5 text-accent" /> {brand.dealers_here} showroom{brand.dealers_here > 1 ? "s" : ""} in {city}</>
            ) : null}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={onOpenAdvisor} className="border-line bg-panel-soft text-ink hover:border-accent hover:text-accent gap-1.5 text-xs h-9 font-medium shadow-xs">
            <SlidersHorizontal className="h-3.5 w-3.5 text-accent" /> Car Match Advisor
          </Button>
          <Link href="/cars" className="text-xs sm:text-sm text-accent hover:underline">
            Change manufacturer
          </Link>
        </div>
      </div>

      {/* Category Pills */}
      {groups.length > 1 && (
        <div className="mt-6 flex gap-2 overflow-x-auto pb-1.5 no-scrollbar">
          <button 
            onClick={() => set("body", "")} 
            className={cn(
              "shrink-0 rounded-full border px-4 py-1.5 text-xs sm:text-sm transition font-medium", 
              !cat ? "border-accent bg-accent text-white" : "border-line bg-panel text-mute hover:text-ink hover:border-line/80"
            )}
          >
            All <span className="opacity-70">({data?.length})</span>
          </button>
          {groups.map(([k, ms]) => (
            <button 
              key={k} 
              onClick={() => set("body", k)} 
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-full border px-3.5 py-1.5 text-xs sm:text-sm transition font-medium",
                cat === k ? "border-accent bg-accent text-white" : "border-line bg-panel text-mute hover:text-ink hover:border-line/80"
              )}
            >
              <BodyIcon type={k} className="h-4 w-6" />
              <span>{k}</span>
              <span className="opacity-70">({ms.length})</span>
            </button>
          ))}
        </div>
      )}

      {/* Grid of Models */}
      {!data ? (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-72 rounded-3xl" />)}
        </div>
      ) : data.length === 0 ? (
        <div className="mt-8">
          <Empty title={`No ${brand?.name ?? ""} models listed yet`}>
            Manufacturer price lists for {city} are being updated.
          </Empty>
        </div>
      ) : (
        shown.map(([k, ms]) => (
          <section key={k} className="mt-10">
            <h2 className="flex items-center gap-2.5 font-[family-name:var(--font-display)] text-xl sm:text-2xl font-bold text-ink mb-4">
              <BodyIcon type={k} className="h-5 w-8 text-accent" />
              <span>{k === "Other" || k === "Standard" ? k : `${k}s`}</span>
              <span className="text-sm font-normal text-mute">({ms.length})</span>
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {ms.map((m) => <ModelCard key={m.id} m={m} />)}
            </div>
          </section>
        ))
      )}
    </main>
  );
}

/** Filtered view across all brands (budget / body / fuel / search / vehicle_type). */
function Filtered({ onOpenAdvisor }: { onOpenAdvisor: () => void }) {
  const { sp, set } = useQueryState();
  const band = sp.get("band") ?? "";
  const body = sp.get("body") ?? "";
  const fuel = sp.get("fuel") ?? "";
  const brand = sp.get("brand") ?? "";
  const vt = "car";
  const sort = sp.get("sort") ?? "popular";
  const q = sp.get("q") ?? "";

  const apiQ = new URLSearchParams(
    Object.entries({ band, body, fuel, brand, vehicle_type: vt, sort }).filter(([, v]) => v)
  ).toString();

  const { city } = useCity();
  const { data } = useSWR<Model[]>(withCity(`/explore?${apiQ}`, city), fetcher);
  const { data: bands } = useSWR<Band[]>("/bands", fetcher);

  const items = useMemo(
    () => (data ?? []).filter((m) => !q || `${m.brand} ${m.name}`.toLowerCase().includes(q.toLowerCase())),
    [data, q]
  );

  const activeCategories = CAR_CATEGORIES;
  const activeBands = bands ?? [];

  const title = q
    ? `Results for “${q}”`
    : brand
    ? `${brand} Cars`
    : band
    ? activeBands.find((b) => b.id === band)?.label ?? "Budget"
    : body
    ? `${body}s`
    : fuel
    ? `${fuel} Cars`
    : "All Cars";

  return (
    <main className="mx-auto max-w-7xl px-4 sm:px-6 pb-24 pt-24 sm:pt-28">
      <Crumbs />

      {/* Top Header & Car Advisor */}
      <div className="mt-4">
        <CarsHeaderControls onOpenAdvisor={onOpenAdvisor} />
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-[family-name:var(--font-display)] text-2xl sm:text-4xl lg:text-5xl font-bold text-ink">
            {title}
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-mute">
            {data ? `${items.length} models match your filters in ${city}` : "Filtering..."}
          </p>
        </div>
        {brand && (
          <Button size="sm" variant="outline" onClick={() => set("brand", "")} className="text-xs">
            Clear brand filter ({brand})
          </Button>
        )}
      </div>

      {/* Horizontal Brand Filter Strip */}
      <BrandFilterStrip 
        selectedBrand={brand} 
        onSelectBrand={(b) => set("brand", b)} 
        vehicleType={vt} 
      />

      {/* Budget Pills */}
      <div className="mt-5 flex gap-2 overflow-x-auto pb-1.5 no-scrollbar">
        <button
          onClick={() => set("band", "")}
          className={cn(
            "shrink-0 rounded-full border px-3.5 py-1.5 text-xs sm:text-sm transition cursor-pointer font-medium",
            !band ? "border-accent bg-accent text-white shadow-xs" : "border-line bg-panel text-mute hover:text-ink hover:border-line/80"
          )}
        >
          All Budgets
        </button>
        {activeBands.map((b) => (
          <button
            key={b.id}
            onClick={() => set("band", b.id)}
            className={cn(
              "shrink-0 rounded-full border px-3.5 py-1.5 text-xs sm:text-sm transition cursor-pointer font-medium",
              band === b.id ? "border-accent bg-accent text-white shadow-xs" : "border-line bg-panel text-mute hover:text-ink hover:border-line/80"
            )}
          >
            {b.label} <span className="opacity-65 text-[11px]">· {b.hint}</span>
          </button>
        ))}
      </div>

      {/* Secondary Dropdown Filters */}
      <div className="mt-4 grid gap-3 grid-cols-2 sm:grid-cols-3">
        <Select value={body} onChange={(e) => set("body", e.target.value)} className="h-9 text-xs">
          <option value="">All Body Styles</option>
          {activeCategories.map((b) => <option key={b} value={b}>{b}</option>)}
        </Select>

        <Select value={fuel} onChange={(e) => set("fuel", e.target.value)} className="h-9 text-xs">
          <option value="">All Fuel Types</option>
          {FUELS.map((f) => <option key={f} value={f}>{f}</option>)}
        </Select>

        <Select value={sort} onChange={(e) => set("sort", e.target.value)} className="col-span-2 sm:col-span-1 h-9 text-xs">
          <option value="popular">Most Popular in India</option>
          <option value="price">Lowest Price First</option>
          <option value="offers">Most Showroom Offers</option>
        </Select>
      </div>

      {/* Grid of Results */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {!data ? (
          [0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-72 rounded-3xl" />)
        ) : (
          items.map((m) => <ModelCard key={m.id} m={m} showBrand />)
        )}
      </div>

      {data && items.length === 0 && (
        <div className="mt-8">
          <Empty title="No vehicles match these filters">
            Try adjusting your budget, fuel type, or <button onClick={() => { set("band", ""); set("body", ""); set("fuel", ""); set("brand", ""); }} className="text-accent underline">reset all filters</button>.
          </Empty>
        </div>
      )}
    </main>
  );
}

function CarsInner() {
  const sp = useSearchParams();
  const [advisorOpen, setAdvisorOpen] = useState(false);
  // "Find my car" on the home page links here with ?finder=1: open the profile-based finder straight away
  const finderParam = useSearchParams().get("finder") === "1";
  const [finderSeen, setFinderSeen] = useState(false);
  if (finderParam && !finderSeen && !advisorOpen) { setFinderSeen(true); setAdvisorOpen(true); }
  const brand = sp.get("brand");
  const vt = sp.get("vehicle_type") ?? "car";

  const isFiltered = ["band", "body", "fuel", "q", "sort", "vehicle_type"].some((k) => sp.get(k));

  return (
    <>
      {brand ? (
        <BrandLineup slug={brand} onOpenAdvisor={() => setAdvisorOpen(true)} />
      ) : isFiltered ? (
        <Filtered onOpenAdvisor={() => setAdvisorOpen(true)} />
      ) : (
        <ChooseBrand onOpenAdvisor={() => setAdvisorOpen(true)} />
      )}

      {/* Customer Profile Recommendations Modal */}
      <RecommendationsModal
        isOpen={advisorOpen}
        onClose={() => setAdvisorOpen(false)}
        defaultVehicleType={vt === "bike" ? "bike" : "car"}
      />
    </>
  );
}

export default function CarsPage() {
  return (
    <Suspense fallback={<main className="mx-auto max-w-7xl px-5 pt-28"><Skeleton className="h-[60vh] rounded-3xl" /></main>}>
      <CarsInner />
    </Suspense>
  );
}
