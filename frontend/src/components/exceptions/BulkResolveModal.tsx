import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import toast from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { exceptionService } from "@/services/exceptionService";
import { getErrorMessage } from "@/services/api";
import { queryKeys } from "@/lib/queryKeys";

interface BulkResolveModalProps {
  open: boolean;
  onClose: () => void;
  selectedIds: string[];
  onSuccess: () => void;
}

export function BulkResolveModal({
  open,
  onClose,
  selectedIds,
  onSuccess,
}: BulkResolveModalProps) {
  const [note, setNote] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () =>
      exceptionService.bulkResolve({
        result_ids: selectedIds,
        note_text: note,
        confirmation: confirmed,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.exceptions.all });
      toast.success(`Resolved ${data.resolved} exceptions`);
      onSuccess();
      onClose();
      setNote("");
      setConfirmed(false);
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface-elevated p-6 shadow-xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-heading">Bulk Resolve</h2>
              <button onClick={onClose} className="text-muted hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="text-sm text-muted mb-4">
              Resolve {selectedIds.length} selected exception
              {selectedIds.length !== 1 ? "s" : ""} as manually resolved.
            </p>

            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              placeholder="Resolution note (required)..."
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm focus-ring resize-none mb-4"
            />

            <label className="flex items-center gap-2 text-sm mb-6 cursor-pointer">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="rounded border-border"
              />
              I confirm this bulk resolution action
            </label>

            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button
                onClick={() => mutation.mutate()}
                loading={mutation.isPending}
                disabled={!note.trim() || !confirmed}
              >
                Resolve All
              </Button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
