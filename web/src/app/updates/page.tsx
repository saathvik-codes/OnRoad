"use client";

// Everything new in the Indian car and bike market, in two parts:
//   * News: headlines from Indian publishers' RSS feeds (/api/news), each linking to the full story;
//   * Prices & launches: what changed in OnRoad's own records (/api/updates): price revisions read from makers'
//     price lists, models that newly appear on makers' sites, and manufacturer offers that started recently.

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";

import { fetcher } from "@/lib/api";
import { lakh } from "@/lib/format";
import { Card, cn, Empty, SectionTitle, Skeleton } from "@/components/ui";
import { ago, NewsShowcase, TOPIC, type News } from "@/components/news-showcase";

type Update = { kind: "price" | "new" | "offer"; date: string; model_id: string | null; title: string; detail: string;
  source_url?: string | null; image_url?: string | null; brand?: string; model?: string; variants_changed?: number;
  example_variant?: string; old_inr?: number; new_inr?: number };

const TOPICS = ["all", "launch", "price", "ev", "safety", "policy", "spied", "sales"] as const;

function NewsList() {
  const [topic, setTopic] = useState<(typeof TOPICS)[number]>("all");
  const { data, error } = useSWR<News[]>(`/news?limit=100${topic === "all" ? "" : `&topic=${topic}`}`, fetcher);
  return (
    <div className="space-y-5">
      <div className="flex gap-2 overflow-x-auto pb-1">
        {TOPICS.map((t) => (
          <button key={t} onClick={() => setTopic(t)}
                  className={cn("shrink-0 rounded-xl px-3 py-2 text-sm", topic === t ? "bg-panel-soft font-medium text-ink" : "text-mute hover:text-ink")}>
            {t === "all" ? "All news" : TOPIC[t]}
          </button>
        ))}
      </div>
      {error && <Empty title="Couldn't load the news">Please try again in a moment.</Empty>}
      {!data && !error && <div className="grid gap-4 sm:grid-cols-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-64 w-full" />)}</div>}
      {data && data.length === 0 && <Empty title="No stories here yet">New stories appear here within the hour.</Empty>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {(data ?? []).map((n) => (
          <Card key={n.id} className="flex flex-col overflow-hidden p-0">
            <a href={n.url} target="_blank" rel="noopener noreferrer" className="group block">
              {n.image_url
                // eslint-disable-next-line @next/next/no-img-element
                ? <img src={n.image_url} alt="" loading="lazy" className="aspect-[16/9] w-full object-cover transition group-hover:opacity-90"
                       onError={(e) => { e.currentTarget.style.display = "none"; }} />
                : <div className="aspect-[16/9] w-full bg-panel-soft" />}
              <div className="space-y-2 p-4">
                <p className="text-xs text-mute"><span className="font-semibold text-accent">{TOPIC[n.topic] ?? "News"}</span> · {n.source} · {ago(n.published)}</p>
                <p className="font-semibold leading-snug text-ink group-hover:underline">{n.title}</p>
                {n.summary && <p className="line-clamp-2 text-sm text-mute">{n.summary}</p>}
              </div>
            </a>
            {n.model_id && (
              <Link href={`/cars/${n.model_id}`} className="mt-auto border-t border-line px-4 py-3 text-sm font-medium text-ink hover:text-accent">
                {n.model_name}: see on-road price →
              </Link>
            )}
          </Card>
        ))}
      </div>
      <p className="text-xs text-mute">Headlines and images belong to their publishers and link to the full story.</p>
    </div>
  );
}

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function PriceUpdates() {
  const [type, setType] = useState<"car" | "bike">("car");
  const { data, error } = useSWR<Update[]>(`/updates?vehicle_type=${type}&limit=100`, fetcher);
  const launches = (data ?? []).filter((u) => u.kind === "new");
  const prices = (data ?? []).filter((u) => u.kind === "price");
  const offers = (data ?? []).filter((u) => u.kind === "offer");
  return (
    <div className="space-y-10">
      <div className="inline-flex rounded-full border border-line p-0.5">
        {(["car", "bike"] as const).map((t) => (
          <button key={t} onClick={() => setType(t)}
                  className={cn("rounded-full px-4 py-1.5 text-sm font-medium", type === t ? "bg-ink text-bg" : "text-mute hover:text-ink")}>
            {t === "car" ? "Cars" : "Bikes and scooters"}
          </button>
        ))}
      </div>
      {error && <Empty title="Couldn't load updates">Please try again in a moment.</Empty>}
      {!data && !error && <div className="grid gap-4 sm:grid-cols-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-56 w-full" />)}</div>}

      {data && (
        <section className="space-y-4">
          <div className="flex items-baseline justify-between">
            <h2 className="font-display text-xl font-bold text-ink">New on the market</h2>
            <p className="text-sm text-mute">Newly listed by the manufacturer</p>
          </div>
          {launches.length === 0 ? <p className="text-sm text-mute">No new models in the last four months.</p> : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {launches.map((u) => (
                <Link key={u.model_id ?? u.title} href={u.model_id ? `/cars/${u.model_id}` : "#"}
                      className="group overflow-hidden rounded-2xl border border-line bg-panel transition hover:border-mute">
                  <div className="aspect-[4/3] bg-panel-soft">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={u.image_url || `/api/logos/${(u.model_id ?? "").split("/")[0]}`} alt="" loading="lazy"
                         className={cn("h-full w-full object-contain transition group-hover:scale-[1.03]", u.image_url ? "p-3" : "p-12 opacity-80")} />
                  </div>
                  <div className="space-y-0.5 p-4">
                    <p className="text-xs text-mute">{u.brand} · {fmtDate(u.date)}</p>
                    <p className="font-semibold text-ink">{u.model}</p>
                    <p className="text-xs text-mute">{u.detail.replace("Newly listed on the maker's website", "Listed by the maker").replace(/^, /, "")}</p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      )}

      {data && (
        <section className="space-y-4">
          <div className="flex items-baseline justify-between">
            <h2 className="font-display text-xl font-bold text-ink">Price changes</h2>
            <p className="text-sm text-mute">Ex-showroom, from the manufacturer&apos;s price list</p>
          </div>
          {prices.length === 0 ? <p className="text-sm text-mute">No lasting price changes in the last four months.</p> : (
            <div className="grid gap-3 md:grid-cols-2">
              {prices.map((u) => {
                const pct = u.old_inr && u.new_inr ? ((u.new_inr - u.old_inr) / u.old_inr) * 100 : 0;
                const down = pct < 0;
                return (
                  <Link key={u.model_id + u.date} href={u.model_id ? `/cars/${u.model_id}` : "#"}
                        className="flex items-center gap-4 rounded-2xl border border-line bg-panel p-4 transition hover:border-mute">
                    <div className="h-16 w-24 shrink-0 overflow-hidden rounded-xl bg-panel-soft">
                      {u.image_url && /* eslint-disable-next-line @next/next/no-img-element */
                        <img src={u.image_url} alt="" loading="lazy" className="h-full w-full object-contain" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs text-mute">{u.brand} · {fmtDate(u.date)} · {u.variants_changed} variant{u.variants_changed === 1 ? "" : "s"}</p>
                      <p className="truncate font-semibold text-ink">{u.model}</p>
                      <p className="truncate text-xs text-mute">{u.example_variant}</p>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="font-mono text-xs text-mute line-through">{u.old_inr ? lakh(u.old_inr) : ""}</p>
                      <p className="font-mono font-semibold text-ink">{u.new_inr ? lakh(u.new_inr) : ""}</p>
                      <p className={cn("font-mono text-xs font-semibold", down ? "text-good" : "text-accent")}>{down ? "" : "+"}{pct.toFixed(1)}%</p>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </section>
      )}

      {data && offers.length > 0 && (
        <section className="space-y-4">
          <h2 className="font-display text-xl font-bold text-ink">Offers that just started</h2>
          <div className="divide-y divide-line rounded-2xl border border-line bg-panel">
            {offers.map((u) => (
              <div key={u.title + u.date} className="flex items-start justify-between gap-4 p-4">
                <div className="min-w-0">
                  <p className="font-medium text-ink">{u.title}</p>
                  <p className="text-sm text-mute">{u.detail}</p>
                </div>
                {u.source_url && <a href={u.source_url} target="_blank" rel="noopener noreferrer" className="shrink-0 text-xs text-mute underline">source</a>}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default function UpdatesPage() {
  const [tab, setTab] = useState<"news" | "prices">("news");
  return (
    <main className="mx-auto max-w-6xl space-y-8 px-4 pb-16 pt-28">
      <SectionTitle eyebrow="Updates" title="What's new in the auto world"
        sub="The latest launches, price changes and rules, from India's auto publishers and manufacturers' own price lists." />
      <NewsShowcase />
      <div className="flex gap-2 border-b border-line">
        {([["news", "Latest news"], ["prices", "Prices & launches"]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)}
                  className={cn("-mb-px border-b-2 px-4 py-3 text-sm font-semibold", tab === k ? "border-accent text-ink" : "border-transparent text-mute hover:text-ink")}>{l}</button>
        ))}
      </div>
      {tab === "news" ? <NewsList /> : <PriceUpdates />}
    </main>
  );
}
