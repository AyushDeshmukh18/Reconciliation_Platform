import { Card } from "@/components/ui/Card";
import { ProgressRing } from "@/components/ui/ProgressRing";

interface MatchRateGaugeProps {
  matched: number;
  total: number;
}

export function MatchRateGauge({ matched, total }: MatchRateGaugeProps) {
  const rate = total > 0 ? (matched / total) * 100 : 0;

  return (
    <Card title="Match Rate">
      <div className="flex flex-col items-center py-4">
        <ProgressRing value={rate} size={120} strokeWidth={8} label="matched" />
        <div className="mt-4 flex gap-6 text-center">
          <div>
            <p className="text-2xl font-semibold text-success">{matched.toLocaleString()}</p>
            <p className="text-caption">Matched</p>
          </div>
          <div>
            <p className="text-2xl font-semibold">{total.toLocaleString()}</p>
            <p className="text-caption">Total</p>
          </div>
        </div>
      </div>
    </Card>
  );
}
