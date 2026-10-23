"use client";

import { useState, useMemo } from "react";
import { 
  MapPin, 
  Phone, 
  Navigation, 
  Search, 
  ExternalLink,
  LocateFixed,
  Building2,
  CheckCircle2,
  Compass
} from "lucide-react";
import { type Dealer } from "@/lib/api";
import { Card, cn, Input } from "@/components/ui";

interface ShowroomMapProps {
  dealers: Dealer[];
  brandName: string;
  city: string;
}

export function ShowroomMap({ dealers, brandName, city }: ShowroomMapProps) {
  const [selectedDealerId, setSelectedDealerId] = useState<string | null>(
    dealers.length > 0 ? dealers[0].id : null
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"split" | "map" | "list">("split");


  // Filter dealers based on search query
  const filteredDealers = useMemo(() => {
    if (!searchQuery.trim()) return dealers;
    const q = searchQuery.toLowerCase();
    return dealers.filter(
      (d) =>
        d.name.toLowerCase().includes(q) ||
        d.address.toLowerCase().includes(q) ||
        d.city.toLowerCase().includes(q) ||
        (d.pincode && d.pincode.includes(q))
    );
  }, [dealers, searchQuery]);

  const selectedDealer = useMemo(
    () => dealers.find((d) => d.id === selectedDealerId) || dealers[0],
    [dealers, selectedDealerId]
  );

  // Free Google Maps Embed URL (zero API key required, reliable worldwide)
  const googleMapUrl = useMemo(() => {
    if (selectedDealer) {
      if (selectedDealer.lat && selectedDealer.lng) {
        return `https://maps.google.com/maps?q=${selectedDealer.lat},${selectedDealer.lng}&hl=en&z=15&output=embed`;
      }
      return `https://maps.google.com/maps?q=${encodeURIComponent(
        `${selectedDealer.name}, ${selectedDealer.address}, ${selectedDealer.city}`
      )}&hl=en&z=15&output=embed`;
    }
    return `https://maps.google.com/maps?q=${encodeURIComponent(
      `${brandName} showroom ${city}`
    )}&hl=en&z=13&output=embed`;
  }, [selectedDealer, brandName, city]);

  if (dealers.length === 0) {
    return (
      <Card className="p-8 text-center border border-line bg-panel">
        <MapPin className="mx-auto h-8 w-8 text-mute/50 mb-3" />
        <h4 className="font-semibold text-ink">No authorized showroom listed in {city}</h4>
        <p className="mt-1 text-xs text-mute max-w-sm mx-auto">
          We couldn&apos;t find an official {brandName} showroom directly inside {city} city limits. Nearby showrooms in adjacent metro territories can be arranged for home test-drives.
        </p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden border border-line bg-panel p-0 shadow-xl">
      {/* Component Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line p-5 sm:p-6">
        <div>
          <h2 className="font-[family-name:var(--font-display)] text-xl font-bold text-ink sm:text-2xl">
            Authorized {brandName} Showrooms in {city}
          </h2>
          <p className="mt-1 text-xs text-mute sm:text-sm">
            {dealers.length} showroom{dealers.length === 1 ? "" : "s"} serving {city} & nearby region. Live Google Map navigation & phone direct lines.
          </p>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-1 rounded-xl bg-panel-soft p-1 border border-line shrink-0">
          <button
            onClick={() => setViewMode("split")}
            className={cn(
              "hidden sm:inline-block rounded-lg px-3 py-1.5 text-xs font-semibold transition cursor-pointer",
              viewMode === "split" ? "bg-accent text-white shadow" : "text-mute hover:text-ink"
            )}
          >
            Split View
          </button>
          <button
            onClick={() => setViewMode("map")}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-semibold transition cursor-pointer",
              viewMode === "map" ? "bg-accent text-white shadow" : "text-mute hover:text-ink"
            )}
          >
            Google Map
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-semibold transition cursor-pointer",
              viewMode === "list" ? "bg-accent text-white shadow" : "text-mute hover:text-ink"
            )}
          >
            Showroom List ({dealers.length})
          </button>
        </div>
      </div>

      {/* Main Content Layout */}
      <div
        className={cn(
          "grid",
          viewMode === "split" && "lg:grid-cols-[1.1fr_1.3fr]",
          viewMode === "map" && "grid-cols-1",
          viewMode === "list" && "grid-cols-1"
        )}
      >
        {/* Left Column: Search & Dealer List */}
        {(viewMode === "split" || viewMode === "list") && (
          <div className="flex flex-col border-r border-line bg-panel-soft/30">
            {/* Search Bar */}
            <div className="p-4 border-b border-line">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-mute" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={`Search ${dealers.length} showrooms in ${city}...`}
                  className="pl-9 text-xs h-9 bg-panel-soft border-line text-ink placeholder-mute"
                />
              </div>
            </div>

            {/* Scrollable Dealer Cards */}
            <div data-lenis-prevent className="scroll-thin overscroll-contain overflow-y-auto max-h-[540px] p-4 space-y-3">
              {filteredDealers.map((d, index) => {
                const isSelected = selectedDealerId === d.id;
                return (
                  <div
                    key={d.id}
                    onClick={() => setSelectedDealerId(d.id)}
                    className={cn(
                      "cursor-pointer rounded-2xl border p-4 transition-all duration-200",
                      isSelected
                        ? "border-accent bg-accent/[0.08] shadow-md shadow-accent/5 ring-1 ring-accent/30"
                        : "border-line bg-panel hover:border-line/80 hover:bg-panel-soft"
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-sm text-ink">{d.name}</h4>
                          {isSelected && (
                            <span className="flex h-2 w-2 rounded-full bg-accent animate-ping" />
                          )}
                        </div>
                        <p className="mt-1 flex items-start gap-1.5 text-xs text-mute">
                          <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" />
                          <span>{d.address}{d.pincode ? `, ${d.pincode}` : ""}{d.city ? ` (${d.city})` : ""}</span>
                        </p>
                      </div>

                      {d.distance_km != null && d.distance_km < 150 && (
                        <span className="shrink-0 rounded-full bg-panel-soft px-2 py-0.5 text-[10px] font-mono text-mute border border-line">
                          {d.distance_km} km
                        </span>
                      )}
                    </div>

                    <div className="mt-2.5 flex flex-wrap items-center gap-2 text-[11px] text-mute">
                      <span className="rounded-md border border-line bg-panel-soft px-2 py-0.5">
                        {d.kind === "sales+service" ? "Sales & service" : d.kind === "service" ? "Service only" : "Sales"}
                      </span>
                      {d.email && <a href={`mailto:${d.email}`} onClick={(e) => e.stopPropagation()} className="truncate hover:text-ink">{d.email}</a>}
                    </div>

                    <div className="mt-3 flex items-center justify-end border-t border-line/60 pt-3">
                      <div className="flex items-center gap-2">
                        {d.phone && (
                          <a
                            href={`tel:${d.phone.split(/[,/]/)[0].trim()}`}
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center gap-1 rounded-lg bg-panel-soft px-2.5 py-1 text-xs text-ink hover:bg-panel-soft/80 border border-line"
                          >
                            <Phone className="h-3 w-3 text-good" />
                            <span>Call</span>
                          </a>
                        )}
                        <a
                          href={d.lat && d.lng
                            ? `https://www.google.com/maps/dir/?api=1&destination=${d.lat},${d.lng}`
                            : `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${d.name}, ${d.address}, ${d.city}`)}`
                          }
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs text-white hover:brightness-110 shadow-sm font-semibold transition"
                        >
                          <Navigation className="h-3.5 w-3.5" />
                          <span>Get Directions</span>
                        </a>
                      </div>
                    </div>
                  </div>
                );
              })}

              {filteredDealers.length === 0 && (
                <div className="py-8 text-center text-xs text-mute">
                  No showrooms matching &ldquo;{searchQuery}&rdquo;. Clear search or check all locations.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Right Column: Google Maps Embed View */}
        {(viewMode === "split" || viewMode === "map") && (
          <div className="relative min-h-[380px] sm:min-h-[480px] lg:min-h-[540px] bg-panel-soft overflow-hidden">
            {/* Free Google Maps iframe embed */}
            <iframe
              src={googleMapUrl}
              className="absolute inset-0 h-full w-full border-0"
              loading="lazy"
              title={`${brandName} showroom location`}
              allowFullScreen
            />

            {/* Selected Dealer Overlay Preview Card */}
            {selectedDealer && (
              <div className="absolute bottom-4 inset-x-4 z-10 pointer-events-auto sm:inset-x-auto sm:left-4 sm:max-w-md">
                <div className="rounded-2xl border border-line bg-panel/95 p-4 shadow-2xl backdrop-blur-xl">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-mono uppercase tracking-wider text-accent font-semibold flex items-center gap-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-accent" /> Active Showroom
                      </span>
                      <h3 className="mt-0.5 font-bold text-sm text-ink">
                        {selectedDealer.name}
                      </h3>
                      <p className="text-xs text-mute line-clamp-2 mt-0.5">
                        {selectedDealer.address}{selectedDealer.pincode ? `, ${selectedDealer.pincode}` : ""}
                      </p>
                    </div>

                    <div className="flex flex-col gap-1.5 shrink-0">
                      <a
                        href={selectedDealer.lat && selectedDealer.lng
                          ? `https://www.google.com/maps/dir/?api=1&destination=${selectedDealer.lat},${selectedDealer.lng}`
                          : `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${selectedDealer.name}, ${selectedDealer.address}`)}`
                        }
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-accent px-3 py-1.5 text-xs font-semibold text-white shadow-md shadow-accent/20 hover:brightness-110"
                      >
                        <Navigation className="h-3 w-3" />
                        <span>Navigate</span>
                      </a>
                      {selectedDealer.phone && (
                        <a
                          href={`tel:${selectedDealer.phone.split(/[,/]/)[0].trim()}`}
                          className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-line bg-panel-soft px-3 py-1.5 text-xs font-medium text-ink hover:bg-panel-soft/80"
                        >
                          <Phone className="h-3 w-3 text-good" />
                          <span>Call</span>
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
