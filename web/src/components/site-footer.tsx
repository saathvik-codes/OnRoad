"use client";

import Link from "next/link";
import { Logo } from "@/components/logo";
import { usePathname } from "next/navigation";

export function SiteFooter() {
  if (usePathname().startsWith("/lab")) return null;
  return (
    <footer className="border-t border-line bg-panel">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-14 sm:grid-cols-4">
        <div className="sm:col-span-2">
          <Logo size={34} />
          <p className="mt-3 max-w-md text-sm leading-relaxed text-mute">
            Ex-showroom prices come from each manufacturer&apos;s own website for your city. On-road prices are calculated from state
            transport department rules, central RTO fees, IRDAI third-party premiums and the Income-tax Act, with every line sourced.
            Dealer prices appear only when a dealer quotes them.
          </p>
        </div>
        <div className="text-sm">
          <p className="mb-3 text-ink font-semibold">Explore</p>
          {[
            ["/cars", "All cars"],
            ["/bikes", "Bikes"],
            ["/brands", "Brands"],
            ["/calculator", "Price calculator"],
            ["/compare", "Compare"],
            ["/updates", "Price changes & new launches"],
            ["/buying-guide", "Buying & registration guide"],
            ["/download", "Mobile App (Android & iOS)"],
          ].map(([h, l]) => (
            <Link key={h} href={h} className="block py-1 text-mute hover:text-accent transition">
              {l}
            </Link>
          ))}
        </div>
        <div className="text-sm">
          <p className="mb-3 text-ink font-semibold">For dealers</p>
          <Link href="/signup?role=dealer" className="block py-1 text-mute hover:text-accent transition">
            List your showroom
          </Link>
          <Link href="/dealer" className="block py-1 text-mute hover:text-accent transition">
            Dealer desk
          </Link>
        </div>
      </div>
      <div className="mx-auto max-w-7xl space-y-1 px-5 pb-10 text-xs text-mute/70">
        <p>Brand names and logos belong to their owners and are used only to identify the brand. OnRoad is not affiliated with any manufacturer.</p>
        <p>
          3D showcase car: &quot;CarConcept&quot; from the Khronos glTF Sample Assets by Eric Chadwick / Darmstadt Graphics Group, based on a model by
          Unity Fan, licensed <a className="underline" href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC BY 4.0</a>.
          It is a generic concept car, not any manufacturer&apos;s model.
        </p>
      </div>
    </footer>
  );
}
