"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { 
  Smartphone, 
  Download, 
  ArrowRight, 
  CheckCircle2, 
  Share2, 
  PlusSquare, 
  Apple, 
  ChevronRight
} from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui";
import { Logo } from "@/components/logo";

export default function AppRedirectPage() {
  const [device, setDevice] = useState<"detecting" | "android" | "ios" | "desktop">("detecting");
  const [downloadTriggered, setDownloadTriggered] = useState(false);
  const [iosEmail, setIosEmail] = useState("");
  const [iosSubmitted, setIosSubmitted] = useState(false);

  useEffect(() => {
    const ua = navigator.userAgent || navigator.vendor || "";
    const isAndroid = /android/i.test(ua);
    const isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

    if (isAndroid) {
      setDevice("android");
      const timer = setTimeout(() => {
        setDownloadTriggered(true);
        const link = document.createElement("a");
        link.href = "/onroad.apk";
        link.download = "onroad.apk";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        toast.success("Downloading OnRoad for Android (v1.0.4)...");
      }, 700);
      return () => clearTimeout(timer);
    } else if (isIOS) {
      setDevice("ios");
    } else {
      setDevice("desktop");
    }
  }, []);

  const handleIosWaitlist = (e: React.FormEvent) => {
    e.preventDefault();
    if (!iosEmail || !iosEmail.includes("@")) {
      toast.error("Please enter a valid email address");
      return;
    }
    setIosSubmitted(true);
    toast.success("Thank you! You will receive the TestFlight invite shortly.");
  };

  return (
    <main className="min-h-screen bg-night text-ink flex flex-col justify-between selection:bg-accent/30 selection:text-white">
      {/* Header */}
      <header className="border-b border-line bg-panel/60 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <Logo size={28} />
          <span className="font-[family-name:var(--font-display)] text-lg font-bold text-white tracking-tight">
            OnRoad
          </span>
        </Link>
        <Link 
          href="/" 
          className="text-xs text-mute hover:text-ink transition flex items-center gap-1 font-medium"
        >
          Open Web App <ChevronRight className="h-3.5 w-3.5" />
        </Link>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-8">
        <div className="w-full max-w-lg">
          {/* 1. Android View */}
          {device === "android" && (
            <Card className="p-6 sm:p-8 border-line bg-panel shadow-2xl relative overflow-hidden text-center space-y-6">
              <div className="flex flex-col items-center gap-3">
                <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-panel-soft text-accent border border-line">
                  <Smartphone className="h-7 w-7" />
                </span>
                <div>
                  <h1 className="font-[family-name:var(--font-display)] text-2xl sm:text-3xl font-bold text-ink">
                    OnRoad for Android
                  </h1>
                  <p className="text-xs text-mute mt-1">
                    Official Release · v1.0.4 (6.2 MB)
                  </p>
                </div>
              </div>

              {/* Download Status */}
              <div className="rounded-xl border border-line bg-panel-soft/60 p-4 text-xs text-mute flex items-center justify-between gap-3 text-left">
                <div className="flex items-center gap-2.5">
                  <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
                  <span>
                    {downloadTriggered 
                      ? "Download started. Check your notifications or downloads folder." 
                      : "Starting download..."}
                  </span>
                </div>
                <a
                  href="/onroad.apk"
                  download="onroad.apk"
                  className="font-semibold text-accent hover:underline shrink-0 text-xs"
                >
                  Restart
                </a>
              </div>

              {/* Quick 3-Step Install Guide */}
              <div className="text-left space-y-2.5 pt-1">
                <p className="text-xs font-semibold text-mute">
                  How to install:
                </p>
                <div className="space-y-2 text-xs">
                  <div className="flex items-start gap-3 rounded-xl border border-line bg-panel-soft p-3">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent text-[11px] font-bold text-white">
                      1
                    </span>
                    <p className="text-ink/90">
                      Tap <strong className="text-white">onroad.apk</strong> in your browser notifications or Downloads.
                    </p>
                  </div>
                  <div className="flex items-start gap-3 rounded-xl border border-line bg-panel-soft p-3">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent text-[11px] font-bold text-white">
                      2
                    </span>
                    <p className="text-ink/90">
                      Tap <strong className="text-white">Install</strong> when prompted by the package installer.
                    </p>
                  </div>
                  <div className="flex items-start gap-3 rounded-xl border border-line bg-panel-soft p-3">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent text-[11px] font-bold text-white">
                      3
                    </span>
                    <p className="text-ink/90">
                      Open OnRoad to check official prices and verify dealer quotations.
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-col sm:flex-row gap-3">
                <a
                  href="/onroad.apk"
                  download="onroad.apk"
                  className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-accent px-5 py-3 text-xs sm:text-sm font-semibold text-white shadow-md hover:brightness-110 transition cursor-pointer"
                >
                  <Download className="h-4 w-4" /> Download APK (6.2 MB)
                </a>
                <Link
                  href="/"
                  className="inline-flex items-center justify-center rounded-xl border border-line bg-panel-soft px-4 py-3 text-xs sm:text-sm font-medium text-mute hover:text-ink transition"
                >
                  Open in Browser
                </Link>
              </div>
            </Card>
          )}

          {/* 2. iOS View */}
          {device === "ios" && (
            <Card className="p-6 sm:p-8 border-line bg-panel shadow-2xl relative overflow-hidden space-y-6">
              <div className="flex flex-col items-center text-center gap-3">
                <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-white border border-white/20">
                  <Apple className="h-8 w-8" />
                </span>
                <div>
                  <h1 className="font-[family-name:var(--font-display)] text-2xl sm:text-3xl font-bold text-ink">
                    OnRoad for iPhone
                  </h1>
                  <p className="text-xs text-mute mt-1">
                    Official on-road prices and quote audits on iOS
                  </p>
                </div>
              </div>

              {/* Option 1: Add to Home Screen */}
              <div className="rounded-2xl border border-line bg-panel-soft/60 p-4 sm:p-5 space-y-3">
                <div className="flex items-center gap-2 text-ink font-semibold text-sm">
                  <Smartphone className="h-4 w-4 text-accent" />
                  <span>Add to Home Screen (Instant)</span>
                </div>
                <p className="text-xs text-mute">
                  Install OnRoad directly to your home screen for instant access and full offline pricing:
                </p>
                <div className="space-y-2 text-xs text-ink/90">
                  <div className="flex items-center gap-2.5 rounded-xl bg-panel p-2.5 border border-line">
                    <Share2 className="h-4 w-4 text-blue-400 shrink-0" />
                    <span>1. Tap the <strong className="text-white">Share</strong> button at the bottom of Safari</span>
                  </div>
                  <div className="flex items-center gap-2.5 rounded-xl bg-panel p-2.5 border border-line">
                    <PlusSquare className="h-4 w-4 text-accent shrink-0" />
                    <span>2. Tap <strong className="text-white">&quot;Add to Home Screen&quot;</strong></span>
                  </div>
                  <div className="flex items-center gap-2.5 rounded-xl bg-panel p-2.5 border border-line">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>3. Tap <strong className="text-white">Add</strong> in the top right corner</span>
                  </div>
                </div>
              </div>

              {/* Option 2: TestFlight Waitlist */}
              <div className="rounded-2xl border border-line bg-panel-soft/60 p-4 sm:p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-ink">
                    Join Native iOS Preview (TestFlight)
                  </span>
                  <span className="text-[10px] text-mute">
                    Native Swift Build
                  </span>
                </div>
                {iosSubmitted ? (
                  <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-400 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                    <span>Invitation queued for <strong>{iosEmail}</strong>.</span>
                  </div>
                ) : (
                  <form onSubmit={handleIosWaitlist} className="flex gap-2">
                    <input
                      type="email"
                      required
                      placeholder="Enter your email"
                      value={iosEmail}
                      onChange={(e) => setIosEmail(e.target.value)}
                      className="flex-1 rounded-xl border border-line bg-panel px-3.5 py-2.5 text-xs text-ink placeholder:text-mute focus:outline-none focus:border-accent"
                    />
                    <button
                      type="submit"
                      className="rounded-xl bg-white text-black px-4 py-2.5 text-xs font-semibold hover:bg-white/90 transition cursor-pointer shrink-0"
                    >
                      Get Invite
                    </button>
                  </form>
                )}
              </div>

              <div className="pt-2 flex flex-col gap-2.5">
                <Link
                  href="/"
                  className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-accent px-5 py-3 text-xs sm:text-sm font-semibold text-white shadow-md hover:brightness-110 active:scale-95 transition"
                >
                  <Smartphone className="h-4 w-4" />
                  <span>Open OnRoad App (Instant Fullscreen)</span>
                </Link>
                <p className="text-[11px] text-mute text-center">
                  Follow steps 1–3 above to add OnRoad directly to your iPhone Home Screen.
                </p>
              </div>
            </Card>
          )}

          {/* 3. Desktop View */}
          {(device === "desktop" || device === "detecting") && (
            <Card className="p-6 sm:p-8 border-line bg-panel shadow-2xl text-center space-y-6">
              <div className="flex flex-col items-center gap-2">
                <Logo size={36} />
                <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold text-ink">
                  Get OnRoad on your phone
                </h1>
                <p className="text-xs text-mute">
                  Scan the QR code with your phone camera to download.
                </p>
              </div>

              <div className="flex flex-col items-center justify-center p-5 rounded-2xl bg-panel-soft/60 border border-line">
                <div className="bg-white p-3 rounded-2xl shadow-lg">
                  <Image
                    src="/onroad-apk-qr.png"
                    alt="OnRoad App QR Code"
                    width={160}
                    height={160}
                    className="rounded-lg"
                  />
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 pt-1">
                <a
                  href="/onroad.apk"
                  download="onroad.apk"
                  className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-accent px-4 py-3 text-xs font-semibold text-white shadow-md hover:brightness-110 transition"
                >
                  <Download className="h-4 w-4" /> Download APK (6.2 MB)
                </a>
                <Link
                  href="/"
                  className="inline-flex items-center justify-center rounded-xl border border-line bg-panel-soft px-4 py-3 text-xs font-medium text-mute hover:text-ink transition"
                >
                  Return to Home
                </Link>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-line px-6 py-4 text-center text-xs text-mute">
        OnRoad Automotive Suite · Official Indian Road Tax & Price Engine
      </footer>
    </main>
  );
}
