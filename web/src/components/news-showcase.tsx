"use client";

// Rotating showcase of the latest automotive stories (/api/news: Indian publishers' RSS feeds). Each slide shows the
// publisher's own headline, summary and image and links to the full story; stories about a car we list also link to
// its on-road price page. Renders nothing when there is no news.

import Link from "next/link";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { ArrowRight, ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { fetcher } from "@/lib/api";
import { cn } from "@/components/ui";

export type News = { id: string; title: string; summary: string; url: string; image_url: string | null; source: string;
  published: string; model_id: string | null; model_name: string | null; model_image: string | null; topic: string };

export const TOPIC: Record<string, string> = {
  launch: "Launch", price: "Price", safety: "Safety", ev: "Electric", policy: "Rules & tax", sales: "Sales",
  spied: "Spotted testing", industry: "Industry",
};

export function ago(iso: string) {
  const h = Math.max(1, Math.round((Date.now() - new Date(iso).getTime()) / 3.6e6));
  return h < 24 ? `${h}h ago` : `${Math.round(h / 24)}d ago`;
}

export function NewsShowcase({ limit = 6, className }: { limit?: number; className?: string }) {
  const { data } = useSWR<News[]>(`/news?limit=30`, fetcher);
  const slides = (data ?? []).filter((n) => n.image_url).slice(0, limit);
  const [i, setI] = useState(0);
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    if (slides.length < 2 || paused) return;
    const t = setInterval(() => setI((x) => (x + 1) % slides.length), 6000);
    return () => clearInterval(t);
  }, [slides.length, paused]);
  if (!slides.length) return null;
  const s = slides[i % slides.length];

  return (
    <section className={cn("relative overflow-hidden rounded-3xl border border-line bg-panel", className)}
             onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      <div className="grid md:grid-cols-[1.3fr_1fr]">
        <div className="relative aspect-[16/9] md:aspect-auto md:min-h-[320px]">
          {slides.map((n, k) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={n.id} src={n.image_url!} alt="" loading={k === 0 ? "eager" : "lazy"}
                 className={cn("absolute inset-0 h-full w-full object-cover transition-opacity duration-700", k === i ? "opacity-100" : "opacity-0")} />
          ))}
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent md:bg-gradient-to-r md:from-transparent md:via-transparent md:to-panel/30" />
          <span className="absolute left-4 top-4 rounded-lg bg-black/60 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-white">
            {TOPIC[s.topic] ?? "News"}
          </span>
        </div>
        <div className="flex flex-col justify-between gap-5 p-6 md:p-8">
          <div key={s.id} className="animate-[fadeUp_.5s_ease-out] space-y-3">
            <p className="text-xs text-mute">{s.source} · {ago(s.published)}</p>
            <h3 className="font-display text-2xl font-bold leading-snug text-ink md:text-[28px]">{s.title}</h3>
            {s.summary && <p className="line-clamp-3 text-sm text-mute">{s.summary}</p>}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <a href={s.url} target="_blank" rel="noopener noreferrer"
               className="inline-flex items-center gap-1.5 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-white hover:opacity-90">
              Read on {s.source}<ExternalLink className="h-4 w-4" />
            </a>
            {s.model_id && (
              <Link href={`/cars/${s.model_id}`} className="inline-flex items-center gap-1.5 rounded-xl border border-line px-4 py-2.5 text-sm font-semibold text-ink hover:border-accent/50">
                {s.model_name} on-road price<ArrowRight className="h-4 w-4" />
              </Link>
            )}
          </div>
          <div className="flex items-center gap-3">
            <button aria-label="Previous story" onClick={() => setI((i - 1 + slides.length) % slides.length)}
                    className="grid h-9 w-9 place-items-center rounded-full border border-line text-mute hover:text-ink"><ChevronLeft className="h-4 w-4" /></button>
            <div className="flex flex-1 gap-1.5">
              {slides.map((n, k) => (
                <button key={n.id} aria-label={`Story ${k + 1}`} onClick={() => setI(k)}
                        className="h-1.5 flex-1 overflow-hidden rounded-full bg-line">
                  <span className={cn("block h-full rounded-full bg-accent transition-all", k === i ? "w-full" : k < i ? "w-full opacity-40" : "w-0")} />
                </button>
              ))}
            </div>
            <button aria-label="Next story" onClick={() => setI((i + 1) % slides.length)}
                    className="grid h-9 w-9 place-items-center rounded-full border border-line text-mute hover:text-ink"><ChevronRight className="h-4 w-4" /></button>
          </div>
        </div>
      </div>
    </section>
  );
}
