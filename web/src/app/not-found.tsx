import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[70vh] max-w-xl flex-col items-center justify-center px-4 text-center">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/illustrations/web-404.webp" alt="" className="h-56 w-auto" />
      <h1 className="mt-6 text-2xl font-semibold">This road doesn&apos;t go anywhere</h1>
      <p className="mt-2 opacity-70">The page you asked for isn&apos;t here. It may have moved, or the car may no longer be sold.</p>
      <Link href="/" className="mt-6 rounded-full bg-orange-500 px-5 py-2.5 font-semibold text-white">Back to OnRoad</Link>
    </main>
  );
}
