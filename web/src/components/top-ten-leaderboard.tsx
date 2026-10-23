"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { 
  Trophy, 
  Crown, 
  ArrowRight, 
  Car, 
  Bike,
  Sparkles,
  Layers
} from "lucide-react";
import { fetcher, type ModelSummary } from "@/lib/api";
import { useCity, withCity } from "@/components/city";
import { CarImage } from "@/components/car-image";
import { range, inr } from "@/lib/format";
import { SectionTitle, Skeleton, cn } from "@/components/ui";

export function TopTenLeaderboard() {
  const { city } = useCity();
  const [vehicleTab, setVehicleTab] = useState<"cars" | "bikes">("cars");

  const { data: cars, isLoading: carsLoading } = useSWR<ModelSummary[]>(
    withCity("/explore?sort=popular&vehicle_type=car", city),
    fetcher
  );
  const { data: bikes, isLoading: bikesLoading } = useSWR<ModelSummary[]>(
    withCity("/explore?sort=popular&vehicle_type=bike", city),
    fetcher
  );

  const activeList = (vehicleTab === "cars" ? cars : bikes)?.slice(0, 10);
  const isLoading = vehicleTab === "cars" ? carsLoading : bikesLoading;

  return (
    <section className="mx-auto max-w-7xl px-5 pb-24">
      <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <SectionTitle
            eyebrow="Six-month sales data"
            title="Top 10 Most-Bought in India"
            sub={`Ranked by factory dispatches over the last six months (company and industry sales reports), with on-road prices for ${city}.`}
          />
        </div>

        {/* Tab Toggle */}
        <div className="inline-flex shrink-0 items-center rounded-2xl border border-line bg-panel p-1.5 shadow-sm">
          <button
            type="button"
            onClick={() => setVehicleTab("cars")}
            className={cn(
              "flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition duration-200",
              vehicleTab === "cars"
                ? "bg-accent text-white shadow-md shadow-accent/25"
                : "text-mute hover:text-white"
            )}
          >
            <Car className="h-4 w-4" />
            Top 10 Cars
          </button>
          <button
            type="button"
            onClick={() => setVehicleTab("bikes")}
            className={cn(
              "flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition duration-200",
              vehicleTab === "bikes"
                ? "bg-accent text-white shadow-md shadow-accent/25"
                : "text-mute hover:text-white"
            )}
          >
            <Bike className="h-4 w-4" />
            Top 10 Two-Wheelers
          </button>
        </div>
      </div>

      {/* Grid of 10 items */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {isLoading || !activeList
          ? Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="rounded-3xl border border-line bg-panel p-4">
                <Skeleton className="h-32 w-full rounded-2xl" />
                <Skeleton className="mt-4 h-4 w-24" />
                <Skeleton className="mt-2 h-6 w-36" />
                <Skeleton className="mt-3 h-4 w-28" />
              </div>
            ))
          : activeList.map((m, index) => {
              const rank = index + 1;
              const isTop1 = rank === 1;
              const isTop3 = rank <= 3;

              return (
                <Link
                  key={m.id}
                  href={`/cars/${m.id}`}
                  className={cn(
                    "group relative flex flex-col justify-between overflow-hidden rounded-3xl border bg-panel p-4 transition-all duration-300 hover:-translate-y-1.5 shadow-sm",
                    isTop1
                      ? "border-amber-500/50 hover:border-amber-400 hover:shadow-[0_8px_30px_rgba(245,158,11,0.15)]"
                      : isTop3
                      ? "border-accent/40 hover:border-accent hover:shadow-[0_8px_30px_rgba(255,77,46,0.12)]"
                      : "border-line hover:border-white/25 hover:shadow-lg"
                  )}
                >
                  <div>
                    {/* Header: Rank Badge & Logo */}
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold tracking-tight",
                          isTop1
                            ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                            : rank === 2
                            ? "bg-slate-300/15 text-slate-200 border border-slate-300/30"
                            : rank === 3
                            ? "bg-amber-700/15 text-amber-500 border border-amber-700/30"
                            : "bg-white/5 text-mute border border-white/10"
                        )}
                      >
                        {isTop1 ? <Crown className="h-3 w-3" /> : null}
                        #{rank} {isTop1 ? "Most Bought" : ""}
                      </span>

                      {m.logo && (
                        <img
                          src={m.logo}
                          alt=""
                          referrerPolicy="no-referrer"
                          className="h-5 w-auto max-w-[50px] object-contain opacity-75 group-hover:opacity-100 transition"
                        />
                      )}
                    </div>

                    {/* Image Stage */}
                    <div className="relative mt-3 aspect-[16/10] overflow-hidden rounded-2xl bg-gradient-to-b from-white/[0.04] to-transparent p-2">
                      <CarImage
                        src={m.image_url}
                        alt={`${m.brand} ${m.name}`}
                        bodyType={m.body_type}
                      />
                    </div>

                    {/* Metadata */}
                    <div className="mt-3">
                      <p className="text-xs font-medium text-mute uppercase tracking-wider">
                        {m.brand}
                      </p>
                      <h4 className="mt-0.5 font-[family-name:var(--font-display)] text-lg font-bold text-white group-hover:text-accent transition">
                        {m.name}
                      </h4>

                      <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-mute">
                        {m.body_type && (
                          <span className="rounded bg-white/5 px-1.5 py-0.5 capitalize">
                            {m.body_type}
                          </span>
                        )}
                        {m.variants ? (
                          <span className="rounded bg-white/5 px-1.5 py-0.5">
                            {m.variants} variants
                          </span>
                        ) : null}
                      </div>

                      {m.six_month_units ? (
                        <p className="mt-2 text-[11px] font-mono text-emerald-400/90 flex items-center gap-1">
                          <Sparkles className="h-2.5 w-2.5 shrink-0" />
                          {m.six_month_units.toLocaleString("en-IN")} units (H1)
                        </p>
                      ) : null}
                    </div>
                  </div>

                  {/* Pricing footer */}
                  <div className="mt-4 border-t border-line pt-3">
                    <p className="text-[11px] text-mute">Starting ex-showroom</p>
                    <p className="font-[family-name:var(--font-display)] text-base font-bold text-white">
                      {range(m.from_inr, m.to_inr)}
                    </p>
                    <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-accent group-hover:translate-x-1 transition">
                      View details <ArrowRight className="h-3 w-3" />
                    </span>
                  </div>
                </Link>
              );
            })}
      </div>
    </section>
  );
}
