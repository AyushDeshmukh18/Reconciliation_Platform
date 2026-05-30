import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { auditService } from "@/services/auditService";
import { queryKeys } from "@/lib/queryKeys";
import { DataTable } from "@/components/ui/DataTable";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { formatDate, truncateId } from "@/lib/utils";

export function AuditLog() {
  const [eventType, setEventType] = useState("");
  const [actor, setActor] = useState("");
  const [page, setPage] = useState(1);

  const filters = { event_type: eventType || undefined, actor: actor || undefined, page, page_size: 50 };

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.audit.list(filters as Record<string, unknown>),
    queryFn: () => auditService.list(filters),
  });

  const auditSummary = useMemo(() => {
    const events = data ?? [];
    const actors = new Set(events.map((entry) => entry.actor));
    const latest = events.length
      ? events.reduce((prev, next) => {
          return new Date(prev.created_at_utc) > new Date(next.created_at_utc) ? prev : next;
        })
      : null;

    return {
      total: events.length,
      actors: actors.size,
      latest,
    };
  }, [data]);

  const eventVariant = (eventType: string) => {
    if (eventType.includes("ERROR") || eventType.includes("FAIL")) return "danger";
    if (eventType.includes("LOGIN") || eventType.includes("COMPLETE") || eventType.includes("RESOLVE")) return "success";
    if (eventType.includes("UPLOAD") || eventType.includes("START") || eventType.includes("GENERATE")) return "accent";
    return "default";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-display">Audit Log</h1>
        <p className="text-muted text-sm mt-1">
          Immutable record of all system events
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="p-4">
          <p className="text-sm text-muted uppercase tracking-wide">Events</p>
          <p className="text-3xl font-semibold">{auditSummary.total}</p>
          <p className="text-sm text-muted mt-2">Showing current page results</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-muted uppercase tracking-wide">Actors</p>
          <p className="text-3xl font-semibold">{auditSummary.actors}</p>
          <p className="text-sm text-muted mt-2">Unique actors in view</p>
        </Card>
        <Card className="p-4 md:col-span-2">
          <p className="text-sm text-muted uppercase tracking-wide">Latest event</p>
          {auditSummary.latest ? (
            <div className="mt-3 space-y-1">
              <p className="font-medium">{auditSummary.latest.event_type}</p>
              <p className="text-sm text-muted">{formatDate(auditSummary.latest.created_at_utc)}</p>
              <p className="text-sm">Actor: {auditSummary.latest.actor}</p>
            </div>
          ) : (
            <p className="text-sm text-muted">No recent activity</p>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input
          label="Event Type"
          placeholder="e.g. USER_LOGIN"
          value={eventType}
          onChange={(e) => {
            setEventType(e.target.value);
            setPage(1);
          }}
        />
        <Input
          label="Actor"
          placeholder="username"
          value={actor}
          onChange={(e) => {
            setActor(e.target.value);
            setPage(1);
          }}
        />
      </div>

      <DataTable
        data={data ?? []}
        loading={isLoading}
        keyExtractor={(r) => r.event_id}
        columns={[
          {
            key: "event_type",
            header: "Event",
            render: (r) => (
              <Badge variant={eventVariant(r.event_type)}>{r.event_type}</Badge>
            ),
          },
          {
            key: "entity",
            header: "Entity",
            render: (r) => (
              <div>
                <Badge variant="default" className="mb-1">{r.entity_type}</Badge>
                <p className="font-mono text-xs">{truncateId(r.entity_id, 12)}</p>
              </div>
            ),
          },
          {
            key: "actor",
            header: "Actor",
            render: (r) => (
              <div className="space-y-1">
                <p className="font-medium">{r.actor}</p>
                {r.file_hash && <span className="text-xs text-muted">{r.file_hash}</span>}
              </div>
            ),
          },
          {
            key: "created_at",
            header: "Timestamp",
            render: (r) => formatDate(r.created_at_utc),
          },
          {
            key: "correlation_id",
            header: "Correlation",
            render: (r) => (
              <span className="font-mono text-xs text-muted">
                {truncateId(r.correlation_id, 8)}
              </span>
            ),
          },
        ]}
      />

      <div className="flex justify-center gap-2">
        <button
          disabled={page <= 1}
          onClick={() => setPage((p) => p - 1)}
          className="text-sm text-muted hover:text-foreground disabled:opacity-40"
        >
          Previous
        </button>
        <span className="text-sm text-muted">Page {page}</span>
        <button
          disabled={(data?.length ?? 0) < 50}
          onClick={() => setPage((p) => p + 1)}
          className="text-sm text-muted hover:text-foreground disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  );
}
