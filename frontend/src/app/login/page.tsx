"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Dumbbell } from "lucide-react";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@liftai.app");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.login(email, password);
      setToken(res.access_token);
      router.push("/dashboard");
    } catch {
      setError("Invalid credentials. Try demo@liftai.app / demo1234");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
      <div className="pointer-events-none absolute -left-24 top-16 h-72 w-72 rounded-full bg-brand-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-16 bottom-10 h-80 w-80 rounded-full bg-sky-500/10 blur-3xl" />

      <div className="relative z-10 w-full max-w-md animate-fade-up">
        <div className="mb-10 text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500 text-surface shadow-lift">
            <Dumbbell className="h-7 w-7" strokeWidth={2.25} />
          </div>
          <h1 className="font-display text-4xl font-semibold tracking-tight text-ink">LiftAI</h1>
          <p className="mt-2 text-sm text-surface-muted">Train smarter with analytics-backed coaching</p>
        </div>

        <form onSubmit={handleLogin} className="panel space-y-5 p-7 sm:p-8">
          {error && (
            <div className="rounded-xl border border-red-500/25 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <div>
            <label className="label mb-2 block">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              autoComplete="email"
            />
          </div>

          <div>
            <label className="label mb-2 block">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              autoComplete="current-password"
            />
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full py-3">
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <p className="text-center text-xs text-ink-faint">
            Demo ready — <span className="text-surface-muted">demo@liftai.app</span> / demo1234
          </p>
        </form>
      </div>
    </div>
  );
}
