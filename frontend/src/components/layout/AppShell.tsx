import { Outlet } from "react-router-dom";
import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

interface AppShellProps {
  children?: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-canvas">
      <Sidebar />
      <div className="pl-[var(--sidebar-width)]">
        <TopBar />
        <main className="p-6 animate-fade-in">
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  );
}
