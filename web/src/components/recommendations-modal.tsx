"use client";

// Car / bike finder. The buyer answers a few questions (budget, where they drive, what matters most, optional
// filters) and gets models ranked by /api/recommendations: official prices for their city, the full on-road cost,
// ARAI efficiency, equipment and crash-test results. Results update as they answer.

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { X } from "lucide-react";
import { fetcher, type Brand } from "@/lib/api";
import { lakh } from "@/lib/format";
import { useCity, withCity } from "@/components/city";
import { cn, Skeleton } from "@/components/ui";

export interface RecommendedModel {
  id: string; name: string; slug: string; brand_slug: string; brand: string; body_type?: string; image_url?: string;
  logo?: string; from_inr: number; to_inr: number; fuels?: string; variants: number; match_score: number;
  reasons: string[]; warnings?: string[]; variant?: string; variant_id?: string; transmission?: string | null;
  crash_stars?: number | null; efficiency?: number | null; pool: number;
}

const FUELS = { car: ["Petrol", "Diesel", "CNG", "Hybrid", "Electric"], bike: ["Petrol", "Electric"] } as const;
const BODIES = {
  car: ["Hatchback", "Sedan", "SUV", "MUV", "Coupe", "Convertible", "Pickup"],
  bike: ["Commuter", "Scooter", "Street", "Sports", "Adventure", "Cruiser", "Electric Scooter"],
} as const;
const USES = [
  { id: "city", label: "Mostly city" }, { id: "mixed", label: "City and highway" }, { id: "highway", label: "Mostly highway" },
];
const PRIOS = [
  { id: "value", label: "Value for money" }, { id: "safety", label: "Safety", car: true }, { id: "mileage", label: "Mileage" },
  { id: "features", label: "Features" }, { id: "performance", label: "Performance" }, { id: "popular", label: "Popularity" },
];
const BUDGETS = {
  car: [8, 12, 18, 25, 45, 0].map((l) => l * 100_000),
  bike: [1, 1.5, 2.5, 4, 0].map((l) => l * 100_000),
};

function Choice({ on, children, onClick }: { on: boolean; children: React.ReactNode; onClick: () => void }) {
  return (
    <button onClick={onClick}
            className={cn("rounded-full border px-3.5 py-1.5 text-sm transition",
              on ? "border-ink bg-ink text-bg" : "border-line text-ink hover:border-mute")}>
      {children}
    </button>
  );
}

function Question({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3 border-b border-line py-5 first:pt-0 last:border-0">
      <div>
        <h3 className="font-semibold text-ink">{title}</h3>
        {hint && <p className="text-sm text-mute">{hint}</p>}
      </div>
      {children}
    </section>
  );
}

export function RecommendationsModal({ isOpen, onClose, defaultVehicleType = "car" }:
  { isOpen: boolean; onClose: () => void; defaultVehicleType?: "car" | "bike" }) {
  const { city } = useCity();
  const [type, setType] = useState<"car" | "bike">(defaultVehicleType);
  const [budget, setBudget] = useState(0);                  // 0 = any
  const [usage, setUsage] = useState("mixed");
  const [prios, setPrios] = useState<string[]>(["value"]);
  const [fuels, setFuels] = useState<string[]>([]);
  const [gear, setGear] = useState<"" | "Manual" | "Automatic">("");
  const [bodies, setBodies] = useState<string[]>([]);
  const [seats, setSeats] = useState(0);
  const [brands, setBrands] = useState<string[]>([]);
  const [more, setMore] = useState(false);

  useEffect(() => { setType(defaultVehicleType); }, [defaultVehicleType]);       // eslint-disable-line react-hooks/set-state-in-effect
  useEffect(() => {
    if (!isOpen) return;
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", k);
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", k); document.body.style.overflow = ""; };
  }, [isOpen, onClose]);

  const switchType = (t: "car" | "bike") => {
    if (t === type) return;
    setType(t); setBudget(0); setFuels([]); setBodies([]); setBrands([]); setSeats(0); setGear("");
    setPrios((p) => p.filter((x) => x !== "safety").length ? p.filter((x) => x !== "safety") : ["value"]);
  };
  const toggle = (list: string[], set: (v: string[]) => void, v: string) => set(list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);
  const togglePrio = (id: string) => setPrios((p) => p.includes(id) ? (p.length > 1 ? p.filter((x) => x !== id) : p) : [...p, id]);

  const { data: allBrands } = useSWR<Brand[]>(isOpen ? withCity(`/brands?vehicle_type=${type}`, city) : null, fetcher);
  const query = useMemo(() => {
    const p = new URLSearchParams({ vehicle_type: type, usage, limit: "12", priorities: prios.join(",") });
    if (budget) p.set("budget", String(budget));
    if (fuels.length) p.set("fuel", fuels.join(","));
    if (gear) p.set("transmission", gear);
    if (bodies.length) p.set("body", bodies.join(","));
    if (brands.length) p.set("brands", brands.join(","));
    if (type === "car" && seats) p.set("seats", String(seats));
    return p.toString();
  }, [type, usage, prios, budget, fuels, gear, bodies, brands, seats]);
  const { data: recs, isLoading, error } = useSWR<RecommendedModel[]>(isOpen ? withCity(`/recommendations?${query}`, city) : null, fetcher,
    { keepPreviousData: true });

  if (!isOpen) return null;
  const pool = recs?.[0]?.pool ?? recs?.length ?? 0;
  const moreCount = fuels.length + (gear ? 1 : 0) + bodies.length + brands.length + (seats ? 1 : 0);

  return (
    <div className="fixed inset-0 z-[60] flex items-stretch justify-center bg-black/60 sm:items-center sm:p-6" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-label={`Find a ${type}`} onClick={(e) => e.stopPropagation()}
           className="flex h-full w-full max-w-6xl flex-col overflow-hidden bg-bg sm:h-[88vh] sm:rounded-3xl sm:border sm:border-line">
        <header className="flex items-center justify-between gap-4 border-b border-line px-5 py-4 sm:px-7">
          <div>
            <h2 className="font-display text-xl font-bold text-ink">Find the right {type === "car" ? "car" : "bike or scooter"}</h2>
            <p className="text-sm text-mute">On-road prices for {city}. Results change as you answer.</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden rounded-full border border-line p-0.5 sm:flex">
              {(["car", "bike"] as const).map((t) => (
                <button key={t} onClick={() => switchType(t)}
                        className={cn("rounded-full px-4 py-1.5 text-sm font-medium", type === t ? "bg-ink text-bg" : "text-mute hover:text-ink")}>
                  {t === "car" ? "Cars" : "Bikes"}
                </button>
              ))}
            </div>
            <button onClick={onClose} aria-label="Close" className="grid h-9 w-9 place-items-center rounded-full border border-line text-mute hover:text-ink">
              <X className="h-4 w-4" />
            </button>
          </div>
        </header>

        <div className="grid min-h-0 flex-1 lg:grid-cols-[380px_1fr]">
          <div className="overflow-y-auto border-line px-5 py-5 sm:px-7 lg:border-r">
            <div className="mb-4 flex rounded-full border border-line p-0.5 sm:hidden">
              {(["car", "bike"] as const).map((t) => (
                <button key={t} onClick={() => switchType(t)}
                        className={cn("flex-1 rounded-full py-1.5 text-sm font-medium", type === t ? "bg-ink text-bg" : "text-mute")}>
                  {t === "car" ? "Cars" : "Bikes"}
                </button>
              ))}
            </div>

            <Question title="Budget" hint="On-road, including road tax and insurance">
              <div className="flex flex-wrap gap-2">
                {BUDGETS[type].map((b) => (
                  <Choice key={b} on={budget === b} onClick={() => setBudget(b)}>{b ? `Under ${lakh(b)}` : "Any"}</Choice>
                ))}
              </div>
            </Question>

            <Question title="Where you'll ride it most">
              <div className="flex flex-wrap gap-2">
                {USES.map((u) => <Choice key={u.id} on={usage === u.id} onClick={() => setUsage(u.id)}>{u.label}</Choice>)}
              </div>
            </Question>

            <Question title="What matters most" hint="Tap in order of importance">
              <div className="flex flex-wrap gap-2">
                {PRIOS.filter((p) => type === "car" || !p.car).map((p) => {
                  const rank = prios.indexOf(p.id);
                  return (
                    <Choice key={p.id} on={rank >= 0} onClick={() => togglePrio(p.id)}>
                      {rank >= 0 && <span className="mr-1.5 font-mono text-xs">{rank + 1}</span>}{p.label}
                    </Choice>
                  );
                })}
              </div>
            </Question>

            <section className="py-5">
              <button onClick={() => setMore((m) => !m)} className="text-sm font-semibold text-ink underline-offset-4 hover:underline">
                {more ? "Fewer options" : `More options${moreCount ? ` (${moreCount})` : ""}`}
              </button>
              {more && (
                <div className="mt-4 space-y-5">
                  <div className="space-y-2">
                    <p className="text-sm text-mute">Fuel</p>
                    <div className="flex flex-wrap gap-2">{FUELS[type].map((f) => <Choice key={f} on={fuels.includes(f)} onClick={() => toggle(fuels, setFuels, f)}>{f}</Choice>)}</div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-mute">Gearbox</p>
                    <div className="flex flex-wrap gap-2">
                      {(["", "Manual", "Automatic"] as const).map((g) => <Choice key={g} on={gear === g} onClick={() => setGear(g)}>{g || "Either"}</Choice>)}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-mute">Body type</p>
                    <div className="flex flex-wrap gap-2">{BODIES[type].map((b) => <Choice key={b} on={bodies.includes(b)} onClick={() => toggle(bodies, setBodies, b)}>{b}</Choice>)}</div>
                  </div>
                  {type === "car" && (
                    <div className="space-y-2">
                      <p className="text-sm text-mute">Seats</p>
                      <div className="flex flex-wrap gap-2">
                        {[0, 5, 7].map((n) => <Choice key={n} on={seats === n} onClick={() => setSeats(n)}>{n ? `${n} or more` : "Any"}</Choice>)}
                      </div>
                    </div>
                  )}
                  {(allBrands ?? []).length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm text-mute">Brands</p>
                      <div className="flex flex-wrap gap-2">
                        {(allBrands ?? []).filter((b) => b.models > 0).map((b) => (
                          <Choice key={b.slug} on={brands.includes(b.slug)} onClick={() => toggle(brands, setBrands, b.slug)}>{b.name}</Choice>
                        ))}
                      </div>
                    </div>
                  )}
                  {moreCount > 0 && (
                    <button onClick={() => { setFuels([]); setGear(""); setBodies([]); setBrands([]); setSeats(0); }}
                            className="text-sm text-mute underline underline-offset-4 hover:text-ink">Clear these</button>
                  )}
                </div>
              )}
            </section>
          </div>

          <div className="min-h-0 overflow-y-auto px-5 py-5 sm:px-7">
            <p className="mb-4 text-sm text-mute">
              {isLoading && !recs ? "Looking…" : error ? "Couldn't load matches. Please try again." :
                recs && recs.length ? `${pool > recs.length ? `Top ${recs.length} of ${pool}` : recs.length} ${recs.length === 1 ? "match" : "matches"}` : "No matches"}
            </p>
            {isLoading && !recs && <div className="grid gap-3 md:grid-cols-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-36 w-full" />)}</div>}
            {recs && recs.length === 0 && (
              <p className="max-w-sm text-sm text-mute">Nothing fits all of this in {city}. Try a higher budget or fewer options.</p>
            )}
            <ol className="grid gap-3 md:grid-cols-2">
              {(recs ?? []).map((r, i) => (
                <li key={r.id}>
                  <Link href={`/cars/${r.id}`} onClick={onClose}
                        className="group flex h-full gap-4 rounded-2xl border border-line bg-panel p-4 transition hover:border-mute">
                    <div className="relative h-20 w-28 shrink-0 overflow-hidden rounded-xl bg-panel-soft">
                      {r.image_url && /* eslint-disable-next-line @next/next/no-img-element */
                        <img src={r.image_url} alt="" className="h-full w-full object-contain" loading="lazy" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline justify-between gap-2">
                        <p className="truncate text-xs text-mute"><span className="mr-1.5 font-mono">{i + 1}</span>{r.brand}</p>
                        <span className="shrink-0 font-mono text-xs text-mute">{Math.round(r.match_score)}% fit</span>
                      </div>
                      <p className="truncate font-semibold text-ink group-hover:underline">{r.name}</p>
                      <p className="text-sm text-ink">{lakh(r.from_inr)}{r.to_inr > r.from_inr ? ` – ${lakh(r.to_inr)}` : ""} <span className="text-mute">on-road</span></p>
                      {r.variant && <p className="truncate text-xs text-mute">Best fit: {r.variant}</p>}
                      <ul className="mt-2 space-y-0.5 text-xs text-mute">
                        {r.reasons.slice(0, 2).map((x) => <li key={x}>{x}</li>)}
                        {(r.warnings ?? []).slice(0, 1).map((x) => <li key={x} className="text-accent">{x}</li>)}
                      </ul>
                    </div>
                  </Link>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
