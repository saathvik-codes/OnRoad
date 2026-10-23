"use client";

import { useState } from "react";
import useSWR from "swr";
import { AlertTriangle, BadgeCheck } from "lucide-react";
import { fetcher, type Breakdown, type Variant } from "@/lib/api";
import { inr } from "@/lib/format";
import { BreakdownView } from "@/components/breakdown";
import { CarPicker } from "@/components/car-picker";
import { useCity, type City } from "@/components/city";
import { Card, Input, Label, SectionTitle, Select, Skeleton } from "@/components/ui";

type State = { code: string; name: string; coverage: string | null };

export default function CalculatorPage() {
  const [mode, setMode] = useState<"car" | "price">("car");
  const [variant, setVariant] = useState<(Variant & { model: string; brand: string }) | null>(null);
  const [price, setPrice] = useState("1000000");
  const [stateOverride, setState] = useState<string | null>(null);
  const [fuel, setFuel] = useState("Petrol");
  const [cc, setCc] = useState("1197");
  const [loan, setLoan] = useState(false);
  const [ownership, setOwnership] = useState("first_vehicle");
  const [quote, setQuote] = useState("");
  const { data: states } = useSWR<State[]>("/states", fetcher);
  const { city } = useCity();
  const { data: cities } = useSWR<City[]>("/cities", fetcher);
  const state = stateOverride ?? cities?.find((x) => x.name === city)?.state ?? "TS";

  const exs = mode === "car" ? variant?.ex_showroom_inr : Number(price.replace(/\D/g, ""));
  const f = mode === "car" ? variant?.fuel ?? "Petrol" : fuel;
  const c = mode === "car" ? variant?.engine_cc ?? "" : cc;
  const key = exs && exs > 50_000
    ? `/onroad/quick?ex_showroom=${exs}&state=${state}&city=${encodeURIComponent(city)}&fuel=${encodeURIComponent(f)}${c ? `&engine_cc=${c}` : ""}&loan=${loan}&ownership=${ownership}${mode === "car" && variant ? `&variant_id=${encodeURIComponent(variant.id)}` : ""}`
    : null;
  const { data: b, isLoading } = useSWR<Breakdown>(key, fetcher);
  const q = Number(quote.replace(/\D/g, ""));
  const diff = b && q ? q - b.total_inr : 0;

  return (
    <main className="mx-auto max-w-7xl px-5 pt-28 pb-24">
      <SectionTitle eyebrow="On-road calculator" title="What you should really pay"
        sub="Road tax, registration, insurance, TCS and fees from each state's own rules, line by line with sources. Paste a dealer's quote to see if it's padded." />
      <div className="mt-10 grid gap-8 lg:grid-cols-[420px_1fr]">
        <Card className="h-fit space-y-5 p-6">
          <div className="flex rounded-full border border-line p-1 text-sm">
            {(["car", "price"] as const).map((m) => (
              <button key={m} onClick={() => setMode(m)} className={`flex-1 rounded-full py-2 ${mode === m ? "bg-white text-black" : "text-mute"}`}>
                {m === "car" ? "Pick a car" : "Type a price"}
              </button>
            ))}
          </div>
          {mode === "car" ? <CarPicker onPick={setVariant} /> : (
            <div className="space-y-4">
              <div><Label>Ex-showroom price (₹)</Label><Input inputMode="numeric" value={price} onChange={(e) => setPrice(e.target.value)} /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><Label>Fuel</Label><Select value={fuel} onChange={(e) => setFuel(e.target.value)}>
                  {["Petrol", "Diesel", "CNG", "Electric", "Hybrid"].map((x) => <option key={x}>{x}</option>)}</Select></div>
                <div><Label>Engine cc</Label><Input inputMode="numeric" value={cc} onChange={(e) => setCc(e.target.value)} disabled={fuel === "Electric"} /></div>
              </div>
            </div>
          )}
          <div><Label>State of registration</Label>
            <Select value={state} onChange={(e) => setState(e.target.value)}>
              {(states ?? [{ code: "TS", name: "Telangana", coverage: null }]).map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
            </Select></div>
          <div><Label>Registered as</Label>
            <Select value={ownership} onChange={(e) => setOwnership(e.target.value)}>
              <option value="first_vehicle">My first car</option><option value="second_vehicle">A second car in my name</option><option value="company">Company-owned</option>
            </Select></div>
          <label className="flex items-center gap-2 text-sm text-white/80">
            <input type="checkbox" checked={loan} onChange={(e) => setLoan(e.target.checked)} className="accent-[#ff4d2e]" /> Buying on a car loan (adds hypothecation)
          </label>
          <div className="border-t border-line pt-5">
            <Label hint="(optional)">Dealer&apos;s on-road quote (₹)</Label>
            <Input inputMode="numeric" value={quote} onChange={(e) => setQuote(e.target.value)} placeholder="e.g. 1312000" />
          </div>
        </Card>

        <div className="space-y-5">
          {b && q > 0 && (
            <Card className={`flex items-start gap-3 p-5 ${diff > 5000 ? "border-amber-400/40" : "border-emerald-400/40"}`}>
              {diff > 5000 ? <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-300" /> : <BadgeCheck className="mt-0.5 h-5 w-5 text-emerald-300" />}
              <div>
                <p className="font-semibold text-white">{diff > 5000 ? `The quote is ${inr(diff)} above the statutory on-road price` : "The quote is fair"}</p>
                <p className="text-sm text-mute">
                  {diff > 5000 ? "Ask the dealer to itemise it. Common padding: \"handling\" or \"logistics\" charges, bundled accessories, extended warranty and dealer insurance you can buy cheaper yourself. You can refuse all of them."
                    : diff < -5000 ? `It's ${inr(-diff)} below our estimate: a genuine discount. Get it in writing.` : "It matches the statutory charges closely."}
                </p>
              </div>
            </Card>
          )}
          {b ? <BreakdownView b={b} /> : isLoading ? <Skeleton className="h-[480px]" /> : (
            <Card className="grid h-[420px] place-items-center p-10 text-center text-mute">
              {mode === "car" ? "Search a car and choose a variant to see its on-road price." : "Enter an ex-showroom price above ₹50,000."}
            </Card>
          )}
        </div>
      </div>
    </main>
  );
}
