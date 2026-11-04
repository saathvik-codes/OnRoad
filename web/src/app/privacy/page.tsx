import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy policy · OnRoad", description: "What OnRoad collects, why, and how to delete it." };

const CONTACT = "privacy@onroad.in";

export default function Privacy() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-12 leading-relaxed text-ink/85">
      <h1 className="text-3xl font-semibold text-ink">Privacy policy</h1>
      <p className="mt-2 text-sm opacity-60">Last updated 4 November 2026 · applies to the OnRoad website and the OnRoad Android and iOS apps</p>

      <h2 className="mt-8 text-xl font-semibold text-ink">What we collect</h2>
      <ul className="mt-3 list-disc space-y-2 pl-5">
        <li><b>Account details</b>: your name and email address when you sign up, or your Google account name and email if you sign in with Google.</li>
        <li><b>Mobile number</b>: only if you verify it. We send a one-time code by SMS to confirm it is yours. Showrooms never see it.</li>
        <li><b>City and pincode</b>: to show on-road prices, offers and showrooms for where you live.</li>
        <li><b>Location</b> (only when you tap &ldquo;Showrooms near me&rdquo; and allow it): used on your device to sort showrooms by distance. We don&apos;t store a location history.</li>
        <li><b>Your activity in OnRoad</b>: cars you save, price alerts and target prices you set, comparisons and quote requests.</li>
        <li><b>Device data</b>: a notification token so we can send the price alerts you asked for, crash reports, and app usage statistics (Firebase Crashlytics and Analytics).</li>
        <li><b>Advertising</b>: the Android app shows banner ads from Google AdMob, which may use your device&apos;s advertising ID. You can reset or limit it in your phone&apos;s settings.</li>
      </ul>

      <h2 className="mt-8 text-xl font-semibold text-ink">How we use it</h2>
      <ul className="mt-3 list-disc space-y-2 pl-5">
        <li>To show prices, offers and showrooms for your city, and to keep your saved cars and alerts across devices.</li>
        <li>To send the price-drop and launch alerts you turned on.</li>
        <li>To pass a quote request to authorized showrooms, <b>only when you tick the consent box</b> on that request. The showroom receives the car, variant, colour, city and whether you want a loan comparison. It does not receive your mobile number.</li>
        <li>To keep OnRoad secure: one account per verified number, and limits on how often codes can be requested.</li>
      </ul>
      <p className="mt-3">We don&apos;t sell your personal data.</p>

      <h2 className="mt-8 text-xl font-semibold text-ink">Who processes it for us</h2>
      <p className="mt-3">Render (hosting), Google Firebase (sign-in, backup, notifications, crash reports, analytics), Google AdMob (ads) and Message Central (SMS codes). Each handles data only to provide its service to OnRoad.</p>

      <h2 className="mt-8 text-xl font-semibold text-ink">How long we keep it</h2>
      <p className="mt-3">Account data, saved cars, alerts and quote requests are kept while your account exists and deleted with it. One-time codes expire after 10 minutes.</p>

      <h2 className="mt-8 text-xl font-semibold text-ink">Your choices</h2>
      <ul className="mt-3 list-disc space-y-2 pl-5">
        <li>Turn alerts off in the app, or turn off notifications for OnRoad in your phone&apos;s settings.</li>
        <li>Deny location access. Everything except &ldquo;near me&rdquo; sorting still works.</li>
        <li><b>Delete your account</b>: email <a className="text-[#ff4d2e] underline" href={`mailto:${CONTACT}?subject=Delete my OnRoad account`}>{CONTACT}</a> from your registered email address with the subject &ldquo;Delete my OnRoad account&rdquo;. We delete your account and its data within 7 days and confirm by email.</li>
      </ul>

      <h2 className="mt-8 text-xl font-semibold text-ink">Children</h2>
      <p className="mt-3">OnRoad is meant for people aged 18 and over who are buying a car.</p>

      <h2 className="mt-8 text-xl font-semibold text-ink">Contact</h2>
      <p className="mt-3">Questions about this policy or your data: <a className="text-[#ff4d2e] underline" href={`mailto:${CONTACT}`}>{CONTACT}</a>.</p>
    </main>
  );
}
