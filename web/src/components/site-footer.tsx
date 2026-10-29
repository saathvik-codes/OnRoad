"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/logo";

const COLUMNS: { title: string; links: [string, string][] }[] = [
  { title: "Browse", links: [["/cars", "Cars"], ["/bikes", "Bikes and scooters"], ["/brands", "Brands"], ["/updates", "News and price changes"]] },
  { title: "Tools", links: [["/calculator", "On-road price calculator"], ["/compare", "Compare"], ["/buying-guide", "Buying and registration guide"],
    ["/download", "Get the app"]] },
  { title: "Showrooms", links: [["/signup?role=dealer", "List your showroom"], ["/dealer", "Dealer desk"]] },
];

export function SiteFooter() {
  if (usePathname().startsWith("/lab")) return null;
  return (
    <footer className="border-t border-line bg-panel">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-14 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <Logo size={32} />
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-mute">
            The full on-road price of every new car and bike in India, worked out for your city, and quotes from showrooms near you.
          </p>
        </div>
        {COLUMNS.map((c) => (
          <div key={c.title} className="text-sm">
            <p className="mb-3 font-semibold text-ink">{c.title}</p>
            {c.links.map(([h, l]) => <Link key={h} href={h} className="block py-1 text-mute transition hover:text-ink">{l}</Link>)}
          </div>
        ))}
      </div>

      <div className="border-t border-line">
        <div className="mx-auto max-w-7xl space-y-3 px-5 py-8 text-xs leading-relaxed text-mute">
          <p>
            <b className="font-semibold text-ink">Where the numbers come from.</b> Ex-showroom prices are taken from manufacturers&apos;
            websites and published price lists, and each price links to its source. Road tax, registration
            and insurance are calculated from state transport department rules, central registration fees and IRDAI third-party premiums.
            Showroom prices appear only when a showroom quotes them. Prices can change without notice: confirm the final figure with the
            showroom before you pay.
          </p>
          <p>
            Brand names and logos belong to their owners and are used only to identify them. OnRoad is independent and is not affiliated with
            any manufacturer, showroom or insurer. News headlines and images belong to their publishers and link to the original story.
          </p>
          <p>
            Credits: 3D concept car &ldquo;CarConcept&rdquo; from the Khronos glTF Sample Assets (Eric Chadwick, Darmstadt Graphics Group,
            after a model by Unity Fan), licensed{" "}
            <a className="underline" href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC BY 4.0</a>.
            It is not a model of any manufacturer.
          </p>
          <p>© {new Date().getFullYear()} OnRoad</p>
        </div>
      </div>
    </footer>
  );
}
