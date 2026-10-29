"use client";

import Script from "next/script";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

/** Firebase / Google Analytics for the website: a page view on every navigation (the site is a single-page app, so
 *  route changes are sent by hand), plus the buyer events in lib/track.ts. No ads signals; IPs anonymised. */
const GA_ID = process.env.NEXT_PUBLIC_GA_ID ?? "G-EQYHBV82ZV";

function PageViews() {
  const path = usePathname();
  const qs = useSearchParams();
  useEffect(() => {
    const g = (window as unknown as { gtag?: (...a: unknown[]) => void }).gtag;
    g?.("event", "page_view", { page_path: path + (qs?.toString() ? `?${qs}` : ""), page_location: window.location.href });
  }, [path, qs]);
  return null;
}

export function Analytics() {
  if (!GA_ID) return null;
  return (
    <>
      <Script src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`} strategy="afterInteractive" />
      <Script id="ga" strategy="afterInteractive">{`
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', '${GA_ID}', { anonymize_ip: true, allow_google_signals: false, allow_ad_personalization_signals: false, send_page_view: false });
      `}</Script>
      <Suspense fallback={null}><PageViews /></Suspense>
    </>
  );
}
