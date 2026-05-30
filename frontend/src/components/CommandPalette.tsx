import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Command } from "cmdk";
import {
  LayoutDashboard,
  AlertTriangle,
  FileText,
  ScrollText,
  ArrowLeftRight,
  Upload,
} from "lucide-react";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const pages = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload Center", icon: Upload },
  { to: "/exceptions", label: "Exception Workbench", icon: AlertTriangle },
  { to: "/transactions", label: "Transactions", icon: ArrowLeftRight },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/audit", label: "Audit Log", icon: ScrollText },
];

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onOpenChange(!open);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      <div className="absolute left-1/2 top-[20%] w-full max-w-lg -translate-x-1/2">
        <Command
          className="rounded-lg border border-border bg-surface-elevated shadow-2xl overflow-hidden"
          loop
        >
          <Command.Input
            placeholder="Search pages..."
            className="w-full border-b border-border bg-transparent px-4 py-3 text-sm outline-none placeholder:text-muted"
          />
          <Command.List className="max-h-64 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-muted">
              No results found.
            </Command.Empty>
            <Command.Group heading="Navigation" className="text-label px-2 py-1.5">
              {pages.map(({ to, label, icon: Icon }) => (
                <Command.Item
                  key={to}
                  value={label}
                  onSelect={() => {
                    navigate(to);
                    onOpenChange(false);
                  }}
                  className="flex items-center gap-3 rounded-md px-3 py-2 text-sm cursor-pointer aria-selected:bg-accent/10 aria-selected:text-accent"
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
