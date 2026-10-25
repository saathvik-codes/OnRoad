import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Space_Grotesk } from "next/font/google";
import { Suspense } from "react";
import { Toaster } from "sonner";
import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";
import { SmoothScroll } from "@/components/smooth-scroll";
import { CityProvider } from "@/components/city";
import { THEME_SCRIPT, ThemeProvider } from "@/components/theme";
import { MobileNav } from "@/components/mobile-nav";
import { Analytics } from "@/components/analytics";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
const display = Space_Grotesk({ variable: "--font-display", subsets: ["latin"], weight: ["500", "700"] });

export const viewport: Viewport = {
  themeColor: "#05060a",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  viewportFit: "cover",
};

export const metadata: Metadata = {
  title: { default: "OnRoad · The real on-road price of every car in India", template: "%s · OnRoad" },
  description: "Every car sold in India with every variant, the manufacturer's ex-showroom price for your city, an itemised on-road price "
    + "with road tax, RTO, insurance and TCS, live offers, nearby dealers, and dealer quotes that compete for you.",
  openGraph: { images: [{ url: "/og.jpg", width: 1200, height: 630 }] },
  twitter: { card: "summary_large_image", images: ["/og.jpg"] },
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "OnRoad",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en-IN" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} ${display.variable} antialiased`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className="grain min-h-screen">
        <ThemeProvider>
          <SmoothScroll />
          <CityProvider>
            <Suspense><SiteNav /></Suspense>
            {children}
            <Suspense><SiteFooter /></Suspense>
            <MobileNav />
          </CityProvider>
          <Toaster richColors position="top-right" />
        </ThemeProvider>
              <Analytics />
      </body>
    </html>
  );
}
