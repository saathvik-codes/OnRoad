"use client";

// The QR code points here. Android phones get the APK straight away; iPhones get "Add to Home Screen" steps (the
// web app installs like an app and needs no App Store); computers are sent to /download, which shows the QR code.

import Link from "next/link";
import { useEffect, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import { Download, PlusSquare, Share } from "lucide-react";
import { Button, Card } from "@/components/ui";
import { Logo } from "@/components/logo";

type Device = "detecting" | "android" | "ios" | "desktop";

function detect(): Device {
  const ua = navigator.userAgent || "";
  if (/android/i.test(ua)) return "android";
  if (/iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)) return "ios";
  return "desktop";
}

export default function AppInstall() {
  const router = useRouter();
  const device = useSyncExternalStore(() => () => {}, detect, () => "detecting" as Device);
  useEffect(() => {
    if (device === "desktop") router.replace("/download");
  }, [device, router]);

  return (
    <main className="mx-auto flex min-h-[80vh] max-w-md flex-col justify-center gap-6 px-4 py-10">
      <Link href="/" className="mx-auto"><Logo /></Link>

      {device === "android" && (
        <Card className="space-y-5 p-6">
          <div>
            <h1 className="font-display text-2xl font-bold text-ink">OnRoad for Android</h1>
            <p className="mt-1 text-sm text-mute">Android 8.0 or newer · about 6 MB</p>
          </div>
          <a href="/onroad.apk" download="OnRoad.apk"><Button className="w-full"><Download className="mr-2 h-4 w-4" />Download the app</Button></a>
          <ol className="list-decimal space-y-2 pl-5 text-sm text-mute">
            <li>Open <b className="text-ink">OnRoad.apk</b> from the download notification or your Downloads folder.</li>
            <li>If Android asks, allow installs from your browser for this one download, then tap <b className="text-ink">Install</b>.</li>
            <li>Open OnRoad and pick your city.</li>
          </ol>
          <p className="text-xs text-mute">Updating from a build installed before 26 October 2026? Uninstall that one first; the app&apos;s signing key changed.</p>
        </Card>
      )}

      {device === "ios" && (
        <Card className="space-y-5 p-6">
          <div>
            <h1 className="font-display text-2xl font-bold text-ink">OnRoad on your iPhone</h1>
            <p className="mt-1 text-sm text-mute">Add OnRoad to your Home Screen. It opens full-screen like an app, with no App Store download.</p>
          </div>
          <ol className="space-y-4 text-sm text-mute">
            <li className="flex gap-3"><span className="font-mono text-accent">1</span><span>Open this page in <b className="text-ink">Safari</b>.</span></li>
            <li className="flex gap-3"><span className="font-mono text-accent">2</span>
              <span>Tap <Share className="inline h-4 w-4 align-text-bottom text-ink" /> <b className="text-ink">Share</b> at the bottom of the screen.</span></li>
            <li className="flex gap-3"><span className="font-mono text-accent">3</span>
              <span>Choose <PlusSquare className="inline h-4 w-4 align-text-bottom text-ink" /> <b className="text-ink">Add to Home Screen</b>, then <b className="text-ink">Add</b>.</span></li>
          </ol>
          <Link href="/"><Button variant="outline" className="w-full">Open OnRoad now</Button></Link>
          <p className="text-xs text-mute">The native iPhone app isn&apos;t on the App Store yet. The Home Screen version has the same prices, offers and showrooms.</p>
        </Card>
      )}

      {(device === "detecting" || device === "desktop") && <p className="text-center text-sm text-mute">Checking your phone…</p>}
    </main>
  );
}
