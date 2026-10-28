"use client";

import { useState, useMemo } from "react";
import { 
  ShieldCheck, 
  Check, 
  ExternalLink, 
  Info, 
  AlertTriangle, 
  Percent, 
  ArrowRight, 
    Zap,
  Building,
  CheckCircle2,
  HelpCircle
} from "lucide-react";
import { inr } from "@/lib/format";
import { Button, cn } from "@/components/ui";

export interface InsurancePartner {
  id: string;
  name: string;
  logoText: string;
  badge: string;
  rating: number;
  claimRatio: string;
  garages: string;
  baseRateMultiplier: number; // vs standard IRDAI OD tariff
  highlights: string[];
  recommendedAddons: string[];
}

export const PARTNERS: InsurancePartner[] = [
  {
    id: "acko",
    name: "Acko General Insurance",
    logoText: "ACKO",
    badge: "Direct Digital (Zero Dealer Markup)",
    rating: 4.6,
    claimRatio: "97.8%",
    garages: "7,000+ Cashless",
    baseRateMultiplier: 0.72, // ~28% cheaper than dealer markup
    highlights: ["1-hour claim pickup", "Direct zero-commission pricing", "Instant digital paperless policy"],
    recommendedAddons: ["zero_dep", "engine_protect", "rti", "rsa"],
  },
  {
    id: "digit",
    name: "Go Digit General Insurance",
    logoText: "DIGIT",
    badge: "High Claim Speed",
    rating: 4.7,
    claimRatio: "96.5%",
    garages: "8,200+ Cashless",
    baseRateMultiplier: 0.76, // ~24% cheaper
    highlights: ["Smartphone video self-inspection", "7-year zero depreciation eligibility", "Zero paperwork"],
    recommendedAddons: ["zero_dep", "engine_protect", "consumables"],
  },
  {
    id: "hdfc_ergo",
    name: "HDFC ERGO General Insurance",
    logoText: "HDFC ERGO",
    badge: "Largest Cashless Network",
    rating: 4.8,
    claimRatio: "98.4%",
    garages: "12,000+ Cashless",
    baseRateMultiplier: 0.82, // ~18% cheaper
    highlights: ["Overnight minor repair guarantee", "Highest industry settlement ratio", "Original OEM parts warranty"],
    recommendedAddons: ["zero_dep", "engine_protect", "rti", "consumables", "rsa"],
  },
  {
    id: "icici_lombard",
    name: "ICICI Lombard",
    logoText: "ICICI LOMBARD",
    badge: "Doorstep Concierge",
    rating: 4.7,
    claimRatio: "97.5%",
    garages: "10,500+ Cashless",
    baseRateMultiplier: 0.85, // ~15% cheaper
    highlights: ["24x7 doorstep claim assistance", "Dedicated relationship manager", "Accidental towing allowance"],
    recommendedAddons: ["zero_dep", "engine_protect", "rsa"],
  },
];

interface InsurancePartnersProps {
  exShowroomPrice: number;
  engineCc?: number | null;
  fuelType?: string | null;
  modelName: string;
  city: string;
  onSelectPartner?: (partnerId: string, quoteAmount: number) => void;
  onRequestQuote?: () => void;
}

export function InsurancePartnersComparison({
  exShowroomPrice,
  engineCc,
  fuelType,
  modelName,
  city,
  onSelectPartner,
  onRequestQuote,
}: InsurancePartnersProps) {
  // Add-on covers state
  const [zeroDep, setZeroDep] = useState(true);
  const [engineProtect, setEngineProtect] = useState(true);
  const [rti, setRti] = useState(false);
  const [rsa, setRsa] = useState(true);
  const [consumables, setConsumables] = useState(false);

  // Insured Declared Value (IDV) = 95% of Ex-Showroom for brand new cars
  const idv = useMemo(() => Math.round(exShowroomPrice * 0.95), [exShowroomPrice]);

  // Mandatory 3-Year Third Party Premium per IRDAI Tariff
  const tpPremium = useMemo(() => {
    const isEv = fuelType?.toLowerCase().includes("electric");
    if (isEv) return 4038;
    const cc = engineCc || 1200;
    if (cc < 1000) return 5288;
    if (cc <= 1500) return 9534;
    return 24596;
  }, [engineCc, fuelType]);

  // Base 1-Year Comprehensive Own Damage (OD) benchmark
  const baseOdPremium = useMemo(() => Math.round(idv * 0.0175), [idv]);

  // Add-ons cost calculation (percentages of IDV or flat charges)
  const addonsCost = useMemo(() => {
    let cost = 0;
    if (zeroDep) cost += Math.round(idv * 0.0065); // ~0.65% for Zero Dep
    if (engineProtect) cost += Math.round(idv * 0.0025); // ~0.25% for Engine Protect
    if (rti) cost += Math.round(idv * 0.0040); // ~0.40% for Return to Invoice
    if (rsa) cost += 1200; // Flat RSA
    if (consumables) cost += Math.round(idv * 0.0015); // ~0.15% Consumables
    return cost;
  }, [idv, zeroDep, engineProtect, rti, rsa, consumables]);

  // Dealer Showroom Estimate (typically 40% markup on OD + high commission)
  const dealerQuote = useMemo(() => {
    const odWithMarkup = Math.round(baseOdPremium * 1.45) + Math.round(addonsCost * 1.35);
    return Math.round((tpPremium + odWithMarkup) * 1.18); // with 18% GST
  }, [baseOdPremium, addonsCost, tpPremium]);

  return (
    <div className="space-y-5 rounded-2xl border border-line bg-panel p-5 sm:p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              <ShieldCheck className="h-4 w-4" />
            </span>
            <h3 className="font-[family-name:var(--font-display)] text-lg sm:text-xl font-bold text-ink">
              Insurance Partner Quotes & Add-On Customizer
            </h3>
          </div>
          <p className="text-xs text-mute mt-1 leading-relaxed">
            By IRDAI regulation, you are legally entitled to purchase insurance directly from any insurer. Dealership insurance markups average ₹15,000–₹35,000 higher.
          </p>
        </div>

        <div className="text-right">
          <span className="text-[10px] uppercase tracking-wider text-mute block font-semibold">
            Insured Declared Value (IDV)
          </span>
          <span className="font-mono text-base font-bold text-ink">
            {inr(idv)}
          </span>
        </div>
      </div>

      {/* Interactive Add-On Toggles */}
      <div className="rounded-xl border border-line bg-panel-soft/60 p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-ink uppercase tracking-wider flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5 text-accent" />
            Customize Policy Add-On Covers
          </span>
          <span className="text-[11px] text-mute font-mono">
            Add-ons total: +{inr(Math.round(addonsCost * 1.18))} (incl. GST)
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 pt-1">
          {/* 1. Zero Dep */}
          <label className={cn(
            "flex items-start gap-2.5 p-2.5 rounded-xl border text-xs cursor-pointer transition select-none",
            zeroDep ? "border-accent bg-accent/10 text-ink" : "border-line bg-panel text-mute hover:border-line/80"
          )}>
            <input 
              type="checkbox" 
              checked={zeroDep} 
              onChange={(e) => setZeroDep(e.target.checked)} 
              className="mt-0.5 accent-accent" 
            />
            <div>
              <span className="font-semibold block text-ink">Zero Depreciation (Bumper-to-Bumper)</span>
              <span className="text-[11px] text-mute block leading-tight mt-0.5">100% claim on plastics, fibers & glass</span>
            </div>
          </label>

          {/* 2. Engine Protect */}
          <label className={cn(
            "flex items-start gap-2.5 p-2.5 rounded-xl border text-xs cursor-pointer transition select-none",
            engineProtect ? "border-accent bg-accent/10 text-ink" : "border-line bg-panel text-mute hover:border-line/80"
          )}>
            <input 
              type="checkbox" 
              checked={engineProtect} 
              onChange={(e) => setEngineProtect(e.target.checked)} 
              className="mt-0.5 accent-accent" 
            />
            <div>
              <span className="font-semibold block text-ink">Engine & Gearbox Protection</span>
              <span className="text-[11px] text-mute block leading-tight mt-0.5">Protects waterlogging hydrostatic lock</span>
            </div>
          </label>

          {/* 3. Return to Invoice */}
          <label className={cn(
            "flex items-start gap-2.5 p-2.5 rounded-xl border text-xs cursor-pointer transition select-none",
            rti ? "border-accent bg-accent/10 text-ink" : "border-line bg-panel text-mute hover:border-line/80"
          )}>
            <input 
              type="checkbox" 
              checked={rti} 
              onChange={(e) => setRti(e.target.checked)} 
              className="mt-0.5 accent-accent" 
            />
            <div>
              <span className="font-semibold block text-ink">Return to Invoice (RTI)</span>
              <span className="text-[11px] text-mute block leading-tight mt-0.5">Reimburses full ex-showroom + road tax in total loss</span>
            </div>
          </label>

          {/* 4. 24x7 Roadside Assistance */}
          <label className={cn(
            "flex items-start gap-2.5 p-2.5 rounded-xl border text-xs cursor-pointer transition select-none",
            rsa ? "border-accent bg-accent/10 text-ink" : "border-line bg-panel text-mute hover:border-line/80"
          )}>
            <input 
              type="checkbox" 
              checked={rsa} 
              onChange={(e) => setRsa(e.target.checked)} 
              className="mt-0.5 accent-accent" 
            />
            <div>
              <span className="font-semibold block text-ink">24x7 Roadside Assistance</span>
              <span className="text-[11px] text-mute block leading-tight mt-0.5">Emergency towing, flat tyre & fuel drop</span>
            </div>
          </label>

          {/* 5. Consumables Cover */}
          <label className={cn(
            "flex items-start gap-2.5 p-2.5 rounded-xl border text-xs cursor-pointer transition select-none",
            consumables ? "border-accent bg-accent/10 text-ink" : "border-line bg-panel text-mute hover:border-line/80"
          )}>
            <input 
              type="checkbox" 
              checked={consumables} 
              onChange={(e) => setConsumables(e.target.checked)} 
              className="mt-0.5 accent-accent" 
            />
            <div>
              <span className="font-semibold block text-ink">Consumables Protection</span>
              <span className="text-[11px] text-mute block leading-tight mt-0.5">Covers engine oil, nuts, bolts, coolant & AC gas</span>
            </div>
          </label>
        </div>
      </div>

      {/* Showroom Dealer Comparison Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-500/25 bg-amber-500/10 p-3.5 text-xs">
        <div className="flex items-start gap-2.5">
          <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-ink">Typical Dealership In-House Quote: ~{inr(dealerQuote)}</span>
            <p className="text-[11px] text-mute mt-0.5">
              Showrooms add 30–45% dealer broker commission. Below are direct rates available for {modelName} in {city}.
            </p>
          </div>
        </div>
        <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-1 rounded-lg">
          Potential Savings: ~{inr(Math.round(dealerQuote - (tpPremium + baseOdPremium * 0.75 + addonsCost) * 1.18))}
        </span>
      </div>

      {/* Insurance Partners Cards Grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {PARTNERS.map((p) => {
          // Partner premium calculation
          const partnerOd = Math.round(baseOdPremium * p.baseRateMultiplier) + addonsCost;
          const totalPremium = Math.round((tpPremium + partnerOd) * 1.18); // with GST
          const savingsVsDealer = Math.max(0, dealerQuote - totalPremium);

          return (
            <div
              key={p.id}
              className="flex flex-col justify-between rounded-xl border border-line bg-panel-soft/40 p-4 transition hover:border-accent/40 hover:shadow-md"
            >
              <div>
                {/* Top Partner Row */}
                <div className="flex items-start justify-between gap-2 mb-2.5">
                  <div>
                    <span className="text-[10px] font-bold tracking-wider uppercase text-accent">
                      {p.badge}
                    </span>
                    <h4 className="font-bold text-sm text-ink">{p.name}</h4>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-base font-bold text-ink">
                      {inr(totalPremium)}
                    </span>
                    <span className="text-[10px] text-mute block">1-Yr Comprehensive + 3-Yr TP</span>
                  </div>
                </div>

                {/* Savings Pill */}
                {savingsVsDealer > 0 && (
                  <div className="mb-3 inline-flex items-center gap-1 rounded-md bg-emerald-500/15 border border-emerald-500/25 px-2 py-0.5 text-[11px] font-bold text-emerald-600 dark:text-emerald-400">
                    <Percent className="h-3 w-3" /> Saves {inr(savingsVsDealer)} vs Showroom Quote
                  </div>
                )}

                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-2 text-[11px] border-t border-line pt-2.5 mb-3">
                  <div>
                    <span className="text-mute block">Claim Settlement:</span>
                    <span className="font-semibold text-ink">{p.claimRatio} (IRDAI verified)</span>
                  </div>
                  <div>
                    <span className="text-mute block">Network Garages:</span>
                    <span className="font-semibold text-ink">{p.garages}</span>
                  </div>
                </div>

                {/* Features list */}
                <ul className="space-y-1 text-[11px] text-mute">
                  {p.highlights.map((h, i) => (
                    <li key={i} className="flex items-center gap-1.5">
                      <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" />
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Bottom Action */}
              <div className="mt-4 border-t border-line pt-3 flex items-center justify-between">
                <span className="text-[10px] text-mute">
                  Binding quote subject to inspection
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    if (onSelectPartner) onSelectPartner(p.id, totalPremium);
                    if (onRequestQuote) onRequestQuote();
                  }}
                  className="h-8 px-3 text-xs font-semibold hover:bg-accent hover:text-white hover:border-accent"
                >
                  Choose {p.logoText} <ArrowRight className="h-3 w-3" />
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
