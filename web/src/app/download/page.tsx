import Image from "next/image";
import Link from "next/link";
import { Download, PlusSquare, Share, Smartphone } from "lucide-react";
import { Button, Card, SectionTitle } from "@/components/ui";

export const metadata = {
  title: "Get the app",
  description: "Install OnRoad on Android or add it to your iPhone Home Screen: official prices, the full on-road bill and nearby showrooms.",
};

const FAQ = [
  { q: "Why an APK and not Google Play?",
    a: "OnRoad isn't on Google Play yet. The APK here is the same signed release build; Android asks once to allow installs from your browser." },
  { q: "Is there an iPhone app?",
    a: "Not on the App Store yet. On iPhone, add OnRoad to your Home Screen from Safari. It opens full-screen and shows the same prices, offers and showrooms." },
  { q: "Does the app need the internet?",
    a: "Yes. Prices, offers and showrooms load from OnRoad's server so you always see the latest figures, which also keeps the app small." },
  { q: "How do updates work?",
    a: "On Android the app tells you when a newer build is available. On iPhone the Home Screen version always loads the latest version." },
];

export default function DownloadPage() {
  return (
    <main className="mx-auto max-w-5xl space-y-12 px-4 py-12">
      <SectionTitle eyebrow="Get the app" title="OnRoad on your phone"
        sub="Scan the code with your phone's camera. Android phones download the app; iPhones get the steps to add it to the Home Screen." />

      <div className="grid items-start gap-6 md:grid-cols-[auto_1fr_1fr]">
        <Card className="flex flex-col items-center gap-3 p-6">
          <Image src="/onroad-app-qr.png" alt="QR code that opens onroad-frontend.onrender.com/app" width={200} height={200}
                 className="rounded-xl bg-white p-2" />
          <p className="text-center text-xs text-mute">Opens onroad-frontend.onrender.com/app</p>
        </Card>

        <Card className="space-y-4 p-6">
          <p className="flex items-center gap-2 font-semibold text-ink"><Smartphone className="h-5 w-5 text-accent" />Android</p>
          <p className="text-sm text-mute">Android 8.0 or newer · about 6 MB</p>
          <a href="/onroad.apk" download="OnRoad.apk"><Button className="w-full"><Download className="mr-2 h-4 w-4" />Download APK</Button></a>
          <ol className="list-decimal space-y-1.5 pl-5 text-sm text-mute">
            <li>Open OnRoad.apk from your downloads.</li>
            <li>Allow installs from your browser if asked, then tap Install.</li>
            <li>Open OnRoad and pick your city.</li>
          </ol>
        </Card>

        <Card className="space-y-4 p-6">
          <p className="flex items-center gap-2 font-semibold text-ink"><Smartphone className="h-5 w-5 text-accent-2" />iPhone</p>
          <p className="text-sm text-mute">No download needed</p>
          <ol className="list-decimal space-y-1.5 pl-5 text-sm text-mute">
            <li>Open onroad-frontend.onrender.com in Safari.</li>
            <li>Tap <Share className="inline h-4 w-4 align-text-bottom text-ink" /> Share.</li>
            <li>Choose <PlusSquare className="inline h-4 w-4 align-text-bottom text-ink" /> Add to Home Screen.</li>
          </ol>
          <Link href="/"><Button variant="outline" className="w-full">Open OnRoad</Button></Link>
        </Card>
      </div>

      <section className="space-y-4">
        <h2 className="font-display text-xl font-bold text-ink">Questions</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {FAQ.map((f) => (
            <Card key={f.q} className="p-5">
              <p className="font-semibold text-ink">{f.q}</p>
              <p className="mt-1.5 text-sm text-mute">{f.a}</p>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
