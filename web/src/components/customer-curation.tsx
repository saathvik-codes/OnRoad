"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { 
  Award, 
  Car, 
  Gauge, 
  Fuel, 
  ShieldCheck, 
  ArrowRight, 
  CheckCircle2, 
  Flame, 
  ThumbsUp, 
  SlidersHorizontal,
  UserCheck,
  LogIn
} from "lucide-react";
import { fetcher, type Account } from "@/lib/api";
import { lakh, range } from "@/lib/format";
import { useCity, withCity } from "@/components/city";
import { Card, cn, Skeleton } from "@/components/ui";

interface CuratedModel {
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
}

export function CustomerCuration() {
  const { city } = useCity();
  const { data: me } = useSWR<Account>("/auth/me", fetcher, { shouldRetryOnError: false });

  const [vehicleType, setVehicleType] = useState<"car" | "bike">("car");
  const [usage, setUsage] = useState<"family" | "commute" | "performance">("family");
  const [fuel, setFuel] = useState<string>("any");

  const queryParams = new URLSearchParams({
    city,
    vehicle_type: vehicleType,
    usage,
    ...(fuel !== "any" ? { fuel } : {}),
    limit: "6",
  }).toString();

  const { data: models, isLoading } = useSWR<CuratedModel[]>(
    withCity(`/recommendations?${queryParams}`, city),
    fetcher
  );

  const firstName = me?.name ? me.name.split(" ")[0] : null;

  return (
    <section className="mx-auto max-w-7xl px-4 sm:px-6 py-12 sm:py-16">
      {/* Onboarding Banner & Personalization Header */}
      <div className="relative overflow-hidden rounded-3xl border border-line bg-gradient-to-br from-panel via-panel-soft/60 to-panel p-6 sm:p-8 shadow-xl">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-accent/10 blur-3xl" />
        <div className="pointer-events-none absolute -left-24 -bottom-24 h-72 w-72 rounded-full bg-amber-500/10 blur-3xl" />

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 border-b border-line pb-6">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-accent/15 border border-accent/25 px-3 py-0.5 text-xs font-bold text-accent">
                <Award className="h-3.5 w-3.5 text-accent" />
                {firstName ? `CURATED FOR ${firstName.toUpperCase()}` : "INTELLIGENT BUYER ONBOARDING & CURATION"}
              </span>

              {firstName ? (
                <span className="inline-flex items-center gap-1 text-xs text-good font-semibold bg-good/10 px-2.5 py-0.5 rounded-full border border-good/20">
                  <UserCheck className="h-3.5 w-3.5" /> Your preferences
                </span>
              ) : (
                <span className="text-xs text-mute font-medium">
                  Dynamic recommendations personalized to your commute & city
                </span>
              )}
            </div>

            <h2 className="font-[family-name:var(--font-display)] text-2xl sm:text-4xl font-black text-ink tracking-tight">
              {firstName 
                ? `${firstName}'s Recommended Vehicles in ${city}`
                : `Find Your Perfect Car or Two-Wheeler in ${city}`}
            </h2>
            <p className="mt-1 text-xs sm:text-sm text-mute max-w-2xl">
              Cars that fit your budget and needs, priced on-road for your city.
            </p>
          </div>

          {!firstName && (
            <Link
              href="/signup?next=/"
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-2xl bg-panel border border-accent/40 px-5 py-3 text-xs sm:text-sm font-bold text-ink hover:border-accent hover:text-accent shadow-sm transition"
            >
              <LogIn className="h-4 w-4 text-accent" />
              <span>Sign In to Save Garage Preferences</span>
            </Link>
          )}
        </div>

        {/* Interactive Curation Filters */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
          {/* Vehicle Type Tabs */}
          <div className="flex items-center rounded-2xl bg-panel-soft p-1 border border-line shrink-0">
            <button
              onClick={() => setVehicleType("car")}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition cursor-pointer",
                vehicleType === "car" ? "bg-accent text-white shadow-sm" : "text-mute hover:text-ink"
              )}
            >
              <Car className="h-4 w-4" /> Cars & SUVs
            </button>
            <button
              onClick={() => setVehicleType("bike")}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition cursor-pointer",
                vehicleType === "bike" ? "bg-accent text-white shadow-sm" : "text-mute hover:text-ink"
              )}
            >
              <Gauge className="h-4 w-4" /> Two-Wheelers
            </button>
          </div>

          {/* Usage Preferences */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-mute hidden sm:inline">Use Case:</span>
            {[
              { id: "family", label: "👨‍👩‍👧 Family Comfort & Safety" },
              { id: "commute", label: "⚡ Daily Office Commute & Mileage" },
              { id: "performance", label: "🛣️ Long-Distance Highway Touring" }
            ].map((u) => (
              <button
                key={u.id}
                onClick={() => setUsage(u.id as typeof usage)}
                className={cn(
                  "rounded-xl border px-3 py-1.5 text-xs font-semibold transition cursor-pointer",
                  usage === u.id
                    ? "border-accent bg-accent/15 text-accent shadow-xs"
                    : "border-line bg-panel text-mute hover:text-ink hover:border-line/80"
                )}
              >
                {u.label}
              </button>
            ))}
          </div>

          {/* Fuel Filter Chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
            {["any", "Petrol", "Electric", "CNG", "Diesel"].map((f) => (
              <button
                key={f}
                onClick={() => setFuel(f)}
                className={cn(
                  "rounded-full border px-3 py-1 text-[11px] font-medium transition cursor-pointer",
                  fuel === f
                    ? "border-accent bg-accent text-white"
                    : "border-line bg-panel-soft text-mute hover:text-ink"
                )}
              >
                {f === "any" ? "All Powertrains" : f}
              </button>
            ))}
          </div>
        </div>

        {/* Curated Grid */}
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {isLoading ? (
            [0, 1, 2].map((i) => <Skeleton key={i} className="h-80 rounded-3xl" />)
          ) : !models || models.length === 0 ? (
            <div className="col-span-full py-12 text-center text-mute text-sm">
              No direct matches found for this specific filter. Showing popular models in {city}.
            </div>
          ) : (
            models.map((m) => (
              <div
                key={m.id}
                className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-line bg-panel p-5 transition duration-300 hover:-translate-y-1 hover:border-accent/50 hover:shadow-xl"
              >
                <div>
                  {/* Match Score Badge */}
                  <div className="flex items-center justify-between pb-3">
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 border border-emerald-500/25 px-2.5 py-0.5 text-xs font-bold text-emerald-600 dark:text-emerald-400">
                      <ThumbsUp className="h-3 w-3" />
                      {m.match_score}% Match for You
                    </span>
                    <span className="text-xs font-medium text-mute">
                      {m.body_type || (vehicleType === "bike" ? "2-Wheeler" : "Car")}
                    </span>
                  </div>

                  {/* Vehicle Image Stage */}
                  <div className="relative mx-auto my-2 flex h-36 items-center justify-center rounded-2xl bg-panel-soft/60 p-3 overflow-hidden border border-line/60">
                    {m.image_url ? (
                      <img
                        src={m.image_url}
                        alt={`${m.brand} ${m.name}`}
                        className="max-h-28 max-w-full object-contain transition-transform duration-500 group-hover:scale-105"
                        loading="lazy"
                      />
                    ) : (
                      <Car className="h-14 w-14 text-mute/40" />
                    )}
                  </div>

                  {/* Title & Brand */}
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-mute uppercase tracking-wider">{m.brand}</p>
                    <h3 className="font-[family-name:var(--font-display)] text-xl font-bold text-ink mt-0.5 group-hover:text-accent transition">
                      {m.name}
                    </h3>

                    {/* Price Range */}
                    <p className="mt-2 font-mono text-base font-black text-ink">
                      {range(m.from_inr, m.to_inr)}
                    </p>
                    <p className="text-[11px] text-mute">Ex-showroom {city} · {m.variants} variants</p>
                  </div>

                  {/* Match Reasons */}
                  <div className="mt-4 space-y-1.5 border-t border-line/70 pt-3 text-xs">
                    {m.reasons.map((r, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-mute">
                        <CheckCircle2 className="h-3.5 w-3.5 text-good shrink-0 mt-0.5" />
                        <span className="text-[11px] leading-tight text-ink/80">{r}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* View Details Link */}
                <div className="mt-5 pt-3 border-t border-line">
                  <Link
                    href={`/cars/${m.id}`}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-panel-soft hover:bg-accent hover:text-white border border-line px-4 py-2.5 text-xs font-bold text-ink transition"
                  >
                    <span>Inspect On-Road Price & Variants</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
