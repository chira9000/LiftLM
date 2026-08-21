"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";
import LoadingState from "@/components/LoadingState";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    } else {
      setReady(true);
    }
  }, [router]);

  if (!ready) {
    return (
      <div className="app-shell flex min-h-screen items-center justify-center">
        <LoadingState label="Checking session" />
      </div>
    );
  }

  return <>{children}</>;
}
