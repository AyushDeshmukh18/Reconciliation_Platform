import { ArrowRight } from "lucide-react";
import { StateMachineBadge } from "./StateMachineBadge";
import { RECON_STATUS_LABELS, type ReconStatus } from "@/types";

const FLOW: ReconStatus[] = [
  "unprocessed",
  "flagged",
  "manually_resolved",
  "closed",
];

interface ReconStateMachineProps {
  currentStatus: ReconStatus | string;
  allowedTransitions: ReconStatus[];
  selectedStatus: ReconStatus | "";
  onSelect: (status: ReconStatus | "") => void;
}

export function ReconStateMachine({
  currentStatus,
  allowedTransitions,
  selectedStatus,
  onSelect,
}: ReconStateMachineProps) {
  return (
    <div className="space-y-3">
      <p className="text-label">Resolution Workflow</p>
      <div className="flex flex-wrap items-center gap-2">
        {FLOW.map((status, i) => {
          const isCurrent = status === currentStatus;
          const isAllowed = allowedTransitions.includes(status);
          const isSelected = status === selectedStatus;

          return (
            <div key={status} className="flex items-center gap-2">
              <StateMachineBadge
                status={status}
                active={isCurrent || isSelected}
                clickable={isAllowed && !isCurrent}
                onClick={() => {
                  if (isAllowed && !isCurrent) {
                    onSelect(isSelected ? "" : status);
                  }
                }}
              />
              {i < FLOW.length - 1 && (
                <ArrowRight className="h-3 w-3 text-muted shrink-0" />
              )}
            </div>
          );
        })}
      </div>
      <p className="text-caption">
        Current: {RECON_STATUS_LABELS[currentStatus as ReconStatus] ?? currentStatus}
        {allowedTransitions.length > 0 && (
          <> · Can transition to: {allowedTransitions.map((s) => RECON_STATUS_LABELS[s]).join(", ")}</>
        )}
      </p>
    </div>
  );
}
