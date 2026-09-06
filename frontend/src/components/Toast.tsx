"use client";

/**
 * Lightweight toast system (no external dependency).
 * Usage: const { toast } = useToast();
 *        toast({ title: "Uploaded", variant: "success" });
 */
import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { IconAlertTriangle, IconCheckCircle, IconInfo, IconX } from "./icons";

type ToastVariant = "success" | "error" | "info";

interface ToastItem {
  id: number;
  title: string;
  description?: string;
  variant: ToastVariant;
}

interface ToastInput {
  title: string;
  description?: string;
  variant?: ToastVariant;
}

const ToastContext = createContext<{ toast: (input: ToastInput) => void } | null>(
  null
);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within <ToastProvider>");
  return ctx;
}

const VARIANT_STYLES: Record<
  ToastVariant,
  { icon: ReactNode; border: string; iconColor: string }
> = {
  success: {
    icon: <IconCheckCircle className="h-5 w-5" />,
    border: "border-emerald-200",
    iconColor: "text-emerald-600",
  },
  error: {
    icon: <IconAlertTriangle className="h-5 w-5" />,
    border: "border-rose-200",
    iconColor: "text-rose-600",
  },
  info: {
    icon: <IconInfo className="h-5 w-5" />,
    border: "border-blue-200",
    iconColor: "text-blue-600",
  },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const counter = useRef(0);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    ({ title, description, variant = "info" }: ToastInput) => {
      const id = ++counter.current;
      setToasts((prev) => [...prev, { id, title, description, variant }]);
      window.setTimeout(() => dismiss(id), 4500);
    },
    [dismiss]
  );

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-80 flex-col gap-2">
        {toasts.map((t) => {
          const styles = VARIANT_STYLES[t.variant];
          return (
            <div
              key={t.id}
              role="status"
              className={`animate-toast-in pointer-events-auto flex items-start gap-3 rounded-xl border bg-white p-4 shadow-lg ${styles.border}`}
            >
              <span className={`mt-0.5 shrink-0 ${styles.iconColor}`}>
                {styles.icon}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-900">{t.title}</p>
                {t.description && (
                  <p className="mt-0.5 break-words text-xs text-slate-600">
                    {t.description}
                  </p>
                )}
              </div>
              <button
                onClick={() => dismiss(t.id)}
                className="shrink-0 rounded p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                aria-label="Dismiss notification"
              >
                <IconX className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
