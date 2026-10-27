import type { Metadata } from "next";
import Link from "next/link";
import { Download, ShieldCheck, Zap, Sparkles, CheckCircle2, Smartphone, Car } from "lucide-react";

export const metadata: Metadata = {
  title: "Download OnRoad Android App · Latest APK",
  description: "Download the latest OnRoad Android APK (v1.0.4). Real on-road prices, zero dealer padding, official road tax calculations, and showroom quotes.",
};

const FEATURES = [
  {
    icon: Zap,
    title: "Instant Launch & Fast Loading",
    desc: "Parallelized catalogue loading and local caching for lightning-fast speeds.",
  },
  {
    icon: ShieldCheck,
    title: "No Hidden Dealer Padding",
    desc: "Official ex-showroom prices direct from manufacturers with itemized RTO and tax breakdown.",
  },
  {
    icon: Smartphone,
    title: "Lightweight & Battery Efficient",
    desc: "Shrunk and optimized to only ~6.2 MB with zero background bloat.",
  },
];

const STEPS = [
  {
    num: "1",
    title: "Download the APK",
    desc: "Tap the button below to download the latest onroad.apk directly to your phone.",
  },
  {
    num: "2",
    title: "Open the Downloaded File",
    desc: "Tap the download notification or find it in your phone's Files / Downloads folder.",
  },
  {
    num: "3",
    title: "Tap Update (or Install)",
    desc: "Android preserves your city and saved cars. Tap Update and open the fresh app!",
  },
];

export default function DownloadPage() {
  return (
    <main className="min-h-screen pt-24 pb-20 px-4 sm:px-6">
      <div className="mx-auto max-w-4xl">
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-3xl border border-line bg-gradient-to-b from-panel via-panel to-panel-soft p-8 sm:p-12 text-center shadow-2xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-xs font-semibold text-accent mb-6">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Version 1.0.4 Live · Bug Fixes & Speed Boost</span>
          </div>

          <h1 className="font-display text-3xl font-bold tracking-tight text-ink sm:text-5xl">
            Get the Official <span className="text-accent">OnRoad</span> Android App
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-mute sm:text-lg">
            Real on-road prices for every car and bike sold in India. Official RTO tax, state cess, verified showroom locators, and honest dealer quotes in your city.
          </p>

          {/* Primary Action Button */}
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              id="download-apk-btn"
              href="/onroad.apk"
              download="onroad.apk"
              className="inline-flex w-full sm:w-auto items-center justify-center gap-3 rounded-full bg-accent px-8 py-4 text-base font-bold text-white shadow-lg shadow-accent/25 transition hover:brightness-110 active:scale-95"
            >
              <Download className="h-5 w-5" />
              <span>Download Latest APK (6.2 MB)</span>
            </a>
            <Link
              href="/cars"
              className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-full border border-line bg-panel px-6 py-4 text-base font-semibold text-ink transition hover:bg-panel-soft"
            >
              <Car className="h-4 w-4" />
              <span>Explore on Web Instead</span>
            </Link>
          </div>

          <div className="mt-6 flex items-center justify-center gap-6 text-xs text-mute">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-good" /> Verified Virus-Free
            </span>
            <span>•</span>
            <span>Android 8.0 & Above</span>
            <span>•</span>
            <span>Signed Release Build</span>
          </div>
        </div>

        {/* 3 Step Installation Guide */}
        <div className="mt-14">
          <h2 className="text-center font-display text-2xl font-bold text-ink sm:text-3xl">
            How to Update or Install in 3 Easy Steps
          </h2>
          <p className="mt-2 text-center text-sm text-mute">
            Already have OnRoad installed from WhatsApp? Just tap Update—you will NOT lose any saved data.
          </p>

          <div className="mt-8 grid gap-6 sm:grid-cols-3">
            {STEPS.map((s) => (
              <div
                key={s.num}
                className="relative rounded-2xl border border-line bg-panel p-6 shadow-sm transition hover:border-accent/40"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/15 font-display text-lg font-bold text-accent">
                  {s.num}
                </div>
                <h3 className="mt-4 font-display text-lg font-semibold text-ink">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-mute">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* What's New Section */}
        <div className="mt-14 rounded-2xl border border-line bg-panel p-8">
          <h3 className="font-display text-xl font-bold text-ink">What&apos;s New in v1.0.4</h3>
          <ul className="mt-4 space-y-3 text-sm text-mute">
            <li className="flex items-start gap-3">
              <span className="rounded-md bg-good/15 p-1 text-good">✓</span>
              <span><strong>Instant Home Screen:</strong> Fixed the blank screen after intro animation. Home now displays immediate skeleton placeholders while loading.</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="rounded-md bg-good/15 p-1 text-good">✓</span>
              <span><strong>Parallel Loading:</strong> Brands, explore cars, live offers, and budget tiers now fetch concurrently, reducing wait time by 75%.</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="rounded-md bg-good/15 p-1 text-good">✓</span>
              <span><strong>50 MB Local HTTP Cache:</strong> The catalogue is cached on your device for instant launch speeds and offline viewing.</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="rounded-md bg-good/15 p-1 text-good">✓</span>
              <span><strong>In-App Update Checker:</strong> Added an update notification in Profile so future updates can be installed with a single tap.</span>
            </li>
          </ul>
        </div>

        {/* Features Grid */}
        <div className="mt-14 grid gap-6 sm:grid-cols-3">
          {FEATURES.map((f, i) => {
            const Icon = f.icon;
            return (
              <div key={i} className="rounded-2xl border border-line bg-panel p-6">
                <Icon className="h-6 w-6 text-accent" />
                <h4 className="mt-3 font-display font-semibold text-ink">{f.title}</h4>
                <p className="mt-1.5 text-xs leading-relaxed text-mute">{f.desc}</p>
              </div>
            );
          })}
        </div>

        {/* Share Section */}
        <div className="mt-14 text-center">
          <p className="text-sm font-medium text-mute">
            Want to share this with friends or family on WhatsApp?
          </p>
          <p className="mt-1 text-xs text-mute/80">
            Share this link: <code className="rounded bg-panel-soft px-2 py-1 text-accent font-mono">https://onroad-frontend.onrender.com/download</code>
          </p>
        </div>
      </div>
    </main>
  );
}
