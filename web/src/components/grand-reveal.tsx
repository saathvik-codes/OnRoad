"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion, AnimatePresence } from "motion/react";
import { 
    ArrowRight, 
  ShieldCheck, 
  Gauge, 
  Fuel, 
  Zap, 
  ChevronRight, 
  ChevronLeft,
  Flame,
  Award,
  Newspaper,
  Calendar,
  CheckCircle2
} from "lucide-react";
import { cn } from "@/components/ui";
import { useCity } from "@/components/city";

interface RevealVehicle {
  id: string;
  name: string;
  brand: string;
  tagline: string;
  badge: string;
  status: "Now in Showrooms" | "Bookings Open" | "Premiere";
  launchPrice: string;
  power: string;
  efficiency: string;
  safety: string;
  headlineFeatures: string[];
  image: string;
  link: string;
  colorGradient: string;
}

const REVEALS: RevealVehicle[] = [
  {
    id: "hyundai-bayon",
    name: "New Hyundai Bayon",
    brand: "Hyundai",
    tagline: "Futuristic Horizon LED Lightbar, N-Line Turbo Dynamics & SmartSense L2 ADAS",
    badge: "Global Premiere · Subcompact Crossover",
    status: "Premiere",
    launchPrice: "Est. ₹8.49L – ₹12.80L",
    power: "120 PS 1.0L T-GDi Mild-Hybrid",
    efficiency: "19.8 km/l ARAI Est.",
    safety: "SmartSense L2 ADAS & 6 Airbags",
    headlineFeatures: ["Edge-to-Edge Horizon LED Bar", "Dual 10.25\" Panoramic Digital Cockpit", "7-Speed Dual-Clutch Transmission", "411L Class-Leading Luggage Space"],
    image: "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1200&q=80",
    link: "/news",
    colorGradient: "from-blue-600/20 via-cyan-600/10 to-transparent",
  },
  {
    id: "thar-roxx",
    name: "Thar Roxx (5-Door)",
    brand: "Mahindra",
    tagline: "The Legend Expands with 5-Door Luxury & Unmatched Off-Road Prowess",
    badge: "5-Star Bharat NCAP · Flagship SUV",
    status: "Now in Showrooms",
    launchPrice: "From ₹12.99 Lakh",
    power: "177 PS Turbo / 175 PS Diesel",
    efficiency: "15.2 km/l ARAI",
    safety: "5★ Bharat NCAP",
    headlineFeatures: ["Dual-Pane Panoramic Skyroof", "Level 2 ADAS Suite (10 Functions)", "Harman Kardon 9-Speaker Audio", "Frequency Dependent Damping"],
    image: "/illustrations/app-download-hero.jpg",
    link: "/cars?q=Thar",
    colorGradient: "from-amber-600/20 via-orange-600/10 to-transparent",
  },
  {
    id: "curvv",
    name: "Curvv & Curvv.EV",
    brand: "Tata Motors",
    tagline: "India's First Mass Coupe SUV with Striking Aerodynamics",
    badge: "502 km Certified Range · First-in-Segment",
    status: "Now in Showrooms",
    launchPrice: "From ₹9.99 Lakh (ICE) / ₹17.49 Lakh (EV)",
    power: "125 PS Hyperion GDi / 167 PS EV",
    efficiency: "502 km Range / 18.0 km/l",
    safety: "5★ Bharat NCAP Expected",
    headlineFeatures: ["Gesture-Controlled Powered Tailgate", "Multi-Dial Digital Instrument Cluster", "Vehicle-to-Vehicle (V2V) Charging", "Flush Door Handles with Welcome Light"],
    image: "/illustrations/app-download-hero.jpg",
    link: "/cars?q=Curvv",
    colorGradient: "from-blue-600/20 via-indigo-600/10 to-transparent",
  },
  {
    id: "creta-n-line",
    name: "Creta N-Line",
    brand: "Hyundai",
    tagline: "WRC Rally-Inspired Performance with Dual-Tip Exhaust Symphony",
    badge: "160 PS Turbo GDi · Motorsport Tuned",
    status: "Now in Showrooms",
    launchPrice: "From ₹16.82 Lakh",
    power: "160 PS / 253 Nm Torque",
    efficiency: "18.2 km/l ARAI",
    safety: "Level 2 ADAS (SmartSense)",
    headlineFeatures: ["Rally-Tuned Stiffer Dampers & Weighted Steering", "Twin-Tip Resonant Sport Exhaust", "N-Exclusive Leatherette with Red Accents", "18-inch Diamond-Cut N-Line Alloys"],
    image: "/illustrations/app-download-hero.jpg",
    link: "/cars/hyundai/creta",
    colorGradient: "from-red-600/20 via-accent/10 to-transparent",
  },
  {
    id: "dzire",
    name: "All-New Dzire (4th Gen)",
    brand: "Maruti Suzuki",
    tagline: "Historic 5-Star Safety Breakthrough in India's Favourite Compact Sedan",
    badge: "5-Star Global NCAP Historic First",
    status: "Now in Showrooms",
    launchPrice: "From ₹6.79 Lakh",
    power: "82 PS Z-Series 1.2L Engine",
    efficiency: "24.79 km/l (P) / 33.73 km/kg (CNG)",
    safety: "5★ Global NCAP",
    headlineFeatures: ["Segment-First Electric Glass Sunroof", "6 Airbags Standard Across All Trims", "360-Degree Surround Camera", "Wireless Android Auto & Apple CarPlay"],
    image: "/illustrations/app-download-hero.jpg",
    link: "/cars?q=Dzire",
    colorGradient: "from-emerald-600/20 via-teal-600/10 to-transparent",
  },
  {
    id: "bear-650",
    name: "Bear 650",
    brand: "Royal Enfield",
    tagline: "Pure 60s California Desert Racing DNA Powered by Twin Cylinders",
    badge: "648cc Parallel-Twin Scrambler",
    status: "Bookings Open",
    launchPrice: "From ₹3.39 Lakh",
    power: "47.4 PS / 56.5 Nm Torque",
    efficiency: "22.5 km/l Estimated",
    safety: "Dual-Channel Switchable ABS",
    headlineFeatures: ["Showa Upside Down Big-Piston Front Forks", "First RE Twin with 2-into-1 Performance Header", "Full Colour Tripper TFT Navigation", "19-inch Front Wheel with Dual-Purpose Tyres"],
    image: "/illustrations/app-download-hero.jpg",
    link: "/bikes?q=Bear",
    colorGradient: "from-amber-700/20 via-yellow-600/10 to-transparent",
  },
];

const NEWS_BULLETINS = [
  {
    tag: "Government Gazette",
    title: "100% Road Tax Exemption for Electric Vehicles Extended in Key Indian Metros",
    time: "Today",
  },
  {
    tag: "Safety Standard",
    title: "MoRTH Mandates 6 Airbags & Electronic Stability Control as Baseline Norms",
    time: "Yesterday",
  },
  {
    tag: "Insurance IRDAI",
    title: "IRDAI Directs Zero-Depreciation Add-on Standardization Across All Insurers",
    time: "2 days ago",
  },
  {
    tag: "Registration RTA",
    title: "BH-Series Registration Extended to Private Corporate Employees in 4+ States",
    time: "This week",
  },
];

export function GrandRevealSection() {
  const { city } = useCity();
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [paused, setPaused] = useState(false);

  const current = REVEALS[selectedIdx];

  // Auto-advance every 6 seconds unless user is hovering/interacting
  useEffect(() => {
    if (paused) return;
    const timer = setInterval(() => {
      setSelectedIdx((prev) => (prev + 1) % REVEALS.length);
    }, 6000);
    return () => clearInterval(timer);
  }, [paused]);

  return (
    <section 
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      className="relative overflow-hidden rounded-3xl border border-line bg-gradient-to-b from-panel via-panel to-panel-soft p-6 sm:p-10 shadow-2xl"
    >
      {/* Background Ambient Glow */}
      <div 
        className={cn(
          "pointer-events-none absolute inset-0 bg-gradient-to-r opacity-60 transition-all duration-700",
          current.colorGradient
        )} 
      />

      <div className="relative z-10 space-y-8">
        {/* Section Header */}
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-6">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="flex h-6 items-center gap-1.5 rounded-full bg-accent/15 px-2.5 text-[11px] font-bold text-accent border border-accent/25">
                <Flame className="h-3 w-3" /> THE GRAND REVEAL
              </span>
              <span className="text-xs text-mute font-medium">
                Live Automotive Spotlights & Official Launches
              </span>
            </div>
            <h2 className="font-[family-name:var(--font-display)] text-2xl sm:text-4xl font-extrabold text-ink tracking-tight">
              Major New Arrivals in {city}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/news"
              className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-line bg-panel-soft px-3.5 py-1.5 text-xs font-semibold text-ink hover:border-accent hover:text-accent transition shadow-xs"
            >
              <Newspaper className="h-3.5 w-3.5 text-accent" />
              <span>All News & Video Journals</span>
            </Link>

          {/* Carousel Selector Dots & Arrows */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedIdx((prev) => (prev - 1 + REVEALS.length) % REVEALS.length)}
              className="rounded-full border border-line bg-panel p-2 text-mute hover:text-ink hover:bg-panel-soft transition cursor-pointer"
              aria-label="Previous reveal"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <div className="flex gap-1.5 px-2">
              {REVEALS.map((r, i) => (
                <button
                  key={r.id}
                  onClick={() => setSelectedIdx(i)}
                  className={cn(
                    "h-2 rounded-full transition-all cursor-pointer",
                    i === selectedIdx ? "w-6 bg-accent" : "w-2 bg-line hover:bg-mute"
                  )}
                  aria-label={`Go to ${r.name}`}
                />
              ))}
            </div>
            <button
              onClick={() => setSelectedIdx((prev) => (prev + 1) % REVEALS.length)}
              className="rounded-full border border-line bg-panel p-2 text-mute hover:text-ink hover:bg-panel-soft transition cursor-pointer"
              aria-label="Next reveal"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

        {/* Featured Vehicle Showcase Panel */}
        <AnimatePresence mode="wait">
          <motion.div
            key={current.id}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: "easeInOut" }}
            className="grid lg:grid-cols-12 gap-8 items-center"
          >
            {/* Left Content (7 Cols) */}
            <div className="lg:col-span-7 space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-md bg-panel-soft border border-line px-2.5 py-0.5 text-xs font-bold text-accent uppercase tracking-wider">
                  {current.brand}
                </span>
                <span className="rounded-md bg-emerald-500/15 border border-emerald-500/25 px-2.5 py-0.5 text-xs font-bold text-emerald-600 dark:text-emerald-400">
                  {current.badge}
                </span>
                <span className="rounded-md bg-panel border border-line px-2.5 py-0.5 text-xs text-mute">
                  {current.status}
                </span>
              </div>

              <div>
                <h3 className="font-[family-name:var(--font-display)] text-3xl sm:text-5xl font-black text-ink leading-tight">
                  {current.name}
                </h3>
                <p className="mt-1 text-sm sm:text-base text-mute leading-relaxed font-normal">
                  {current.tagline}
                </p>
              </div>

              {/* Price & Specs Matrix */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2">
                <div className="rounded-xl border border-line bg-panel p-3">
                  <span className="text-[10px] uppercase tracking-wider text-mute block font-medium">Launch Price</span>
                  <span className="font-mono text-sm sm:text-base font-bold text-ink mt-0.5 block">{current.launchPrice}</span>
                </div>
                <div className="rounded-xl border border-line bg-panel p-3">
                  <span className="text-[10px] uppercase tracking-wider text-mute block font-medium">Power & Torque</span>
                  <span className="font-mono text-xs sm:text-sm font-semibold text-ink mt-0.5 block line-clamp-1">{current.power}</span>
                </div>
                <div className="rounded-xl border border-line bg-panel p-3">
                  <span className="text-[10px] uppercase tracking-wider text-mute block font-medium">Efficiency / Range</span>
                  <span className="font-mono text-xs sm:text-sm font-semibold text-ink mt-0.5 block">{current.efficiency}</span>
                </div>
                <div className="rounded-xl border border-line bg-panel p-3">
                  <span className="text-[10px] uppercase tracking-wider text-mute block font-medium">Crash Safety</span>
                  <span className="font-mono text-xs sm:text-sm font-semibold text-emerald-500 mt-0.5 block">{current.safety}</span>
                </div>
              </div>

              {/* Reveal Highlights */}
              <div className="space-y-1.5 pt-1">
                <span className="text-xs font-bold uppercase tracking-wider text-mute block">
                  Groundbreaking Innovations:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {current.headlineFeatures.map((f, i) => (
                    <div key={i} className="flex items-center gap-2 text-ink/90">
                      <CheckCircle2 className="h-3.5 w-3.5 text-accent shrink-0" />
                      <span>{f}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Call to Action */}
              <div className="pt-3 flex flex-wrap items-center gap-3">
                <Link
                  href={current.link}
                  className="inline-flex items-center gap-2 rounded-xl bg-accent px-6 py-3 text-xs sm:text-sm font-bold text-white shadow-lg shadow-accent/25 hover:brightness-110 active:scale-95 transition"
                >
                  Unveil On-Road Price in {city} <ArrowRight className="h-4 w-4" />
                </Link>
                <span className="text-xs text-mute font-medium">
                  Includes official {city} RTO registration & road tax calculations
                </span>
              </div>
            </div>

            {/* Right Media Graphic (5 Cols) */}
            <div className="lg:col-span-5 flex flex-col items-center">
              <div className="relative w-full aspect-[16/10] rounded-2xl overflow-hidden border border-line bg-panel shadow-2xl p-2 group">
                <Image
                  src={current.image}
                  alt={current.name}
                  width={640}
                  height={400}
                  className="w-full h-full object-cover rounded-xl transition duration-700 group-hover:scale-105"
                  priority
                />
                <div className="absolute bottom-4 left-4 right-4 rounded-xl bg-black/75 backdrop-blur-md border border-white/10 p-3 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-mono text-white/70 uppercase">Official Reveal Model</span>
                    <p className="text-xs font-bold text-white">{current.brand} {current.name}</p>
                  </div>
                  <span className="rounded-full bg-accent px-2.5 py-0.5 text-[10px] font-bold text-white">
                    2026 Edition
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Live Automotive News Bulletins */}
        <div className="border-t border-line pt-6">
          <div className="flex items-center gap-2 mb-3">
            <Newspaper className="h-4 w-4 text-accent" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-ink">
              Live Industry Bulletins & Regulatory Updates
            </h4>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {NEWS_BULLETINS.map((b, i) => (
              <div 
                key={i} 
                className="rounded-xl border border-line bg-panel/70 p-3.5 space-y-1.5 transition hover:border-accent/40"
              >
                <div className="flex items-center justify-between text-[10px] text-mute font-medium">
                  <span className="text-accent font-semibold">{b.tag}</span>
                  <span>{b.time}</span>
                </div>
                <p className="text-xs font-medium text-ink/90 leading-snug line-clamp-2">
                  {b.title}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
