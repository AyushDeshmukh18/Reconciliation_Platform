const stats = [
  { value: "11", suffix: "", label: "Gap types detected" },
  { value: "99.2", suffix: "%", label: "Avg. match rate" },
  { value: "10M+", suffix: "", label: "Daily tx volume" },
  { value: "7", suffix: " yrs", label: "Audit retention" },
  { value: "<50ms", suffix: "", label: "Rule evaluation" },
  { value: "3-pass", suffix: "", label: "Matching engine" },
  { value: "100MB", suffix: "", label: "Max file size" },
  { value: "INR", suffix: "", label: "Native currency" },
];

function StatItem({ value, suffix, label }: (typeof stats)[0]) {
  return (
    <div className="flex shrink-0 items-center gap-4 px-8">
      <div className="flex items-baseline gap-0.5">
        <span className="font-mono text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          {value}
        </span>
        {suffix && <span className="font-mono text-lg font-medium text-accent">{suffix}</span>}
      </div>
      <span className="whitespace-nowrap text-sm text-muted">{label}</span>
      <span className="h-1 w-1 shrink-0 rounded-full bg-white/20" aria-hidden />
    </div>
  );
}

export function StatsMarquee() {
  const track = [...stats, ...stats];

  return (
    <section className="relative border-y border-white/[0.06] bg-[#0a0e18]/80 py-5 overflow-hidden">
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-24 bg-gradient-to-r from-[#0a0e18] to-transparent sm:w-32" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-24 bg-gradient-to-l from-[#0a0e18] to-transparent sm:w-32" />

      <div className="marquee-track flex w-max items-center">
        {track.map((s, i) => (
          <StatItem key={`${s.label}-${i}`} {...s} />
        ))}
      </div>
    </section>
  );
}
