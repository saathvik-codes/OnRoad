"use client";

import { SWRConfig } from "swr";

/** Every page re-checks the server every five minutes and as soon as the tab is focused again, so prices, offers and
 *  news change on screen without a reload. The server's own cache is cleared whenever new data arrives. */
export function LiveData({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig value={{ refreshInterval: 5 * 60_000, revalidateOnFocus: true, revalidateOnReconnect: true, dedupingInterval: 10_000 }}>
      {children}
    </SWRConfig>
  );
}
