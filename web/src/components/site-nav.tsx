"use client";

import Link from "next/link";
import { Logo } from "@/components/logo";
import { usePathname } from "next/navigation";
import { SearchBox } from "@/components/search-box";
import { CityPicker } from "@/components/city";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { Calculator, Menu, X } from "lucide-react";
import { fetcher, type Account } from "@/lib/api";
import { cn } from "@/components/ui";
import { ThemeToggle } from "@/components/theme";

const LINKS = [
  { href: "/cars", label: "Cars" },
  { href: "/bikes", label: "Bikes" },
  { href: "/brands", label: "Brands" },
  { href: "/calculator", label: "On-road calculator" },
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
    <header className={cn("fixed inset-x-0 top-0 z-50 transition", scrolled ? "glass" : "bg-transparent")}>
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-6 px-5">
        <Link href="/" aria-label="onroad home"><Logo /></Link>
        <nav className="hidden items-center gap-1 lg:flex">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className={cn("rounded-full px-3.5 py-1.5 text-sm font-medium transition",
              path.startsWith(l.href) ? "bg-accent/15 text-accent font-semibold" : "text-mute hover:text-ink hover:bg-panel-soft")}>{l.label}</Link>
          ))}
        </nav>
        <SearchBox className="ml-auto hidden w-56 md:block xl:w-72" />
        <CityPicker className="ml-auto md:ml-0" />
        <ThemeToggle />
        <div className="flex items-center gap-2">
          {me ? (
            <Link href={me.role === "dealer" ? "/dealer" : me.role === "admin" ? "/admin" : "/account"}
              className="rounded-full border border-line bg-panel px-4 py-1.5 text-sm text-ink hover:bg-panel-soft font-medium">
              {me.role === "dealer" ? "Dealer desk" : me.role === "admin" ? "Admin" : "My garage"}
            </Link>
          ) : (
            <Link href="/login" className="rounded-full bg-accent text-white px-4 py-1.5 text-sm font-medium hover:brightness-110 shadow-sm">Log in</Link>
          )}
          <button className="rounded-full p-2 text-ink lg:hidden" aria-label="Menu" onClick={() => setOpen(!open)}>
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>
      {open && (
        <div className="glass border-t border-line px-5 py-4 lg:hidden">
          <SearchBox className="mb-3" onDone={() => setOpen(false)} />
          {LINKS.map((l) => <Link key={l.href} href={l.href} onClick={() => setOpen(false)} className="block py-2 text-ink font-medium hover:text-accent transition">{l.label}</Link>)}
          <Link href="/calculator" onClick={() => setOpen(false)} className="mt-2 flex items-center gap-2 text-accent font-semibold"><Calculator className="h-4 w-4" /> Check a dealer quote</Link>
        </div>
      )}
    </header>
  );
}
