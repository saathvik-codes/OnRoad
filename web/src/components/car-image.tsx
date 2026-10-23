"use client";

import { useState } from "react";
import { BodyIcon } from "@/components/body-icons";

interface CarImageProps {
  src?: string | null;
  alt: string;
  bodyType?: string | null;
  className?: string;
  priority?: boolean;
}

/** Remote manufacturer images go through our resizing cache (/api/img); local files are used as-is. */
export function imgSrc(src: string, w = 800) {
  return src.startsWith("http") ? `/api/img?w=${w}&u=${encodeURIComponent(src)}` : src;
}

export function CarImage({ src, alt, bodyType, className, priority }: CarImageProps) {
  const [failed, setFailed] = useState(false);
  const [direct, setDirect] = useState(false);   // cache miss/error: fall back to the manufacturer's own URL once
  const [loaded, setLoaded] = useState(false);
  const [natural, setNatural] = useState<number | null>(null);   // intrinsic width: never upscale past it (avoids blur)

  // If no source or failed to load, show the accurate vehicle body silhouette
  if (!src || failed) {
    return (
      <div className="absolute inset-0 grid place-items-center bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.06),transparent_70%)]">
        <BodyIcon type={bodyType ?? "SUV"} className="h-20 w-32 text-mute/40 transition-transform duration-500 group-hover:scale-105 group-hover:text-accent/40" />
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      {/* Background silhouette placeholder while image loads */}
      {!loaded && (
        <div className="absolute inset-0 grid place-items-center">
          <BodyIcon type={bodyType ?? "SUV"} className="h-20 w-32 text-mute/30 animate-pulse" />
        </div>
      )}
      <img
        src={direct ? src : imgSrc(src)}
        alt={alt}
        referrerPolicy="no-referrer"
        loading={priority ? "eager" : "lazy"}
        onLoad={(e) => { setLoaded(true); setNatural(e.currentTarget.naturalWidth); }}
        style={natural ? { maxWidth: natural * 1.1, margin: "auto" } : undefined}
        onError={() => (direct || !src.startsWith("http") ? setFailed(true) : setDirect(true))}
        className={`${className ?? "absolute inset-0 h-full w-full object-contain p-4 transition duration-500 group-hover:scale-105"} ${
          loaded ? "opacity-100" : "opacity-0"
        }`}
      />
    </div>
  );
}
