import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Button } from "@/components/ui/Button";
import { exceptionService } from "@/services/exceptionService";
import { getErrorMessage } from "@/services/api";
import { queryKeys } from "@/lib/queryKeys";
import { VALID_TRANSITIONS, type ExceptionDetail, type ReconStatus } from "@/types";
import { ReconStateMachine } from "./ReconStateMachine";

interface ResolutionFormProps {
  exception: ExceptionDetail;
}

export function ResolutionForm({ exception }: ResolutionFormProps) {
  const [note, setNote] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<ReconStatus | "">("");
  const queryClient = useQueryClient();

  const allowed = VALID_TRANSITIONS[exception.recon_status] ?? [];

  const updateMutation = useMutation({
    mutationFn: () =>
      exceptionService.updateStatus(exception.result_id, {
        new_status: selectedStatus as ReconStatus,
        note: note || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.exceptions.detail(exception.result_id),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.exceptions.all });
      toast.success("Status updated");
      setNote("");
      setSelectedStatus("");
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const suggestMutation = useMutation({
    mutationFn: () => exceptionService.suggestResolution(exception.result_id),
    onSuccess: (data) => {
      setNote(data.suggestion);
      toast.success("AI suggestion loaded");
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const noteMutation = useMutation({
    mutationFn: () =>
      exceptionService.addNote(exception.result_id, { note_text: note }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.exceptions.detail(exception.result_id),
      });
      toast.success("Note added");
      setNote("");
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  return (
    <div className="space-y-4">
      <ReconStateMachine
        currentStatus={exception.recon_status}
        allowedTransitions={allowed}
        selectedStatus={selectedStatus}
        onSelect={setSelectedStatus}
      />

      <div className="space-y-3">
        <label className="text-label block">Resolution Note</label>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={4}
          placeholder="Describe the resolution action taken..."
          className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm focus-ring resize-none"
        />
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => suggestMutation.mutate()}
            loading={suggestMutation.isPending}
          >
            Get AI Suggestion
          </Button>
        </div>
      </div>

      <div className="flex gap-2">
        {selectedStatus && (
          <Button
            onClick={() => updateMutation.mutate()}
            loading={updateMutation.isPending}
            disabled={!selectedStatus}
          >
            Update to {selectedStatus.replace("_", " ")}
          </Button>
        )}
        <Button
          variant="secondary"
          onClick={() => noteMutation.mutate()}
          loading={noteMutation.isPending}
          disabled={!note.trim()}
        >
          Add Note
        </Button>
      </div>

      {exception.resolution_notes.length > 0 && (
        <div className="space-y-2 pt-4 border-t border-border">
          <p className="text-label">Notes History</p>
          {exception.resolution_notes.map((n) => (
            <div
              key={n.note_id}
              className="rounded-md border border-border bg-surface-elevated p-3 text-sm"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium">{n.analyst_id}</span>
                {n.is_ai_suggested && (
                  <span className="text-[10px] text-accent bg-accent/10 px-1.5 py-0.5 rounded">
                    AI
                  </span>
                )}
              </div>
              <p className="text-muted">{n.note_text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
