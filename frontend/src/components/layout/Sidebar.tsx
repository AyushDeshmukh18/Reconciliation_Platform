import { Link, NavLink } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  LayoutDashboard,
  AlertTriangle,
  FileText,
  ScrollText,
  ArrowLeftRight,
  Upload,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { queryKeys } from "@/lib/queryKeys";
import { reconciliationService } from "@/services/reconciliationService";
import { exceptionService } from "@/services/exceptionService";
import { transactionService } from "@/services/transactionService";

const navItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard", end: true },
  { to: "/upload", icon: Upload, label: "Upload Center" },
  { to: "/exceptions", icon: AlertTriangle, label: "Exceptions" },
  { to: "/transactions", icon: ArrowLeftRight, label: "Transactions" },
  { to: "/reports", icon: FileText, label: "Reports" },
  { to: "/audit", icon: ScrollText, label: "Audit Log" },
];

export function Sidebar() {
  const queryClient = useQueryClient();

  const prefetchRoute = (path: string) => {
    if (path === "/dashboard") {
      queryClient.prefetchQuery({
        queryKey: queryKeys.runs.list(1),
        queryFn: () => reconciliationService.listRuns(1, 10),
      });
    } else if (path === "/exceptions") {
      const filters = { page: 1, page_size: 25, recon_status: "flagged" as const };
      queryClient.prefetchQuery({
        queryKey: queryKeys.exceptions.list(filters as Record<string, unknown>),
        queryFn: () => exceptionService.list(filters),
      });
    } else if (path === "/transactions") {
      const filters = { page: 1, page_size: 25 };
      queryClient.prefetchQuery({
        queryKey: queryKeys.transactions.platform(filters as Record<string, unknown>),
        queryFn: () => transactionService.listPlatform(filters),
      });
    }
  };

  return (
    <aside className="fixed left-0 top-0 z-30 flex h-screen w-[var(--sidebar-width)] flex-col border-r border-border bg-surface">
      <Link to="/#hero" className="flex h-[var(--topbar-height)] items-center gap-2 border-b border-border px-5 hover:bg-surface-hover transition-colors">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
          <span className="text-accent font-bold text-sm">R</span>
        </div>
        <div>
          <p className="text-sm font-semibold leading-none">Recon</p>
          <p className="text-[10px] text-muted mt-0.5">Gap Detection</p>
        </div>
      </Link>

      <nav className="flex-1 space-y-1 p-3">
        {navItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onMouseEnter={() => prefetchRoute(to)}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-accent/10 text-accent"
                  : "text-muted hover:bg-surface-hover hover:text-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
