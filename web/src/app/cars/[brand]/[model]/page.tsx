"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import useSWR from "swr";
import { toast } from "sonner";
import { 
  ExternalLink, 
  Fuel, 
  Gauge, 
  GitCompare, 
  Heart, 
  IndianRupee, 
  MapPin, 
  Phone, 
  Sparkles, 
  Tag, 
  CheckCircle2, 
  ChevronRight, 
  Layers,
  Landmark,
  Navigation,
  ShieldCheck,
  Star,
  Shield,
  Play,
  AlertTriangle,
  Clock,
  ShieldAlert
} from "lucide-react";
import { api, ApiError, fetcher, type Account, type Breakdown, type ModelDetail, type Variant } from "@/lib/api";
import { ago, inr, lakh, range } from "@/lib/format";
import { BreakdownView } from "@/components/breakdown";
import { Gallery } from "@/components/gallery";
import { useCity, useGeoQuery, withCity } from "@/components/city";
import { Button, Card, cn, Input, Label, Pill, Select, Skeleton } from "@/components/ui";
import { VariantSpecs } from "@/components/variant-specs";
import { ShowroomMap } from "@/components/dealer-map";
import { BankLoansComparison } from "@/components/bank-loans";

function QuoteForm({ variant, city }: { variant: Variant; city: string }) {
  const { data: me } = useSWR<Account>("/auth/me", fetcher, { shouldRetryOnError: false });
  const [pincode, setPin] = useState("");
  const [colour, setColour] = useState("");
  const [finance, setFinance] = useState(false);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  if (!me) return (
    <p className="text-sm text-mute">
      <Link href={`/login?next=${encodeURIComponent(location.pathname)}`} className="text-accent underline font-medium">Log in</Link> to ask nearby authorized dealers for their best on-road price.
    </p>
  );
  async function send() {
    setBusy(true);
    try {
      const r = await api<{ dealers_in_city: number; dealers_on_onroad: number }>("/quotes/request", { 
        method: "POST",
        body: JSON.stringify({ variant_id: variant.id, city, pincode, colour, finance, consent }) 
      });
      toast.success(`Request sent. ${r.dealers_on_onroad} of ${r.dealers_in_city} showrooms in ${city} answer on OnRoad; quotes appear in My garage.`);
    } catch (e) { 
      toast.error((e as Error).message); 
    } finally { 
      setBusy(false); 
    }
  }
  return (
    <div className="space-y-3.5">
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label>Pincode</Label>
          <Input value={pincode} onChange={(e) => setPin(e.target.value)} maxLength={6} placeholder="500081" />
        </div>
        <div>
          <Label hint="(optional)">Preferred Colour</Label>
          <Input value={colour} onChange={(e) => setColour(e.target.value)} placeholder="White / Black / Blue" />
        </div>
      </div>
      <label className="flex items-center gap-2 text-sm text-ink/80 cursor-pointer">
        <input type="checkbox" checked={finance} onChange={(e) => setFinance(e.target.checked)} className="accent-[#ff4d2e] rounded" /> 
        Include bank loan financing comparison
      </label>
      <label className="flex items-start gap-2 text-sm text-ink/80 cursor-pointer">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1 accent-[#ff4d2e] rounded" /> 
        Share this request (without disclosing my phone number) with authorized dealers in {city}.
      </label>
      <Button onClick={send} loading={busy} disabled={!consent} className="w-full sm:w-auto">
        Request Dealer Quotes
      </Button>
    </div>
  );
}

function ModelInner() {
  const { brand, model } = useParams<{ brand: string; model: string }>();
  const { city } = useCity();
  const [activeTab, setActiveTab] = useState<"pricing" | "loan" | "specs" | "safety" | "showrooms" | "offers">("pricing");
  const [fuel, setFuel] = useState("");
  const [trans, setTrans] = useState("");
  const [sel, setSel] = useState<string | null>(null);
  const geo = useGeoQuery();
  const { data: m } = useSWR<ModelDetail>(withCity(`/models/${brand}/${model}`, city) + geo, fetcher);
  const variants = useMemo(() => (m?.variants ?? []).filter((v) => (!fuel || v.fuel === fuel) && (!trans || v.transmission === trans)), [m, fuel, trans]);
  const chosen = variants.find((v) => v.id === sel) ?? variants.find((v) => v.ex_showroom_inr) ?? variants[0] ?? null;
  const { data: bd } = useSWR<Breakdown>(chosen ? withCity(`/onroad?variant_id=${encodeURIComponent(chosen.id)}`, city) : null, fetcher);

  async function watch(v: Variant) {
    try { 
      await api("/me/saved", { method: "POST", body: JSON.stringify({ variant_id: v.id, city }) }); 
      toast.success("Watching this price in My garage"); 
    } catch (e) { 
      toast.error(e instanceof ApiError && e.status === 401 ? "Log in to watch prices" : (e as Error).message); 
    }
  }

  if (!m) return <main className="mx-auto max-w-7xl px-5 pt-28"><Skeleton className="h-[60vh] rounded-3xl" /></main>;
  const prices = m.variants.map((v) => v.ex_showroom_inr).filter(Boolean) as number[];
  const fuels = [...new Set(m.variants.map((v) => v.fuel).filter(Boolean))] as string[];
  const transmissions = [...new Set(m.variants.map((v) => v.transmission).filter(Boolean))] as string[];
  const asOf = m.variants.find((v) => v.price_as_of)?.price_as_of;
  const vehicleType = m.vehicle_type ?? "car";

  return (
    <main className="pb-28">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 sm:pt-24 pb-8 sm:pb-12 border-b border-line bg-gradient-to-b from-transparent to-black/[0.03] dark:to-white/[0.02]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_60%_at_60%_40%,rgba(255,77,46,0.14),transparent_70%)]" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-6 px-4 sm:px-6 lg:grid-cols-[1fr_1.3fr]">
          <div>
            <Link 
              href={`/cars?brand=${m.brand_slug || brand}`} 
              className="inline-flex items-center gap-2.5 text-mute hover:text-ink transition group"
            >
              {m.logo && (
                <span className="grid h-8 w-12 place-items-center rounded-lg bg-white p-1 border border-line shadow-sm">
                  <img src={m.logo} alt="" className="max-h-6 w-auto object-contain" />
                </span>
              )}
              <span className="text-sm font-semibold">{m.brand_name}</span>
              <ChevronRight className="h-3.5 w-3.5 opacity-50 group-hover:opacity-100" />
            </Link>

            <h1 className="mt-2 font-[family-name:var(--font-display)] text-3xl sm:text-5xl lg:text-7xl font-bold tracking-tight text-ink">
              {m.name}
            </h1>

            <p className="mt-3 text-2xl sm:text-4xl font-black text-ink font-mono tracking-tight">
              {prices.length > 0 ? range(Math.min(...prices), Math.max(...prices)) : "Price on request"}
            </p>

            <p className="mt-1 text-xs sm:text-sm text-mute">
              Ex-showroom, {m.variants.find((v) => v.price_city)?.price_city ?? city} · {m.variants.length} variant{m.variants.length > 1 ? "s" : ""} · updated {ago(asOf)}
            </p>

            <div className="mt-5 flex flex-wrap gap-2">
              {m.body_type && <Pill>{m.body_type}</Pill>}
              {fuels.map((f) => (
                <Pill key={f}><Fuel className="h-3 w-3" />{f}</Pill>
              ))}
              {transmissions.map((t) => (
                <Pill key={t}><Gauge className="h-3 w-3" />{t}</Pill>
              ))}
            </div>

            {m.url && (
              <a 
                href={m.url} 
                target="_blank" 
                rel="noreferrer" 
                className="mt-4 inline-flex items-center gap-1.5 text-xs text-accent-2 hover:underline font-medium"
              >
                Official {m.brand_name} manufacturer page <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>

          <div className="relative">
            <Gallery shots={m.gallery ?? []} variantImage={chosen?.image_url} variantName={chosen?.name}
              alt={`${m.brand_name} ${m.name}`} bodyType={m.body_type} />
          </div>
        </div>
      </section>

      {/* Tab Navigation Bar */}
      <section className="sticky top-16 z-30 border-b border-line bg-panel/95 backdrop-blur-md shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center gap-2 overflow-x-auto px-4 sm:px-6 py-2.5 no-scrollbar">
          <button
            onClick={() => setActiveTab("pricing")}
            className={cn(
              "flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-xs sm:text-sm font-semibold transition cursor-pointer",
              activeTab === "pricing" 
                ? "bg-accent text-white shadow-md shadow-accent/25" 
                : "text-mute hover:bg-panel-soft hover:text-ink"
            )}
          >
            <IndianRupee className="h-3.5 w-3.5" />
            <span>On-road price</span>
          </button>

          <button
            onClick={() => setActiveTab("loan")}
            className={cn(
              "flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-xs sm:text-sm font-semibold transition cursor-pointer",
              activeTab === "loan" 
                ? "bg-accent text-white shadow-md shadow-accent/25" 
                : "text-mute hover:bg-panel-soft hover:text-ink"
            )}
          >
            <Landmark className="h-3.5 w-3.5" />
            <span>EMI calculator</span>
          </button>

          <button
            onClick={() => setActiveTab("specs")}
            className={cn(
              "flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-xs sm:text-sm font-semibold transition cursor-pointer",
              activeTab === "specs" 
                ? "bg-accent text-white shadow-md shadow-accent/25" 
                : "text-mute hover:bg-panel-soft hover:text-ink"
            )}
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Equipment & specs</span>
          </button>

          {vehicleType !== "bike" && (
          <button
            onClick={() => setActiveTab("safety")}
            className={cn(
              "flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-xs sm:text-sm font-semibold transition cursor-pointer",
              activeTab === "safety" 
                ? "bg-accent text-white shadow-md shadow-accent/25" 
                : "text-mute hover:bg-panel-soft hover:text-ink"
            )}
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Safety rating</span>
          </button>
          )}

          <button
            onClick={() => setActiveTab("showrooms")}
            className={cn(
              "flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-xs sm:text-sm font-semibold transition cursor-pointer",
              activeTab === "showrooms" 
                ? "bg-accent text-white shadow-md shadow-accent/25" 
                : "text-mute hover:bg-panel-soft hover:text-ink"
            )}
          >
            <Navigation className="h-3.5 w-3.5" />
            <span>Showrooms ({m.dealers.length})</span>
          </button>

          {m.offers.length > 0 && (
            <button
              onClick={() => setActiveTab("offers")}
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-xs sm:text-sm font-semibold transition cursor-pointer",
                activeTab === "offers" 
                  ? "bg-accent text-white shadow-md shadow-accent/25" 
                  : "text-mute hover:bg-panel-soft hover:text-ink"
              )}
            >
              <Tag className="h-3.5 w-3.5" />
              <span>Offers ({m.offers.length})</span>
            </button>
          )}
        </div>
      </section>

      {/* Main Tab Content */}
      <div className="mx-auto mt-6 max-w-7xl px-4 sm:px-6">
        {/* TAB 1: PRICING & EMI */}
        {activeTab === "pricing" && (
          <div className="grid gap-6 lg:grid-cols-[1.25fr_1fr]">
            {/* Left Column: All Variants Selection */}
            <div className="space-y-6">
              <Card className="p-4 sm:p-5">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <h2 className="font-[family-name:var(--font-display)] text-xl sm:text-2xl font-bold text-ink">
                    Select Variant ({variants.length})
                  </h2>
                  <div className="flex flex-wrap gap-2">
                    {fuels.length > 1 && (
                      <Select value={fuel} onChange={(e) => setFuel(e.target.value)} className="h-8 text-xs w-32">
                        <option value="">All fuels</option>
                        {fuels.map((f) => <option key={f}>{f}</option>)}
                      </Select>
                    )}
                    {transmissions.length > 1 && (
                      <Select value={trans} onChange={(e) => setTrans(e.target.value)} className="h-8 text-xs w-36">
                        <option value="">All gearboxes</option>
                        {transmissions.map((t) => <option key={t}>{t}</option>)}
                      </Select>
                    )}
                  </div>
                </div>

                {/* Desktop Table View */}
                <div data-lenis-prevent className="hidden sm:block no-scrollbar max-h-[600px] overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-panel text-left text-xs uppercase tracking-wide text-mute border-b border-line">
                      <tr>
                        <th className="py-2.5">Variant</th>
                        <th className="py-2.5">Ex-showroom</th>
                        <th className="py-2.5 text-right">On-road (est.)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {variants.map((v) => (
                        <tr 
                          key={v.id} 
                          onClick={() => setSel(v.id)} 
                          className={cn(
                            "cursor-pointer border-t border-line transition hover:bg-panel-soft", 
                            chosen?.id === v.id && "bg-accent/15 border-l-2 border-l-accent"
                          )}
                        >
                          <td className="py-3 pr-3">
                            <p className="font-medium text-ink">{v.name}</p>
                            <p className="text-xs text-mute">
                              {[v.fuel, v.transmission, v.engine_cc && `${v.engine_cc} cc`, v.battery_kwh && `${v.battery_kwh} kWh`, v.seats && `${v.seats} seats`].filter(Boolean).join(" · ")}
                            </p>
                          </td>
                          <td className="py-3 pr-3 font-mono text-ink">
                            {v.ex_showroom_inr ? lakh(v.ex_showroom_inr) : "—"}
                          </td>
                          <td className="py-3 text-right font-mono font-semibold text-ink">
                            {v.onroad ? lakh(v.onroad.total_inr - (v.onroad.refundable_inr ?? 0)) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Mobile Responsive Cards View */}
                <div data-lenis-prevent className="sm:hidden space-y-2.5 max-h-[500px] overflow-y-auto no-scrollbar">
                  {variants.map((v) => {
                    const isSelected = chosen?.id === v.id;
                    return (
                      <div
                        key={v.id}
                        onClick={() => setSel(v.id)}
                        className={cn(
                          "cursor-pointer rounded-xl border p-3 transition",
                          isSelected 
                            ? "border-accent bg-accent/10" 
                            : "border-line bg-panel hover:bg-panel-soft"
                        )}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="font-semibold text-ink text-sm">{v.name}</p>
                            <p className="text-[11px] text-mute mt-0.5">
                              {[v.fuel, v.transmission, v.engine_cc && `${v.engine_cc} cc`, v.battery_kwh && `${v.battery_kwh} kWh`].filter(Boolean).join(" · ")}
                            </p>
                          </div>
                          {isSelected && <CheckCircle2 className="h-4 w-4 text-accent shrink-0" />}
                        </div>
                        <div className="mt-2.5 flex items-center justify-between border-t border-line pt-2 text-xs">
                          <span className="text-mute font-mono">Ex: {v.ex_showroom_inr ? lakh(v.ex_showroom_inr) : "—"}</span>
                          <span className="font-mono font-bold text-ink">On-road: {v.onroad ? lakh(v.onroad.total_inr - (v.onroad.refundable_inr ?? 0)) : "—"}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <p className="mt-3 text-xs text-mute">
                  Official ex-showroom price for {chosen?.price_city ?? city}
                  {chosen?.price_city && chosen.price_city !== city && (
                    <> (manufacturer publishes no separate {city} list; on-road is calculated using {city}&apos;s statutory road tax rules)</>
                  )}
                  {chosen?.price_source && (
                    <> · <a href={chosen.price_source} target="_blank" rel="noreferrer" className="text-accent-2 hover:underline">source</a></>
                  )}.
                </p>
              </Card>

              {/* Fast Spec Preview Shortcut */}
              {chosen && (
                <div className="rounded-2xl border border-line bg-panel-soft p-4 flex items-center justify-between shadow-xs">
                  <div className="flex items-center gap-3">
                    <Sparkles className="h-5 w-5 text-accent" />
                    <div>
                      <p className="text-sm font-semibold text-ink">Want to see all equipment included in {chosen.name}?</p>
                      <p className="text-xs text-mute">Explore safety, infotainment, comfort features and technical homologation.</p>
                    </div>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => setActiveTab("specs")} className="shrink-0 text-xs">
                    View Equipment
                  </Button>
                </div>
              )}
            </div>

            {/* Right Column: Detailed On-Road Breakdown Card */}
            <Card className="h-fit p-5 sm:p-6 lg:sticky lg:top-32" id="quote-section">
              {chosen ? (
                <>
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-line">
                    <div>
                      <span className="text-xs text-mute uppercase tracking-wider font-semibold">Selected Variant</span>
                      <p className="font-semibold text-ink text-base">{chosen.name}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => watch(chosen)} className="h-8 text-xs">
                        <Heart className="h-3.5 w-3.5" /> Watch
                      </Button>
                      <Link href={`/compare?ids=${encodeURIComponent(chosen.id)}`}>
                        <Button size="sm" variant="ghost" className="h-8 text-xs">
                          <GitCompare className="h-3.5 w-3.5" /> Compare
                        </Button>
                      </Link>
                    </div>
                  </div>

                  {bd ? <BreakdownView b={bd} /> : <Skeleton className="h-72 rounded-2xl" />}

                  {bd && (
                    <div className="mt-4 rounded-2xl border border-accent/25 bg-accent/5 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <Landmark className="h-4 w-4 text-accent" />
                          <span className="text-xs font-semibold text-accent uppercase tracking-wider">Bank Financing Available</span>
                        </div>
                        <p className="text-sm font-bold text-ink mt-0.5">Work out your EMI</p>
                        <p className="text-[11px] text-mute">Enter the rate your bank quotes you; we show EMI and total interest</p>
                      </div>
                      <Button 
                        size="sm" 
                        onClick={() => setActiveTab("loan")} 
                        className="shrink-0 text-xs gap-1.5"
                      >
                        <span>EMI calculator</span>
                        <ChevronRight className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  )}

                  <div className="mt-6 border-t border-line pt-5">
                    <p className="mb-2 font-semibold text-ink text-base">Request Best On-Road Quote</p>
                    <Link href="/buying-guide" className="mb-3 inline-block text-xs text-accent hover:underline">Buying & registration steps →</Link>
                    <p className="text-xs text-mute mb-3">Compare real dealer offers without spam calls.</p>
                    <QuoteForm variant={chosen} city={city} />
                  </div>
                </>
              ) : (
                <p className="text-mute">Select a variant to view on-road breakdown.</p>
              )}
            </Card>
          </div>
        )}

        {/* TAB 2: BANK LOANS & EMI */}
        {activeTab === "loan" && (
          <div className="space-y-6">
            {chosen && bd ? (
              <div className="space-y-6">
                {/* Variant Quick Switcher Banner */}
                <div className="rounded-2xl border border-line bg-panel p-4 flex flex-wrap items-center justify-between gap-3 shadow-sm">
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wider text-mute">Financing Calculation for</span>
                    <h3 className="text-lg font-bold text-ink">{m.name} — {chosen.name}</h3>
                    <p className="text-xs text-mute font-mono mt-0.5">
                      On-Road Price in {city}: <strong className="text-ink font-semibold">{lakh(bd.total_inr - (bd.refundable_inr ?? 0))}</strong>
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => setActiveTab("pricing")} className="text-xs">
                      Change Variant
                    </Button>
                    <Button size="sm" onClick={() => setActiveTab("pricing")} className="text-xs">
                      View On-Road Breakdown
                    </Button>
                  </div>
                </div>

                {/* Full-width Bank Loans Comparison Component */}
                <BankLoansComparison
                  vehicleType={vehicleType}
                  onRoadPriceInr={bd.total_inr}
                  variantName={chosen.name}
                  isEV={chosen.fuel?.toLowerCase().includes("electric") || Boolean(chosen.battery_kwh)}
                />
              </div>
            ) : (
              <Card className="p-8 text-center border border-line bg-panel">
                <p className="text-mute">Please select a variant to calculate bank car loan EMI.</p>
              </Card>
            )}
          </div>
        )}

        {/* TAB 3: EQUIPMENT & SPECS */}
        {activeTab === "specs" && (
          <div className="space-y-6">
            {chosen ? (
              <VariantSpecs
                variant={chosen}
                modelName={m.name}
                brandName={m.brand_name}
                bodyType={m.body_type}
                vehicleType={vehicleType}
              />
            ) : (
              <Card className="p-8 text-center">
                <p className="text-mute">Please select a variant to view its equipment and technical specs.</p>
              </Card>
            )}
          </div>
        )}

        {/* Official crash-test results (Bharat NCAP / Global NCAP), each linked to its source */}
        {activeTab === "safety" && vehicleType !== "bike" && (
          <div className="space-y-5">
            {m.crash_tests && m.crash_tests.length > 0 ? m.crash_tests.map((t) => (
              <Card key={t.source_url + t.protocol} className="p-5 sm:p-7">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-good"><ShieldCheck className="h-4 w-4" />{t.agency}</p>
                    <p className="mt-1 text-sm text-mute">{t.protocol}{(t.rating_published ?? t.test_date) ? ` · published ${t.rating_published ?? t.test_date}` : ""}{t.variant_tested ? ` · variant: ${t.variant_tested}` : ""}</p>
                  </div>
                  <a href={t.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-sm text-accent-2 hover:underline">Official result <ExternalLink className="h-3.5 w-3.5" /></a>
                </div>
                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  {([["Adult occupant", t.adult_stars, t.adult_score, t.adult_max], ["Child occupant", t.child_stars, t.child_score, t.child_max]] as const).map(([label, stars, score, max]) => (
                    <div key={label} className="rounded-2xl border border-line bg-panel-soft p-4">
                      <p className="text-sm text-mute">{label}</p>
                      <div className="mt-1 flex items-center gap-1">
                        {stars != null && [0, 1, 2, 3, 4].map((i) => <Star key={i} className={cn("h-5 w-5", i < stars ? "fill-amber-400 text-amber-400" : "text-mute/40")} />)}
                        <span className="ml-2 text-xl font-bold text-ink">{stars != null ? `${stars}★` : "—"}</span>
                      </div>
                      {score != null && max != null && <p className="mt-1 font-mono text-sm text-ink">{score} / {max} points</p>}
                    </div>
                  ))}
                </div>
                {t.video_url && /youtube\.com\/embed\/|youtube-nocookie\.com\/embed\//.test(t.video_url) && (
                  <div className="mt-5 aspect-video overflow-hidden rounded-2xl border border-line bg-black">
                    <iframe src={t.video_url} title={`${t.agency} crash test: ${m.name}`} className="h-full w-full" loading="lazy"
                      allow="accelerometer; encrypted-media; gyroscope; picture-in-picture" allowFullScreen />
                  </div>
                )}
                {(t.airbags_tested || t.notes) && <p className="mt-4 text-sm text-mute">{[t.airbags_tested && `Airbags in the tested car: ${t.airbags_tested}`, t.notes].filter(Boolean).join(" · ")}</p>}
              </Card>
            )) : (
              <Card className="p-6">
                <div className="flex items-start gap-3">
                  <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" />
                  <div>
                    <p className="font-semibold text-ink">No official crash-test result on record for the {m.name}</p>
                    <p className="mt-1 text-sm text-mute">We only show ratings published by Bharat NCAP or Global NCAP, with a link to the official result. No rating here doesn&apos;t mean the car is unsafe; there&apos;s just no independent result to quote.</p>
                    <div className="mt-3 flex flex-wrap gap-3 text-sm">
                      <a href="https://www.bncap.in" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent-2 hover:underline">Bharat NCAP <ExternalLink className="h-3 w-3" /></a>
                      <a href="https://www.globalncap.org" target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-accent-2 hover:underline">Global NCAP <ExternalLink className="h-3 w-3" /></a>
                    </div>
                  </div>
                </div>
              </Card>
            )}
          </div>
        )}

        {/* Showrooms from the manufacturer's own dealer locator */}
        {activeTab === "showrooms" && (
          <div className="space-y-5">
            {m.dealers.length > 0 ? <ShowroomMap dealers={m.dealers} brandName={m.brand_name} city={city} /> : (
              <Card className="p-6 text-center">
                <p className="font-semibold text-ink">No {m.brand_name} showroom listed for {city}</p>
                <p className="mt-1 text-sm text-mute">Showrooms come from {m.brand_name}&apos;s own dealer locator. Try another city from the picker at the top.</p>
              </Card>
            )}
          </div>
        )}

        {/* TAB 6: OFFERS & DISCOUNTS */}
        {activeTab === "offers" && (
          <div className="space-y-4">
            <Card className="p-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-line pb-4 mb-5">
                <div>
                  <span className="text-xs uppercase tracking-wider text-good font-bold flex items-center gap-1.5">
                    <Tag className="h-3.5 w-3.5" /> Time-Sensitive Consumer Campaigns
                  </span>
                  <h2 className="font-[family-name:var(--font-display)] text-2xl font-bold text-ink mt-0.5">
                    Active Consumer Offers for {m.name} in {city}
                  </h2>
                  <p className="text-xs text-mute mt-1">
                    Offers published on the manufacturer's website, with their validity and terms.
                  </p>
                </div>

                {/* Dynamic Offer Counter Badge */}
                <span className="rounded-full bg-good/15 border border-good/30 px-3 py-1 text-xs font-bold text-good self-start sm:self-auto shrink-0">
                  {m.offers.length} Active in {city}
                </span>
              </div>

              {m.offers.length === 0 ? (
                <p className="text-mute">No direct discount campaigns currently active in {city}. Dealers may still offer exchange or corporate discounts upon showroom visit.</p>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {m.offers.map((o) => (
                    <div key={o.id} className="rounded-2xl border border-good/25 bg-good/5 p-5 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="rounded-full bg-good/20 px-2 py-0.5 text-[10px] font-bold text-good uppercase tracking-wider">
                            {o.source === "dealer" ? "Dealer Concession" : `Official ${m.brand_name}`}
                          </span>
                          {o.valid_until && (
                            <span className="rounded-full bg-panel px-2 py-0.5 text-[10px] font-mono text-mute border border-line flex items-center gap-1">
                              <Clock className="h-3 w-3 text-amber-500" />
                              Valid until {o.valid_until}
                            </span>
                          )}
                        </div>

                        <p className="flex items-center gap-2 font-semibold text-ink text-base">
                          <Tag className="h-4 w-4 text-good shrink-0" />
                          {o.title}
                        </p>

                        {o.amount_inr ? (
                          <p className="mt-2 font-mono text-3xl font-extrabold text-good">
                            {inr(o.amount_inr)}
                          </p>
                        ) : null}

                        <p className="mt-2 text-xs text-mute leading-relaxed">{o.details}</p>
                      </div>

                      <div className="mt-4 pt-3 border-t border-line/60 flex items-center justify-between">
                        <span className="text-[11px] text-mute">
                          Valid in {city}
                        </span>
                        <Button
                          size="sm"
                          onClick={() => {
                            setActiveTab("pricing");
                            setTimeout(() => {
                              document.getElementById("quote-section")?.scrollIntoView({ behavior: "smooth" });
                            }, 100);
                          }}
                          className="h-7 px-3 text-xs"
                        >
                          Claim Offer
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}
      </div>

      {/* Mobile Sticky Bottom Floating Action Bar */}
      {chosen && (
        <div className="fixed bottom-14 inset-x-0 z-40 border-t border-line bg-panel/95 backdrop-blur-xl px-4 py-2.5 md:hidden shadow-2xl flex items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="truncate text-[11px] text-mute">{chosen.name}</p>
            <p className="text-sm font-bold text-ink font-mono leading-tight">
              {chosen.onroad ? lakh(chosen.onroad.total_inr - (chosen.onroad.refundable_inr ?? 0)) : "—"}
              <span className="text-[10px] font-normal text-mute ml-1">on-road {city}</span>
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button 
              size="sm" 
              onClick={() => {
                setActiveTab("pricing");
                setTimeout(() => {
                  document.getElementById("quote-section")?.scrollIntoView({ behavior: "smooth" });
                }, 100);
              }}
              className="h-8 px-3 text-xs"
            >
              Get Best Price
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => setActiveTab("showrooms")}
              className="h-8 px-2.5 text-xs"
              title="View Showrooms"
            >
              <MapPin className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}
    </main>
  );
}

export default function ModelPage() {
  return (
    <Suspense fallback={<main className="mx-auto max-w-7xl px-5 pt-28"><Skeleton className="h-[60vh] rounded-3xl" /></main>}>
      <ModelInner />
    </Suspense>
  );
}
