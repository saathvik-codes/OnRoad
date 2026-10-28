"use client";

import { useState, useMemo } from "react";
import { motion } from "motion/react";
import { 
  AlertTriangle, 
  BadgeCheck, 
  ExternalLink, 
  RotateCcw, 
  ShieldAlert, 
  ShieldCheck, 
  User, 
  Users, 
  Building2,
  FileText,
  ChevronDown,
  Info
} from "lucide-react";
import type { Breakdown as B } from "@/lib/api";
import { inr } from "@/lib/format";
import { cn } from "@/components/ui";

const COLORS = ["#39d0ff", "#ff4d2e", "#ff8a3d", "#ffc23d", "#7c8cff", "#a96bff", "#34d399", "#5d6577", "#e9ecf3"];

export function BreakdownView({ b, compact = false }: { b: B; compact?: boolean }) {
  const [buyerType, setBuyerType] = useState<"individual_male" | "individual_female" | "corporate">("individual_male");
  const [showInsuranceTips, setShowInsuranceTips] = useState(false);

  // Female Buyer Concession Calculation
  // In multiple Indian states (e.g., Delhi, UP, Maharashtra, Punjab, etc.), female primary registrants receive
  // 2% to 3% concession on road tax/registration, and insurance providers offer ~8-10% lower own-damage claim risk rates.
  const femaleConcession = useMemo(() => {
    if (buyerType !== "individual_female") return 0;
    const rtoLine = b.lines.find((l) => l.label.toLowerCase().includes("road tax") || l.label.toLowerCase().includes("rto"));
    const rtoAmount = rtoLine?.amount_inr ?? 0;
    const insLine = b.lines.find((l) => l.label.toLowerCase().includes("insurance"));
    const insAmount = insLine?.amount_inr ?? 0;

    // Estimated 2% road tax concession + 8% OD insurance discount
    const taxSaving = Math.round(rtoAmount * 0.02);
    const insSaving = Math.round(insAmount * 0.08);
    return Math.max(1200, taxSaving + insSaving);
  }, [b, buyerType]);

  const adjustedTotal = useMemo(() => {
    const base = b.total_inr - b.refundable_inr;
    if (buyerType === "individual_female") {
      return Math.max(0, base - femaleConcession);
    }
    if (buyerType === "corporate") {
      // Commercial corporate tax is typically 2-3% higher in road tax
      return Math.round(base * 1.025);
    }
    return base;
  }, [b, buyerType, femaleConcession]);

  const parts = b.lines.filter((l) => (l.amount_inr ?? 0) > 0 && !l.refundable);
  const cost = parts.reduce((s, l) => s + (l.amount_inr ?? 0), 0);

  return (
    <div className="space-y-6">
      {/* Buyer Profile Selection / Gender Concession */}
      {!compact && (
        <div className="rounded-2xl border border-line bg-panel-soft/70 p-3.5 space-y-3">
          {/* Header row with Title & active badge */}
          <div className="flex items-start justify-between gap-2">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-mute flex items-center gap-1.5">
                <User className="h-3.5 w-3.5 text-accent" />
                Buyer Registration Profile
              </span>
              <p className="text-xs text-mute mt-0.5 leading-relaxed">
                State road tax concessions & insurance incentives by registrant category:
              </p>
            </div>
            {buyerType === "individual_female" && (
              <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                <BadgeCheck className="h-2.5 w-2.5" /> Concession
              </span>
            )}
            {buyerType === "corporate" && (
              <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-accent/15 border border-accent/30 px-2 py-0.5 text-[10px] font-bold text-accent">
                Commercial
              </span>
            )}
          </div>

          {/* 3-column equal grid segmented control */}
          <div className="grid grid-cols-3 gap-1 rounded-xl bg-panel p-1 border border-line text-xs font-medium">
            <button
              type="button"
              onClick={() => setBuyerType("individual_male")}
              className={cn(
                "flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg transition cursor-pointer text-center",
                buyerType === "individual_male" 
                  ? "bg-accent text-white shadow-xs font-semibold" 
                  : "text-mute hover:text-white hover:bg-white/5"
              )}
            >
              <User className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">Individual</span>
            </button>

            <button
              type="button"
              onClick={() => setBuyerType("individual_female")}
              className={cn(
                "flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg transition cursor-pointer text-center",
                buyerType === "individual_female" 
                  ? "bg-emerald-600 text-white shadow-xs font-semibold" 
                  : "text-mute hover:text-white hover:bg-white/5"
              )}
            >
              <BadgeCheck className="h-3.5 w-3.5 shrink-0 text-emerald-400" />
              <span className="truncate">Female Buyer</span>
            </button>

            <button
              type="button"
              onClick={() => setBuyerType("corporate")}
              className={cn(
                "flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg transition cursor-pointer text-center",
                buyerType === "corporate" 
                  ? "bg-accent text-white shadow-xs font-semibold" 
                  : "text-mute hover:text-white hover:bg-white/5"
              )}
            >
              <Building2 className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">Corporate</span>
            </button>
          </div>

          {/* Active Concession Alert */}
          {buyerType === "individual_female" && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }} 
              animate={{ opacity: 1, height: "auto" }}
              className="flex items-start gap-2.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-2.5 text-xs text-emerald-800 dark:text-emerald-300"
            >
              <BadgeCheck className="h-4 w-4 shrink-0 mt-0.5 text-emerald-600 dark:text-emerald-400" />
              <div>
                <span className="font-bold">Female Buyer Concession Active: Saves ~{inr(femaleConcession)}!</span>
                <p className="mt-0.5 text-[11px] opacity-90 leading-relaxed">
                  States like Delhi, UP, Maharashtra, and Punjab provide a 2% road tax discount for female registrants, alongside lower actuarial claim rates from comprehensive motor insurers.
                </p>
              </div>
            </motion.div>
          )}

          {buyerType === "corporate" && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }} 
              animate={{ opacity: 1, height: "auto" }}
              className="flex items-start gap-2.5 rounded-xl border border-line bg-panel p-2.5 text-xs text-mute"
            >
              <Info className="h-4 w-4 shrink-0 mt-0.5 text-accent" />
              <div>
                <span className="font-semibold text-ink">Company / Corporate Registration:</span>
                <p className="mt-0.5 text-[11px] leading-relaxed">
                  Corporate buyer road tax is typically taxed at a higher slab (+2.5%), but GST-registered businesses can claim commercial Input Tax Credit (ITC) where eligible.
                </p>
              </div>
            </motion.div>
          )}
        </div>
      )}

      {/* Main Total Header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-mute font-semibold">
            Real On-Road Quote in {b.state_name}
          </p>
          <div className="flex items-baseline gap-2 mt-1">
            <p className="font-[family-name:var(--font-display)] text-3xl sm:text-4xl lg:text-5xl font-black text-ink font-mono tracking-tight">
              {inr(adjustedTotal)}
            </p>
            {buyerType === "individual_female" && (
              <span className="line-through text-xs sm:text-sm text-mute font-mono">
                {inr(b.total_inr - b.refundable_inr)}
              </span>
            )}
          </div>
          {b.refundable_inr > 0 && (
            <p className="mt-1 text-xs sm:text-sm text-mute">
              + {inr(b.refundable_inr)} TCS paid at showroom, fully refundable / adjusted in your Income Tax return
            </p>
          )}
        </div>

        <span className={cn(
          "rounded-full px-3 py-1 text-xs font-semibold", 
          b.coverage === "verified" ? "bg-good/15 text-good" : "bg-amber-400/15 text-amber-500 dark:text-amber-300"
        )}>
          {b.coverage === "verified" ? "Official Govt Tax Rules" : b.coverage === "partial" ? "Partly verified rates" : "Estimated calculation"}
        </span>
      </div>

      {/* Proportional visual breakdown bar */}
      <div className="mt-4 flex h-3.5 w-full overflow-hidden rounded-full bg-panel-soft border border-line">
        {parts.map((l, i) => (
          <motion.div 
            key={l.label} 
            initial={{ width: 0 }} 
            whileInView={{ width: `${((l.amount_inr ?? 0) / cost) * 100}%` }}
            viewport={{ once: true }} 
            transition={{ duration: 0.8, delay: i * 0.05, ease: [0.22, 1, 0.36, 1] }}
            style={{ background: COLORS[i % COLORS.length] }} 
            title={`${l.label}: ${inr(l.amount_inr)}`} 
          />
        ))}
      </div>

      {/* Line Item Charges */}
      <ul className={cn("mt-6 divide-y divide-line", compact && "text-sm")}>
        {b.lines.map((l, i) => {
          let lineAmount = l.amount_inr;
          let concessionLabel = "";

          if (buyerType === "individual_female") {
            if (l.label.toLowerCase().includes("road tax") || l.label.toLowerCase().includes("rto")) {
              const disc = Math.round((lineAmount ?? 0) * 0.02);
              lineAmount = Math.max(0, (lineAmount ?? 0) - disc);
              concessionLabel = ` (-${inr(disc)} Female Concession)`;
            } else if (l.label.toLowerCase().includes("insurance")) {
              const disc = Math.round((lineAmount ?? 0) * 0.08);
              lineAmount = Math.max(0, (lineAmount ?? 0) - disc);
              concessionLabel = ` (-${inr(disc)} Safe Driver Rebate)`;
            }
          }

          return (
            <motion.li 
              key={l.label} 
              initial={{ opacity: 0, y: 8 }} 
              whileInView={{ opacity: 1, y: 0 }} 
              viewport={{ once: true }}
              transition={{ delay: 0.04 * i }} 
              className="flex items-start justify-between gap-4 py-3"
            >
              <div className="flex min-w-0 gap-3">
                <span 
                  className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full" 
                  style={{ background: l.refundable ? "#34d399" : COLORS[parts.indexOf(l) % COLORS.length] || "#5d6577" }} 
                />
                <div className="min-w-0">
                  <p className="font-semibold text-sm text-ink flex items-center flex-wrap gap-1.5">
                    {l.label}
                    {l.refundable && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-good">
                        <RotateCcw className="h-3 w-3" />refundable
                      </span>
                    )}
                    {!l.verified && !l.refundable && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-500 dark:text-amber-300">
                        <AlertTriangle className="h-3 w-3" />estimate
                      </span>
                    )}
                    {concessionLabel && (
                      <span className="inline-flex items-center gap-0.5 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                        {concessionLabel}
                      </span>
                    )}
                  </p>
                  {!compact && (
                    <p className="text-xs leading-relaxed text-mute mt-0.5">
                      {l.basis}
                      {l.source && (
                        <a 
                          href={l.source} 
                          target="_blank" 
                          rel="noreferrer" 
                          className="ml-1 inline-flex items-center gap-0.5 text-accent hover:underline font-medium"
                        >
                          official source<ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </p>
                  )}
                </div>
              </div>
              <span className="shrink-0 font-mono font-bold text-sm text-ink">
                {lineAmount === null ? "not verified" : inr(lineAmount)}
              </span>
            </motion.li>
          );
        })}
      </ul>

      {/* Insurance Claims Advisory & Policy Advice */}
      {!compact && (
        <div className="rounded-2xl border border-line bg-panel p-4 shadow-sm">
          <button
            type="button"
            onClick={() => setShowInsuranceTips(!showInsuranceTips)}
            className="w-full flex items-center justify-between text-left cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-accent" />
              <div>
                <h4 className="font-bold text-sm text-ink">Smart Insurance Claim Advisory & Negotiation Tips</h4>
                <p className="text-xs text-mute">Optional add-ons worth asking your insurer about</p>
              </div>
            </div>
            <ChevronDown className={cn("h-4 w-4 text-mute transition-transform", showInsuranceTips && "rotate-180")} />
          </button>

          {showInsuranceTips && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }} 
              animate={{ opacity: 1, height: "auto" }}
              className="mt-4 pt-3 border-t border-line space-y-3 text-xs"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-line bg-panel-soft p-3">
                  <span className="font-bold text-ink block text-xs">1. Zero Depreciation (Bumper-to-Bumper)</span>
                  <p className="text-mute mt-1 leading-relaxed text-[11px]">
                    Standard policy cuts 50% on plastic, rubber, and nylon parts during accident repairs. Zero-depreciation cover pays those parts in full (subject to policy terms), and is worth considering for newer cars.
                  </p>
                </div>
                <div className="rounded-xl border border-line bg-panel-soft p-3">
                  <span className="font-bold text-ink block text-xs">2. Engine & Gearbox Protection</span>
                  <p className="text-mute mt-1 leading-relaxed text-[11px]">
                    Protects against hydrostatic lock caused by waterlogging in monsoon rains. Standard comprehensive insurance rejects water ingestion engine seizure.
                  </p>
                </div>
                <div className="rounded-xl border border-line bg-panel-soft p-3">
                  <span className="font-bold text-ink block text-xs">3. Return to Invoice (RTI)</span>
                  <p className="text-mute mt-1 leading-relaxed text-[11px]">
                    In case of total loss or theft, RTI pays out the full original ex-showroom price plus road tax and registration charges instead of depreciated IDV value.
                  </p>
                </div>
                <div className="rounded-xl border border-line bg-panel-soft p-3">
                  <span className="font-bold text-ink block text-xs">4. Legally Buy External Insurance</span>
                  <p className="text-mute mt-1 leading-relaxed text-[11px]">
                    Under IRDAI circulars, no dealer can force you to buy insurance in-house. Comparing independently (PolicyBazaar, Acko, Digit) typically saves ₹15,000 to ₹35,000.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      )}

      {/* Charges You Can Refuse */}
      {!compact && b.optional.length > 0 && (
        <div className="rounded-2xl border border-accent/30 bg-accent/5 p-4">
          <p className="flex items-center gap-2 text-sm font-bold text-ink">
            <ShieldAlert className="h-4 w-4 text-accent" />
            Showroom Charges You Can Legally Refuse
          </p>
          <ul className="mt-2 space-y-1.5 text-xs text-mute">
            {b.optional.map((o) => (
              <li key={o.label}>
                <span className="font-semibold text-ink">{o.label}</span>: {o.basis}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Official Government Tax Rules Notes */}
      {!compact && b.notes.length > 0 && (
        <ul className="space-y-1 text-xs text-mute border-t border-line pt-3">
          {b.notes.map((n) => (
            <li key={n} className="flex gap-2">
              <BadgeCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" />
              <span>{n}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
