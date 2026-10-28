"use client";

import Link from "next/link";
import Image from "next/image";
import { useState, useEffect } from "react";
import {
  Download,
  Copy,
  Check,
  ChevronDown,
  Smartphone,
  Apple,
  Calculator,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/components/ui";

const VALUE_PILLARS = [
  {
    illustration: "/illustrations/hero-calculator.webp",
    category: "RTO Tax Engine",
    title: "Official State Road Tax Calculations",
    desc: "Every state and union territory charges specific road tax percentages based on fuel type, ex-showroom slabs, engine displacement, and registration type. OnRoad applies the exact gazetted statutory rules.",
    highlights: ["28 State transport rules updated", "BH-Series registration support", "Fuel cess and EV incentives included"],
  },
  {
    illustration: "/illustrations/onb-receipt.webp",
    category: "Quotation Breakdown",
    title: "Itemized Showroom Price Audit",
    desc: "Understand every line item on a vehicle quotation. OnRoad clearly isolates statutory charges (road tax, central fees) from optional items (extended warranties, basic accessory kits, handling charges).",
    highlights: ["Line-by-line quotation clarity", "IRDAI compliant insurance benchmarks", "Distinguish statutory vs optional fees"],
  },
  {
    illustration: "/illustrations/onb-showrooms.webp",
    category: "Dealer Network",
    title: "Authorized OEM Showrooms Across 50+ Cities",
    desc: "Locate authorized dealerships for Maruti Suzuki, Hyundai, Tata, Mahindra, Toyota, Kia, Honda, and more. Access showroom telephone numbers, exact map locations, and verified sales desks.",
    highlights: ["Authorized OEM showrooms only", "Verified dealer address and location map", "Direct showroom inquiry support"],
  },
  {
    illustration: "/illustrations/hero-compare.webp",
    category: "Model Research",
    title: "Side-by-Side Variant & Spec Comparison",
    desc: "Compare specifications across vehicle trims. Review official ARAI fuel economy figures, safety test protocols, powertrain options, and equipment lists before visiting the dealership.",
    highlights: ["Independent safety protocol data", "Powertrain and gearbox options", "Detailed feature availability matrix"],
  },
];

const STEPS = [
  {
    step: "01",
    title: "Scan or Download APK",
    desc: "Scan the QR code with your phone camera or tap download to save onroad.apk (v1.0.4, 6.2 MB) directly to your Android device.",
  },
  {
    step: "02",
    title: "Confirm System Prompt",
    desc: "Tap the downloaded package in your notifications or Downloads folder, and tap 'Install' when the Android Package Installer opens.",
  },
  {
    step: "03",
    title: "Select City & Explore",
    desc: "Launch OnRoad, select your city, and immediately browse verified ex-showroom and statutory on-road prices.",
  },
];

const FAQS = [
  {
    q: "How does the direct QR code install work?",
    a: "When you scan the QR code with your phone camera, your mobile browser directly downloads the official onroad.apk package. Once downloaded, tap the notification to launch the native Android Package Installer.",
  },
  {
    q: "Why is OnRoad currently available via direct APK?",
    a: "Our Google Play Store submission is currently undergoing standard developer console review. While that process completes, we offer our official, signed release APK directly to car and bike buyers across India.",
  },
  {
    q: "When will OnRoad be available on Google Play and the Apple App Store?",
    a: "The Google Play Store rollout is anticipated shortly as soon as developer verification concludes. The native iOS version is currently in TestFlight staging and will be published on the Apple App Store.",
  },
  {
    q: "Is installing this APK safe for Android devices?",
    a: "Yes. The OnRoad APK is signed with our official release certificate and requests no invasive permissions (no access to contacts, SMS, or camera).",
  },
  {
    q: "Will my saved data persist when updating from Google Play?",
    a: "Yes. The application uses the permanent package identity (com.onroad.app). Future updates installed via Google Play will seamlessly retain your saved vehicles and preferences.",
  },
];

export default function DownloadPage() {
  const [copied, setCopied] = useState(false);
  const [notifyTarget, setNotifyTarget] = useState<"both" | "playstore" | "appstore">("both");
  const [contactInput, setContactInput] = useState("");
  const [notified, setNotified] = useState(false);
  const [activeFaq, setActiveFaq] = useState<number | null>(null);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    const ua = navigator.userAgent || "";
    setIsIOS(/iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1));
  }, []);

  const universalAppUrl = "https://onroad-frontend.onrender.com/app";

  const handleCopyLink = () => {
    navigator.clipboard.writeText(universalAppUrl);
    setCopied(true);
    toast.success("Smart Universal App download link copied!");
    setTimeout(() => setCopied(false), 2500);
  };

  const handleNotifySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!contactInput.trim() || (!contactInput.includes("@") && contactInput.length < 10)) {
      toast.error("Please enter a valid email address or phone number.");
      return;
    }
    setNotified(true);
    toast.success("Thank you. We will notify you when OnRoad launches on the store.");
  };

  return (
    <main className="min-h-screen pt-24 pb-24 px-4 sm:px-6 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="pointer-events-none absolute top-12 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-gradient-to-b from-accent/8 via-accent/4 to-transparent blur-3xl -z-10 rounded-full" />

      <div className="mx-auto max-w-6xl">
        {/* Top Breadcrumb & Status */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <div className="flex items-center gap-2 text-xs font-medium text-mute">
            <Link href="/" className="hover:text-ink transition">Home</Link>
            <span>/</span>
            <span className="text-ink font-semibold">Mobile Apps</span>
          </div>
          <span className="text-xs text-mute font-medium">
            Android Release v1.0.4 · Store Review in Progress
          </span>
        </div>

        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-3xl border border-line bg-panel/90 backdrop-blur-xl p-6 sm:p-10 lg:p-12 shadow-2xl">
          <div className="grid gap-10 lg:grid-cols-12 lg:items-center">
            
            {/* Left Column: Heading & Install Hub */}
            <div className="lg:col-span-7">
              <p className="text-xs font-bold uppercase tracking-wider text-accent mb-3">
                OnRoad Mobile Suite
              </p>

              <h1 className="font-display text-3xl font-extrabold tracking-tight text-ink sm:text-5xl leading-tight sm:leading-tight">
                Official OnRoad Mobile App.{" "}
                <span className="text-gradient">Real On-Road Prices on Your Phone.</span>
              </h1>

              <p className="mt-4 text-base text-mute sm:text-lg leading-relaxed max-w-xl">
                Access official ex-showroom prices, state transport RTO tax schedules for all 28 states, and verified OEM showroom quotations on your smartphone.
              </p>

              {/* Direct QR Code Installation Station */}
              <div className="mt-8 rounded-3xl border border-line bg-panel-soft/80 p-5 sm:p-6 shadow-xs">
                <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
                  {/* High-Resolution Camera-Scannable QR Code */}
                  <div className="flex flex-col items-center shrink-0">
                    <div className="rounded-2xl border border-line bg-white p-3 shadow-md">
                      <Image
                        src="/onroad-app-universal-qr.png"
                        alt="Scan QR code with phone camera to install OnRoad on iPhone or Android"
                        width={140}
                        height={140}
                        className="rounded-lg object-contain"
                        priority
                        unoptimized
                      />
                    </div>
                  </div>

                  {/* QR Scan Details & Action */}
                  <div className="flex-1 text-center sm:text-left">
                    <h3 className="font-display text-lg font-bold text-ink">
                      Scan with your phone camera
                    </h3>
                    
                    <p className="mt-1 text-xs text-mute leading-relaxed">
                      Point your phone&apos;s camera at the QR code to open OnRoad directly on your device. Works on Android and iOS.
                    </p>

                    <div className="mt-4 flex flex-wrap items-center justify-center sm:justify-start gap-3">
                      {isIOS ? (
                        <Link
                          href="/app"
                          className="inline-flex items-center justify-center gap-2 rounded-full bg-accent px-5 py-2.5 text-xs font-bold text-white shadow-md shadow-accent/25 transition-all hover:brightness-110 active:scale-95"
                        >
                          <Smartphone className="h-3.5 w-3.5" />
                          <span>Install OnRoad for iPhone</span>
                        </Link>
                      ) : (
                        <a
                          id="download-apk-btn"
                          href="/onroad.apk"
                          download="onroad.apk"
                          className="inline-flex items-center justify-center gap-2 rounded-full bg-accent px-5 py-2.5 text-xs font-bold text-white shadow-md shadow-accent/25 transition-all hover:brightness-110 active:scale-95"
                        >
                          <Download className="h-3.5 w-3.5" />
                          <span>Download APK Directly (6.2 MB)</span>
                        </a>
                      )}

                      <button
                        onClick={handleCopyLink}
                        className="inline-flex items-center gap-1.5 rounded-full border border-line bg-panel px-3.5 py-2.5 text-xs font-semibold text-ink hover:bg-panel-soft transition cursor-pointer"
                      >
                        {copied ? <Check className="h-3.5 w-3.5 text-good" /> : <Copy className="h-3.5 w-3.5 text-mute" />}
                        <span>{copied ? "Link Copied" : "Copy Link"}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Official Store Badges */}
              <div className="mt-6 space-y-2.5">
                <p className="text-xs font-bold uppercase tracking-wider text-mute">Upcoming App Store Releases</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  
                  {/* Official Google Play Store Card */}
                  <div className="rounded-2xl border border-line bg-panel-soft/60 p-4 transition hover:border-line">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-3">
                        {/* Official Google Play 4-Color Triangle */}
                        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-panel border border-line shadow-xs">
                          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none">
                            <path d="M3.6 1.8c-.3.3-.5.8-.5 1.4v17.6c0 .6.2 1.1.5 1.4l.1.1 9.9-9.9v-.2L3.7 2.1l-.1-.3z" fill="#4285F4" />
                            <path d="M17.1 15.7l-3.5-3.5v-.2l3.5-3.5.1.1 4.1 2.3c1.2.7 1.2 1.8 0 2.5l-4.2 2.3z" fill="#FBBC04" />
                            <path d="M13.6 12.1L3.6 22.1c.4.4 1 .5 1.7.1l11.9-6.8-3.6-3.3z" fill="#EA4335" />
                            <path d="M13.6 11.9l3.6-3.3L5.3 1.8c-.7-.4-1.3-.3-1.7.1l10 10z" fill="#34A853" />
                          </svg>
                        </div>
                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-wider text-mute">Available Soon On</p>
                          <p className="font-display text-sm font-bold text-ink">Google Play Store</p>
                        </div>
                      </div>
                      <span className="text-xs text-mute font-medium whitespace-nowrap">In review</span>
                    </div>
                    <p className="mt-2 text-[11px] leading-relaxed text-mute">
                      Developer console review in progress. Direct APK available above for immediate access.
                    </p>
                  </div>

                  {/* Official Apple App Store Card */}
                  <div className="rounded-2xl border border-line bg-panel-soft/60 p-4 transition hover:border-line">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-3">
                        {/* Official Apple Logo */}
                        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-panel border border-line shadow-xs">
                          <Apple className="h-5 w-5 text-ink" />
                        </div>
                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-wider text-mute">Available Soon On</p>
                          <p className="font-display text-sm font-bold text-ink">Apple App Store (iOS)</p>
                        </div>
                      </div>
                      <span className="text-xs text-mute font-medium whitespace-nowrap">In staging</span>
                    </div>
                    <p className="mt-2 text-[11px] leading-relaxed text-mute">
                      Native iOS Swift build in TestFlight staging. Pre-register below to receive the launch invite.
                    </p>
                  </div>
                </div>
              </div>

              {/* Technical Specifications Bar */}
              <div className="mt-6 flex flex-wrap items-center gap-y-2 gap-x-4 text-xs text-mute border-t border-line pt-5">
                <span className="font-medium text-ink">Signed Release Package</span>
                <span>•</span>
                <span>Android 8.0 & Above</span>
                <span>•</span>
                <span>Direct Package Installation</span>
                <span>•</span>
                <span>Zero Background Telemetry</span>
              </div>
            </div>

            {/* Right Column: 3D Clay Illustration Showcase */}
            <div className="lg:col-span-5 flex flex-col items-center">
              <div className="w-full rounded-3xl border border-line bg-gradient-to-b from-panel via-panel to-panel-soft p-3 sm:p-4 shadow-xl flex flex-col items-center">
                <div className="relative w-full aspect-[16/10] overflow-hidden rounded-2xl bg-panel-soft/50 flex items-center justify-center">
                  <Image
                    src="/illustrations/app-download-hero.jpg"
                    alt="OnRoad Vehicle Pricing Mobile App Illustration"
                    width={800}
                    height={500}
                    className="w-full h-full object-cover rounded-xl"
                    priority
                  />
                </div>
                <div className="mt-3 w-full px-2 py-1 text-center">
                  <p className="text-xs font-semibold text-ink">OnRoad Automotive Suite</p>
                  <p className="text-[11px] text-mute">Real-time ex-showroom catalogue and statutory road tax calculations</p>
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* Brand Value Pillars Showcase with Official Clay Illustrations */}
        <div className="mt-16 sm:mt-24">
          <div className="text-center max-w-2xl mx-auto">
            <p className="text-xs font-bold uppercase tracking-wider text-accent mb-2">
              Platform Capabilities
            </p>
            <h2 className="font-display text-2xl font-extrabold text-ink sm:text-4xl">
              Key Capabilities of the <span className="text-accent">OnRoad</span> Platform
            </h2>
            <p className="mt-3 text-sm sm:text-base text-mute">
              Structured tools and transparent calculations designed to assist vehicle buyers across India.
            </p>
          </div>

          <div className="mt-12 grid gap-8 md:grid-cols-2">
            {VALUE_PILLARS.map((p, idx) => (
              <div
                key={idx}
                className="group relative overflow-hidden rounded-3xl border border-line bg-panel p-6 sm:p-8 transition-all hover:border-accent/40 hover:shadow-xl flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-3 mb-4">
                    <span className="text-xs font-bold uppercase tracking-wider text-accent">
                      {p.category}
                    </span>
                    <span className="font-mono text-xs text-mute font-bold">0{idx + 1}</span>
                  </div>

                  <h3 className="font-display text-xl font-bold text-ink group-hover:text-accent transition">
                    {p.title}
                  </h3>

                  <p className="mt-3 text-sm leading-relaxed text-mute">
                    {p.desc}
                  </p>

                  <ul className="mt-4 space-y-2 text-xs font-medium text-ink">
                    {p.highlights.map((h, hIdx) => (
                      <li key={hIdx} className="flex items-center gap-2">
                        <span className="text-accent font-bold">•</span>
                        <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 3D Clay Illustration Container */}
                <div className="mt-6 pt-4 border-t border-line/60 flex items-center justify-center">
                  <div className="relative w-full h-44 sm:h-52 overflow-hidden rounded-2xl bg-panel-soft/50 flex items-center justify-center p-2">
                    <Image
                      src={p.illustration}
                      alt={p.title}
                      width={480}
                      height={320}
                      className="max-h-full w-auto object-contain transition-transform duration-300 group-hover:scale-105"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Store Launch Pre-Registration Module */}
        <div className="mt-16 sm:mt-24 rounded-3xl border border-line bg-gradient-to-br from-panel via-panel to-panel-soft p-8 sm:p-12 shadow-xl">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-xs font-bold uppercase tracking-wider text-accent mb-2">
              Launch Notifications
            </p>

            <h3 className="font-display text-2xl font-bold text-ink sm:text-3xl">
              Get Notified When OnRoad Launches on the Stores
            </h3>
            <p className="mt-3 text-sm text-mute max-w-xl mx-auto">
              Select your platform preference. We will send an official notification when the app is live on Google Play or the Apple App Store.
            </p>

            {/* Platform Selection Radios */}
            <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
              {[
                { id: "both", label: "Both Google Play & iOS" },
                { id: "playstore", label: "Google Play Store (Android)" },
                { id: "appstore", label: "Apple App Store (iOS)" },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setNotifyTarget(opt.id as any)}
                  className={cn(
                    "rounded-full px-4 py-2 text-xs font-semibold transition cursor-pointer",
                    notifyTarget === opt.id
                      ? "bg-accent text-white shadow-xs"
                      : "border border-line bg-panel-soft text-mute hover:text-ink hover:border-line/80"
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            {/* Input Form */}
            {notified ? (
              <div className="mt-6 rounded-2xl border border-good/30 bg-good/10 p-4 text-sm font-semibold text-good max-w-md mx-auto flex items-center justify-center gap-2">
                <Check className="h-4 w-4" />
                <span>You are registered. We will notify you upon store availability.</span>
              </div>
            ) : (
              <form onSubmit={handleNotifySubmit} className="mt-6 flex flex-col sm:flex-row gap-2 max-w-md mx-auto">
                <input
                  type="text"
                  value={contactInput}
                  onChange={(e) => setContactInput(e.target.value)}
                  placeholder="Enter email or mobile number"
                  className="h-11 flex-1 rounded-full border border-line bg-panel px-4 text-xs sm:text-sm text-ink placeholder:text-mute focus:outline-none focus:border-accent"
                />
                <button
                  type="submit"
                  className="h-11 rounded-full bg-accent px-6 text-xs sm:text-sm font-bold text-white shadow-xs hover:brightness-110 active:scale-95 transition shrink-0 cursor-pointer"
                >
                  Notify Me
                </button>
              </form>
            )}
            <p className="mt-3 text-[11px] text-mute">We respect your privacy. Strictly one notification upon launch.</p>
          </div>
        </div>

        {/* 3 Step Professional Installation Guide */}
        <div className="mt-16 sm:mt-24">
          <div className="text-center max-w-xl mx-auto">
            <p className="text-xs font-bold uppercase tracking-wider text-accent mb-2">
              Setup Guide
            </p>
            <h3 className="font-display text-2xl font-bold text-ink sm:text-3xl">
              How to Install the Android APK
            </h3>
            <p className="mt-2 text-sm text-mute">
              Follow these simple steps to set up OnRoad on your phone in under a minute.
            </p>
          </div>

          <div className="mt-10 grid gap-6 sm:grid-cols-3">
            {STEPS.map((s) => (
              <div
                key={s.step}
                className="relative rounded-2xl border border-line bg-panel p-6 shadow-xs transition hover:border-accent/40"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/15 font-mono text-sm font-bold text-accent">
                  {s.step}
                </div>
                <h4 className="mt-4 font-display text-base font-semibold text-ink">{s.title}</h4>
                <p className="mt-2 text-xs leading-relaxed text-mute">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Frequently Asked Questions */}
        <div className="mt-16 sm:mt-24 max-w-3xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-xs font-bold uppercase tracking-wider text-accent mb-2">
              Support
            </p>
            <h3 className="font-display text-2xl font-bold text-ink sm:text-3xl">Frequently Asked Questions</h3>
          </div>

          <div className="space-y-3">
            {FAQS.map((faq, index) => {
              const isOpen = activeFaq === index;
              return (
                <div
                  key={index}
                  className="rounded-2xl border border-line bg-panel overflow-hidden transition"
                >
                  <button
                    onClick={() => setActiveFaq(isOpen ? null : index)}
                    className="w-full flex items-center justify-between p-4 sm:p-5 text-left font-display text-sm sm:text-base font-semibold text-ink hover:text-accent transition cursor-pointer"
                  >
                    <span>{faq.q}</span>
                    <ChevronDown className={cn("h-4 w-4 shrink-0 text-mute transition-transform duration-200", isOpen && "rotate-180 text-accent")} />
                  </button>
                  {isOpen && (
                    <div className="px-4 pb-4 sm:px-5 sm:pb-5 text-xs sm:text-sm text-mute leading-relaxed border-t border-line/40 pt-3">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Final CTA Banner */}
        <div className="mt-16 sm:mt-24 rounded-3xl border border-accent/30 bg-gradient-to-r from-accent/15 via-panel to-panel p-8 sm:p-12 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-xl">
          <div>
            <h3 className="font-display text-2xl font-bold text-ink sm:text-3xl">
              Explore On-Road Vehicle Pricing
            </h3>
            <p className="mt-2 text-sm text-mute max-w-lg">
              Download the APK or calculate on-road pricing directly on the web.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <a
              href="/onroad.apk"
              download="onroad.apk"
              className="inline-flex items-center gap-2 rounded-full bg-accent px-6 py-3.5 text-xs sm:text-sm font-bold text-white shadow-md hover:brightness-110 active:scale-95 transition cursor-pointer"
            >
              <Download className="h-4 w-4" />
              <span>Download APK</span>
            </a>
            <Link
              href="/calculator"
              className="inline-flex items-center gap-2 rounded-full border border-line bg-panel-soft px-5 py-3.5 text-xs sm:text-sm font-semibold text-ink hover:bg-panel transition"
            >
              <Calculator className="h-4 w-4" />
              <span>Web Calculator</span>
            </Link>
          </div>
        </div>

      </div>
    </main>
  );
}
