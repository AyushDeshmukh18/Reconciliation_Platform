import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  action?: React.ReactNode;
}

export function Card({ children, className, title, action }: CardProps) {
  return (
    <div className={cn("glass-panel", className)}>
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          {title && <h3 className="text-subheading">{title}</h3>}
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}
