import { useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  AlertTriangle,
  ArrowLeftRight,
  FileText,
  ScrollText,
  Upload,
  Menu,
  X,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

const navLinks = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload", icon: Upload },
  { to: "/exceptions", label: "Exceptions", icon: AlertTriangle },
  { to: "/transactions", label: "Transactions", icon: ArrowLeftRight },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/audit", label: "Audit Log", icon: ScrollText },
];

export function LandingNavbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const scrollToHero = () => {
    const heroElement = document.getElementById("hero");
    if (heroElement) {
      heroElement.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
    }
  };

  const handleHomeClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
    if (location.pathname === "/") {
      event.preventDefault();
      scrollToHero();
    }
  };

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <nav
          className={cn(
            "mt-4 flex items-center justify-between rounded-2xl border border-white/[0.08]",
            "bg-[#0a0e18]/80 px-4 py-2.5 shadow-[0_8px_32px_rgba(0,0,0,0.5)] backdrop-blur-xl",
            "sm:px-6"
          )}
        >
          <Link to="/#hero" onClick={handleHomeClick} className="flex items-center gap-2.5 group">
            <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-blue-600 shadow-[0_0_20px_rgba(59,130,246,0.35)]">
              <span className="font-mono text-sm font-bold text-white">R</span>
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-semibold tracking-tight text-foreground">ReconcileIQ</p>
              <p className="text-[10px] font-medium uppercase tracking-widest text-muted">Gap Intelligence</p>
            </div>
          </Link>

          <div className="hidden lg:flex items-center gap-0.5">
            {navLinks.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 rounded-lg px-3.5 py-2 text-[13px] font-medium transition-all duration-200",
                    isActive
                      ? "bg-accent/15 text-accent"
                      : "text-muted hover:bg-white/[0.04] hover:text-foreground"
                  )
                }
              >
                <Icon className="h-3.5 w-3.5 opacity-70" />
                {label}
              </NavLink>
            ))}
          </div>

          <div className="hidden lg:flex items-center gap-3">
            <Button onClick={() => navigate("/dashboard")} className="gap-1.5">
              Open Console
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          <button
            type="button"
            className="lg:hidden rounded-lg p-2 text-muted hover:bg-white/[0.06] hover:text-foreground"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </nav>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="lg:hidden mx-4 mt-2 rounded-2xl border border-white/[0.08] bg-[#0a0e18]/95 backdrop-blur-xl p-4 shadow-xl"
          >
            <div className="space-y-1">
              {navLinks.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted hover:bg-white/[0.04] hover:text-foreground"
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </NavLink>
              ))}
            </div>
            <div className="mt-4 flex flex-col gap-2 border-t border-white/[0.06] pt-4">
              <Button className="w-full" onClick={() => { setMobileOpen(false); navigate("/dashboard"); }}>
                Open Console
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
