"use client";

import { useState, useMemo, useEffect } from "react";
import Link from "next/link";
import useSWR from "swr";
import { 
  X, 
  Car, 
  Bike, 
  SlidersHorizontal,
  CheckCircle2, 
  ArrowRight, 
  ShieldCheck, 
  AlertTriangle,
  RotateCcw,
  Fuel,
  Gauge,
  Users,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { fetcher, type Brand } from "@/lib/api";
import { inr, lakh } from "@/lib/format";
import { useCity, withCity } from "@/components/city";
import { Button, cn, Skeleton } from "@/components/ui";
import { CarImage } from "@/components/car-image";

export interface RecommendedModel {
  id: string;
  name: string;
  slug: string;
  brand_slug: string;
  brand: string;
  body_type?: string;
  image_url?: string;
  logo?: string;
  from_inr: number;
  to_inr: number;
  fuels?: string;
  variants: number;
  match_score: number;
  reasons: string[];
  warnings?: string[];
  variant?: string;
  variant_id?: string;
  transmission?: string | null;
  crash_stars?: number | null;
  efficiency?: number | null;
  pool: number;
}

interface MatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultVehicleType?: "car" | "bike";
}

const CAR_FUELS = ["Petrol", "Diesel", "CNG", "Hybrid", "Electric"] as const;
const BIKE_FUELS = ["Petrol", "Electric"] as const;
const GEARBOX = ["Manual", "Automatic"] as const;

const CAR_BODIES = ["SUV", "Hatchback", "Sedan", "MUV", "Coupe", "Convertible", "Pickup"] as const;
const BIKE_BODIES = ["Commuter", "Scooter", "Street", "Sports", "Adventure", "Cruiser", "Electric Scooter"] as const;

const USES = [
  { id: "city", label: "Mostly city", desc: "Start-stop traffic & easy parking" },
  { id: "mixed", label: "City + highway", desc: "Balanced commute & weekend trips" },
  { id: "highway", label: "Long drives", desc: "High-speed stability & overtaking" },
] as const;

const PRIOS_ALL: { id: string; label: string; desc: string; carOnly?: boolean }[] = [
  { id: "value", label: "Value for money", desc: "Best equipment and pricing balance" },
  { id: "safety", label: "Safety", desc: "Crash test stars & electronic aids", carOnly: true },
  { id: "mileage", label: "Mileage", desc: "Highest fuel economy or EV range" },
  { id: "features", label: "Features", desc: "Ventilated seats, cameras, screens" },
  { id: "performance", label: "Performance", desc: "Engine punch & passing power" },
  { id: "popular", label: "Popular choice", desc: "Top sales rank & easy service" },
];

const SEATS = [
  { count: 0, label: "Any seating" },
  { count: 5, label: "5 or more" },
  { count: 6, label: "6 or more" },
  { count: 7, label: "7 or more" },
] as const;

function formatBudgetLakh(amt: number): string {
  if (amt <= 0) return "₹0";
  if (amt < 100000) return inr(amt);
  const l = amt / 100000;
  return l % 1 === 0 ? `₹${l} L` : `₹${l.toFixed(1)} L`;
}

export function RecommendationsModal({ isOpen, onClose, defaultVehicleType = "car" }: MatchModalProps) {
  const { city } = useCity();
  const [vehicleType, setVehicleType] = useState<"car" | "bike">(defaultVehicleType);

  // Sync default vehicle type if prop changes
  useEffect(() => {
    setVehicleType(defaultVehicleType);
  }, [defaultVehicleType]);

  // Budget state: min and max in INR
  const maxLimit = vehicleType === "car" ? 8000000 : 800000;
  const step = vehicleType === "car" ? 50000 : 10000;
  const [budgetMax, setBudgetMax] = useState<number>(vehicleType === "car" ? 1500000 : 180000);
  const [budgetMin, setBudgetMin] = useState<number>(0);

  // When switching vehicle type, adjust default budget and reset type-specific filters
  const handleVehicleTypeChange = (type: "car" | "bike") => {
    if (type === vehicleType) return;
    setVehicleType(type);
    if (type === "car") {
      setBudgetMin(0);
      setBudgetMax(1500000);
      setFuels([]);
      setGears([]);
      setBodies([]);
      setBrands([]);
      setPrios(["value", "safety"]);
    } else {
      setBudgetMin(0);
      setBudgetMax(180000);
      setFuels([]);
      setGears([]);
      setBodies([]);
      setBrands([]);
      setSeats(0);
      setPrios((p) => p.filter((x) => x !== "safety"));
    }
  };

  const [usage, setUsage] = useState<"city" | "mixed" | "highway">("mixed");
  const [prios, setPrios] = useState<string[]>(vehicleType === "car" ? ["value", "safety"] : ["value"]);
  const [fuels, setFuels] = useState<string[]>([]);
  const [gears, setGears] = useState<string[]>([]);
  const [bodies, setBodies] = useState<string[]>([]);
  const [brands, setBrands] = useState<string[]>([]);
  const [seats, setSeats] = useState<number>(0);
  const [km, setKm] = useState<number>(1000);

  // Filter drawer toggle
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [activeFilterTab, setActiveFilterTab] = useState<"fuel" | "body" | "brands" | "running">("fuel");

  // Fetch available brands dynamically for this city & vehicle type
  const { data: rawBrands } = useSWR<Brand[]>(
    isOpen ? withCity(`/brands?vehicle_type=${vehicleType}`, city) : null,
    fetcher
  );

  const availableBrands = useMemo(() => {
    if (!rawBrands) return [];
    return rawBrands
      .filter((b) => (b.models ?? 0) > 0)
      .sort((a, b) => (b.models ?? 0) - (a.models ?? 0));
  }, [rawBrands]);

  // Priorities list tailored to vehicle type
  const availablePrios = useMemo(() => {
    return PRIOS_ALL.filter((p) => vehicleType === "car" || !p.carOnly);
  }, [vehicleType]);

  const togglePrio = (id: string) => {
    setPrios((prev) => {
      if (prev.includes(id)) {
        const next = prev.filter((x) => x !== id);
        return next.length > 0 ? next : ["value"];
      }
      return [...prev, id];
    });
  };

  const toggleFuel = (f: string) => {
    setFuels((prev) => prev.includes(f) ? prev.filter((x) => x !== f) : [...prev, f]);
  };

  const toggleGear = (g: string) => {
    setGears((prev) => prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g]);
  };

  const toggleBody = (b: string) => {
    setBodies((prev) => prev.includes(b) ? prev.filter((x) => x !== b) : [...prev, b]);
  };

  const toggleBrand = (slug: string) => {
    setBrands((prev) => prev.includes(slug) ? prev.filter((x) => x !== slug) : [...prev, slug]);
  };

  // Active filters count
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (budgetMin > 0) count++;
    if (fuels.length > 0) count += fuels.length;
    if (gears.length > 0) count += gears.length;
    if (bodies.length > 0) count += bodies.length;
    if (brands.length > 0) count += brands.length;
    if (vehicleType === "car" && seats > 0) count++;
    if (km !== 1000) count++;
    return count;
  }, [budgetMin, fuels, gears, bodies, brands, vehicleType, seats, km]);

  const resetAllFilters = () => {
    setBudgetMin(0);
    setFuels([]);
    setGears([]);
    setBodies([]);
    setBrands([]);
    setSeats(0);
    setKm(1000);
  };

  // Query parameters constructed for live API
  const queryParams = useMemo(() => {
    const p = new URLSearchParams();
    p.set("city", city);
    p.set("vehicle_type", vehicleType);
    p.set("usage", usage);
    p.set("limit", "14");
    if (budgetMax < maxLimit) p.set("budget", String(budgetMax));
    if (budgetMin > 0) p.set("budget_min", String(budgetMin));
    if (fuels.length > 0) p.set("fuel", fuels.join(","));
    if (gears.length === 1) p.set("transmission", gears[0]);
    if (vehicleType === "car" && seats > 0) p.set("seats", String(seats));
    if (km !== 1000) p.set("monthly_km", String(km));
    if (bodies.length > 0) p.set("body", bodies.join(","));
    if (brands.length > 0) p.set("brands", brands.join(","));
    p.set("priorities", (prios.length > 0 ? prios : ["value"]).join(","));
    return p.toString();
  }, [city, vehicleType, usage, budgetMax, budgetMin, maxLimit, fuels, gears, seats, km, bodies, brands, prios]);

  const { data: recommendations, isLoading } = useSWR<RecommendedModel[]>(
    isOpen ? withCity(`/recommendations?${queryParams}`, city) : null,
    fetcher,
    { keepPreviousData: true }
  );

  if (!isOpen) return null;

  const totalPool = recommendations?.[0]?.pool ?? recommendations?.length ?? 0;
  const prioNames = prios.map((k) => availablePrios.find((p) => p.id === k)?.label?.toLowerCase() || k);

  // Budget quick presets
  const carPresets = [
    { label: "Under ₹8L", max: 800000 },
    { label: "Under ₹12L", max: 1200000 },
    { label: "Under ₹18L", max: 1800000 },
    { label: "Under ₹25L", max: 2500000 },
    { label: "Under ₹45L", max: 4500000 },
    { label: "Any budget", max: maxLimit },
  ];

  const bikePresets = [
    { label: "Under ₹1L", max: 100000 },
    { label: "Under ₹1.5L", max: 150000 },
    { label: "Under ₹2.5L", max: 250000 },
    { label: "Under ₹4L", max: 400000 },
    { label: "Any budget", max: maxLimit },
  ];

  const presets = vehicleType === "car" ? carPresets : bikePresets;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        className="relative flex flex-col w-full max-w-5xl h-[92vh] rounded-3xl border border-line bg-panel shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-line px-5 py-4 bg-panel-soft/70 shrink-0">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-accent/15 text-accent border border-accent/25">
              <SlidersHorizontal className="h-5 w-5" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg sm:text-xl font-bold text-ink font-[family-name:var(--font-display)]">
                  Find My {vehicleType === "bike" ? "Two-Wheeler" : "Car"}
                </h2>
                <span className="rounded-full bg-panel px-2.5 py-0.5 text-[11px] font-semibold text-accent border border-accent/20">
                  {city}
                </span>
              </div>
              <p className="text-xs text-mute hidden sm:block">
                Ranked by official road tax, real ARAI mileage, equipment and safety tests
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Vehicle Type Switcher */}
            <div className="inline-flex rounded-xl bg-panel border border-line p-1">
              <button
                type="button"
                onClick={() => handleVehicleTypeChange("car")}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer",
                  vehicleType === "car" 
                    ? "bg-accent text-white shadow-xs font-semibold" 
                    : "text-mute hover:text-ink"
                )}
              >
                <Car className="h-3.5 w-3.5" />
                <span>Cars</span>
              </button>
              <button
                type="button"
                onClick={() => handleVehicleTypeChange("bike")}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer",
                  vehicleType === "bike" 
                    ? "bg-accent text-white shadow-xs font-semibold" 
                    : "text-mute hover:text-ink"
                )}
              >
                <Bike className="h-3.5 w-3.5" />
                <span>Bikes</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="rounded-full p-2 text-mute hover:bg-panel-soft hover:text-ink transition cursor-pointer"
              aria-label="Close dialog"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Content Area */}
        <div data-lenis-prevent className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
          {/* Section 1: Budget & Usage */}
          <div className="grid gap-4 md:grid-cols-12 rounded-2xl border border-line bg-panel-soft/40 p-4">
            {/* On-Road Budget Controls (7 cols) */}
            <div className="md:col-span-7 flex flex-col justify-between space-y-3">
              <div className="flex items-baseline justify-between">
                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-mute block">
                    On-Road Budget in {city}
                  </span>
                  <div className="flex items-baseline gap-2 mt-0.5">
                    <span className="font-[family-name:var(--font-display)] text-2xl font-bold text-ink">
                      {budgetMin > 0 ? `${formatBudgetLakh(budgetMin)} – ` : "Up to "}
                      {budgetMax >= maxLimit ? "Any Budget" : formatBudgetLakh(budgetMax)}
                    </span>
                  </div>
                </div>
                <span className="text-[11px] text-mute hidden sm:inline">
                  Includes road tax & insurance
                </span>
              </div>

              {/* Range slider for budgetMax */}
              <div className="space-y-1.5">
                <input
                  type="range"
                  min={step}
                  max={maxLimit}
                  step={step}
                  value={budgetMax}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setBudgetMax(val);
                    if (val < budgetMin) setBudgetMin(0);
                  }}
                  className="w-full accent-accent h-2 bg-panel rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[11px] font-mono text-mute">
                  <span>{formatBudgetLakh(step)}</span>
                  <span>{formatBudgetLakh(maxLimit / 2)}</span>
                  <span>{formatBudgetLakh(maxLimit)}</span>
                </div>
              </div>

              {/* Fast Presets */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {presets.map((p) => {
                  const isActive = budgetMax === p.max && budgetMin === 0;
                  return (
                    <button
                      key={p.label}
                      type="button"
                      onClick={() => {
                        setBudgetMax(p.max);
                        setBudgetMin(0);
                      }}
                      className={cn(
                        "rounded-lg px-2.5 py-1 text-xs font-medium transition cursor-pointer border",
                        isActive 
                          ? "border-accent bg-accent/15 text-accent font-semibold" 
                          : "border-line bg-panel text-mute hover:text-ink hover:border-line/80"
                      )}
                    >
                      {p.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Primary Usage Controls (5 cols) */}
            <div className="md:col-span-5 md:border-l md:border-line md:pl-4 flex flex-col justify-between space-y-2">
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-mute block mb-2">
                  Daily Driving Context
                </span>
                <div className="grid grid-cols-1 gap-1.5">
                  {USES.map((u) => {
                    const isSelected = usage === u.id;
                    return (
                      <button
                        key={u.id}
                        type="button"
                        onClick={() => setUsage(u.id)}
                        className={cn(
                          "flex flex-col text-left px-3 py-2 rounded-xl border transition cursor-pointer",
                          isSelected
                            ? "border-accent bg-accent/15 text-ink shadow-xs"
                            : "border-line bg-panel text-mute hover:text-ink hover:bg-panel-soft"
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span className={cn("text-xs font-semibold", isSelected ? "text-accent" : "text-ink")}>
                            {u.label}
                          </span>
                          {isSelected && <CheckCircle2 className="h-3.5 w-3.5 text-accent" />}
                        </div>
                        <span className="text-[11px] text-mute leading-tight mt-0.5">
                          {u.desc}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Ordered Priorities */}
          <div className="rounded-2xl border border-line bg-panel-soft/30 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
              <div>
                <span className="text-xs font-bold text-ink">
                  What matters most to you?
                </span>
                <span className="text-xs text-mute ml-2 hidden sm:inline">
                  Tap to rank. Number 1 carries the highest weight in scoring.
                </span>
              </div>
              {prios.length > 1 && (
                <button
                  type="button"
                  onClick={() => setPrios(["value"])}
                  className="text-[11px] text-accent hover:underline cursor-pointer"
                >
                  Reset priorities
                </button>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              {availablePrios.map((p) => {
                const orderIndex = prios.indexOf(p.id);
                const isSelected = orderIndex >= 0;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => togglePrio(p.id)}
                    className={cn(
                      "flex items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-medium transition cursor-pointer",
                      isSelected
                        ? "border-accent bg-accent/15 text-ink font-semibold shadow-xs"
                        : "border-line bg-panel text-mute hover:text-ink hover:border-line/80"
                    )}
                  >
                    {isSelected ? (
                      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-accent text-[10px] font-bold text-white">
                        {orderIndex + 1}
                      </span>
                    ) : (
                      <span className="h-2 w-2 rounded-full bg-line" />
                    )}
                    <span>{p.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Section 3: Detailed Filter Accordion Drawer */}
          <div className="rounded-2xl border border-line bg-panel-soft/20 overflow-hidden">
            <button
              type="button"
              onClick={() => setFilterDrawerOpen(!filterDrawerOpen)}
              className="w-full flex items-center justify-between px-4 py-3 bg-panel-soft/50 hover:bg-panel-soft text-left transition cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <Gauge className="h-4 w-4 text-accent" />
                <span className="text-xs font-bold text-ink">
                  Detailed Specifications & Filter Options
                </span>
                {activeFiltersCount > 0 && (
                  <span className="rounded-full bg-accent text-white text-[10px] font-bold px-2 py-0.5">
                    {activeFiltersCount} applied
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-mute">
                <span>{filterDrawerOpen ? "Hide filters" : "Show fuel, gearbox, body & brands"}</span>
                {filterDrawerOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </div>
            </button>

            {filterDrawerOpen && (
              <div className="p-4 border-t border-line space-y-4">
                {/* Tabs */}
                <div className="flex flex-wrap gap-1.5 border-b border-line pb-3">
                  <button
                    type="button"
                    onClick={() => setActiveFilterTab("fuel")}
                    className={cn(
                      "px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer",
                      activeFilterTab === "fuel" ? "bg-accent text-white font-semibold" : "text-mute hover:text-ink"
                    )}
                  >
                    Fuel {fuels.length > 0 && `(${fuels.length})`}
                  </button>
                  {vehicleType === "car" && (
                    <button
                      type="button"
                      onClick={() => setActiveFilterTab("body")}
                      className={cn(
                        "px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer",
                        activeFilterTab === "body" ? "bg-accent text-white font-semibold" : "text-mute hover:text-ink"
                      )}
                    >
                      Body & Seating {bodies.length > 0 && `(${bodies.length})`}
                    </button>
                  )}
                  {vehicleType === "bike" && (
                    <button
                      type="button"
                      onClick={() => setActiveFilterTab("body")}
                      className={cn(
                        "px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer",
                        activeFilterTab === "body" ? "bg-accent text-white font-semibold" : "text-mute hover:text-ink"
                      )}
                    >
                      Style / Segment {bodies.length > 0 && `(${bodies.length})`}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setActiveFilterTab("brands")}
                    className={cn(
                      "px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer",
                      activeFilterTab === "brands" ? "bg-accent text-white font-semibold" : "text-mute hover:text-ink"
                    )}
                  >
                    Brands {brands.length > 0 && `(${brands.length})`}
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveFilterTab("running")}
                    className={cn(
                      "px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer",
                      activeFilterTab === "running" ? "bg-accent text-white font-semibold" : "text-mute hover:text-ink"
                    )}
                  >
                    Monthly Running {km !== 1000 && `(${km} km)`}
                  </button>
                </div>

                {/* Tab 1: Fuel & Gearbox */}
                {activeFilterTab === "fuel" && (
                  <div className="space-y-4">
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-mute block mb-2">
                        Fuel / Powertrain
                      </span>
                      <div className="flex flex-wrap gap-2">
                        {(vehicleType === "car" ? CAR_FUELS : BIKE_FUELS).map((f) => {
                          const active = fuels.includes(f);
                          return (
                            <button
                              key={f}
                              type="button"
                              onClick={() => toggleFuel(f)}
                              className={cn(
                                "flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition cursor-pointer",
                                active 
                                  ? "border-accent bg-accent/15 text-accent font-semibold" 
                                  : "border-line bg-panel text-mute hover:text-ink"
                              )}
                            >
                              <Fuel className="h-3.5 w-3.5" />
                              <span>{f}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {vehicleType === "car" && (
                      <div>
                        <span className="text-[11px] font-semibold uppercase tracking-wider text-mute block mb-2">
                          Transmission / Gearbox
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {GEARBOX.map((g) => {
                            const active = gears.includes(g);
                            return (
                              <button
                                key={g}
                                type="button"
                                onClick={() => toggleGear(g)}
                                className={cn(
                                  "flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition cursor-pointer",
                                  active 
                                    ? "border-accent bg-accent/15 text-accent font-semibold" 
                                    : "border-line bg-panel text-mute hover:text-ink"
                                )}
                              >
                                <span>{g}</span>
                                {g === "Automatic" && (
                                  <span className="text-[10px] text-mute font-normal">(AMT/CVT/DCT/EV)</span>
                                )}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 2: Body & Seating */}
                {activeFilterTab === "body" && (
                  <div className="space-y-4">
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-mute block mb-2">
                        Body Style
                      </span>
                      <div className="flex flex-wrap gap-2">
                        {(vehicleType === "car" ? CAR_BODIES : BIKE_BODIES).map((b) => {
                          const active = bodies.includes(b);
                          return (
                            <button
                              key={b}
                              type="button"
                              onClick={() => toggleBody(b)}
                              className={cn(
                                "px-3 py-1.5 rounded-xl border text-xs font-medium transition cursor-pointer",
                                active 
                                  ? "border-accent bg-accent/15 text-accent font-semibold" 
                                  : "border-line bg-panel text-mute hover:text-ink"
                              )}
                            >
                              {b}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {vehicleType === "car" && (
                      <div>
                        <span className="text-[11px] font-semibold uppercase tracking-wider text-mute block mb-2">
                          Seating Capacity
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {SEATS.map((s) => {
                            const active = seats === s.count;
                            return (
                              <button
                                key={s.count}
                                type="button"
                                onClick={() => setSeats(s.count)}
                                className={cn(
                                  "flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition cursor-pointer",
                                  active 
                                    ? "border-accent bg-accent/15 text-accent font-semibold" 
                                    : "border-line bg-panel text-mute hover:text-ink"
                                )}
                              >
                                <Users className="h-3 w-3" />
                                <span>{s.label}</span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 3: Brands */}
                {activeFilterTab === "brands" && (
                  <div>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-mute block mb-2">
                      Brands Active in {city}
                    </span>
                    <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto pr-2">
                      {availableBrands.map((b) => {
                        const active = brands.includes(b.slug);
                        return (
                          <button
                            key={b.slug}
                            type="button"
                            onClick={() => toggleBrand(b.slug)}
                            className={cn(
                              "flex items-center gap-1.5 px-3 py-1 rounded-xl border text-xs font-medium transition cursor-pointer",
                              active 
                                ? "border-accent bg-accent/15 text-accent font-semibold" 
                                : "border-line bg-panel text-mute hover:text-ink"
                            )}
                          >
                            <span>{b.name}</span>
                            <span className="text-[10px] text-mute font-mono">({b.models})</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Tab 4: Monthly Running */}
                {activeFilterTab === "running" && (
                  <div className="space-y-2 max-w-md">
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs font-bold text-ink">
                        {km.toLocaleString("en-IN")} km a month
                      </span>
                      <span className="text-[11px] text-mute">
                        Standard commute: 1,000 km
                      </span>
                    </div>
                    <input
                      type="range"
                      min={200}
                      max={4000}
                      step={100}
                      value={km}
                      onChange={(e) => setKm(Number(e.target.value))}
                      className="w-full accent-accent h-2 bg-panel rounded-lg cursor-pointer"
                    />
                    <p className="text-[11px] text-mute">
                      Higher monthly running heavily prioritizes high fuel economy, diesel, CNG, and electric powertrains.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Active Chips Strip */}
          {activeFiltersCount > 0 && (
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-xs text-mute font-medium mr-1">Active filters:</span>
              {budgetMin > 0 && (
                <span className="inline-flex items-center gap-1 rounded-lg border border-accent/40 bg-accent/10 px-2.5 py-1 text-xs text-accent">
                  Min {formatBudgetLakh(budgetMin)}
                  <button onClick={() => setBudgetMin(0)} className="hover:text-white cursor-pointer"><X className="h-3 w-3" /></button>
                </span>
              )}
              {fuels.map((f) => (
                <span key={f} className="inline-flex items-center gap-1 rounded-lg border border-accent/40 bg-accent/10 px-2.5 py-1 text-xs text-accent">
                  {f}
                  <button onClick={() => toggleFuel(f)} className="hover:text-white cursor-pointer"><X className="h-3 w-3" /></button>
                </span>
              ))}
              {gears.map((g) => (
                <span key={g} className="inline-flex items-center gap-1 rounded-lg border border-accent/40 bg-accent/10 px-2.5 py-1 text-xs text-accent">
                  {g}
                  <button onClick={() => toggleGear(g)} className="hover:text-white cursor-pointer"><X className="h-3 w-3" /></button>
                </span>
              ))}
              {bodies.map((b) => (
                <span key={b} className="inline-flex items-center gap-1 rounded-lg border border-accent/40 bg-accent/10 px-2.5 py-1 text-xs text-accent">
                  {b}
                  <button onClick={() => toggleBody(b)} className="hover:text-white cursor-pointer"><X className="h-3 w-3" /></button>
                </span>
              ))}
              {brands.map((slug) => {
                const bName = availableBrands.find((b) => b.slug === slug)?.name || slug;
                return (
                  <span key={slug} className="inline-flex items-center gap-1 rounded-lg border border-accent/40 bg-accent/10 px-2.5 py-1 text-xs text-accent">
                    {bName}
                    <button onClick={() => toggleBrand(slug)} className="hover:text-white cursor-pointer"><X className="h-3 w-3" /></button>
                  </span>
                );
              })}
              {vehicleType === "car" && seats > 0 && (
                <span className="inline-flex items-center gap-1 rounded-lg border border-accent/40 bg-accent/10 px-2.5 py-1 text-xs text-accent">
                  {seats}+ Seats
                  <button onClick={() => setSeats(0)} className="hover:text-white cursor-pointer"><X className="h-3 w-3" /></button>
                </span>
              )}
              {km !== 1000 && (
                <span className="inline-flex items-center gap-1 rounded-lg border border-accent/40 bg-accent/10 px-2.5 py-1 text-xs text-accent">
                  {km} km/month
                  <button onClick={() => setKm(1000)} className="hover:text-white cursor-pointer"><X className="h-3 w-3" /></button>
                </span>
              )}
              <button
                type="button"
                onClick={resetAllFilters}
                className="text-xs font-semibold text-accent hover:underline ml-2 cursor-pointer"
              >
                Clear all
              </button>
            </div>
          )}

          {/* Section 4: Live Results Header */}
          <div className="border-t border-line pt-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2 mb-4">
              <div>
                <h3 className="text-base sm:text-lg font-bold text-ink">
                  {isLoading && !recommendations
                    ? "Evaluating models and live on-road pricing…"
                    : recommendations && recommendations.length > 0
                    ? `Top ${recommendations.length} of ${totalPool} matches in ${city}`
                    : "No matching models"}
                </h3>
                <p className="text-xs text-mute mt-0.5">
                  Within {budgetMin > 0 ? `${formatBudgetLakh(budgetMin)} – ` : "up to "}
                  {budgetMax >= maxLimit ? "any budget" : formatBudgetLakh(budgetMax)} on-road · 
                  ranked by {prioNames.join(", ")}
                </p>
              </div>
              {recommendations && recommendations.length > 0 && (
                <span className="text-xs font-medium text-emerald-500 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                  Calculated with official road taxes
                </span>
              )}
            </div>

            {/* Results Grid */}
            {isLoading && !recommendations ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-64 rounded-2xl" />
                ))}
              </div>
            ) : !recommendations || recommendations.length === 0 ? (
              <div className="text-center py-12 rounded-2xl border border-dashed border-line bg-panel-soft/30 p-6 space-y-3">
                <AlertTriangle className="h-8 w-8 text-amber-400 mx-auto" />
                <h4 className="text-sm font-bold text-ink">Nothing in {city} fits all of these criteria</h4>
                <p className="text-xs text-mute max-w-md mx-auto">
                  Try relaxing your budget ceiling, clearing specific fuel filters, or removing brand constraints.
                </p>
                <div className="flex flex-wrap justify-center gap-2 pt-2">
                  {budgetMax < maxLimit && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setBudgetMax(Math.min(maxLimit, Math.round(budgetMax * 1.3)))}
                    >
                      Raise budget to {formatBudgetLakh(Math.min(maxLimit, Math.round(budgetMax * 1.3)))}
                    </Button>
                  )}
                  {budgetMin > 0 && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setBudgetMin(0)}
                    >
                      Remove minimum price
                    </Button>
                  )}
                  {activeFiltersCount > 0 && (
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={resetAllFilters}
                    >
                      <RotateCcw className="h-3.5 w-3.5" /> Clear Filters
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {recommendations.map((m, idx) => {
                  const underBudget = budgetMax < maxLimit && m.from_inr ? budgetMax - m.from_inr : 0;
                  const isTopPick = idx === 0;
                  const targetHref = vehicleType === "bike" ? `/bikes/${m.id}` : `/cars/${m.id}`;

                  // Score badge coloring
                  const scoreColor = m.match_score >= 80 
                    ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/25" 
                    : m.match_score >= 65 
                    ? "bg-accent/15 text-accent border-accent/25" 
                    : "bg-amber-500/15 text-amber-500 border-amber-500/25";

                  return (
                    <div
                      key={m.id}
                      className={cn(
                        "flex flex-col justify-between rounded-2xl border bg-panel p-4 sm:p-5 transition hover:shadow-lg relative overflow-hidden",
                        isTopPick 
                          ? "border-accent/60 shadow-[0_0_24px_-10px_rgba(255,77,46,0.3)]" 
                          : "border-line hover:border-line/80"
                      )}
                    >
                      {/* Top Bar: Rank & Match Score */}
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-3">
                          <div className="flex items-center gap-2">
                            <span className={cn(
                              "flex h-6 items-center px-2 rounded-md text-xs font-bold font-mono",
                              isTopPick ? "bg-accent text-white" : "bg-panel-soft text-mute border border-line"
                            )}>
                              #{idx + 1}
                            </span>
                            <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold border", scoreColor)}>
                              <CheckCircle2 className="h-3 w-3" /> {m.match_score}% Match
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5 text-xs text-mute">
                            {m.crash_stars != null && (
                              <span className={cn(
                                "inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full border text-[11px] font-bold",
                                m.crash_stars >= 4 
                                  ? "border-emerald-500/30 text-emerald-600 dark:text-emerald-400 bg-emerald-500/10" 
                                  : "border-amber-500/30 text-amber-500 bg-amber-500/10"
                              )}>
                                <ShieldCheck className="h-3 w-3" /> {m.crash_stars}★ NCAP
                              </span>
                            )}
                            {m.body_type && (
                              <span className="rounded-md bg-panel-soft border border-line px-2 py-0.5 text-[11px]">
                                {m.body_type}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Vehicle Image & Headings */}
                        <div className="grid grid-cols-[1fr_105px] sm:grid-cols-[1fr_120px] gap-3 items-center">
                          <div>
                            <p className="text-xs font-medium text-mute">{m.brand}</p>
                            <h4 className="font-[family-name:var(--font-display)] text-lg sm:text-xl font-bold text-ink leading-tight">
                              {m.name}
                            </h4>
                            {m.variant && (
                              <p className="text-xs text-accent font-medium mt-0.5 line-clamp-1">
                                {m.variant}
                              </p>
                            )}
                            <div className="mt-2">
                              <p className="font-mono text-base sm:text-lg font-bold text-ink">
                                {inr(m.from_inr)}
                              </p>
                              <p className="text-[10px] text-mute uppercase tracking-wider font-medium">
                                True On-Road in {city}
                              </p>
                            </div>
                          </div>

                          <div className="relative aspect-[16/10] rounded-xl overflow-hidden bg-panel-soft border border-line p-1">
                            <CarImage
                              src={m.image_url}
                              alt={`${m.brand} ${m.name}`}
                              bodyType={m.body_type}
                              className="h-full w-full object-contain"
                            />
                          </div>
                        </div>

                        {/* Match Strength Bar */}
                        <div className="mt-3 w-full bg-panel-soft h-1.5 rounded-full overflow-hidden">
                          <div 
                            className={cn(
                              "h-full rounded-full transition-all duration-500",
                              m.match_score >= 80 ? "bg-emerald-500" : m.match_score >= 65 ? "bg-accent" : "bg-amber-500"
                            )}
                            style={{ width: `${Math.min(100, Math.max(10, m.match_score))}%` }}
                          />
                        </div>

                        {/* Concrete Spec Chips */}
                        <div className="mt-2.5 flex flex-wrap gap-1.5">
                          {m.fuels && (
                            <span className="rounded-md bg-panel-soft px-2 py-0.5 text-[11px] font-medium text-mute border border-line">
                              {m.fuels}
                            </span>
                          )}
                          {m.transmission && (
                            <span className="rounded-md bg-panel-soft px-2 py-0.5 text-[11px] font-medium text-mute border border-line">
                              {m.transmission}
                            </span>
                          )}
                          {m.efficiency && (
                            <span className="rounded-md bg-panel-soft px-2 py-0.5 text-[11px] font-medium text-mute border border-line font-mono">
                              {m.efficiency} {m.fuels?.includes("Electric") ? "km range" : "km/l"}
                            </span>
                          )}
                        </div>

                        {/* Concrete Evaluated Reasons */}
                        <div className="mt-3.5 space-y-1 border-t border-line pt-3">
                          {underBudget >= 10000 && (
                            <div className="flex items-start gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                              <span>₹{Math.round(underBudget / 1000)}k under your budget target</span>
                            </div>
                          )}
                          {m.reasons && m.reasons.filter((r) => !r.startsWith("On-road")).slice(0, 3).map((r, rIdx) => (
                            <div key={rIdx} className="flex items-start gap-1.5 text-xs text-ink/90">
                              <CheckCircle2 className="h-3.5 w-3.5 text-accent shrink-0 mt-0.5" />
                              <span>{r}</span>
                            </div>
                          ))}
                          {m.warnings && m.warnings.map((w, wIdx) => (
                            <div key={wIdx} className="flex items-start gap-1.5 text-xs text-amber-500">
                              <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                              <span>{w}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Card Footer Action */}
                      <div className="mt-4 border-t border-line pt-3 flex items-center justify-between">
                        <span className="text-[11px] text-mute">
                          Official pricing for {city}
                        </span>
                        <Link
                          href={targetHref}
                          onClick={onClose}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-accent hover:underline cursor-pointer"
                        >
                          View Breakdown & Variants <ArrowRight className="h-3 w-3" />
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Note for electric cars */}
            {vehicleType === "car" && !fuels.includes("Electric") && recommendations && recommendations.length > 0 && (
              <p className="mt-4 text-xs text-mute">
                Tip: Electric cars appear when you pick <span className="text-ink font-medium">Electric</span> under Filters → Fuel (they require home or office charging infrastructure).
              </p>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="border-t border-line bg-panel-soft/70 px-5 py-3.5 flex items-center justify-between shrink-0">
          <p className="text-xs text-mute">
            Live evaluation across official ex-showroom prices and Indian state road tax tables
          </p>
          <Button size="sm" variant="outline" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  );
}
