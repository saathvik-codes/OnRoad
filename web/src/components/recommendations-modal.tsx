"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { 
  Sparkles, 
  X, 
  Car, 
  Bike, 
  Fuel, 
  IndianRupee, 
  CheckCircle2, 
  ArrowRight, 
  ThumbsUp,
  Shield,
  Zap,
  RotateCcw
} from "lucide-react";
import { fetcher } from "@/lib/api";
import { lakh, range } from "@/lib/format";
import { useCity, withCity } from "@/components/city";
import { Button, Card, cn, Skeleton } from "@/components/ui";
import { CarImage } from "@/components/car-image";

interface RecommendedModel {
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

interface MatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultVehicleType?: "car" | "bike";
}

export function RecommendationsModal({ isOpen, onClose, defaultVehicleType = "car" }: MatchModalProps) {
  const { city } = useCity();
  const [vehicleType, setVehicleType] = useState<"car" | "bike">(defaultVehicleType);
  const [usage, setUsage] = useState<"commute" | "family" | "performance">("commute");
  const [budget, setBudget] = useState<number | "any">(vehicleType === "car" ? 1500000 : 200000);
  const [fuel, setFuel] = useState<string>("any");

  // Fetch recommendations dynamically from the backend API
  const queryParams = new URLSearchParams({
    city,
    vehicle_type: vehicleType,
    usage,
    ...(budget !== "any" ? { budget: String(budget) } : {}),
    ...(fuel !== "any" ? { fuel } : {}),
  }).toString();

  const { data: recommendations, isLoading } = useSWR<RecommendedModel[]>(
    isOpen ? withCity(`/recommendations?${queryParams}`, city) : null,
    fetcher
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative flex flex-col w-full max-w-4xl max-h-[90vh] rounded-3xl border border-line bg-panel shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-line px-6 py-5 bg-panel-soft/60">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-accent/15 text-accent border border-accent/20">
              <Sparkles className="h-5 w-5" />
            </span>
            <div>
              <h2 className="text-xl font-bold text-ink font-[family-name:var(--font-display)]">
                Personalized Vehicle Match
              </h2>
              <p className="text-xs text-mute">
                Suggestions priced on-road for {city}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-mute hover:bg-panel-soft hover:text-ink transition cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body: Questionnaire Controls + Live Recommendations */}
        <div data-lenis-prevent className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Top Questionnaire Controls */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 rounded-2xl border border-line bg-panel-soft/60 p-4">
            {/* 1. Vehicle Type */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-mute mb-2 block">
                Vehicle Type
              </label>
              <div className="grid grid-cols-2 gap-1.5 p-1 rounded-xl bg-panel border border-line">
                <button
                  type="button"
                  onClick={() => {
                    setVehicleType("car");
                    setBudget(1500000);
                  }}
                  className={cn(
                    "flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer",
                    vehicleType === "car" ? "bg-accent text-white shadow-xs" : "text-mute hover:text-ink"
                  )}
                >
                  <Car className="h-3.5 w-3.5" /> Cars
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setVehicleType("bike");
                    setBudget(200000);
                  }}
                  className={cn(
                    "flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition",
                    vehicleType === "bike" ? "bg-accent text-white shadow-sm" : "text-mute hover:text-white"
                  )}
                >
                  <Bike className="h-3.5 w-3.5" /> Bikes
                </button>
              </div>
            </div>

            {/* 2. Primary Usage */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-mute mb-2 block">
                Primary Usage
              </label>
              <select
                value={usage}
                onChange={(e) => setUsage(e.target.value as typeof usage)}
                className="w-full h-9 rounded-xl border border-white/10 bg-black/40 px-3 text-xs text-white focus:outline-none focus:border-accent"
              >
                <option value="commute">Daily City Commute</option>
                <option value="family">Family & Long Distance</option>
                <option value="performance">Power & Highway Touring</option>
              </select>
            </div>

            {/* 3. Budget */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-mute mb-2 block">
                Target Budget
              </label>
              <select
                value={budget}
                onChange={(e) => setBudget(e.target.value === "any" ? "any" : Number(e.target.value))}
                className="w-full h-9 rounded-xl border border-white/10 bg-black/40 px-3 text-xs text-white focus:outline-none focus:border-accent"
              >
                {vehicleType === "car" ? (
                  <>
                    <option value={800000}>Under ₹8 Lakh</option>
                    <option value={1500000}>Under ₹15 Lakh</option>
                    <option value={2500000}>Under ₹25 Lakh</option>
                    <option value={5000000}>Under ₹50 Lakh</option>
                    <option value="any">Any Budget</option>
                  </>
                ) : (
                  <>
                    <option value={100000}>Under ₹1 Lakh</option>
                    <option value={200000}>Under ₹2 Lakh</option>
                    <option value={350000}>Under ₹3.5 Lakh</option>
                    <option value="any">Any Budget</option>
                  </>
                )}
              </select>
            </div>

            {/* 4. Fuel Preference */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-mute mb-2 block">
                Fuel / Powertrain
              </label>
              <select
                value={fuel}
                onChange={(e) => setFuel(e.target.value)}
                className="w-full h-9 rounded-xl border border-line bg-panel px-3 text-xs text-ink focus:outline-none focus:border-accent"
              >
                <option value="any">Any Powertrain</option>
                <option value="Petrol">Petrol</option>
                <option value="Electric">100% Electric (EV)</option>
                {vehicleType === "car" && <option value="Diesel">Diesel</option>}
                {vehicleType === "car" && <option value="CNG">CNG</option>}
              </select>
            </div>
          </div>

          {/* Results List */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-ink">
                Top Matches for your criteria in <span className="text-accent font-semibold">{city}</span>
              </p>
              <span className="text-xs text-mute">
                {recommendations ? `${recommendations.length} vehicles suggested` : "Analyzing profile..."}
              </span>
            </div>

            {isLoading ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-52 rounded-2xl" />
                ))}
              </div>
            ) : !recommendations || recommendations.length === 0 ? (
              <div className="text-center py-12 rounded-2xl border border-dashed border-line p-6">
                <p className="text-ink font-medium">No vehicles directly match this exact filter.</p>
                <p className="text-xs text-mute mt-1">Try relaxing the budget or fuel type preference.</p>
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={() => { setBudget("any"); setFuel("any"); }}
                  className="mt-4"
                >
                  <RotateCcw className="h-3.5 w-3.5" /> Reset Preferences
                </Button>
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {recommendations.map((m) => (
                  <div
                    key={m.id}
                    className="flex flex-col justify-between rounded-2xl border border-line bg-panel p-5 transition hover:border-accent/40 hover:shadow-lg"
                  >
                    <div>
                      {/* Top Match Bar */}
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="h-3 w-3" /> {m.match_score}% Match
                        </span>
                        <span className="text-xs text-mute">{m.body_type || "Standard"}</span>
                      </div>

                      {/* Image & Title */}
                      <div className="grid grid-cols-[1fr_90px] gap-3 items-center">
                        <div>
                          <p className="text-xs font-medium text-mute">{m.brand}</p>
                          <h3 className="font-[family-name:var(--font-display)] text-lg font-bold text-ink">
                            {m.name}
                          </h3>
                          <p className="mt-1 font-mono text-sm font-semibold text-ink">
                            {range(m.from_inr, m.to_inr)}
                          </p>
                          <p className="text-[11px] text-mute">
                            Ex-showroom · {m.variants} variants
                          </p>
                        </div>
                        <div className="relative aspect-[4/3] rounded-xl overflow-hidden bg-panel-soft border border-line p-1">
                          <CarImage
                            src={m.image_url}
                            alt={`${m.brand} ${m.name}`}
                            bodyType={m.body_type}
                            className="h-full w-full object-contain"
                          />
                        </div>
                      </div>

                      {/* Key Concrete Benefits */}
                      <div className="mt-4 space-y-1.5 border-t border-line pt-3">
                        {m.reasons.map((r, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-xs text-ink/90">
                            <CheckCircle2 className="h-3.5 w-3.5 text-accent shrink-0 mt-0.5" />
                            <span>{r}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Bottom Action */}
                    <div className="mt-5 border-t border-line pt-3 flex items-center justify-between">
                      <span className="text-xs text-mute">
                        Prices for {city}
                      </span>
                      <Link
                        href={`/cars/${m.id}`}
                        onClick={onClose}
                        className="inline-flex items-center gap-1.5 text-xs font-semibold text-accent hover:underline"
                      >
                        View On-Road Price & Variants <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="border-t border-line bg-panel-soft/60 px-6 py-4 flex items-center justify-between">
          <p className="text-xs text-mute">
            Calculated with official road tax rules for {city}
          </p>
          <Button size="sm" variant="outline" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  );
}
