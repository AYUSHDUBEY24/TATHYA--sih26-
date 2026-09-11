"use client";

/**
 * Centralized inline SVG icon set (no external icon dependency).
 * All icons inherit `currentColor` and accept a `className`.
 */
import type { ReactNode, SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { className?: string };

function makeIcon(paths: ReactNode) {
  return function Icon({ className = "h-5 w-5", ...props }: IconProps) {
    return (
      <svg
        className={className}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        {...props}
      >
        {paths}
      </svg>
    );
  };
}

export const IconHome = makeIcon(
  <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
);

export const IconFolder = makeIcon(
  <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
);

export const IconSearch = makeIcon(
  <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
);

export const IconSparkles = makeIcon(
  <path d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
);

export const IconClipboardList = makeIcon(
  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
);

export const IconShield = makeIcon(
  <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
);

export const IconLogOut = makeIcon(
  <path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
);

export const IconMenu = makeIcon(<path d="M4 6h16M4 12h16M4 18h16" />);

export const IconX = makeIcon(<path d="M6 18L18 6M6 6l12 12" />);

export const IconUpload = makeIcon(
  <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
);

export const IconDownload = makeIcon(
  <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
);

export const IconTrash = makeIcon(
  <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
);

export const IconPlus = makeIcon(<path d="M12 4v16m8-8H4" />);

export const IconLayoutGrid = makeIcon(
  <path d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
);

export const IconList = makeIcon(<path d="M4 6h16M4 12h16M4 18h16" />);

export const IconFileText = makeIcon(
  <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
);

export const IconLock = makeIcon(
  <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
);

export const IconSend = makeIcon(
  <path d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
);

export const IconRefresh = makeIcon(
  <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
);

export const IconLink = makeIcon(
  <path d="M13.828 10.172a4 4 0 010 5.656l-3 3a4 4 0 01-5.656-5.656l1.5-1.5m8.156-8.156l1.5-1.5a4 4 0 015.656 5.656l-3 3a4 4 0 01-5.656 0" />
);

export const IconAlertTriangle = makeIcon(
  <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
);

export const IconCheckCircle = makeIcon(
  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
);

export const IconXCircle = makeIcon(
  <path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
);

export const IconInfo = makeIcon(
  <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
);

export const IconCopy = makeIcon(
  <path d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
);

export const IconUser = makeIcon(
  <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
);

export const IconChevronRight = makeIcon(<path d="M9 5l7 7-7 7" />);

export const IconScale = makeIcon(
  <path d="M3 6l6 0M15 6l6 0M3 6l4.5 9a3.5 3.5 0 006.9 0M21 6l-4.5 9a3.5 3.5 0 01-6.9 0M12 3v18" />
);

export const IconHistory = makeIcon(
  <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
);

export const IconRestore = makeIcon(
  <path d="M3 3v5h5M3.05 13A9 9 0 106 5.3L3 8m1 14v-6h6" />
);

/**
 * TATHYA product logo mark — shield + checkmark in a trust-blue gradient
 * square. Used in the sidebar and login screen.
 */
export function LogoMark({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <span
      className={`flex items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-blue-500 shadow-sm ${className}`}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2.2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-[60%] w-[60%] text-white"
      >
        <path d="M12 2.5l7 2.8v5.2c0 4.9-3 8.9-7 10.5-4-1.6-7-5.6-7-10.5V5.3l7-2.8z" />
        <path d="M9 12l2.2 2.2L15.5 9.7" />
      </svg>
    </span>
  );
}

/** TATHYA wordmark + tagline block. */
export function LogoBlock({
  size = "sm",
  dark = false,
}: {
  size?: "sm" | "lg";
  dark?: boolean;
}) {
  const mark = size === "lg" ? "h-11 w-11" : "h-9 w-9";
  return (
    <div className="flex items-center gap-3">
      <LogoMark className={mark} />
      <div className="min-w-0">
        <p
          className={`${size === "lg" ? "text-lg" : "text-sm"} font-bold tracking-[0.18em] ${
            dark ? "text-slate-900" : "text-white"
          }`}
        >
          TATHYA
        </p>
        <p
          className={`${
            size === "lg" ? "text-xs" : "text-[10px]"
          } italic tracking-wide ${dark ? "text-slate-500" : "text-slate-400"}`}
        >
          Where Facts Find Forever
        </p>
      </div>
    </div>
  );
}
