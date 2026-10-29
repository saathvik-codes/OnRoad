import { redirect } from "next/navigation";

// The old news page now lives at /updates (price changes, new models and offers from makers' own data).
export default function News() {
  redirect("/updates");
}
