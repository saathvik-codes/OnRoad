"use client";

// Three-part header: browsing on the left, the wordmark centred, tools and account on the right. Search opens as a
// full-width bar under the header so the row itself stays quiet. On phones: wordmark left, city, search and a menu.

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { Menu, Search, X } from "lucide-react";
import { Logo } from "@/components/logo";
import { SearchBox } from "@/components/search-box";
import { CityPicker } from "@/components/city";
import { ThemeToggle } from "@/components/theme";
import { fetcher, type Account } from "@/lib/api";
import { cn } from "@/components/ui";

const LEFT = [
  { href: "/cars", label: "Cars" },
  { href: "/bikes", label: "Bikes" },
  { href: "/brands", label: "Brands" },
  { href: "/updates", label: "Updates" },
];
const RIGHT = [
  { href: "/compare", label: "Compare" },
  { href: "/calculator", label: "Calculator" },
  { href: "/download", label: "App" },
];

function NavLink({ href, label, path }: { href: string; label: string; path: string }) {
  const active = path.startsWith(href);
  return (
    <Link href={href}
          className={cn("relative px-1 py-2 text-sm transition after:absolute after:inset-x-1 after:-bottom-0.5 after:h-0.5 after:rounded-full after:transition",
            active ? "font-semibold text-ink after:bg-accent" : "text-mute hover:text-ink after:bg-transparent")}>
      {label}
    </Link>
  );
}

export function SiteNav() {
  const path = usePathname();
  const [menu, setMenu] = useState(false);
  const [search, setSearch] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { data: me } = useSWR<Account>("/auth/me", fetcher, { shouldRetryOnError: false });

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 24);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);
  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if (e.key === "/" && !(e.target as HTMLElement)?.closest("input,textarea")) { e.preventDefault(); setSearch(true); }
      if (e.key === "Escape") setSearch(false);
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, []);

  if (path.startsWith("/lab")) return null;
  const account = me
    ? { href: me.role === "dealer" ? "/dealer" : me.role === "admin" ? "/admin" : "/account",
        label: me.role === "dealer" ? "Dealer desk" : me.role === "admin" ? "Admin" : "My garage" }
    : { href: "/login", label: "Log in" };

  return (
    <header className={cn("fixed inset-x-0 top-0 z-50 border-b transition duration-200",
      scrolled || search || menu ? "glass border-line" : "border-transparent bg-transparent")}>
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:grid lg:grid-cols-[1fr_auto_1fr]">
        {/* left: browsing */}
        <nav className="hidden items-center gap-6 lg:flex">
          {LEFT.map((l) => <NavLink key={l.href} {...l} path={path} />)}
        </nav>

        {/* centre: wordmark */}
        <Link href="/" aria-label="OnRoad home" className="shrink-0 justify-self-center"><Logo /></Link>

        {/* right: tools and account */}
        <div className="ml-auto flex min-w-0 items-center justify-end gap-2 sm:gap-3">
          <nav className="hidden items-center gap-5 2xl:flex">
            {RIGHT.map((l) => <NavLink key={l.href} {...l} path={path} />)}
          </nav>
          <CityPicker className="min-w-0 shrink" />
          <button onClick={() => { setSearch((s) => !s); setMenu(false); }} aria-label="Search"
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-full text-ink hover:bg-panel-soft">
            {search ? <X className="h-4 w-4" /> : <Search className="h-4 w-4" />}
          </button>
          <span className="hidden sm:block"><ThemeToggle /></span>
          <Link href={account.href}
                className={cn("hidden whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium sm:inline-block",
                  me ? "border border-line text-ink hover:bg-panel-soft" : "bg-ink text-bg hover:opacity-90")}>
            {account.label}
          </Link>
          <button className="grid h-9 w-9 place-items-center rounded-full text-ink hover:bg-panel-soft 2xl:hidden" aria-label="Menu"
                  onClick={() => { setMenu((m) => !m); setSearch(false); }}>
            {menu ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {search && (
        <div className="border-t border-line px-4 py-3 sm:px-6">
          <div className="mx-auto max-w-3xl"><SearchBox onDone={() => setSearch(false)} /></div>
        </div>
      )}

      {menu && (
        <div className="border-t border-line px-4 py-4 sm:px-6 2xl:hidden">
          <div className="mx-auto grid max-w-7xl gap-1 sm:grid-cols-2 lg:grid-cols-4">
            {[...LEFT, ...RIGHT].map((l) => (
              <Link key={l.href} href={l.href} onClick={() => setMenu(false)}
                    className={cn("rounded-lg px-2 py-2.5 font-medium transition hover:bg-panel-soft",
                      path.startsWith(l.href) ? "text-accent" : "text-ink")}>
                {l.label}
              </Link>
            ))}
            <Link href={account.href} onClick={() => setMenu(false)} className="rounded-lg px-2 py-2.5 font-medium text-ink hover:bg-panel-soft sm:hidden">
              {account.label}
            </Link>
          </div>
          <div className="mx-auto mt-3 flex max-w-7xl items-center justify-between border-t border-line pt-3 sm:hidden">
            <span className="text-sm text-mute">Appearance</span>
            <ThemeToggle />
          </div>
        </div>
      )}
    </header>
  );
}
