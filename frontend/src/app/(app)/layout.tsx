import AuthGuard from "@/components/AuthGuard";
import Sidebar from "@/components/Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="app-shell">
        <Sidebar />
        <main className="relative z-10 min-h-screen px-4 pb-10 pt-16 lg:ml-[16.5rem] lg:px-8 lg:pt-8">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>
      </div>
    </AuthGuard>
  );
}
