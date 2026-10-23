"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Compass, Bike, Calculator, User } from "lucide-react";
import { cn } from "@/components/ui";

const TABS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/cars", label: "Cars", icon: Compass },
  { href: "/bikes", label: "Bikes", icon: Bike },
  { href: "/calculator", label: "Calculator", icon: Calculator },
  { href: "/account", label: "Garage", icon: User },
];

import { Suspense } from "react";

function MobileNavContent() {
  const path = usePathname();

  // Hide in lab or embed modes
  if (path && path.startsWith("/lab")) return null;

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-panel/90 backdrop-blur-xl md:hidden pb-[env(safe-area-inset-bottom,0px)]">
      <div className="flex h-14 items-center justify-around px-2">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = tab.href === "/" ? path === "/" : path?.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "flex flex-1 flex-col items-center justify-center gap-0.5 py-1 text-[10px] font-medium transition",
                isActive
                  ? "text-accent font-semibold"
                  : "text-mute hover:text-ink"
              )}
            >
              <Icon className={cn("h-4 w-4 transition-transform", isActive && "scale-110")} />
              <span>{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export function MobileNav() {
  return (
    <Suspense fallback={null}>
      <MobileNavContent />
    </Suspense>
  );
}

