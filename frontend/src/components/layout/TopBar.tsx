import { useState } from "react";
import { Search, Bell } from "lucide-react";
import { CommandPalette } from "@/components/CommandPalette";
import { JobProgressPanel } from "@/components/dashboard/JobProgressPanel";

export function TopBar() {
  const [paletteOpen, setPaletteOpen] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-20 flex h-[var(--topbar-height)] items-center justify-between border-b border-border bg-canvas/80 backdrop-blur-md px-6">
        <button
          onClick={() => setPaletteOpen(true)}
          className="flex items-center gap-2 rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-muted hover:border-border hover:text-foreground transition-colors"
        >
          <Search className="h-4 w-4" />
          <span>Search...</span>
          <kbd className="ml-4 rounded border border-border bg-surface-elevated px-1.5 py-0.5 text-[10px] font-mono">
            ⌘K
          </kbd>
        </button>

        <div className="flex items-center gap-3">
          <JobProgressPanel />
          <button className="relative rounded-md p-2 text-muted hover:bg-surface-hover hover:text-foreground transition-colors">
            <Bell className="h-4 w-4" />
          </button>
        </div>
      </header>

      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </>
  );
}
