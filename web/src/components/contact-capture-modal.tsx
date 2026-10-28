"use client";

import { useState } from "react";
import { 
  X, 
  ShieldCheck, 
  CheckCircle2, 
    ArrowRight, 
  Phone, 
  Mail, 
  User, 
  MapPin,
  Lock
} from "lucide-react";
import { toast } from "sonner";
import { Button, Card, Input, Label, cn } from "@/components/ui";
import { Logo } from "@/components/logo";
import { GoogleButton } from "@/components/google-button";
import type { Account } from "@/lib/api";

export type SupportContext = 
  | "insurance" 
  | "accessories" 
  | "rta" 
  | "updates" 
  | "quotes";

interface ContactCaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  context: SupportContext;
  modelName?: string;
  city?: string;
  onSuccess?: (details: { name: string; phone: string; email: string }) => void;
}

const CONTEXT_DETAILS: Record<SupportContext, { title: string; subtitle: string; benefit: string }> = {
  insurance: {
    title: "Unlock Insurer Partner Quotes",
    subtitle: "Compare binding quotes from Acko, Digit, and HDFC ERGO with Zero-Dep & Engine Protect add-ons.",
    benefit: "Saves up to ₹35,000 vs showroom marked-up dealer insurance.",
  },
  accessories: {
    title: "Access OEM Genuine Accessories Guide",
    subtitle: "Itemized genuine accessory packs, warranty-safe additions, and wholesale price comparisons.",
    benefit: "Avoid paying 40% dealer markup on essential accessory kits.",
  },
  rta: {
    title: "Request Doorstep RTA / RTO Registration Support",
    subtitle: "State transport department filings, BH-Series eligibility checks, and HSRP number plate delivery.",
    benefit: "Verified liaison guidance for government registration without touts.",
  },
  updates: {
    title: "Track Price Revisions & City Discount Alerts",
    subtitle: "Instant notification when manufacturer ex-showroom prices or state road taxes change.",
    benefit: "Never miss festive cash drops or seasonal dealer inventory clearance.",
  },
  quotes: {
    title: "Request Verified Dealer On-Road Quotes",
    subtitle: "Let authorized showrooms in your city compete with their best out-the-door price.",
    benefit: "Compare real proforma invoices without spam marketing calls.",
  },
};

export function ContactCaptureModal({
  isOpen,
  onClose,
  context,
  modelName = "Vehicle",
  city = "your city",
  onSuccess,
}: ContactCaptureModalProps) {
  const [form, setForm] = useState({ name: "", phone: "", email: "" });
  const [busy, setBusy] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const config = CONTEXT_DETAILS[context] || CONTEXT_DETAILS.quotes;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      toast.error("Please enter your name");
      return;
    }
    if (!form.phone.trim() && !form.email.trim()) {
      toast.error("Please provide either your phone number or email");
      return;
    }
    setBusy(true);

    setTimeout(() => {
      setBusy(false);
      setSubmitted(true);
      toast.success("Details received! Unlocking your custom summary...");
      if (onSuccess) {
        onSuccess(form);
      }
      setTimeout(() => {
        onClose();
        setSubmitted(false);
      }, 1800);
    }, 600);
  };

  const onGoogleDone = (acc: Account) => {
    toast.success(`Welcome, ${acc.name.split(" ")[0]}! Access granted.`);
    if (onSuccess) {
      onSuccess({ name: acc.name, phone: acc.phone || "", email: acc.email });
    }
    onClose();
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        className="relative flex flex-col w-full max-w-md rounded-3xl border border-line bg-panel shadow-2xl overflow-hidden p-6 sm:p-7"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 rounded-full p-1.5 text-mute hover:bg-panel-soft hover:text-ink transition cursor-pointer"
          aria-label="Close modal"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="space-y-2 pr-6">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent/15 text-accent border border-accent/25">
              <ShieldCheck className="h-4 w-4" />
            </span>
            <span className="text-[11px] font-bold uppercase tracking-wider text-accent">
              OnRoad Concierge · {city}
            </span>
          </div>

          <h3 className="font-[family-name:var(--font-display)] text-xl sm:text-2xl font-bold text-ink leading-snug">
            {config.title}
          </h3>
          <p className="text-xs text-mute leading-relaxed">
            {config.subtitle}
          </p>
        </div>

        {/* Context Highlight Badge */}
        <div className="mt-4 rounded-xl border border-emerald-500/25 bg-emerald-500/10 p-3 text-xs text-emerald-600 dark:text-emerald-400 flex items-start gap-2.5">
          <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Verified Buyer Benefit for {modelName}:</span>
            <p className="text-[11px] opacity-90 mt-0.5">{config.benefit}</p>
          </div>
        </div>

        {submitted ? (
          <div className="py-8 text-center space-y-2 animate-in zoom-in-95 duration-200">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500 text-white">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <p className="font-bold text-ink text-base">Request Verified & Unlocked!</p>
            <p className="text-xs text-mute">Opening your custom breakdown...</p>
          </div>
        ) : (
          <div className="mt-5 space-y-4">
            {/* 1-Tap Google Sign-In */}
            <GoogleButton onDone={onGoogleDone} onError={(m) => toast.error(m)} dividerText="Or enter contact details" />

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <Label>Your Full Name</Label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-mute" />
                  <Input
                    required
                    placeholder="e.g. Rahul Sharma"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="pl-10 text-xs sm:text-sm h-10"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <Label>Mobile Number</Label>
                  <div className="relative">
                    <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-mute" />
                    <Input
                      type="tel"
                      placeholder="98765 43210"
                      value={form.phone}
                      onChange={(e) => setForm({ ...form, phone: e.target.value })}
                      className="pl-10 text-xs sm:text-sm h-10 font-mono"
                    />
                  </div>
                </div>

                <div>
                  <Label>Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-mute" />
                    <Input
                      type="email"
                      placeholder="rahul@example.com"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      className="pl-10 text-xs sm:text-sm h-10"
                    />
                  </div>
                </div>
              </div>

              {/* Privacy Shield Note */}
              <div className="flex items-start gap-2 pt-1 text-[11px] text-mute">
                <Lock className="h-3.5 w-3.5 text-accent shrink-0 mt-0.5" />
                <span>
                  <strong>Zero-Spam Assurance:</strong> Your contact info is strictly used to deliver verified quotes and RTA guidance. We never sell your number to telemarketing agencies.
                </span>
              </div>

              <Button
                type="submit"
                loading={busy}
                className="w-full mt-2 h-11 text-xs sm:text-sm font-semibold rounded-xl"
              >
                Unlock Complete Information <ArrowRight className="h-4 w-4" />
              </Button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
