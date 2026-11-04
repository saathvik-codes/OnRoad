"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Mail,
  Copy,
  Check,
  Building2,
  ShieldCheck,
  Clock,
  Sparkles,
  Send,
  HelpCircle,
  ChevronDown,
  ArrowRight,
  ExternalLink,
  Receipt,
  Handshake,
  BellRing,
  Car
} from "lucide-react";
import { Card, SectionTitle, Button, Input, Textarea, Select, Label, Pill } from "@/components/ui";

const SUPPORT_EMAIL = "support@onroad.in";
const DEALER_EMAIL = "dealers@onroad.in";
const PRIVACY_EMAIL = "privacy@onroad.in";

const FAQ_ITEMS = [
  {
    category: "Pricing & Taxes",
    q: "Where do OnRoad prices come from?",
    a: "Ex-showroom prices are sourced directly from each manufacturer's official published price lists and audited daily. We then compute the exact on-road price by applying your state's Motor Vehicle Taxation Act (lifetime road tax, state registration levies, green cess), IRDAI-mandated third-party insurance, TCS (for vehicles above ₹10 Lakh), and mandatory FASTag. We link every ex-showroom price to its source."
  },
  {
    category: "Pricing & Taxes",
    q: "Why is the on-road price different in every city or state?",
    a: "State governments in India set their own motor vehicle road tax rates. For example, EV road tax can be 0% in some states while petrol/diesel tax ranges from 6% to over 18% depending on fuel type, engine displacement, vehicle value, and individual vs. company registration."
  },
  {
    category: "Pricing & Taxes",
    q: "What should I do if a showroom quotes a different price?",
    a: "Showrooms frequently add optional dealer charges (handling/logistics fees, extended warranties, basic accessory kits). Handling fees have been declared illegal by multiple High Courts and state transport authorities. Always ask for a written, itemised quotation and report discrepancies to our pricing desk so we can review it."
  },
  {
    category: "Dealer Quotes",
    q: "Who sees my quote request, and is my phone number shared?",
    a: "Your mobile number is NEVER shared with showrooms. Only verified authorized showrooms in your selected city receive your requested model, trim, and fuel type. They submit their best competitive price directly through OnRoad, keeping you safe from unsolicited sales calls."
  },
  {
    category: "Dealer Quotes",
    q: "How fast do showrooms reply with quotes?",
    a: "Most authorized dealerships reply within 2 to 4 business hours with an official breakdown including available dealer discounts, waiting periods, and delivery estimates."
  },
  {
    category: "Alerts & Account",
    q: "How do price-drop alerts work?",
    a: "Tap the bell icon on any vehicle model, choose your target price or trigger point, and OnRoad monitors manufacturer price revisions and local offer announcements. As soon as the price reaches your target, you receive a direct notification."
  },
  {
    category: "Alerts & Account",
    q: "How do I request account deletion or data removal?",
    a: "We believe in complete data sovereignty. You can delete your account anytime by emailing privacy@onroad.in with the subject 'Delete my OnRoad account' from your registered email. Your account, saved vehicles, and quote requests are purged within 7 business days."
  },
  {
    category: "Showrooms",
    q: "How can our authorized dealership join the quoting network?",
    a: "Authorized franchised dealers can sign up through our Dealer Portal at /dealer or write to dealers@onroad.in with your dealership name, manufacturer brand, and dealer code. Our partner relations team activates dealer dashboards within 24 hours."
  }
];

const CONTACT_REASONS = [
  {
    title: "Price Discrepancy & State RTO Updates",
    description: "State transport departments frequently revise road tax slabs and registration fees. If a local RTO charge or new manufacturer discount needs an update, our pricing desk validates and amends it within 24 hours.",
    image: "/illustrations/onb-receipt.webp",
    badge: "Accurate Pricing",
    action: "Report a price update"
  },
  {
    title: "Showroom Quotes & Fair Pricing",
    description: "Questions about a showroom quote you received, or need help with a delayed quote from a dealer? We monitor showroom response times and maintain strict quality standards.",
    image: "/illustrations/hero-quote.webp",
    badge: "Buyer Protection",
    action: "Quote assistance"
  },
  {
    title: "Missing Vehicles, Trims & Special Editions",
    description: "Looking for a newly announced vehicle variant, special edition, or commercial fleet trim that hasn't appeared in search yet? Request a priority catalog addition.",
    image: "/illustrations/hero-guide.webp",
    badge: "Catalog Addition",
    action: "Request a vehicle"
  },
  {
    title: "Price-Drop Alerts & App Features",
    description: "Need help fine-tuning your target price alerts, mobile notifications on Android/iOS, or syncing saved cars across your devices?",
    image: "/illustrations/notifications-permission.webp",
    badge: "App Support",
    action: "Get app help"
  }
];

export default function SupportPage() {
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null);
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const [activeTopic, setActiveTopic] = useState("Price Discrepancy or RTO Update");
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formCity, setFormCity] = useState("");
  const [formMessage, setFormMessage] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const copyToClipboard = (email: string) => {
    navigator.clipboard.writeText(email);
    setCopiedEmail(email);
    setTimeout(() => setCopiedEmail(null), 2500);
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    const subject = encodeURIComponent(`[${activeTopic}] OnRoad Support Request - ${formName || "User"}`);
    const body = encodeURIComponent(
      `Name: ${formName}\nEmail: ${formEmail}\nCity: ${formCity || "Not specified"}\nTopic: ${activeTopic}\n\nMessage:\n${formMessage}`
    );
    // Open default email client
    window.location.href = `mailto:${SUPPORT_EMAIL}?subject=${subject}&body=${body}`;
    setSubmitted(true);
  };

  return (
    <main className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      {/* HERO SECTION */}
      <div className="relative overflow-hidden rounded-3xl border border-line bg-gradient-to-b from-panel via-panel-soft/40 to-panel p-6 sm:p-12">
        <div className="grid items-center gap-8 lg:grid-cols-2">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
              </span>
              Support Desk Online · Typical reply under 4 hours
            </div>
            <h1 className="font-[family-name:var(--font-display)] text-3xl font-extrabold tracking-tight text-ink sm:text-5xl">
              We&apos;re here to help you get the <span className="text-accent">right price</span>
            </h1>
            <p className="text-base text-mute sm:text-lg">
              Have a question about an on-road price breakdown, state RTO taxes, or showroom quotes?
              Our dedicated automotive and research team is here to support you.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-2 text-xs text-mute">
              <span className="flex items-center gap-1.5"><Clock className="h-4 w-4 text-accent" /> Mon – Sat, 9:00 AM – 7:00 PM IST</span>
              <span>•</span>
              <span className="flex items-center gap-1.5"><ShieldCheck className="h-4 w-4 text-emerald-500" /> 100% Spam-free Guarantee</span>
            </div>
          </div>
          <div className="flex justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/illustrations/support-hero.webp"
              alt="OnRoad Help Desk"
              className="max-h-72 w-auto object-contain sm:max-h-88 drop-shadow-xl"
            />
          </div>
        </div>
      </div>

      {/* OFFICIAL CONTACT CHANNELS */}
      <section className="mt-14 space-y-6">
        <div>
          <Pill>Official Desks</Pill>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-ink sm:text-3xl">Get in touch with the right team</h2>
          <p className="mt-1 text-sm text-mute">Direct communication channels monitored by our operations, data, and partnership desks.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {/* Card 1: Customer Support */}
          <Card className="flex flex-col justify-between p-6 transition-all hover:border-accent/40 hover:shadow-md">
            <div className="space-y-4">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10 text-accent">
                <Mail className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-ink">General Support & Pricing</h3>
                <p className="mt-1 text-xs text-accent font-semibold">{SUPPORT_EMAIL}</p>
                <p className="mt-2 text-sm text-mute leading-relaxed">
                  Questions regarding car or bike on-road breakdowns, tax rules, app issues, or price-drop notifications.
                </p>
              </div>
            </div>
            <div className="mt-6 flex items-center gap-2 pt-4 border-t border-line">
              <a href={`mailto:${SUPPORT_EMAIL}`} className="flex-1">
                <Button size="sm" className="w-full">Email us</Button>
              </a>
              <button
                type="button"
                onClick={() => copyToClipboard(SUPPORT_EMAIL)}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-line text-mute hover:text-ink transition cursor-pointer"
                title="Copy email"
              >
                {copiedEmail === SUPPORT_EMAIL ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
          </Card>

          {/* Card 2: Showroom Relations */}
          <Card className="flex flex-col justify-between p-6 transition-all hover:border-amber-500/40 hover:shadow-md">
            <div className="space-y-4">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-500">
                <Building2 className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-ink">Showroom & Dealer Desk</h3>
                <p className="mt-1 text-xs text-amber-500 font-semibold">{DEALER_EMAIL}</p>
                <p className="mt-2 text-sm text-mute leading-relaxed">
                  For authorized car & bike dealerships looking to join OnRoad&apos;s verified quoting platform or update dealer listings.
                </p>
              </div>
            </div>
            <div className="mt-6 flex items-center gap-2 pt-4 border-t border-line">
              <Link href="/dealer" className="flex-1">
                <Button variant="outline" size="sm" className="w-full">Dealer portal</Button>
              </Link>
              <button
                type="button"
                onClick={() => copyToClipboard(DEALER_EMAIL)}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-line text-mute hover:text-ink transition cursor-pointer"
                title="Copy email"
              >
                {copiedEmail === DEALER_EMAIL ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
          </Card>

          {/* Card 3: Privacy & Data Protection */}
          <Card className="flex flex-col justify-between p-6 transition-all hover:border-emerald-500/40 hover:shadow-md">
            <div className="space-y-4">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-500">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-ink">Privacy & Data Requests</h3>
                <p className="mt-1 text-xs text-emerald-500 font-semibold">{PRIVACY_EMAIL}</p>
                <p className="mt-2 text-sm text-mute leading-relaxed">
                  Data access requests, account deletion, or questions about how we protect your personal information and phone numbers.
                </p>
              </div>
            </div>
            <div className="mt-6 flex items-center gap-2 pt-4 border-t border-line">
              <Link href="/privacy" className="flex-1">
                <Button variant="outline" size="sm" className="w-full">Privacy policy</Button>
              </Link>
              <button
                type="button"
                onClick={() => copyToClipboard(PRIVACY_EMAIL)}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-line text-mute hover:text-ink transition cursor-pointer"
                title="Copy email"
              >
                {copiedEmail === PRIVACY_EMAIL ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
          </Card>
        </div>
      </section>

      {/* WHY CONTACT US / WHEN TO REACH OUT */}
      <section className="mt-20 space-y-6">
        <div>
          <Pill>Why Contact Us</Pill>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-ink sm:text-3xl">How we assist car and bike buyers</h2>
          <p className="mt-1 text-sm text-mute">We actively curate and verify our data across all 36 States and Union Territories.</p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          {CONTACT_REASONS.map((item) => (
            <Card key={item.title} className="flex flex-col justify-between p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="inline-flex rounded-full bg-panel-soft px-3 py-1 text-xs font-semibold text-accent border border-line">
                    {item.badge}
                  </span>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={item.image} alt="" className="h-16 w-auto object-contain" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-ink">{item.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-mute">{item.description}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setActiveTopic(item.title);
                  const el = document.getElementById("inquiry-form");
                  el?.scrollIntoView({ behavior: "smooth" });
                }}
                className="mt-6 flex items-center gap-1.5 text-xs font-semibold text-accent hover:underline cursor-pointer"
              >
                {item.action} <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </Card>
          ))}
        </div>
      </section>

      {/* INTERACTIVE INQUIRY FORM */}
      <section id="inquiry-form" className="mt-20 scroll-mt-10">
        <Card className="p-6 sm:p-10 border-accent/20">
          <div className="grid gap-8 lg:grid-cols-[1.2fr_1.8fr]">
            <div className="space-y-4">
              <Pill>Direct Message</Pill>
              <h2 className="text-2xl font-bold tracking-tight text-ink sm:text-3xl">Send our team a message</h2>
              <p className="text-sm text-mute leading-relaxed">
                Fill out the quick form and we&apos;ll direct your inquiry to the right data or operations specialist.
                Every request is answered by a human.
              </p>

              <div className="space-y-3 pt-4 text-xs text-mute">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-emerald-500" /> Direct email dispatch to {SUPPORT_EMAIL}
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-emerald-500" /> Monitored by live team in India
                </div>
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-emerald-500" /> No spam or unsolicited marketing calls
                </div>
              </div>
            </div>

            <form onSubmit={handleSendMessage} className="space-y-4">
              <div>
                <Label>What can we help you with?</Label>
                <Select value={activeTopic} onChange={(e) => setActiveTopic(e.target.value)}>
                  <option value="Price Discrepancy or RTO Update">Price Discrepancy or State RTO Update</option>
                  <option value="Showroom Quotes & Fair Pricing">Showroom Quote Inquiry or Feedback</option>
                  <option value="Missing Vehicles, Trims & Special Editions">Request a Missing Car or Bike</option>
                  <option value="Price-Drop Alerts & App Features">Price Alerts & Notification Support</option>
                  <option value="Showroom & Dealer Partnership">Showroom Partnership / Dealer Portal</option>
                  <option value="Account, Security & Privacy">Account, Login or Data Deletion</option>
                  <option value="Other Feedback">Other Question or Suggestion</option>
                </Select>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label>Your Name</Label>
                  <Input
                    required
                    placeholder="e.g. Rahul Sharma"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Email Address</Label>
                  <Input
                    required
                    type="email"
                    placeholder="name@example.com"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <Label hint="(Optional)">City / State</Label>
                <Input
                  placeholder="e.g. Hyderabad, Bengaluru, Delhi NCR"
                  value={formCity}
                  onChange={(e) => setFormCity(e.target.value)}
                />
              </div>

              <div>
                <Label>Your Message</Label>
                <Textarea
                  required
                  rows={4}
                  placeholder="Tell us what vehicle or topic you have in mind..."
                  value={formMessage}
                  onChange={(e) => setFormMessage(e.target.value)}
                />
              </div>

              {submitted && (
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-700 dark:text-emerald-400">
                  <p className="font-semibold">Message prepared!</p>
                  <p className="mt-1 text-xs">
                    Your email client has opened with your request addressed to {SUPPORT_EMAIL}.
                    If your email client didn&apos;t open automatically, you can directly email us at{" "}
                    <a href={`mailto:${SUPPORT_EMAIL}`} className="underline font-semibold">{SUPPORT_EMAIL}</a>.
                  </p>
                </div>
              )}

              <Button type="submit" size="lg" className="w-full">
                <Send className="mr-2 h-4 w-4" /> Send message to support
              </Button>
            </form>
          </div>
        </Card>
      </section>

      {/* COMPREHENSIVE FAQ ACCORDION */}
      <section className="mt-20 space-y-6">
        <div>
          <Pill>FAQ</Pill>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-ink sm:text-3xl">Frequently Asked Questions</h2>
          <p className="mt-1 text-sm text-mute">Clear answers about on-road pricing, RTO tax slabs, showroom quotes, and your account.</p>
        </div>

        <div className="space-y-3">
          {FAQ_ITEMS.map((item, idx) => {
            const isOpen = openFaq === idx;
            return (
              <Card key={item.q} className="overflow-hidden">
                <button
                  type="button"
                  onClick={() => setOpenFaq(isOpen ? null : idx)}
                  className="flex w-full items-center justify-between p-5 text-left font-semibold text-ink hover:bg-panel-soft/60 transition cursor-pointer"
                >
                  <span className="flex items-center gap-3">
                    <span className="text-xs font-semibold uppercase tracking-wider text-accent/80">
                      {item.category}
                    </span>
                    <span className="text-sm sm:text-base">{item.q}</span>
                  </span>
                  <ChevronDown
                    className={`h-4 w-4 text-mute transition-transform duration-200 ${isOpen ? "rotate-180 text-accent" : ""}`}
                  />
                </button>
                {isOpen && (
                  <div className="border-t border-line/60 bg-panel-soft/30 p-5 text-sm leading-relaxed text-mute">
                    {item.a}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </section>

      {/* QUICK FOOTER STRIP */}
      <section className="mt-16 rounded-2xl border border-line bg-panel-soft/50 p-6 sm:p-8 text-center sm:text-left sm:flex sm:items-center sm:justify-between">
        <div>
          <h3 className="font-semibold text-ink">Looking for vehicle research and guides?</h3>
          <p className="mt-1 text-xs text-mute">
            Explore our step-by-step registration guides or calculate exact EMI options.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex flex-wrap items-center justify-center sm:justify-end gap-3 text-xs">
          <Link href="/buying-guide" className="rounded-full border border-line bg-panel px-4 py-2 font-medium text-ink hover:border-accent">
            Buying Guide
          </Link>
          <Link href="/calculator" className="rounded-full border border-line bg-panel px-4 py-2 font-medium text-ink hover:border-accent">
            EMI Calculator
          </Link>
          <Link href="/privacy" className="rounded-full border border-line bg-panel px-4 py-2 font-medium text-ink hover:border-accent">
            Privacy Policy
          </Link>
        </div>
      </section>
    </main>
  );
}
