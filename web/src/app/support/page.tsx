import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Help · OnRoad", description: "Get help with OnRoad prices, alerts, quotes and your account." };

const CONTACT = "saathvikk202@gmail.com";

const FAQ: [string, string][] = [
  ["Where do the prices come from?", "Ex-showroom prices come from each carmaker's official price lists. We add RTO tax, insurance and other charges for your city to give the on-road price. Showrooms can quote a little differently, so ask for a written quote before you pay."],
  ["Why isn't my city's price shown?", "Pick your city at the top of the screen. If a model shows \"Price on request\", the carmaker hasn't published a price for it yet."],
  ["How do price alerts work?", "Tap the bell on any car and pick a target price. We notify you once when the on-road price in your city drops to it."],
  ["Who sees my quote request?", "Only authorized showrooms in your city, and only after you tick the consent box. They see the car and variant you chose, never your mobile number."],
  ["I didn't get the SMS code", "Wait 30 seconds and tap Resend. You can request up to 5 codes an hour. Check the number has no leading 0 or +91 typed twice."],
  ["How do I delete my account?", "Email us from your registered address with the subject \"Delete my OnRoad account\". It's done within 7 days."],
];

export default function Support() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-12 leading-relaxed text-ink/85">
      <h1 className="text-3xl font-semibold text-ink">Help</h1>
      <p className="mt-2">Write to <a className="text-[#ff4d2e] underline" href={`mailto:${CONTACT}`}>{CONTACT}</a>. We reply within two working days.</p>
      <div className="mt-8 divide-y divide-black/10 border-y border-black/10">
        {FAQ.map(([q, a]) => (
          <details key={q} className="py-4">
            <summary className="cursor-pointer font-semibold text-ink">{q}</summary>
            <p className="mt-2">{a}</p>
          </details>
        ))}
      </div>
      <p className="mt-8 text-sm opacity-70">Read our <Link href="/privacy" className="underline">privacy policy</Link>.</p>
    </main>
  );
}
