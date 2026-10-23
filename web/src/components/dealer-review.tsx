"use client";

// Buyers rate the showroom they dealt with: overall stars, price honesty, add-on pressure, delivery. First-party data.

import { useState } from "react";
import { toast } from "sonner";
import { Star } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { cn } from "@/components/ui";

export function RatingSummary({ rating, count, noAddons }: { rating?: number | null; count?: number | null; noAddons?: number | null }) {
  if (!rating || !count) return null;
  return (
    <span className="rounded-md border border-line bg-panel-soft px-2 py-0.5 text-ink">
      ★ {rating.toFixed(1)} <span className="text-mute">({count} OnRoad buyer{count > 1 ? "s" : ""}{noAddons != null ? ` · ${Math.round(noAddons * 100)}% no forced add-ons` : ""})</span>
    </span>
  );
}

export function RateShowroom({ dealerId, onDone }: { dealerId: string; onDone?: () => void }) {
  const [open, setOpen] = useState(false);
  const [rating, setRating] = useState(0);
  const [honest, setHonest] = useState(0);
  const [noAddons, setNoAddons] = useState<boolean | null>(null);
  const [onTime, setOnTime] = useState<boolean | null>(null);
  const [visit, setVisit] = useState("purchase");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  if (!open) return (
    <button onClick={(e) => { e.stopPropagation(); setOpen(true); }} className="text-xs text-accent hover:underline">Rate this showroom</button>
  );
  const stars = (v: number, set: (n: number) => void) => (
    <span className="inline-flex">{[1, 2, 3, 4, 5].map((n) => (
      <button key={n} type="button" aria-label={`${n} stars`} onClick={() => set(n)}><Star className={cn("h-5 w-5", n <= v ? "fill-amber-400 text-amber-400" : "text-mute/40")} /></button>
    ))}</span>
  );
  const yesNo = (v: boolean | null, set: (b: boolean) => void) => (
    <span className="inline-flex gap-1">{([true, false] as const).map((b) => (
      <button key={String(b)} type="button" onClick={() => set(b)}
        className={cn("rounded-full border px-2.5 py-0.5 text-xs", v === b ? "border-accent bg-accent text-white" : "border-line text-mute")}>{b ? "Yes" : "No"}</button>
    ))}</span>
  );
  async function send() {
    if (!rating) return toast.error("Pick an overall rating");
    setBusy(true);
    try {
      await api("/dealer-reviews", { method: "POST", body: JSON.stringify({ dealer_id: dealerId, rating, price_honesty: honest || null,
        no_forced_addons: noAddons, delivery_on_time: onTime, visit, text }) });
      toast.success("Thanks, your review is live"); setOpen(false); onDone?.();
    } catch (e) {
      toast.error(e instanceof ApiError && e.status === 401 ? "Log in to review a showroom" : (e as Error).message);
    } finally { setBusy(false); }
  }
  return (
    <div onClick={(e) => e.stopPropagation()} className="mt-3 space-y-2.5 rounded-2xl border border-line bg-panel-soft p-3 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2"><span className="text-ink">Overall</span>{stars(rating, setRating)}</div>
      <div className="flex flex-wrap items-center justify-between gap-2"><span className="text-mute">Final bill matched the quote</span>{stars(honest, setHonest)}</div>
      <div className="flex flex-wrap items-center justify-between gap-2"><span className="text-mute">No pressure for add-ons / handling fees</span>{yesNo(noAddons, setNoAddons)}</div>
      <div className="flex flex-wrap items-center justify-between gap-2"><span className="text-mute">Delivered on the promised date</span>{yesNo(onTime, setOnTime)}</div>
      <select value={visit} onChange={(e) => setVisit(e.target.value)} className="h-8 w-full rounded-lg border border-line bg-panel px-2 text-xs text-ink">
        <option value="purchase">I bought here</option><option value="enquiry">I visited / took a quote</option><option value="service">I serviced my vehicle here</option>
      </select>
      <textarea value={text} onChange={(e) => setText(e.target.value)} rows={2} maxLength={1200} placeholder="What should other buyers know?"
        className="w-full rounded-lg border border-line bg-panel p-2 text-xs text-ink" />
      <div className="flex justify-end gap-2">
        <button onClick={() => setOpen(false)} className="text-xs text-mute">Cancel</button>
        <button onClick={send} disabled={busy} className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-white">{busy ? "Saving…" : "Post review"}</button>
      </div>
    </div>
  );
}
