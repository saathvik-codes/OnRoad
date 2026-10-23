import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "OnRoad · Live Car Prices & On-Road Calculator",
    short_name: "OnRoad",
    description: "The real on-road price of every car in India, with road tax, RTO, insurance, and live dealer quotes.",
    start_url: "/",
    display: "standalone",
    background_color: "#05060a",
    theme_color: "#05060a",
    orientation: "portrait",
    icons: [
      {
        src: "/favicon.ico",
        sizes: "any",
        type: "image/x-icon",
      },
    ],
  };
}
