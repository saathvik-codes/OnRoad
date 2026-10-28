"use client";

import { useState } from "react";
import Link from "next/link";
import { 
  Calendar, 
  Clock, 
  Search, 
  ChevronRight, 
  Share2, 
  Bookmark, 
  Eye, 
  Zap, 
  ShieldCheck, 
  SlidersHorizontal,
  Flame,
  Award,
  ArrowUpRight,
  TrendingUp,
  Fuel,
  Gauge,
  Tag
} from "lucide-react";
import { NewsVideoPlayer } from "@/components/news-video-player";
import { cn } from "@/components/ui";

interface Article {
  id: string;
  slug: string;
  category: "New Reveals" | "Video Deep Dives" | "Spy Radar" | "Tax & Regulations";
  title: string;
  excerpt: string;
  publishedAt: string;
  readTime: string;
  author: string;
  image: string;
  featured?: boolean;
  tags: string[];
  specs?: { label: string; value: string }[];
}

const ARTICLES: Article[] = [
  {
    id: "hyundai-bayon-reveal",
    slug: "new-hyundai-bayon-revealed-specs-india-launch",
    category: "New Reveals",
    title: "New Hyundai Bayon Revealed: N-Line Aero, 1.0L Turbo Mild-Hybrid & India Launch Radar",
    excerpt: "Hyundai has pulled the wraps off the heavily updated Bayon crossover featuring an edge-to-edge Horizon LED lightbar, dual 10.25-inch cockpit screens, Level 2 ADAS radar, and a 120 PS 48V electrified powertrain evaluated for the Indian market.",
    publishedAt: "October 28, 2026",
    readTime: "5 min read",
    author: "Rohan Varma",
    image: "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1200&q=80",
    featured: true,
    tags: ["Hyundai", "Bayon", "Subcompact SUV", "ADAS", "Turbo Petrol"],
    specs: [
      { label: "Engine", value: "1.0L T-GDi Turbo Petrol 48V" },
      { label: "Power / Torque", value: "120 PS / 172 Nm" },
      { label: "Transmission", value: "7-speed DCT / 6-speed iMT" },
      { label: "Est. India Price", value: "₹8.49L – ₹12.80L Ex-Showroom" },
      { label: "Launch Window", value: "Evaluated Q3 2025 / 2026" },
      { label: "Direct Rivals", value: "Maruti Fronx, Skoda Kylaq, Venue" }
    ]
  },
  {
    id: "skoda-kylaq-launch",
    slug: "skoda-kylaq-sub-4m-suv-pricing-variants-breakdown",
    category: "New Reveals",
    title: "Skoda Kylaq Debuts at ₹7.89 Lakh: German Engineering at Sub-4 Metre Prices",
    excerpt: "Skoda India enters the high-volume sub-compact SUV arena with the MQB-A0-IN Kylaq. Powered by the proven 1.0L TSI 115 PS engine with 6 airbags as standard, 189 mm ground clearance, and 446 litres of boot capacity.",
    publishedAt: "October 26, 2026",
    readTime: "4 min read",
    author: "Ananya Deshmukh",
    image: "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80",
    tags: ["Skoda", "Kylaq", "Turbo Petrol", "MQB-A0-IN", "Sub4m"],
  },
  {
    id: "thar-roxx-bncap",
    slug: "mahindra-thar-roxx-5-star-bncap-crash-rating-delivery-timelines",
    category: "Video Deep Dives",
    title: "Mahindra Thar Roxx Scores 5-Star Bharat NCAP: Real-World Delivery Timelines & On-Road Cost",
    excerpt: "The 5-door Thar Roxx registers historic safety scores in adult and child occupant protection. We inspect real-world waiting periods spanning up to 14 months and calculate state-by-state road taxes on the 4x4 AX7L diesel.",
    publishedAt: "October 24, 2026",
    readTime: "6 min read",
    author: "Karan Singhal",
    image: "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80",
    tags: ["Mahindra", "Thar Roxx", "Bharat NCAP", "4x4", "Delivery Times"],
  },
  {
    id: "maruti-dzire-gncap",
    slug: "all-new-maruti-dzire-5-star-gncap-z-series-engine",
    category: "New Reveals",
    title: "All-New Maruti Dzire Bags 5-Star Global NCAP: What It Means for Indian Compact Sedans",
    excerpt: "In a landmark safety achievement, Maruti Suzuki's fourth-generation Dzire achieves 5 stars in Global NCAP with 6 airbags, electronic stability program, and a 25.71 km/l 3-cylinder Z-Series engine.",
    publishedAt: "October 22, 2026",
    readTime: "4 min read",
    author: "Rohan Varma",
    image: "https://images.unsplash.com/photo-1550355291-bbee04a92027?auto=format&fit=crop&w=800&q=80",
    tags: ["Maruti", "Dzire", "Global NCAP", "Sedan", "Z-Series"],
  },
  {
    id: "ev-tax-waiver-tracker",
    slug: "telangana-karnataka-ev-road-tax-waiver-policy-tracker",
    category: "Tax & Regulations",
    title: "State EV Road Tax Tracker: Telangana & Karnataka Roll Out 100% Life Tax Waivers",
    excerpt: "Comprehensive breakdown of statutory notifications granting zero road tax and registration fee exemptions on electric cars and two-wheelers, saving buyers between ₹1.2 Lakh and ₹4.5 Lakh on on-road purchase costs.",
    publishedAt: "October 20, 2026",
    readTime: "5 min read",
    author: "Pooja Hegde",
    image: "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=800&q=80",
    tags: ["EV Policy", "Road Tax", "Telangana", "Karnataka", "Subsidies"],
  },
  {
    id: "tata-curvv-ice-ev",
    slug: "tata-curvv-ice-vs-ev-real-world-cost-of-ownership",
    category: "Spy Radar",
    title: "Tata Curvv ICE vs Curvv EV: 5-Year Total Cost of Ownership Audit",
    excerpt: "Should you buy the 1.2L Hyperion Turbo-Petrol Curvv or the 55 kWh Long-Range EV? We calculate real-world fuel, battery charging, fast-charger tariff surges, and state RTO charges across Delhi, Mumbai, and Bengaluru.",
    publishedAt: "October 18, 2026",
    readTime: "7 min read",
    author: "Karan Singhal",
    image: "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=800&q=80",
    tags: ["Tata", "Curvv", "EV vs Petrol", "Ownership Cost", "Coupe SUV"],
  },
];

const CATEGORIES = [
  "All Updates",
  "New Reveals",
  "Video Deep Dives",
  "Spy Radar",
  "Tax & Regulations",
] as const;

export default function NewsHubPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("All Updates");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"overview" | "specs" | "comparison">("overview");

  const filteredArticles = ARTICLES.filter((article) => {
    const matchesCategory = selectedCategory === "All Updates" || article.category === selectedCategory;
    const matchesSearch = 
      article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const leadStory = ARTICLES[0]; // Hyundai Bayon

  return (
    <main className="min-h-screen bg-[#06080d] text-ink pb-24 pt-24 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* Newsroom Header */}
        <div className="border-b border-white/10 pb-8 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs font-mono font-semibold uppercase text-accent mb-3">
                <Flame className="h-3.5 w-3.5" />
                <span>OnRoad Automotive Journal &amp; Video Radar</span>
              </div>
              <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white font-[family-name:var(--font-display)]">
                The Automotive Intelligence Hub
              </h1>
              <p className="mt-2 text-sm sm:text-base text-mute max-w-2xl">
                Uncompromising editorial reports, interactive motion reels, new vehicle reveals, and live state RTO statutory tax alerts.
              </p>
            </div>

            {/* Search Bar */}
            <div className="relative w-full sm:w-72">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-mute" />
              <input
                type="text"
                placeholder="Search models, reveals, rules..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-full border border-white/10 bg-panel-soft/80 pl-9 pr-4 py-2 text-xs sm:text-sm text-ink placeholder-mute focus:border-accent focus:outline-none transition"
              />
            </div>
          </div>

          {/* Category Tabs */}
          <div className="mt-6 flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={cn(
                  "whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-medium transition shrink-0",
                  selectedCategory === cat
                    ? "bg-accent text-white shadow-xs font-semibold"
                    : "bg-panel-soft/60 border border-white/5 text-mute hover:text-white hover:bg-panel-soft"
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* HERO FEATURED STORY: THE NEW HYUNDAI BAYON */}
        <section className="mt-10 rounded-3xl border border-white/10 bg-gradient-to-b from-[#0c0f18] to-[#07090f] p-5 sm:p-8 shadow-2xl relative overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-accent animate-ping" />
              <span className="text-xs font-mono font-bold tracking-widest text-accent uppercase">
                Global Premier &bull; In-Depth Automotive Motion Feature
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-mute font-mono">
              <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" /> {leadStory.publishedAt}</span>
              <span>&bull;</span>
              <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> {leadStory.readTime}</span>
            </div>
          </div>

          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight font-[family-name:var(--font-display)]">
            {leadStory.title}
          </h2>
          <p className="mt-3 text-sm sm:text-base text-mute leading-relaxed max-w-4xl">
            {leadStory.excerpt}
          </p>

          {/* Interactive Custom Video / Motion Player (NO RAW YOUTUBE IFRAME!) */}
          <NewsVideoPlayer />

          {/* Story In-Depth Editorial Breakdown */}
          <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8 pt-8 border-t border-white/10">
            {/* Left 2 Cols: Journalistic Article */}
            <div className="lg:col-span-2 space-y-6 text-sm text-mute leading-relaxed">
              <div>
                <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2 font-[family-name:var(--font-display)]">
                  <span className="h-2 w-2 rounded-full bg-accent" />
                  Sharp European Crossover Design Meets N-Line Flair
                </h3>
                <p>
                  Built on the high-rigidity K2 platform that underpins the acclaimed i20 and international Kona, the refreshed Hyundai Bayon brings a futuristic aesthetic to the subcompact crossover segment. The most striking visual element is the seamless, full-width horizon LED daytime running light bar running across the front bonnet shut line, mirrored by segmented multi-projector LED headlamps housed within muscular bumper recesses.
                </p>
                <p className="mt-2">
                  At the rear, the Bayon features distinct arrow-shaped taillights connected by an ultra-thin LED light guide, accentuating vehicle stance. In its sporty N Line trim, the crossover gains bespoke 17-inch aerodynamic diamond-cut alloys, gloss black mirror caps, a dual-tip chrome exhaust finisher, and a bold rear diffuser skid plate.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2 font-[family-name:var(--font-display)]">
                  <span className="h-2 w-2 rounded-full bg-accent" />
                  1.0-Litre T-GDi Turbo Mild-Hybrid: Punchy Dynamics
                </h3>
                <p>
                  At the core of the Bayon is Hyundai’s refined 1.0-litre, 3-cylinder turbocharged gasoline direct injection (T-GDi) powerplant mated to an advanced 48-Volt mild-hybrid system. The internal combustion engine produces 120 PS at 6,000 rpm and a broad torque band of 172 Nm from 1,500 to 4,000 rpm. 
                </p>
                <p className="mt-2">
                  The 48V integrated starter-generator (MHSG) recuperates energy during deceleration and coasting, cutting fuel consumption in stop-and-go urban traffic while delivering instantaneous torque-fill under hard throttle openings. Buyers can choose between a crisp 6-speed intelligent manual transmission (iMT) with automatic electronic rev-matching or a rapid 7-speed dual-clutch transmission (DCT) with steering paddle shifters.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2 font-[family-name:var(--font-display)]">
                  <span className="h-2 w-2 rounded-full bg-accent" />
                  Cabin Architecture, SmartSense L2 ADAS &amp; Practicality
                </h3>
                <p>
                  Inside, the driver is greeted by dual 10.25-inch high-definition digital displays—one serving as a configurable digital cluster with selectable Drive Mode graphic themes (Eco, Normal, Sport), and the central touchscreen supporting wireless Apple CarPlay, Android Auto, and over-the-air (OTA) navigation maps.
                </p>
                <p className="mt-2">
                  Safety is headlined by standard 6 airbags and Hyundai SmartSense Level 2 ADAS: Forward Collision Avoidance Assist (FCA) with pedestrian and bicycle detection, Lane Keeping Assist (LKA), Blind-Spot Collision-Avoidance Assist (BCA), and Smart Cruise Control with stop-and-go radar support. Despite its tidy 4,180 mm overall footprint, the crossover delivers a cavernous 411-litre boot capacity with a double luggage floor.
                </p>
              </div>
            </div>

            {/* Right Col: Verified Spec Card & India Launch Matrix */}
            <div className="space-y-6">
              <div className="rounded-2xl border border-white/10 bg-panel-soft/60 p-5">
                <div className="flex items-center gap-2 pb-3 border-b border-white/10 mb-4">
                  <Award className="h-4 w-4 text-accent" />
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-white">
                    Hyundai Bayon Fast Facts
                  </span>
                </div>

                <div className="space-y-3 font-mono text-xs">
                  {leadStory.specs?.map((s, idx) => (
                    <div key={idx} className="flex items-start justify-between gap-2 py-1.5 border-b border-white/5">
                      <span className="text-mute">{s.label}</span>
                      <span className="text-white font-semibold text-right">{s.value}</span>
                    </div>
                  ))}
                </div>

                <div className="mt-5 pt-3 border-t border-white/10">
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="text-mute">Boot Capacity:</span>
                    <span className="text-emerald-400 font-bold">411 L (Class Leading)</span>
                  </div>
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="text-mute">Ground Clearance:</span>
                    <span className="text-white font-bold">183 mm</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-mute">ARAI Est. Mileage:</span>
                    <span className="text-emerald-400 font-bold">19.8 km/l</span>
                  </div>
                </div>

                <div className="mt-5">
                  <Link
                    href="/compare?add=hyundai/venue&add=skoda/kylaq"
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-xs font-semibold text-white shadow-xs hover:brightness-110 transition"
                  >
                    <span>Compare with Venue &amp; Kylaq</span>
                    <ChevronRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>

              {/* Subcompact Crossover Segment Radar */}
              <div className="rounded-2xl border border-white/10 bg-panel-soft/60 p-5">
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white mb-3">
                  How Bayon Slots In India
                </h4>
                <p className="text-xs text-mute leading-relaxed mb-3">
                  Hyundai currently fields the Venue in the upright sub-4m SUV segment and the Creta in the mid-size segment. The Bayon's crossover coupe stance directly targets the roaring success of the <strong>Maruti Suzuki Fronx</strong> and <strong>Skoda Kylaq</strong>, offering young urban buyers sporty dynamics over tall-boy utility.
                </p>
                <div className="rounded-lg bg-black/40 p-3 border border-white/5 text-[11px] font-mono text-white/80">
                  <p className="text-accent font-bold">Expected Showroom Price:</p>
                  <p className="mt-0.5">Base 1.0 MT: ~₹8.49 Lakh</p>
                  <p>Top N-Line 1.0 DCT: ~₹12.80 Lakh</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* FEED OF AUTOMOTIVE ARTICLES & RADAR STORIES */}
        <section className="mt-16">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-white font-[family-name:var(--font-display)]">
                Latest Automotive News &amp; Verified Reviews
              </h2>
              <p className="text-xs sm:text-sm text-mute mt-1">
                Real-time ex-showroom revisions, structural crash ratings, and state statutory policy updates.
              </p>
            </div>
            <span className="text-xs font-mono text-mute hidden sm:inline-block">
              Showing {filteredArticles.length} stories
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredArticles.slice(1).map((article) => (
              <article
                key={article.id}
                className="group flex flex-col justify-between rounded-2xl border border-white/10 bg-panel-soft/40 hover:bg-panel-soft/80 hover:border-white/20 transition-all duration-200 overflow-hidden shadow-sm"
              >
                <div>
                  {/* Article Image Container */}
                  <div className="relative aspect-[16/10] w-full overflow-hidden bg-black/60">
                    <div
                      className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105"
                      style={{ backgroundImage: `url(${article.image})` }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                    
                    {/* Category pill */}
                    <div className="absolute top-3 left-3">
                      <span className="rounded-full bg-black/70 px-2.5 py-1 text-[10px] font-mono font-medium text-accent border border-white/10 backdrop-blur-md">
                        {article.category}
                      </span>
                    </div>

                    <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-[11px] font-mono text-white/80">
                      <span>{article.author}</span>
                      <span>{article.readTime}</span>
                    </div>
                  </div>

                  {/* Body Content */}
                  <div className="p-5">
                    <div className="flex flex-wrap gap-1.5 mb-2.5">
                      {article.tags.map((t) => (
                        <span key={t} className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-mute border border-white/5">
                          #{t}
                        </span>
                      ))}
                    </div>

                    <h3 className="text-base font-bold text-white group-hover:text-accent transition-colors font-[family-name:var(--font-display)] line-clamp-2">
                      {article.title}
                    </h3>
                    <p className="mt-2 text-xs text-mute leading-relaxed line-clamp-3">
                      {article.excerpt}
                    </p>
                  </div>
                </div>

                {/* Footer Link */}
                <div className="px-5 pb-5 pt-2 border-t border-white/5 flex items-center justify-between text-xs">
                  <span className="text-mute font-mono">{article.publishedAt}</span>
                  <div className="flex items-center gap-1 font-semibold text-accent group-hover:translate-x-1 transition-transform">
                    <span>Full Journal</span>
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* AUTOMOTIVE ADVISORY & STATUTORY NEWSLETTER */}
        <section className="mt-16 rounded-2xl border border-white/10 bg-gradient-to-r from-panel-soft via-panel to-panel-soft p-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="max-w-xl text-center md:text-left">
              <h3 className="text-xl font-bold text-white font-[family-name:var(--font-display)]">
                Never Miss a New Car Reveal or Road Tax Cut
              </h3>
              <p className="mt-2 text-xs sm:text-sm text-mute leading-relaxed">
                Receive instant notifications when manufacturers revise ex-showroom price lists, reveal new generational facelifts, or when state governments issue EV road tax exemption gazettes. Zero spam.
              </p>
            </div>

            <div className="w-full md:w-auto flex flex-col sm:flex-row gap-2">
              <input
                type="email"
                placeholder="Enter your email address"
                className="rounded-full border border-white/10 bg-panel px-4 py-2.5 text-xs sm:text-sm text-ink placeholder-mute focus:border-accent focus:outline-none w-full sm:w-72"
              />
              <button
                type="button"
                className="whitespace-nowrap rounded-full bg-accent px-5 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs hover:brightness-110 active:scale-95 transition"
              >
                Subscribe Alerts
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
