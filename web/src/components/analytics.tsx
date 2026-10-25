import Script from "next/script";

/** Firebase / Google Analytics for the website (page views only; no ads signals, IPs anonymised). */
const GA_ID = process.env.NEXT_PUBLIC_GA_ID ?? "G-EQYHBV82ZV";

export function Analytics() {
  if (!GA_ID) return null;
  return (
    <>
      <Script src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`} strategy="afterInteractive" />
      <Script id="ga" strategy="afterInteractive">{`
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', '${GA_ID}', { anonymize_ip: true, allow_google_signals: false, allow_ad_personalization_signals: false });
      `}</Script>
    </>
  );
}
