"use client";

import type { ReactNode } from "react";
import { ToastProvider } from "./Toast";

/** Client-side providers mounted once in the root layout. */
export function Providers({ children }: { children: ReactNode }) {
  return <ToastProvider>{children}</ToastProvider>;
}
