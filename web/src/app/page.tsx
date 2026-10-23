"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { motion, useScroll, useTransform, type MotionValue } from "motion/react";
import { useRef } from "react";
import useSWR from "swr";
import { ArrowRight, BadgeIndianRupee, Building2, Calculator, Car, Clock, Compass, Crown, Flame, Gem, Handshake, Layers3, MapPin, Sparkles, Tag, Wallet } from "lucide-react";
import { fetcher, type Brand, type Breakdown, type Meta, type ModelSummary, type Offer } from "@/lib/api";
import { inr, lakh, range } from "@/lib/format";
import { BrandGrid, BodyRow } from "@/components/browse";
import { BreakdownView } from "@/components/breakdown";
import { CarImage } from "@/components/car-image";
import { useCity, withCity } from "@/components/city";
import { Card, SectionTitle, Skeleton, cn } from "@/components/ui";
import { AdBanner } from "@/components/ad-banner";
import { TopTenLeaderboard } from "@/components/top-ten-leaderboard";

const CarStage = dynamic(() => import("@/components/three/car-stage").then((m) => m.CarStage), { ssr: false,
  loading: () => <div className="h-full w-full bg-[#05060a]" /> });

const CHAPTERS = [
  { k: "01", title: <>The price on the brochure<br /><span className="text-gradient">isn&apos;t what you pay.</span></>,
    body: "Every car sold in India, every variant, with the manufacturer's own ex-showroom price for your city." },
  { k: "02", title: <>Road tax. RTO. Insurance.<br />Cess. TCS.</>,
    body: "We take the price apart, line by line, using your state's official transport rules, so you know the real on-road number before you walk in." },
  { k: "03", title: <>Spot the padding<br /><span className="text-gradient">in any quote.</span></>,
    body: "Handling charges, number-plate fees and ‘essential kits’ are not part of the legal price. We flag every one." },
  { k: "04", title: <>Then let dealers<br />compete for you.</>,
    body: "Ask once. Nearby showrooms send their best on-road price with offers and waiting time, ranked from lowest." },
];

function Chapter({ i, progress, children }: { i: number; progress: MotionValue<number>; children: React.ReactNode }) {
  const n = CHAPTERS.length;
  const start = i / n, end = (i + 1) / n;
  // the first chapter is visible before any scrolling; the last one stays up at the end
  const opacity = useTransform(progress, [start, start + 0.06, end - 0.06, end], [i === 0 ? 1 : 0, 1, 1, i === n - 1 ? 1 : 0]);
  const y = useTransform(progress, [start, start + 0.08], [i === 0 ? 0 : 40, 0]);
  return <motion.div style={{ opacity, y }} className="absolute inset-0 flex items-center">{children}</motion.div>;
}

function Story() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end end"] });
  return (
    <section ref={ref} data-invert className="relative h-[520vh] bg-[#05060a]">
      <div className="sticky top-0 h-screen overflow-hidden bg-[#05060a]">
        <CarStage progress={scrollYProgress} lookOffset={1.6} className="absolute inset-0" />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-[#05060a] via-[#05060a]/60 to-transparent" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#05060a] to-transparent" />
        <div className="relative mx-auto h-full max-w-7xl px-5">
          {CHAPTERS.map((c, i) => (
            <Chapter key={c.k} i={i} progress={scrollYProgress}>
              <div className="max-w-xl">
                <p className="mb-5 font-mono text-sm text-accent">{c.k} / 0{CHAPTERS.length}</p>
                <h1 className="font-[family-name:var(--font-display)] text-5xl font-bold leading-[1.02] tracking-tight text-white sm:text-7xl">{c.title}</h1>
                <p className="mt-6 max-w-md text-lg text-white/70">{c.body}</p>
                {i === 0 && (
                  <div className="pointer-events-auto mt-9 flex flex-wrap gap-3">
                    <Link href="/cars" className="inline-flex h-12 items-center gap-2 rounded-full bg-accent px-7 font-medium text-white shadow-[0_0_40px_-6px_rgba(255,77,46,0.8)]">
                      Find my car <ArrowRight className="h-4 w-4" />
                    </Link>
                    <Link href="/calculator" className="inline-flex h-12 items-center gap-2 rounded-full border border-white/20 px-7 text-white hover:bg-white/5">
                      <Calculator className="h-4 w-4" /> Check a quote
                    </Link>
                  </div>
                )}
              </div>
            </Chapter>
          ))}
        </div>
        <motion.div style={{ opacity: useTransform(scrollYProgress, [0, 0.05], [1, 0]) }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-xs uppercase tracking-[0.3em] text-white/50">Scroll</motion.div>
      </div>
    </section>
  );
}

const BAND_CONFIG = [
  { icon: Wallet, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/25 group-hover:bg-emerald-500/20" },
  { icon: Car, color: "text-sky-400", bg: "bg-sky-500/10 border-sky-500/25 group-hover:bg-sky-500/20" },
  { icon: Compass, color: "text-indigo-400", bg: "bg-indigo-500/10 border-indigo-500/25 group-hover:bg-indigo-500/20" },
  { icon: Flame, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/25 group-hover:bg-amber-500/20" },
  { icon: Sparkles, color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/25 group-hover:bg-purple-500/20" },
  { icon: Crown, color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/25 group-hover:bg-rose-500/20" },
];

export default function Home() {
  const { data: meta } = useSWR<Meta>("/meta", fetcher);
  const { data: bands } = useSWR<{ id: string; label: string; hint: string }[]>("/bands", fetcher);
  const { city } = useCity();
  const { data: popular } = useSWR<ModelSummary[]>(withCity("/explore?sort=popular", city), fetcher);
  const { data: brands } = useSWR<Brand[]>(withCity("/brands", city), fetcher);
  const { data: sample } = useSWR<Breakdown>(withCity("/onroad/quick?ex_showroom=1090700&fuel=Petrol&engine_cc=1497", city), fetcher);
  const { data: liveOffers } = useSWR<Offer[]>(withCity("/offers?limit=6", city), fetcher);

  return (
    <main>
      <Story />

      <section className="mx-auto max-w-7xl px-5 py-24">
        <div className="grid gap-4 sm:grid-cols-4">
          {[[meta?.counts.brands, "brands"], [meta?.counts.models, "models"], [meta?.counts.variants, "variants with live prices"],
            [meta?.states_with_rules.length, "states & UTs with on-road rules"]].map(([n, l]) => (
            <Card key={l as string} className="p-6">
              <p className="font-[family-name:var(--font-display)] text-4xl font-bold text-white">{n ?? "—"}</p>
              <p className="mt-1 text-sm text-mute">{l}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-24">
        <div className="flex items-end justify-between gap-4">
          <SectionTitle eyebrow="Brands" title="Browse by brand" sub="Every manufacturer selling in India, with its starting price." />
          <Link href="/brands" className="hidden shrink-0 text-sm text-accent hover:underline sm:block">All brands →</Link>
        </div>
        <div className="mt-8"><BrandGrid limit={12} /></div>
        <h3 className="mt-14 mb-5 font-[family-name:var(--font-display)] text-2xl font-bold text-white">Browse by body type</h3>
        <BodyRow />
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-24">
        <SectionTitle eyebrow="Your budget" title="Shop by what you can spend" sub="Grouped by starting ex-showroom price. Every band shows the real on-road cost too." />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(bands ?? []).map((b, i) => {
            const cfg = BAND_CONFIG[i] ?? BAND_CONFIG[0];
            const Icon = cfg.icon;
            return (
              <Link key={b.id} href={`/cars?band=${b.id}`} className="group relative overflow-hidden rounded-3xl border border-line bg-gradient-to-br from-panel to-panel-soft p-7 transition hover:border-accent/60 hover:-translate-y-1">
                <div className={cn("inline-flex h-12 w-12 items-center justify-center rounded-2xl border transition duration-300 group-hover:scale-110 shadow-lg", cfg.bg, cfg.color)}>
                  <Icon className="h-6 w-6" />
                </div>
                <p className="mt-6 font-[family-name:var(--font-display)] text-2xl font-bold text-white">{b.label}</p>
                <p className="text-mute">{b.hint}</p>
                <ArrowRight className="absolute right-6 top-7 h-5 w-5 text-mute transition group-hover:translate-x-1 group-hover:text-accent" />
              </Link>
            );
          })}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-16">
        <AdBanner />
      </section>

      {/* Grand Reveal: Top 10 Most-Bought Cars & Two-Wheelers in India */}
      <TopTenLeaderboard />

      {liveOffers && liveOffers.length > 0 && (
        <section className="mx-auto max-w-7xl px-5 pb-20">
          <SectionTitle
            eyebrow="Time-sensitive savings"
            title={<>Festive & Showroom Offers in {city}</>}
            sub={`Offers currently published on manufacturers' websites for ${city}, with their validity.`}
          />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {liveOffers.slice(0, 6).map((o) => (
              <Link
                key={o.id}
                href={o.model_id ? `/cars/${o.model_id}` : `/cars?brand=${o.brand_slug}`}
                className="group flex flex-col justify-between rounded-3xl border border-line bg-panel p-5 transition hover:-translate-y-1 hover:border-good/40 shadow-sm"
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="rounded-full bg-good/10 px-2.5 py-0.5 text-xs font-semibold text-good">
                      {o.kind && o.kind !== "other" ? `${o.kind[0].toUpperCase()}${o.kind.slice(1)} offer` : "Manufacturer offer"}
                    </span>
                    {o.days_left !== null && o.days_left !== undefined && (
                      <span className="flex items-center gap-1 text-[11px] text-mute">
                        <Clock className="h-3 w-3" /> {o.days_left > 0 ? `${o.days_left}d left` : "Ending soon"}
                      </span>
                    )}
                  </div>
                  <h4 className="mt-3 font-[family-name:var(--font-display)] text-lg font-bold text-ink group-hover:text-good transition">
                    {o.brand_name} {o.model_name ? o.model_name : ""}
                  </h4>
                  <p className="mt-0.5 text-sm font-semibold text-accent">{o.title}</p>
                  {o.amount_inr ? (
                    <p className="mt-2 font-mono text-2xl font-bold text-good">
                      Save {inr(o.amount_inr)}
                    </p>
                  ) : null}
                  <p className="mt-1.5 text-xs text-mute leading-relaxed line-clamp-2">
                    {o.details}
                  </p>
                </div>
                <div className="mt-4 flex items-center justify-between border-t border-line pt-3 text-xs text-mute">
                  <span>{o.source === "dealer" ? "Showroom offer" : "Manufacturer offer"}</span>
                  <span className="inline-flex items-center gap-1 text-ink font-medium group-hover:translate-x-1 transition">
                    View car <ArrowRight className="h-3 w-3 text-accent" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="border-y border-line bg-panel/40 py-24">
        <div className="mx-auto grid max-w-7xl gap-12 px-5 lg:grid-cols-2">
          <div>
            <SectionTitle
              eyebrow="Worked example"
              title={<>Hyundai Creta E petrol,<br />{city}</>}
              sub={<>Ex-showroom {lakh(1090700)} for {city} ({sample?.state_name ?? city}). Here&apos;s where the rest of the money goes, calculated using state transport department rules.</>}
            />
            <div className="space-y-4 text-sm text-mute">
              {sample?.lines.find((l) => l.label.toLowerCase().includes("road tax")) && (
                <p className="flex gap-3">
                  <Layers3 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                  <span>
                    Road tax is the biggest add-on: {sample.lines.find((l) => l.label.toLowerCase().includes("road tax"))?.basis ?? "State motor vehicle tax"} in {sample.state_name ?? city}.
                  </span>
                </p>
              )}
              <p className="flex gap-3">
                <BadgeIndianRupee className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                <span>TCS (1% on ex-showroom above ₹10 lakh under Sec 206C(1F)) comes back to you when you file your income-tax return.</span>
              </p>
              <p className="flex gap-3">
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                <span>Own-damage insurance is an upper estimate: get 2–3 insurer quotes and it usually drops by ₹8,000–₹15,000.</span>
              </p>
            </div>
          </div>
          <Card className="p-6 sm:p-8">{sample ? <BreakdownView b={sample} /> : <Skeleton className="h-96" />}</Card>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-24">
        <SectionTitle eyebrow="How it works" title="From browsing to the best price" />
        <div className="grid gap-4 md:grid-cols-4">
          {[[Building2, "Pick a car", "Every variant with its ex-showroom price for your city, straight from the manufacturer."],
            [Calculator, "See the true on-road price", "Itemised by your state's rules, with charges you can refuse called out."],
            [MapPin, "Find dealers near you", "Official showroom list for your city with phone, address and map."],
            [Handshake, "Get competing quotes", "Dealers reply with their best on-road price; we rank them against the fair price."]].map(([Icon, t, d], i) => {
              const I = Icon as typeof Building2;
              return (
                <Card key={i} className="p-6">
                  <I className="h-6 w-6 text-accent" />
                  <p className="mt-5 font-medium text-white">{t as string}</p>
                  <p className="mt-2 text-sm text-mute">{d as string}</p>
                </Card>
              );
            })}
        </div>
      </section>

      {brands && brands.length > 0 && (
        <section className="overflow-hidden border-t border-line py-14">
          <div className="marquee flex w-max gap-12">
            {[...brands, ...brands].map((b, i) => (
              <Link key={`${b.slug}-${i}`} href={`/brands/${b.slug}`} className="flex h-14 items-center gap-3 opacity-70 grayscale transition hover:opacity-100 hover:grayscale-0">
                {b.logo ? <img src={b.logo} alt={b.name} className="h-10 w-auto max-w-[120px] object-contain invert-[.85]" /> : <span className="text-lg text-white">{b.name}</span>}
              </Link>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
