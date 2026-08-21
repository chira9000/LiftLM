"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Dumbbell,
  TrendingUp,
  ArrowUpCircle,
  MessageCircle,
  LogOut,
  Plus,
  Menu,
  X,
} from "lucide-react";
import clsx from "clsx";
import { clearToken } from "@/lib/api";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/workouts", label: "Workouts", icon: Dumbbell },
  { href: "/analytics", label: "Analytics", icon: TrendingUp },
  { href: "/progression", label: "Progression", icon: ArrowUpCircle },
  { href: "/coach", label: "AI Coach", icon: MessageCircle },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  const logout = () => {
    clearToken();
    router.push("/login");
  };

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");

  const content = (
    <>
      <div className="border-b border-surface-border px-5 py-6">
        <Link href="/dashboard" className="group flex items-center gap-3" onClick={() => setOpen(false)}>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500 text-surface shadow-panel transition-transform duration-200 group-hover:scale-105">
            <Dumbbell className="h-5 w-5" strokeWidth={2.25} />
          </div>
          <div>
            <span className="font-display text-lg font-semibold tracking-tight text-ink">LiftAI</span>
            <p className="text-[11px] text-ink-faint">Strength coach</p>
          </div>
        </Link>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        <p className="label mb-2 px-3.5 pt-2">Navigate</p>
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            onClick={() => setOpen(false)}
            className={clsx("nav-link", isActive(href) && "nav-link-active")}
          >
            {isActive(href) && (
              <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r bg-brand-400" />
            )}
            <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
            {label}
          </Link>
        ))}
      </nav>

      <div className="space-y-2 border-t border-surface-border p-4">
        <Link href="/workouts/new" onClick={() => setOpen(false)} className="btn-primary w-full">
          <Plus className="h-4 w-4" />
          Log Workout
        </Link>
        <button onClick={logout} className="btn-ghost w-full justify-start">
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </>
  );

  return (
    <>
      <button
        type="button"
        aria-label="Open menu"
        onClick={() => setOpen(true)}
        className="fixed left-4 top-4 z-40 flex h-10 w-10 items-center justify-center rounded-xl border border-surface-border bg-surface-card text-ink lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {open && (
        <button
          type="button"
          aria-label="Close menu"
          className="fixed inset-0 z-40 bg-black/55 backdrop-blur-[2px] lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={clsx(
          "fixed left-0 top-0 z-50 flex h-screen w-[16.5rem] flex-col border-r border-surface-border bg-surface-raised/95 backdrop-blur-md transition-transform duration-300 lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <button
          type="button"
          aria-label="Close menu"
          onClick={() => setOpen(false)}
          className="absolute right-3 top-4 rounded-lg p-1.5 text-ink-faint hover:text-ink lg:hidden"
        >
          <X className="h-4 w-4" />
        </button>
        {content}
      </aside>
    </>
  );
}
