"use client";

// The buyer's city drives everything: the ex-showroom list (where the brand publishes one per city) and the state's
// road tax / registration rules. Saved per visitor; "Use my location" picks the nearest supported city.

import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import useSWR from "swr";
import { Check, LocateFixed, MapPin, Search } from "lucide-react";
import { toast } from "sonner";
import { fetcher } from "@/lib/api";
import { cn } from "@/components/ui";

export type City = { name: string; state: string; state_name: string; tax_rules: string; city_prices: number; lat: number; lng: number };

const KEY = "onroad.city";

// External store over localStorage: the server (and hydration) render Hyderabad, then React switches to the saved
// city without a hydration mismatch.
const listeners = new Set<() => void>();
let memory: string | null = null;
const read = () => {
  if (memory) return memory;
  try { memory = localStorage.getItem(KEY); } catch { /* storage blocked */ }
  return memory ?? "Hyderabad";
};
const subscribe = (fn: () => void) => { listeners.add(fn); return () => { listeners.delete(fn); }; };
const write = (c: string) => {
  memory = c;
  try { localStorage.setItem(KEY, c); } catch { /* storage blocked */ }
  listeners.forEach((fn) => fn());
};

/** Kept for the layout; the city itself is read per component (below) so each one hydrates with the server's value. */
export function CityProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

export function useCity() {
  const city = useSyncExternalStore(subscribe, read, () => "Hyderabad");
  return { city, setCity: write };
}

/** Appends ?city= / &city= to an API path. */
export function withCity(path: string, city: string) {
  return `${path}${path.includes("?") ? "&" : "?"}city=${encodeURIComponent(city)}`;
}

function nearest(cities: City[], lat: number, lng: number) {
  const d = (c: City) => (c.lat - lat) ** 2 + ((c.lng - lng) * Math.cos((lat * Math.PI) / 180)) ** 2;
  return [...cities].sort((a, b) => d(a) - d(b))[0];
}

export function CityPicker({ className, onDone }: { className?: string; onDone?: () => void }) {
  const { city, setCity } = useCity();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [locating, setLocating] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const { data: cities } = useSWR<City[]>("/cities", fetcher);

  useEffect(() => {
    const close = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const list = useMemo(() => (cities ?? []).filter((c) => `${c.name} ${c.state_name}`.toLowerCase().includes(q.toLowerCase())), [cities, q]);
  const pick = (name: string) => { setCity(name); setOpen(false); setQ(""); onDone?.(); };

  function locate() {
    if (!navigator.geolocation || !cities) return toast.error("Location isn't available in this browser");
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => { const c = nearest(cities, pos.coords.latitude, pos.coords.longitude); setLocating(false); setGeo(pos.coords.latitude, pos.coords.longitude); pick(c.name); toast.success(`Showing prices for ${c.name}, ${c.state_name}`); },
      () => { setLocating(false); toast.error("Couldn't get your location. Pick your city instead."); },
      { timeout: 10000, maximumAge: 600000 },
    );
  }

  return (
    <div ref={box} className={cn("relative", className)}>
      <button onClick={() => setOpen(!open)} aria-label="Choose city"
        className="flex h-9 items-center gap-1.5 rounded-full border border-line bg-panel-soft px-3 text-sm sm:px-3.5 text-ink hover:border-line/80 font-medium cursor-pointer shadow-xs">
        <MapPin className="h-4 w-4 text-accent" /><span className="max-w-[84px] truncate sm:max-w-[110px]">{city}</span>
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-[320px] overflow-hidden rounded-2xl border border-line bg-panel shadow-2xl backdrop-blur-xl">
          <div className="border-b border-line p-3.5 bg-panel-soft/60">
            <p className="text-xs text-mute font-medium">Prices and road tax follow your city</p>
            <button onClick={locate} disabled={locating} className="mt-2.5 flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-3 py-2 text-xs font-semibold text-white hover:brightness-110 shadow-xs cursor-pointer">
              <LocateFixed className="h-3.5 w-3.5" />{locating ? "Finding you…" : "Use my location"}
            </button>
            <div className="mt-2.5 flex items-center gap-2 rounded-xl border border-line bg-panel px-3">
              <Search className="h-3.5 w-3.5 text-mute" />
              <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search city or state"
                className="h-9 w-full bg-transparent text-xs text-ink placeholder:text-mute focus:outline-none" />
            </div>
          </div>
          <div data-lenis-prevent className="max-h-72 overflow-auto p-1.5 scroll-thin">
            {list.map((c) => (
              <button key={c.name} onClick={() => { setGeo(c.lat, c.lng); pick(c.name); }} className={cn("flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left transition cursor-pointer", c.name === city ? "bg-accent/10 border border-accent/20" : "hover:bg-panel-soft")}>
                <span>
                  <span className="block text-sm font-semibold text-ink">{c.name}</span>
                  <span className="block text-xs text-mute">{c.state_name}{c.city_prices ? ` · city prices for ${c.city_prices} variants` : ""}</span>
                </span>
                {c.name === city && <Check className="h-4 w-4 text-accent shrink-0" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── The buyer's exact location (only after they tap "Use my location"): nearest showrooms + real distances ──
const GEO_KEY = "onroad.geo";
const geoListeners = new Set<() => void>();
let geoMem: string | null | undefined;
const readGeo = () => {
  if (geoMem === undefined) { try { geoMem = localStorage.getItem(GEO_KEY); } catch { geoMem = null; } }
  return geoMem ?? "";
};
export function setGeo(lat: number, lng: number) {
  geoMem = `${lat.toFixed(5)},${lng.toFixed(5)}`;
  try { localStorage.setItem(GEO_KEY, geoMem); } catch { /* storage blocked */ }
  geoListeners.forEach((f) => f());
}
/** "&lat=..&lng=.." when the buyer shared their location, else "". */
export function useGeoQuery() {
  const g = useSyncExternalStore((f) => { geoListeners.add(f); return () => { geoListeners.delete(f); }; }, readGeo, () => "");
  if (!g) return "";
  const [lat, lng] = g.split(",");
  return `&lat=${lat}&lng=${lng}`;
}
