import { useEffect, useRef } from "react";
import * as d3 from "d3";
import { Card } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/utils";
import { GAP_TYPE_LABELS, type GapType } from "@/types";
import { getGapTypeColor } from "@/lib/utils";

interface MonetaryExposureChartProps {
  breakdown: Record<string, { monetary_exposure_minor_units: number }>;
}

export function MonetaryExposureChart({ breakdown }: MonetaryExposureChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  const data = Object.entries(breakdown)
    .map(([key, val]) => ({
      key: key as GapType,
      label: GAP_TYPE_LABELS[key as GapType] ?? key,
      exposure: val.monetary_exposure_minor_units,
    }))
    .filter((d) => d.exposure > 0)
    .sort((a, b) => b.exposure - a.exposure)
    .slice(0, 8);

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const margin = { top: 8, right: 8, bottom: 8, left: 120 };
    const width = 400 - margin.left - margin.right;
    const height = data.length * 32 + margin.top + margin.bottom;

    const g = svg
      .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height}`)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d.exposure) ?? 1])
      .range([0, width]);

    const y = d3
      .scaleBand()
      .domain(data.map((d) => d.label))
      .range([0, data.length * 32])
      .padding(0.2);

    g.selectAll("rect")
      .data(data)
      .join("rect")
      .attr("x", 0)
      .attr("y", (d) => y(d.label) ?? 0)
      .attr("width", (d) => x(d.exposure))
      .attr("height", y.bandwidth())
      .attr("rx", 4)
      .attr("fill", (d) => getGapTypeColor(d.key))
      .attr("opacity", 0.85);

    g.selectAll("text.label")
      .data(data)
      .join("text")
      .attr("class", "label")
      .attr("x", -8)
      .attr("y", (d) => (y(d.label) ?? 0) + y.bandwidth() / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", "end")
      .attr("fill", "#94a3b8")
      .attr("font-size", "11px")
      .text((d) => d.label);
  }, [data]);

  return (
    <Card title="Monetary Exposure by Gap Type">
      {data.length === 0 ? (
        <p className="text-muted text-sm text-center py-8">No exposure data</p>
      ) : (
        <div className="space-y-2">
          <svg ref={svgRef} className="w-full" />
          <p className="text-caption text-right">
            Total:{" "}
            {formatCurrency(data.reduce((s, d) => s + d.exposure, 0))}
          </p>
        </div>
      )}
    </Card>
  );
}
