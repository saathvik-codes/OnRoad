"use client";

// Model image carousel: the selected variant's own image first, then the model's other variant / colour images and the
// manufacturer's feature photos. Swipe (scroll-snap) on touch, arrows + dots on desktop. Images come via /api/img.

import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { imgSrc } from "@/components/car-image";
import { BodyIcon } from "@/components/body-icons";
import { cn } from "@/components/ui";

export type Shot = { url: string; label: string; kind: "model" | "variant" | "feature" };

export function Gallery({ shots, variantImage, variantName, alt, bodyType }: {
  shots: Shot[]; variantImage?: string | null; variantName?: string; alt: string; bodyType?: string | null;
}) {
  const list = useMemo(() => {
    const first: Shot[] = variantImage ? [{ url: variantImage, label: variantName ?? alt, kind: "variant" }] : [];
    return [...first, ...shots.filter((s) => s.url !== variantImage)];
  }, [shots, variantImage, variantName, alt]);
  const [i, setI] = useState(0);
  const strip = useRef<HTMLDivElement>(null);

  useEffect(() => { strip.current?.scrollTo({ left: 0 }); }, [variantImage]);   // new variant -> back to its picture

  const go = (n: number) => {
    const k = (n + list.length) % list.length;
    strip.current?.scrollTo({ left: k * (strip.current?.clientWidth ?? 0), behavior: "smooth" });
  };

  if (!list.length) return (
    <div className="grid aspect-[16/9] place-items-center"><BodyIcon type={bodyType ?? "SUV"} className="h-24 w-40 text-mute/40" /></div>
  );

  return (
    <div className="relative">
      <div ref={strip} data-lenis-prevent onScroll={(e) => setI(Math.round(e.currentTarget.scrollLeft / e.currentTarget.clientWidth))}
        className="no-scrollbar flex aspect-[16/9] snap-x snap-mandatory overflow-x-auto scroll-smooth">
        {list.map((s) => (
          <figure key={s.url} className="relative h-full w-full shrink-0 snap-center">
            <img src={imgSrc(s.url, 1200)} alt={`${alt}: ${s.label}`} loading="lazy" referrerPolicy="no-referrer"
              className={cn("h-full w-full", s.kind === "feature" ? "rounded-2xl object-cover" : "object-contain drop-shadow-[0_25px_45px_rgba(0,0,0,0.45)]")} />
            {s.kind !== "model" && (
              <figcaption className="absolute bottom-2 left-2 rounded-full bg-black/60 px-3 py-1 text-xs text-white">{s.label}</figcaption>
            )}
          </figure>
        ))}
      </div>
      {list.length > 1 && (
        <>
          <button aria-label="Previous image" onClick={() => go(i - 1)}
            className="absolute left-2 top-1/2 hidden -translate-y-1/2 rounded-full border border-line bg-panel/80 p-2 text-ink backdrop-blur sm:block"><ChevronLeft className="h-4 w-4" /></button>
          <button aria-label="Next image" onClick={() => go(i + 1)}
            className="absolute right-2 top-1/2 hidden -translate-y-1/2 rounded-full border border-line bg-panel/80 p-2 text-ink backdrop-blur sm:block"><ChevronRight className="h-4 w-4" /></button>
          <div className="mt-3 flex justify-center gap-1.5">
            {list.slice(0, 12).map((s, k) => (
              <button key={s.url} aria-label={`Image ${k + 1}`} onClick={() => go(k)}
                className={cn("h-1.5 rounded-full transition-all", k === i ? "w-6 bg-accent" : "w-1.5 bg-mute/40")} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
