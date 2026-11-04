import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Help & Support Desk · OnRoad",
  description: "Get help with OnRoad on-road prices, state RTO tax calculations, dealer quotes, price alerts, or get in touch with our team.",
};

export default function SupportLayout({ children }: { children: React.ReactNode }) {
  return children;
}
