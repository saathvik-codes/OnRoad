"use client";

import { useState } from "react";
import useSWR from "swr";
import { 
  Bell, 
  Package, 
  ShieldCheck, 
  FileCheck, 
  CheckCircle2, 
  ChevronRight, 
  ArrowRight, 
  Lock, 
  UserCheck, 
  ExternalLink,
  Tag,
  AlertCircle,
  HelpCircle,
  } from "lucide-react";
import { toast } from "sonner";
import { fetcher, type Account, type Variant } from "@/lib/api";
import { inr } from "@/lib/format";
import { Button, cn } from "@/components/ui";
import { InsurancePartnersComparison } from "@/components/insurance-partners";
import { ContactCaptureModal, type SupportContext } from "@/components/contact-capture-modal";

interface OwnershipSupportHubProps {
  modelName: string;
  brandName: string;
  city: string;
  stateCode?: string;
  variant?: Variant;
  exShowroomPrice: number;
}

export function OwnershipSupportHub({
  modelName,
  brandName,
  city,
  stateCode = "TS",
  variant,
  exShowroomPrice,
}: OwnershipSupportHubProps) {
  const { data: me } = useSWR<Account>("/auth/me", fetcher, { shouldRetryOnError: false });
  const [activeTab, setActiveTab] = useState<"insurance" | "accessories" | "rta" | "updates">("insurance");
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContext, setModalContext] = useState<SupportContext>("insurance");
  const [unlockedSections, setUnlockedSections] = useState<Record<string, boolean>>({});

  const handleOpenGate = (context: SupportContext) => {
    if (me) {
      // Already logged in!
      toast.success(`Access verified for ${me.name}. Information unlocked!`);
      setUnlockedSections((prev) => ({ ...prev, [context]: true }));
      return;
    }
    setModalContext(context);
    setModalOpen(true);
  };

  const handleCaptureSuccess = () => {
    setUnlockedSections((prev) => ({ ...prev, [modalContext]: true }));
  };

  // Sample Genuine OEM Accessories package for this vehicle
  const ACCESSORIES = [
    { name: "All-Weather 7D Custom Deep-Dish Mats", price: 4500, oem: true, mandatory: false, benefit: "Protects cabin carpet against water, mud and beverage spills" },
    { name: "Aerodynamic Mud Flaps & Window Visors", price: 2800, oem: true, mandatory: false, benefit: "Reduces stone-chip paint scratches and highway wind turbulence" },
    { name: "Dual-Channel 4K Dashcam with Parking Monitor", price: 8900, oem: false, mandatory: false, benefit: "Critical for false claim prevention and insurance dispute defense" },
    { name: "Custom-Fit UV & Weather Protective Body Cover", price: 3200, oem: true, mandatory: false, benefit: "Shields clearcoat from bird droppings, acid rain & UV fading" },
    { name: "Illuminated Scuff Plates & LED Footwell Kit", price: 5500, oem: true, mandatory: false, benefit: "Prevents door sill scratches during daily boarding" },
  ];

  const totalAccessoriesCost = ACCESSORIES.reduce((s, a) => s + a.price, 0);

  return (
    <div className="space-y-6">
      {/* Tab Navigation Strip */}
      <div className="flex flex-wrap items-center gap-2 border-b border-line pb-3">
        <button
          type="button"
          onClick={() => setActiveTab("insurance")}
          className={cn(
            "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition cursor-pointer",
            activeTab === "insurance"
              ? "bg-accent text-white shadow-xs"
              : "border border-line bg-panel text-mute hover:text-ink hover:bg-panel-soft"
          )}
        >
          <ShieldCheck className="h-4 w-4" />
          <span>Insurance Partners & Add-Ons</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("accessories")}
          className={cn(
            "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition cursor-pointer",
            activeTab === "accessories"
              ? "bg-accent text-white shadow-xs"
              : "border border-line bg-panel text-mute hover:text-ink hover:bg-panel-soft"
          )}
        >
          <Package className="h-4 w-4" />
          <span>OEM Genuine Accessories</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("rta")}
          className={cn(
            "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition cursor-pointer",
            activeTab === "rta"
              ? "bg-accent text-white shadow-xs"
              : "border border-line bg-panel text-mute hover:text-ink hover:bg-panel-soft"
          )}
        >
          <FileCheck className="h-4 w-4" />
          <span>RTA / RTO Registration Guidance</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("updates")}
          className={cn(
            "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition cursor-pointer",
            activeTab === "updates"
              ? "bg-accent text-white shadow-xs"
              : "border border-line bg-panel text-mute hover:text-ink hover:bg-panel-soft"
          )}
        >
          <Bell className="h-4 w-4" />
          <span>Price & Tax Revision Alerts</span>
        </button>
      </div>

      {/* Tab 1: Insurance Partners */}
      {activeTab === "insurance" && (
        <div className="space-y-4">
          <InsurancePartnersComparison
            exShowroomPrice={exShowroomPrice}
            engineCc={variant?.engine_cc}
            fuelType={variant?.fuel}
            modelName={modelName}
            city={city}
            onRequestQuote={() => handleOpenGate("insurance")}
          />
        </div>
      )}

      {/* Tab 2: Accessories Catalogue */}
      {activeTab === "accessories" && (
        <div className="rounded-2xl border border-line bg-panel p-5 sm:p-6 space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/15 text-accent border border-accent/30">
                  <Package className="h-4 w-4" />
                </span>
                <h3 className="font-[family-name:var(--font-display)] text-lg sm:text-xl font-bold text-ink">
                  OEM Genuine Accessories & Fair Price Audit
                </h3>
              </div>
              <p className="text-xs text-mute mt-1 leading-relaxed">
                Dealers frequently quote mandatory &quot;essential accessory kits&quot; priced at ₹35,000–₹50,000. You are never legally obligated to buy accessories from the dealership.
              </p>
            </div>

            <div className="text-right">
              <span className="text-[10px] uppercase tracking-wider text-mute block font-semibold">
                Fair Market Value Pack
              </span>
              <span className="font-mono text-base font-bold text-ink">
                ~{inr(totalAccessoriesCost)}
              </span>
            </div>
          </div>

          {/* Itemized Table */}
          <div className="divide-y divide-line rounded-xl border border-line bg-panel-soft/40 overflow-hidden text-xs">
            {ACCESSORIES.map((a, i) => (
              <div key={i} className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 gap-2">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-ink">{a.name}</span>
                    {a.oem && (
                      <span className="rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-1.5 py-0.2 text-[10px] font-bold">
                        OEM Genuine
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-mute">{a.benefit}</p>
                </div>
                <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0">
                  <span className="font-mono font-bold text-ink sm:text-right">{inr(a.price)}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Action Row */}
          <div className="rounded-xl border border-line bg-panel-soft p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-xs text-mute text-center sm:text-left">
              <span className="font-bold text-ink block">Need an itemized accessory quotation from verified distributors?</span>
              <span>Login or provide contact details to receive genuine accessory part numbers and warranty certificates.</span>
            </div>
            <Button
              size="sm"
              onClick={() => handleOpenGate("accessories")}
              className="shrink-0 text-xs font-semibold px-4"
            >
              Request Accessories Estimate <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}

      {/* Tab 3: RTA / RTO Registration Guidance */}
      {activeTab === "rta" && (
        <div className="rounded-2xl border border-line bg-panel p-5 sm:p-6 space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/15 text-blue-400 border border-blue-500/30">
                  <FileCheck className="h-4 w-4" />
                </span>
                <h3 className="font-[family-name:var(--font-display)] text-lg sm:text-xl font-bold text-ink">
                  RTA & RTO Vehicle Registration Support ({city})
                </h3>
              </div>
              <p className="text-xs text-mute mt-1 leading-relaxed">
                Official Motor Vehicle Act compliance guidelines for state registration, HSRP plates, and BH-series eligibility.
              </p>
            </div>
          </div>

          {/* Guidelines Grid */}
          <div className="grid gap-3 sm:grid-cols-2 text-xs">
            <div className="rounded-xl border border-line bg-panel-soft/50 p-4 space-y-1.5">
              <span className="font-bold text-ink block text-xs">1. High-Security Registration Plates (HSRP)</span>
              <p className="text-mute leading-relaxed text-[11px]">
                Under MoRTH Notification GSR 1162(E), high-security number plates and colour-coded third-license plate stickers are supplied free by the vehicle manufacturer with the vehicle. Showrooms cannot legally add a separate ₹800–₹1,500 HSRP charge.
              </p>
            </div>

            <div className="rounded-xl border border-line bg-panel-soft/50 p-4 space-y-1.5">
              <span className="font-bold text-ink block text-xs">2. Bharat (BH) Series Registration</span>
              <p className="text-mute leading-relaxed text-[11px]">
                Eligible for Central/State Govt employees, defence personnel, and private employees with offices in 4+ states or UTs. Saves upfront lump sum tax by paying road tax in 2-year installments.
              </p>
            </div>

            <div className="rounded-xl border border-line bg-panel-soft/50 p-4 space-y-1.5">
              <span className="font-bold text-ink block text-xs">3. Doorstep Smart Card RC Delivery</span>
              <p className="text-mute leading-relaxed text-[11px]">
                State transport departments dispatch the original smart card RC via India Post Speed Post directly to your registered Aadhaar address within 15–21 days of vehicle verification.
              </p>
            </div>

            <div className="rounded-xl border border-line bg-panel-soft/50 p-4 space-y-1.5">
              <span className="font-bold text-ink block text-xs">4. Refuse Dealership &quot;Logistics / Handling&quot;</span>
              <p className="text-mute leading-relaxed text-[11px]">
                Delhi High Court (W.P.(C) 4407/2012) and various State Transport Commissioners have repeatedly ruled that &quot;handling / logistics / delivery&quot; charges charged by dealers are illegal.
              </p>
            </div>
          </div>

          {/* Action Row */}
          <div className="rounded-xl border border-line bg-panel-soft p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-xs text-mute text-center sm:text-left">
              <span className="font-bold text-ink block">Need doorstep RTA paperwork assistance or BH-Series Form 60 guidance?</span>
              <span>Our liaison desk assists with legitimate state transport paperwork in {city}.</span>
            </div>
            <Button
              size="sm"
              onClick={() => handleOpenGate("rta")}
              className="shrink-0 text-xs font-semibold px-4"
            >
              Request RTA Support <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}

      {/* Tab 4: Price & Tax Updates Alert */}
      {activeTab === "updates" && (
        <div className="rounded-2xl border border-line bg-panel p-5 sm:p-6 space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/15 text-accent border border-accent/30">
                  <Bell className="h-4 w-4" />
                </span>
                <h3 className="font-[family-name:var(--font-display)] text-lg sm:text-xl font-bold text-ink">
                  Price Change & Tax Revision Monitor
                </h3>
              </div>
              <p className="text-xs text-mute mt-1 leading-relaxed">
                Stay updated on official manufacturer ex-showroom price increases, state road tax gazette notifications, and seasonal discount schemes in {city}.
              </p>
            </div>
          </div>

          <div className="rounded-xl border border-emerald-500/25 bg-emerald-500/10 p-4 text-xs space-y-2">
            <span className="font-bold text-emerald-600 dark:text-emerald-400 block text-xs">
              Live Regulatory Updates for {city}:
            </span>
            <ul className="space-y-1.5 text-[11px] text-ink/90">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <span>Road tax slabs in {city} are actively monitored against the latest State Transport gazettes.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <span>100% road tax waiver and registration fee exemption in effect for electric vehicles where applicable.</span>
              </li>
            </ul>
          </div>

          {/* Action Row */}
          <div className="rounded-xl border border-line bg-panel-soft p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-xs text-mute text-center sm:text-left">
              <span className="font-bold text-ink block">Receive automated notifications when {modelName} prices or discounts drop?</span>
              <span>We&apos;ll alert you as soon as official manufacturer circulars are updated.</span>
            </div>
            <Button
              size="sm"
              onClick={() => handleOpenGate("updates")}
              className="shrink-0 text-xs font-semibold px-4"
            >
              Track Price Changes <Bell className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}

      {/* Contact Capture Modal */}
      <ContactCaptureModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        context={modalContext}
        modelName={`${brandName} ${modelName}`}
        city={city}
        onSuccess={handleCaptureSuccess}
      />
    </div>
  );
}
