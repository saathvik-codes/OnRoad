"use client";

import Link from "next/link";
import { Logo } from "@/components/logo";
import { usePathname } from "next/navigation";
import { SearchBox } from "@/components/search-box";
import { CityPicker } from "@/components/city";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { Calculator, Menu, Smartphone, X } from "lucide-react";
import { fetcher, type Account } from "@/lib/api";
import { cn } from "@/components/ui";
import { ThemeToggle } from "@/components/theme";

const LINKS = [
  { href: "/cars", label: "Cars" },
  { href: "/bikes", label: "Bikes" },
  { href: "/brands", label: "Brands" },
  { href: "/news", label: "News & Reviews" },
  { href: "/calculator", label: "Calculator" },
  { href: "/compare", label: "Compare" },
];

export function SiteNav() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { data: me } = useSWR<Account>("/auth/me", fetcher, { shouldRetryOnError: false });

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 24);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  if (path.startsWith("/lab")) return null;
  return (
    <header className={cn("fixed inset-x-0 top-0 z-50 transition duration-200", scrolled ? "glass shadow-xs" : "bg-transparent")}>
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-1.5 px-3 sm:gap-2.5 sm:px-5 lg:gap-3 xl:gap-5">
        <Link href="/" aria-label="onroad home" className="shrink-0"><Logo /></Link>
        <nav className="hidden items-center gap-0.5 lg:flex xl:gap-1">
          {LINKS.map((l) => {
            const active = path.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                className={cn(
                  "whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-medium transition shrink-0",
                  active
                    ? "bg-accent/15 text-accent font-semibold"
                    : "text-mute hover:text-ink hover:bg-panel-soft"
                )}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
        <SearchBox className="ml-auto hidden md:block w-40 lg:w-48 xl:w-64 2xl:w-72 shrink-0" />
        <Link
          href="/download"
          className={cn(
            "hidden sm:inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-line bg-panel-soft/70 px-3 py-1.5 text-xs font-semibold text-ink transition-all hover:border-accent/40 hover:bg-panel hover:text-accent shadow-xs shrink-0",
            path.startsWith("/download") && "border-accent/40 bg-accent/10 text-accent font-semibold"
          )}
        >
          <Smartphone className="h-3.5 w-3.5 text-accent shrink-0" />
          <span>Get App</span>
        </Link>
        <CityPicker className="ml-auto min-w-0 md:ml-0 shrink-0" />
        <span className="hidden sm:block shrink-0"><ThemeToggle /></span>
        <div className="flex shrink-0 items-center gap-1 sm:gap-2">
          {me ? (
            <Link
              href={me.role === "dealer" ? "/dealer" : me.role === "admin" ? "/admin" : "/account"}
              className="whitespace-nowrap rounded-full border border-line bg-panel px-3 py-1.5 text-xs sm:text-sm font-medium text-ink hover:bg-panel-soft sm:px-4"
            >
              {me.role === "dealer" ? "Dealer desk" : me.role === "admin" ? "Admin" : "My garage"}
            </Link>
          ) : (
            <Link
              href="/login"
              className="whitespace-nowrap rounded-full bg-accent px-3.5 py-1.5 text-xs sm:text-sm font-medium text-white shadow-xs hover:brightness-110 sm:px-4"
            >
              Log in
            </Link>
          )}
          <button
            className="rounded-full p-2 text-ink lg:hidden hover:bg-panel-soft"
            aria-label="Menu"
            onClick={() => setOpen(!open)}
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>
      {open && (
        <div className="glass border-t border-line px-5 py-4 lg:hidden">
          <SearchBox className="mb-3" onDone={() => setOpen(false)} />
          <div className="space-y-1">
            {LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="block rounded-lg px-2 py-2 text-ink font-medium hover:text-accent hover:bg-panel-soft transition"
              >
                {l.label}
              </Link>
            ))}
          </div>
          <Link
            href="/download"
            onClick={() => setOpen(false)}
            className="mt-3 flex items-center justify-between rounded-2xl border border-accent/25 bg-accent/10 p-3.5 transition hover:bg-accent/15"
          >
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-accent text-white shadow-xs">
                <Smartphone className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-bold text-ink">Get OnRoad Mobile App</p>
                <p className="text-xs text-mute">Android Live · iOS Soon</p>
              </div>
            </div>
            <span className="rounded-full bg-accent px-3 py-1 text-xs font-bold text-white shadow-xs">Get</span>
          </Link>
          <Link
            href="/calculator"
            onClick={() => setOpen(false)}
            className="mt-3 flex items-center gap-2 px-2 text-sm text-accent font-semibold"
          >
            <Calculator className="h-4 w-4" /> Check a dealer quote
          </Link>
          <div className="mt-3 flex items-center justify-between border-t border-line pt-3 sm:hidden">
            <span className="text-sm text-mute">Appearance</span>
            <ThemeToggle />
          </div>
        </div>
      )}
    </header>
  );
}
