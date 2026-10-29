"use client";

// After the price: insurance, registration (RTA), accessories and recent changes for the chosen variant and city.
// Everything comes from /api/ownership: amounts from the verified rules file, links to insurers, regulators and the
// maker's own accessory store. OnRoad has no tie-up with any insurer; nothing here is gated behind a sign-up.

import { useState } from "react";
import useSWR from "swr";
import { Ban, ExternalLink, FileCheck, History, Package, ShieldCheck } from "lucide-react";
import { fetcher } from "@/lib/api";
import { inr } from "@/lib/format";
import { Card, cn, Skeleton } from "@/components/ui";
import type { Variant } from "@/lib/api";

type Line = { label: string; amount_inr: number | null; basis: string; verified?: boolean };
type LinkT = { name?: string; title?: string; url: string };
type Insurer = { name: string; url: string; logo_url: string | null; logo_dark?: boolean; garages: string | null; stated_on: string | null };
type Rule = { item: string; status: string };
type Update = { kind: "price" | "new" | "offer"; date: string; title: string; detail: string; source_url?: string | null };
type Ownership = {
  insurance: { lines: Line[]; tips: string[]; insurers: Insurer[]; compare: LinkT[]; regulator: LinkT; disclosure: string };
  rta: {
    state: string; coverage: string; road_tax_basis?: string | null; fuel_differential?: string | null;
    second_vehicle_rule?: string | null; ev?: { life_tax_exempt?: boolean; order?: string; valid_to?: string; conditions?: string } | null;
    charges: Line[]; steps: string[]; not_allowed: Rule[]; optional: Rule[]; sources: { title: string; url: string }[];
    links: LinkT[]; as_of?: string;
  };
  accessories: { items: { code: string; name: string; category: string | null; price_inr: number | null; image_url: string | null; description: string | null }[];
    official: { url: string; checked: string } | null; advice: string[] };
  updates: Update[];
};

const TABS = [
  { id: "insurance", label: "Insurance", icon: ShieldCheck },
  { id: "rta", label: "Registration (RTA)", icon: FileCheck },
  { id: "accessories", label: "Accessories", icon: Package },
  { id: "updates", label: "Updates", icon: History },
] as const;

function Out({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer"
       className="inline-flex items-center gap-1.5 rounded-xl border border-line bg-panel px-3 py-2 text-sm font-medium text-ink hover:border-accent/50">
      {children}<ExternalLink className="h-3.5 w-3.5 text-mute" />
    </a>
  );
}

function Amounts({ lines }: { lines: Line[] }) {
  return (
    <div className="divide-y divide-line rounded-2xl border border-line">
      {lines.map((l) => (
        <div key={l.label} className="flex items-start justify-between gap-4 p-4">
          <div>
            <p className="font-medium text-ink">{l.label}</p>
            <p className="mt-0.5 text-xs text-mute">{l.basis}</p>
          </div>
          <p className="shrink-0 font-mono font-semibold text-ink">{l.amount_inr != null ? inr(l.amount_inr) : "—"}</p>
        </div>
      ))}
    </div>
  );
}

export function OwnershipSupportHub({ modelName, brandName, city, variant }: {
  modelName: string; brandName: string; city: string; stateCode?: string; variant?: Variant; exShowroomPrice?: number;
}) {
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("insurance");
  const { data: o, error } = useSWR<Ownership>(variant ? `/ownership?variant_id=${encodeURIComponent(variant.id)}&city=${encodeURIComponent(city)}` : null, fetcher);

  return (
    <div className="space-y-5">
      <div className="flex gap-2 overflow-x-auto pb-1">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
                  className={cn("inline-flex shrink-0 items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium",
                    tab === t.id ? "border-accent bg-accent/10 text-accent" : "border-line text-mute hover:text-ink")}>
            <t.icon className="h-4 w-4" />{t.label}
          </button>
        ))}
      </div>

      {!variant && <Card className="p-6 text-mute">Choose a variant to see insurance and registration details.</Card>}
      {error && <Card className="p-6 text-mute">Couldn&apos;t load this right now. Please try again in a moment.</Card>}
      {variant && !o && !error && <Skeleton className="h-64 w-full" />}

      {o && tab === "insurance" && (
        <div className="grid gap-5 lg:grid-cols-[1.2fr_1fr]">
          <Card className="space-y-4 p-6">
            <p className="font-semibold text-ink">Insurance for {brandName} {modelName} {variant?.name} in {city}</p>
            <Amounts lines={o.insurance.lines} />
            <ul className="space-y-2 text-sm text-mute">
              {o.insurance.tips.map((t) => <li key={t} className="flex gap-2"><span className="text-accent">•</span>{t}</li>)}
            </ul>
          </Card>
          <Card className="space-y-4 p-6">
            <p className="font-semibold text-ink">Get your own quotes</p>
            <p className="text-sm text-mute">Enter the same insured value and add-ons on each site, then compare with the dealer&apos;s quote.</p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {o.insurance.insurers.map((x) => (
                <a key={x.url} href={x.url} target="_blank" rel="noopener noreferrer"
                   className="group rounded-2xl border border-line bg-panel p-3 transition hover:border-mute">
                  <div className={cn("grid h-12 place-items-center rounded-xl px-3", x.logo_dark ? "bg-[#1b1f2a]" : "bg-white")}>
                    {x.logo_url
                      ? /* eslint-disable-next-line @next/next/no-img-element */ <img src={x.logo_url} alt={x.name} className="max-h-8 w-auto object-contain" />
                      : <span className="font-semibold text-[#1b1f2a]">{x.name}</span>}
                  </div>
                  <p className="mt-2 text-sm font-semibold text-ink group-hover:underline">{x.name}</p>
                  <p className="text-xs text-mute">{x.garages ? `${x.garages} cashless garages*` : "Get a quote"}</p>
                </a>
              ))}
            </div>
            <p className="pt-2 text-sm font-medium text-ink">Compare many insurers at once</p>
            <div className="flex flex-wrap gap-2">{o.insurance.compare.map((x) => <Out key={x.url} href={x.url}>{x.name}</Out>)}</div>
            <p className="text-xs text-mute">* As stated on each insurer&apos;s website. {o.insurance.disclosure} Check an insurer&apos;s registration with the{" "}
              <a className="underline" href={o.insurance.regulator.url} target="_blank" rel="noopener noreferrer">IRDAI</a>.</p>
          </Card>
        </div>
      )}

      {o && tab === "rta" && (
        <div className="grid gap-5 lg:grid-cols-2">
          <Card className="space-y-4 p-6">
            <p className="font-semibold text-ink">Registration charges in {o.rta.state}</p>
            <Amounts lines={o.rta.charges} />
            {o.rta.ev?.life_tax_exempt && (
              <p className="rounded-xl bg-good/10 p-3 text-sm text-good">
                Electric vehicles are exempt from road tax in {o.rta.state}{o.rta.ev.valid_to ? ` until ${o.rta.ev.valid_to}` : ""} ({o.rta.ev.order}).
              </p>
            )}
            {o.rta.road_tax_basis && <p className="text-xs text-mute">{o.rta.road_tax_basis}</p>}
            {o.rta.second_vehicle_rule && <p className="text-xs text-mute"><b className="text-ink">Second vehicle:</b> {o.rta.second_vehicle_rule}</p>}
            <div className="flex flex-wrap gap-2">
              {[...o.rta.links, ...o.rta.sources].map((s) => <Out key={s.url} href={s.url}>{s.title}</Out>)}
            </div>
            {o.rta.as_of && <p className="text-xs text-mute">Rules checked {o.rta.as_of}.</p>}
          </Card>
          <div className="space-y-5">
            <Card className="space-y-3 p-6">
              <p className="font-semibold text-ink">How registration works</p>
              <ol className="list-decimal space-y-2 pl-5 text-sm text-mute">{o.rta.steps.map((s) => <li key={s}>{s}</li>)}</ol>
            </Card>
            <Card className="space-y-3 p-6">
              <p className="flex items-center gap-2 font-semibold text-ink"><Ban className="h-4 w-4 text-accent" />Charges a dealer cannot add</p>
              <ul className="space-y-2 text-sm">
                {o.rta.not_allowed.map((r) => <li key={r.item}><b className="text-ink">{r.item}.</b> <span className="text-mute">{r.status}</span></li>)}
              </ul>
              {o.rta.optional.length > 0 && (
                <p className="text-sm text-mute"><b className="text-ink">Optional, your choice:</b> {o.rta.optional.map((r) => r.item).join("; ")}.</p>
              )}
            </Card>
          </div>
        </div>
      )}

      {o && tab === "accessories" && (
        <Card className="space-y-4 p-6">
          <p className="font-semibold text-ink">Genuine {brandName} accessories</p>
          {o.accessories.items.length > 0 && (
            <>
              <p className="text-sm text-mute">{o.accessories.items.length} items at {brandName}&apos;s list prices. Fitting charges may apply at the dealer.</p>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                {o.accessories.items.map((a) => (
                  <div key={a.code} className="overflow-hidden rounded-2xl border border-line bg-panel">
                    <div className="aspect-[4/3] bg-white">
                      {a.image_url && /* eslint-disable-next-line @next/next/no-img-element */
                        <img src={a.image_url} alt={a.name} loading="lazy" className="h-full w-full object-cover" />}
                    </div>
                    <div className="space-y-0.5 p-3">
                      {a.category && <p className="text-[11px] uppercase tracking-wide text-mute">{a.category}</p>}
                      <p className="line-clamp-2 text-sm font-medium text-ink">{a.name}</p>
                      {a.price_inr != null && <p className="font-mono text-sm font-semibold text-ink">{inr(a.price_inr)}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
          {o.accessories.official
            ? <Out href={o.accessories.official.url}>{brandName} accessories store</Out>
            : <p className="text-sm text-mute">{brandName} doesn&apos;t publish an accessory catalogue online. Ask the dealer for the itemised genuine accessories price list.</p>}
          <ul className="space-y-2 text-sm text-mute">
            {o.accessories.advice.map((t) => <li key={t} className="flex gap-2"><span className="text-accent">•</span>{t}</li>)}
          </ul>
        </Card>
      )}

      {o && tab === "updates" && (
        <Card className="p-6">
          <p className="mb-4 font-semibold text-ink">What changed for the {brandName} {modelName}</p>
          {o.updates.length === 0 && <p className="text-sm text-mute">No price revisions or new offers in the last four months.</p>}
          <ul className="divide-y divide-line">
            {o.updates.map((u) => (
              <li key={u.kind + u.date + u.title} className="flex items-start justify-between gap-4 py-3">
                <div>
                  <p className="font-medium text-ink">{u.title}</p>
                  <p className="text-sm text-mute">{u.detail}</p>
                </div>
                <div className="shrink-0 text-right text-xs text-mute">
                  <p>{u.date}</p>
                  {u.source_url && <a className="underline" href={u.source_url} target="_blank" rel="noopener noreferrer">source</a>}
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
