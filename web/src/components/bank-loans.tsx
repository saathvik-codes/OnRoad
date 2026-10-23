"use client";

// EMI calculator with car-loan rate ranges read daily from each bank's own rate page (/api/loan-rates).
// The rate you get depends on your credit profile, so we show EMI at both ends of each published range.

import { useMemo, useState } from "react";
import useSWR from "swr";
import { ExternalLink, Landmark } from "lucide-react";
import { fetcher } from "@/lib/api";
import { ago, inr } from "@/lib/format";
import { Card, cn, Input, Label } from "@/components/ui";

type Rate = { bank: string; product: string; ev_only: number; min_pct: number; max_pct: number; source_url: string; fetched_at: string };

const OTHER_BANKS = [
  { name: "HDFC Bank", url: "https://www.hdfcbank.com/personal/borrow/popular-loans/new-car-loan" },
  { name: "ICICI Bank", url: "https://www.icicibank.com/personal-banking/loans/car-loan" },
  { name: "Bank of Baroda", url: "https://www.bankofbaroda.in/personal-banking/loans/vehicle-loan" },
  { name: "Kotak Mahindra Bank", url: "https://www.kotak.com/en/personal-banking/loans/car-loan.html" },
];

export function emi(principal: number, annualRatePct: number, months: number) {
  const r = annualRatePct / 1200;
  if (!principal || !months) return 0;
  if (!r) return principal / months;
  return (principal * r * (1 + r) ** months) / ((1 + r) ** months - 1);
}

export function BankLoansComparison({ onRoadPriceInr, variantName, isEV, vehicleType }: { onRoadPriceInr: number; variantName: string; isEV?: boolean; vehicleType?: string }) {
  const isBike = vehicleType === "bike";
  const { data: rates } = useSWR<Rate[]>(isBike ? null : "/loan-rates", fetcher);
  const [down, setDown] = useState("");
  const downInr = down === "" ? Math.round(onRoadPriceInr * 0.2) : Number(down.replace(/\D/g, "") || 0);
  const [rate, setRate] = useState("");
  const [years, setYears] = useState(5);
  const principal = Math.max(0, onRoadPriceInr - downInr);
  const months = years * 12;
  const r = Number(rate);
  const monthly = useMemo(() => emi(principal, r, months), [principal, r, months]);
  const list = (rates ?? []).filter((x) => !x.ev_only || isEV);

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
      <Card className="space-y-5 p-6">
        <div className="flex items-center gap-2"><Landmark className="h-5 w-5 text-accent" /><p className="font-semibold text-ink">EMI for {variantName}</p></div>
        <div><Label>On-road price</Label><p className="font-mono text-lg font-bold text-ink">{inr(onRoadPriceInr)}</p></div>
        <div><Label hint="(₹)">Down payment</Label><Input inputMode="numeric" value={down} placeholder={String(Math.round(onRoadPriceInr * 0.2))} onChange={(e) => setDown(e.target.value)} /></div>
        <div>
          <Label hint="(% a year)">Interest rate</Label>
          <Input inputMode="decimal" value={rate} placeholder="Pick a bank on the right, or type your offer" onChange={(e) => setRate(e.target.value.replace(/[^\d.]/g, ""))} />
        </div>
        <div>
          <Label>Tenure: {years} years</Label>
          <input type="range" min={1} max={7} value={years} onChange={(e) => setYears(Number(e.target.value))} className="w-full accent-[#ff4d2e]" />
        </div>
        {r > 0 && (
          <div className="rounded-2xl border border-line bg-panel-soft p-4">
            <p className="text-sm text-mute">Monthly EMI at {r}%</p>
            <p className="font-mono text-3xl font-black text-ink">{inr(monthly)}</p>
            <p className="mt-2 text-xs text-mute">Loan {inr(principal)} · interest {inr(monthly * months - principal)} · total repaid {inr(monthly * months)}</p>
          </div>
        )}
      </Card>

      <Card className="p-6">
        <p className="font-semibold text-ink">{isBike ? "Two-wheeler loans" : "Car-loan rates published by banks"}</p>
        <p className="mt-1 text-xs text-mute">Read daily from each bank&apos;s own rate page. Your rate within the range depends on your credit score and profile.</p>
        <div className="mt-4 divide-y divide-line">
          {list.map((x) => (
            <button key={x.product} onClick={() => setRate(String(x.min_pct))}
              className={cn("flex w-full flex-wrap items-center justify-between gap-2 py-3 text-left", Number(rate) === x.min_pct && "text-accent")}>
              <span>
                <span className="block text-sm font-medium text-ink">{x.product}</span>
                <span className="block text-xs text-mute">{x.max_pct ? `${x.min_pct}% – ${x.max_pct}%` : `from ${x.min_pct}%`} a year · read {ago(x.fetched_at)} ·{" "}
                  <a href={x.source_url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()} className="text-accent-2 hover:underline">source</a></span>
              </span>
              <span className="text-right font-mono text-sm text-ink">
                {x.max_pct ? `${inr(emi(principal, x.min_pct, months))} – ${inr(emi(principal, x.max_pct, months))}` : `from ${inr(emi(principal, x.min_pct, months))}`}<span className="block text-[11px] font-sans text-mute">EMI a month</span>
              </span>
            </button>
          ))}
          {isBike && <p className="py-3 text-sm text-mute">Banks don&apos;t publish two-wheeler loan rates in a form we can read reliably. Ask your bank or the showroom&apos;s finance desk for the rate, enter it on the left, and compare.</p>}
          {!isBike && rates && list.length === 0 && <p className="py-3 text-sm text-mute">No bank rates could be read today.</p>}
        </div>
        <p className="mt-5 text-xs font-semibold uppercase tracking-wide text-mute">{isBike ? "Two-wheeler loans at" : "Check rates directly"}</p>
        <ul className="mt-1 grid gap-x-6 sm:grid-cols-2">
          {OTHER_BANKS.map((b) => (
            <li key={b.name}><a href={b.url} target="_blank" rel="noreferrer" className="flex items-center justify-between py-1.5 text-sm text-ink hover:text-accent">{b.name}<ExternalLink className="h-3.5 w-3.5 text-mute" /></a></li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
