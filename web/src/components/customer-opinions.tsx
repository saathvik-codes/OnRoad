"use client";

import { useState } from "react";
import useSWR, { mutate } from "swr";
import { 
  Star, 
  MessageSquare, 
  ShieldCheck, 
  Fuel, 
  Wrench, 
  CheckCircle2, 
  AlertCircle, 
  PlusCircle, 
  X, 
  ThumbsUp,
  MapPin,
  Calendar,
  
} from "lucide-react";
import { toast } from "sonner";
import { fetcher } from "@/lib/api";
import { useCity } from "@/components/city";
import { Button, Card, cn, Input, Label, Skeleton } from "@/components/ui";

interface Opinion {
  id: number;
  model_id: string;
  model_name: string;
  vehicle_type: "car" | "bike";
  author_name: string;
  city: string;
  rating: number;
  ownership_period: string;
  real_mileage: string;
  annual_service_cost: string;
  pros: string;
  cons: string;
  verdict: string;
  verified_buyer: number;
  created_at: string;
}

export function CustomerOpinions() {
  const { city } = useCity();
  const [filterType, setFilterType] = useState<"all" | "car" | "bike">("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  // Form state
  const [authorName, setAuthorName] = useState("");
  const [userCity, setUserCity] = useState(city || "Hyderabad");
  const [modelName, setModelName] = useState("");
  const [vehicleType, setVehicleType] = useState<"car" | "bike">("car");
  const [rating, setRating] = useState("5.0");
  const [ownershipPeriod, setOwnershipPeriod] = useState("");
  const [realMileage, setRealMileage] = useState("");
  const [annualServiceCost, setAnnualServiceCost] = useState("");
  const [pros, setPros] = useState("");
  const [cons, setCons] = useState("");
  const [verdict, setVerdict] = useState("");

  const url = filterType === "all" ? "/opinions" : `/opinions?vehicle_type=${filterType}`;
  const { data: opinions, isLoading } = useSWR<Opinion[]>(url, fetcher);

  async function handleSubmitOpinion(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await fetch("/api/opinions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_id: modelName.toLowerCase().replace(/[^a-z0-9]/g, "_"),
          model_name: modelName,
          vehicle_type: vehicleType,
          author_name: authorName,
          city: userCity,
          rating: parseFloat(rating) || 5.0,
          ownership_period: ownershipPeriod,
          real_mileage: realMileage,
          annual_service_cost: annualServiceCost,
          pros,
          cons,
          verdict
        })
      });
      if (res.status === 401) throw new Error("Please log in to post a review");
      if (!res.ok) throw new Error("Could not submit review");
      toast.success("Thank you! Your owner review is live.");
      setModalOpen(false);
      mutate(url);
      // Reset fields
      setModelName("");
      setPros("");
      setCons("");
      setVerdict("");
    } catch (err) {
      toast.error((err as Error).message || "Submission failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-7xl px-4 sm:px-6 py-16 sm:py-20 border-t border-line/60">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-8 border-b border-line">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 border border-emerald-500/25 px-3 py-1 text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-3">
            <MessageSquare className="h-3.5 w-3.5" />
            OWNER REVIEWS
          </div>
          <h2 className="font-[family-name:var(--font-display)] text-3xl sm:text-5xl font-black text-ink tracking-tight">
            Real Customer Opinions & Mileage
          </h2>
          <p className="mt-2 text-xs sm:text-base text-mute max-w-2xl leading-relaxed">
            Reports posted by signed-in owners. Actual city mileage vs ARAI, annual authorized workshop service bills, and honest gotchas.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Filter Pills */}
          <div className="flex items-center rounded-2xl bg-panel-soft p-1 border border-line">
            {(["all", "car", "bike"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={cn(
                  "px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer",
                  filterType === t ? "bg-accent text-white shadow-xs" : "text-mute hover:text-ink"
                )}
              >
                {t === "all" ? "All Feedback" : t === "car" ? "Cars" : "Two-Wheelers"}
              </button>
            ))}
          </div>

          <Button
            onClick={() => setModalOpen(true)}
            className="bg-accent text-white hover:bg-accent/90 shadow-md shadow-accent/20 font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-1.5 cursor-pointer"
          >
            <PlusCircle className="h-4 w-4" /> Share Your Ownership Opinion
          </Button>
        </div>
      </div>

      {/* Opinions Grid */}
      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          [0, 1, 2].map((i) => <Skeleton key={i} className="h-72 rounded-3xl" />)
        ) : !opinions || opinions.length === 0 ? (
          <div className="col-span-full py-12 text-center text-mute text-sm">
            No reviews matching this filter yet. Be the first to share your experience!
          </div>
        ) : (
          opinions.map((op) => (
            <div
              key={op.id}
              className="flex flex-col justify-between rounded-3xl border border-line bg-panel p-6 shadow-sm hover:border-line/90 transition"
            >
              <div>
                {/* Header: Author + City + Rating */}
                <div className="flex items-start justify-between gap-2 border-b border-line/60 pb-3">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <p className="font-bold text-ink text-sm sm:text-base">{op.author_name}</p>
                      {op.verified_buyer ? (
                        <span className="inline-flex items-center text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded-md">
                          <ShieldCheck className="h-3 w-3 mr-0.5" /> Verified
                        </span>
                      ) : null}
                    </div>
                    <p className="flex items-center gap-1 text-xs text-mute mt-0.5">
                      <MapPin className="h-3 w-3 text-accent" /> {op.city} · {op.ownership_period}
                    </p>
                  </div>

                  <div className="flex items-center gap-1 rounded-xl bg-amber-500/10 border border-amber-500/20 px-2 py-1 text-xs font-black text-amber-500">
                    <Star className="h-3.5 w-3.5 fill-amber-500" />
                    <span>{op.rating.toFixed(1)}</span>
                  </div>
                </div>

                {/* Model Title */}
                <p className="mt-3 font-[family-name:var(--font-display)] text-lg font-bold text-ink">
                  {op.model_name}
                </p>

                {/* Metrics Matrix (Real Mileage + Service Cost) */}
                <div className="mt-3 grid grid-cols-2 gap-2 rounded-2xl bg-panel-soft p-3 border border-line/60 text-xs">
                  <div>
                    <span className="flex items-center gap-1 text-[11px] text-mute">
                      <Fuel className="h-3 w-3 text-accent" /> Real-World Fuel
                    </span>
                    <p className="mt-0.5 font-mono font-bold text-ink truncate text-[11px] sm:text-xs">
                      {op.real_mileage}
                    </p>
                  </div>

                  <div>
                    <span className="flex items-center gap-1 text-[11px] text-mute">
                      <Wrench className="h-3 w-3 text-good" /> Annual Upkeep
                    </span>
                    <p className="mt-0.5 font-mono font-bold text-good text-[11px] sm:text-xs">
                      {op.annual_service_cost}
                    </p>
                  </div>
                </div>

                {/* Pros & Cons */}
                <div className="mt-3.5 space-y-2 text-xs">
                  {op.pros && (
                    <div className="flex items-start gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-good shrink-0 mt-0.5" />
                      <p className="text-[11px] text-mute leading-relaxed">
                        <span className="font-semibold text-ink">What I Love: </span>
                        {op.pros}
                      </p>
                    </div>
                  )}

                  {op.cons && (
                    <div className="flex items-start gap-1.5">
                      <AlertCircle className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
                      <p className="text-[11px] text-mute leading-relaxed">
                        <span className="font-semibold text-ink">Watchout: </span>
                        {op.cons}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Verdict */}
              {op.verdict && (
                <div className="mt-4 pt-3 border-t border-line/60">
                  <p className="text-xs text-ink/80 italic leading-relaxed">
                    &ldquo;{op.verdict}&rdquo;
                  </p>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Share Opinion Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div data-lenis-prevent
            className="relative flex flex-col w-full max-w-lg max-h-[90vh] rounded-3xl border border-line bg-panel p-6 shadow-2xl overflow-y-auto no-scrollbar"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-line pb-4">
              <div>
                <h3 className="font-[family-name:var(--font-display)] text-xl font-bold text-ink">
                  Share Your Vehicle Experience
                </h3>
                <p className="text-xs text-mute mt-0.5">
                  Help fellow Indian buyers know true real-world mileage and maintenance.
                </p>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="rounded-full p-1.5 text-mute hover:bg-panel-soft hover:text-ink transition cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitOpinion} className="mt-5 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Your Name</Label>
                  <Input required placeholder="e.g. Saathvik R." value={authorName} onChange={(e) => setAuthorName(e.target.value)} />
                </div>
                <div>
                  <Label>City</Label>
                  <Input required placeholder="e.g. Hyderabad" value={userCity} onChange={(e) => setUserCity(e.target.value)} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Vehicle Model & Trim</Label>
                  <Input required placeholder="e.g. Tata Nexon Creative+ S" value={modelName} onChange={(e) => setModelName(e.target.value)} />
                </div>
                <div>
                  <Label>Type</Label>
                  <select
                    value={vehicleType}
                    onChange={(e) => setVehicleType(e.target.value as typeof vehicleType)}
                    className="w-full h-9 rounded-xl border border-line bg-panel-soft px-3 text-ink text-xs"
                  >
                    <option value="car">Car / SUV</option>
                    <option value="bike">Two-Wheeler</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Rating (1 - 5 ★)</Label>
                  <select
                    value={rating}
                    onChange={(e) => setRating(e.target.value)}
                    className="w-full h-9 rounded-xl border border-line bg-panel-soft px-3 text-ink text-xs"
                  >
                    <option value="5.0">5.0 ★ Excellent</option>
                    <option value="4.5">4.5 ★ Very Good</option>
                    <option value="4.0">4.0 ★ Good</option>
                    <option value="3.5">3.5 ★ Average</option>
                    <option value="3.0">3.0 ★ Below Average</option>
                  </select>
                </div>
                <div>
                  <Label>Ownership Duration & Kms</Label>
                  <Input placeholder="e.g. 14 months · 18,000 km" value={ownershipPeriod} onChange={(e) => setOwnershipPeriod(e.target.value)} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Real-World Mileage (City / Hwy)</Label>
                  <Input placeholder="e.g. 17.5 kmpl / 22.0 kmpl" value={realMileage} onChange={(e) => setRealMileage(e.target.value)} />
                </div>
                <div>
                  <Label>Annual Service Cost</Label>
                  <Input placeholder="e.g. ₹5,200/yr" value={annualServiceCost} onChange={(e) => setAnnualServiceCost(e.target.value)} />
                </div>
              </div>

              <div>
                <Label>What You Love (Pros)</Label>
                <Input placeholder="e.g. High crash safety, strong AC, rock-solid stability" value={pros} onChange={(e) => setPros(e.target.value)} />
              </div>

              <div>
                <Label>Things to Watch Out For (Cons)</Label>
                <Input placeholder="e.g. Mild turbo lag under 1500 RPM, firm suspension" value={cons} onChange={(e) => setCons(e.target.value)} />
              </div>

              <div>
                <Label>Final Verdict / OnRoad Savings</Label>
                <textarea
                  rows={3}
                  placeholder="e.g. Best family car for the price. Saved ₹24,000 using OnRoad's itemized breakdown to refuse dealer handling fees."
                  value={verdict}
                  onChange={(e) => setVerdict(e.target.value)}
                  className="w-full rounded-xl border border-line bg-panel-soft p-3 text-ink text-xs"
                />
              </div>

              <Button
                type="submit"
                disabled={busy}
                className="w-full bg-accent text-white font-bold h-10 rounded-xl cursor-pointer"
              >
                {busy ? "Submitting..." : "Publish owner review"}
              </Button>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
