"use client";

// Everything new in the Indian car and bike market, in two parts:
//   * News: headlines from Indian publishers' RSS feeds (/api/news), each linking to the full story;
//   * Prices & launches: what changed in OnRoad's own records (/api/updates): price revisions read from makers'
//     price lists, models that newly appear on makers' sites, and manufacturer offers that started recently.

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import { CirclePlus, ExternalLink, Tag, TrendingDown, TrendingUp } from "lucide-react";
import { fetcher } from "@/lib/api";
import { Card, cn, Empty, SectionTitle, Skeleton } from "@/components/ui";
import { ago, NewsShowcase, TOPIC, type News } from "@/components/news-showcase";

type Update = { kind: "price" | "new" | "offer"; date: string; model_id: string | null; title: string; detail: string;
  source_url?: string | null; image_url?: string | null };

const TOPICS = ["all", "launch", "price", "ev", "safety", "policy", "spied", "sales"] as const;

function UpdateIcon({ u }: { u: Update }) {
  if (u.kind === "new") return <CirclePlus className="h-4 w-4 text-accent-2" />;
  if (u.kind === "offer") return <Tag className="h-4 w-4 text-good" />;
  return / down/.test(u.title) ? <TrendingDown className="h-4 w-4 text-good" /> : <TrendingUp className="h-4 w-4 text-accent" />;
}

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
                ? <img src={n.image_url} alt="" loading="lazy" className="aspect-[16/9] w-full object-cover transition group-hover:opacity-90" />
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

function PriceUpdates() {
  const [type, setType] = useState<"car" | "bike">("car");
  const [kind, setKind] = useState<"all" | Update["kind"]>("all");
  const { data, error } = useSWR<Update[]>(`/updates?vehicle_type=${type}&limit=100`, fetcher);
  const list = (data ?? []).filter((u) => kind === "all" || u.kind === kind);
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        {(["car", "bike"] as const).map((t) => (
          <button key={t} onClick={() => setType(t)}
                  className={cn("rounded-xl border px-4 py-2 text-sm font-medium", type === t ? "border-accent bg-accent/10 text-accent" : "border-line text-mute")}>
            {t === "car" ? "Cars" : "Bikes & scooters"}
          </button>
        ))}
        <span className="mx-2 h-6 w-px bg-line" />
        {([["all", "Everything"], ["price", "Price changes"], ["new", "New models"], ["offer", "New offers"]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setKind(k)}
                  className={cn("rounded-xl px-3 py-2 text-sm", kind === k ? "bg-panel-soft font-medium text-ink" : "text-mute hover:text-ink")}>{l}</button>
        ))}
      </div>
      {error && <Empty title="Couldn't load updates">Please try again in a moment.</Empty>}
      {!data && !error && <div className="space-y-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-20 w-full" />)}</div>}
      {data && list.length === 0 && <Empty title="Nothing new here yet">Price changes and new launches appear here as makers publish them.</Empty>}
      <div className="space-y-3">
        {list.map((u) => {
          const body = (
            <Card className="flex items-start gap-4 p-4 transition hover:border-accent/40">
              <div className="mt-1"><UpdateIcon u={u} /></div>
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-ink">{u.title}</p>
                <p className="text-sm text-mute">{u.detail}</p>
              </div>
              <div className="shrink-0 text-right text-xs text-mute">
                <p>{new Date(u.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</p>
                {u.source_url && (
                  <a href={u.source_url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}
                     className="mt-1 inline-flex items-center gap-1 underline">source<ExternalLink className="h-3 w-3" /></a>
                )}
              </div>
            </Card>
          );
          return u.model_id
            ? <Link key={u.kind + u.date + u.title} href={`/cars/${u.model_id}`}>{body}</Link>
            : <div key={u.kind + u.date + u.title}>{body}</div>;
        })}
      </div>
    </div>
  );
}

export default function UpdatesPage() {
  const [tab, setTab] = useState<"news" | "prices">("news");
  return (
    <main className="mx-auto max-w-6xl space-y-8 px-4 py-10">
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
