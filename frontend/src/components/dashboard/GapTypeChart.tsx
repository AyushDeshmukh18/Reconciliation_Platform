import { useEffect, useRef } from "react";
import * as d3 from "d3";
import { Card } from "@/components/ui/Card";
import { GAP_TYPE_LABELS, type GapType } from "@/types";
import { getGapTypeColor } from "@/lib/utils";

interface GapTypeChartProps {
  breakdown: Record<string, { count: number; percentage: number }>;
}

export function GapTypeChart({ breakdown }: GapTypeChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  const data = Object.entries(breakdown)
    .map(([key, val]) => ({
      key: key as GapType,
      label: GAP_TYPE_LABELS[key as GapType] ?? key,
      count: val.count,
      percentage: val.percentage,
    }))
    .sort((a, b) => b.count - a.count);

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 280;
    const height = 280;
    const radius = Math.min(width, height) / 2 - 10;

    const g = svg
      .attr("viewBox", `0 0 ${width} ${height}`)
      .append("g")
      .attr("transform", `translate(${width / 2},${height / 2})`);

    const pie = d3
      .pie<(typeof data)[0]>()
      .value((d) => d.count)
      .sort(null);

    const arc = d3
      .arc<d3.PieArcDatum<(typeof data)[0]>>()
      .innerRadius(radius * 0.55)
      .outerRadius(radius)
      .cornerRadius(4)
      .padAngle(0.02);

    g.selectAll("path")
      .data(pie(data))
      .join("path")
      .attr("fill", (d) => getGapTypeColor(d.data.key))
      .attr("d", arc)
      .attr("opacity", 0.85)
      .style("transition", "opacity 0.2s")
      .on("mouseenter", function () {
        d3.select(this).attr("opacity", 1);
      })
      .on("mouseleave", function () {
        d3.select(this).attr("opacity", 0.85);
      });
  }, [data]);

  return (
    <Card title="Gap Type Distribution">
      {data.length === 0 ? (
        <p className="text-muted text-sm text-center py-8">No gap data yet</p>
      ) : (
        <div className="flex flex-col items-center gap-4">
          <svg ref={svgRef} className="w-full max-w-[280px]" />
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 w-full">
            {data.slice(0, 6).map((d) => (
              <div key={d.key} className="flex items-center gap-2 text-xs">
                <span
                  className="h-2 w-2 rounded-full shrink-0"
                  style={{ backgroundColor: getGapTypeColor(d.key) }}
                />
                <span className="text-muted truncate">{d.label}</span>
                <span className="ml-auto font-mono text-foreground">{d.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
