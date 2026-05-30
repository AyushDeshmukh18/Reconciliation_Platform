import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Shield,
  Zap,
  BarChart3,
  GitMerge,
  CheckCircle2,
  TrendingUp,
  Lock,
  Globe,
} from "lucide-react";
import { LandingNavbar } from "@/components/layout/LandingNavbar";
import { StatsMarquee } from "@/components/landing/StatsMarquee";
import { Button } from "@/components/ui/Button";
import { cn, formatCurrency } from "@/lib/utils";

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
};

const logos = ["Stripe Atlas", "Razorpay", "PayU", "NPCI UPI", "Visa Direct"];

const features = [
  {
    icon: GitMerge,
    title: "Multi-pass reconciliation",
    description: "Exact, fuzzy, and composite matching across platform and bank ledgers with tiered tolerance bands.",
  },
  {
    icon: Zap,
    title: "Real-time gap classification",
    description: "Eleven production gap classifiers with confidence scoring and rule evaluation traces.",
  },
  {
    icon: Shield,
    title: "Immutable audit trail",
    description: "Append-only event log with correlation IDs — built for regulatory and SOC2 workflows.",
  },
  {
    icon: BarChart3,
    title: "Analyst workbench",
    description: "Exception queue, bulk resolve, AI-assisted resolution notes, and state-machine enforcement.",
  },
];

function HeroMockup() {
  return (
    <div className="relative">
      <div className="absolute -inset-4 rounded-3xl bg-gradient-to-r from-accent/20 via-transparent to-emerald-500/10 blur-3xl" />
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.7, delay: 0.2 }}
        className="relative overflow-hidden rounded-2xl border border-white/[0.1] bg-[#0c1018]/90 shadow-[0_24px_80px_rgba(0,0,0,0.5)]"
      >
        <div className="flex items-center gap-2 border-b border-white/[0.06] bg-[#080b12] px-4 py-3">
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
          </div>
          <span className="ml-2 font-mono text-[11px] text-muted">reconcile.run / May 2024 batch</span>
        </div>

        <div className="grid grid-cols-3 gap-px bg-white/[0.04] p-px">
          {[
            { label: "Matched", value: "9,842", color: "text-emerald-400", pct: "94.2%" },
            { label: "Flagged", value: "87", color: "text-red-400", pct: "0.8%" },
            { label: "Exposure", value: formatCurrency(42381200, "INR"), color: "text-amber-400", pct: "INR" },
          ].map((m) => (
            <div key={m.label} className="bg-[#0c1018] px-4 py-4">
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted">{m.label}</p>
              <p className={cn("mt-1 font-mono text-lg font-semibold", m.color)}>{m.value}</p>
              <p className="text-[10px] text-muted-subtle">{m.pct}</p>
            </div>
          ))}
        </div>

        <div className="space-y-2 p-4">
          {[
            { type: "Status Mismatch", conf: 99, amt: "₹1,24,500", status: "flagged" },
            { type: "Timing Gap", conf: 95, amt: "₹48,200", status: "open" },
            { type: "Partial Settlement", conf: 92, amt: "₹2,10,000", status: "review" },
          ].map((row, i) => (
            <motion.div
              key={row.type}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + i * 0.1 }}
              className="flex items-center justify-between rounded-lg border border-white/[0.05] bg-white/[0.02] px-3 py-2.5"
            >
              <div className="flex items-center gap-3">
                <div className="h-8 w-1 rounded-full bg-accent" />
                <div>
                  <p className="text-xs font-medium">{row.type}</p>
                  <p className="font-mono text-[11px] text-muted">{row.amt}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="hidden sm:block">
                  <div className="h-1 w-16 overflow-hidden rounded-full bg-white/[0.06]">
                    <div className="h-full rounded-full bg-emerald-500" style={{ width: `${row.conf}%` }} />
                  </div>
                  <p className="mt-0.5 text-right font-mono text-[10px] text-muted">{row.conf}%</p>
                </div>
                <span className="rounded-full border border-red-500/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-red-400">
                  {row.status}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -right-4 top-8 hidden rounded-xl border border-emerald-500/20 bg-[#0c1018]/95 px-4 py-3 shadow-xl backdrop-blur sm:block"
      >
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span className="text-xs font-medium">Run completed · 67s</span>
        </div>
      </motion.div>

      <motion.div
        animate={{ y: [0, 6, 0] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        className="absolute -left-4 bottom-12 hidden rounded-xl border border-accent/20 bg-[#0c1018]/95 px-4 py-3 shadow-xl backdrop-blur sm:block"
      >
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-accent" />
          <span className="font-mono text-xs">+12.3% match rate</span>
        </div>
      </motion.div>
    </div>
  );
}

export function Landing() {
  return (
    <div className="min-h-screen bg-[#060810] text-foreground overflow-x-hidden">
      <div className="landing-grid pointer-events-none fixed inset-0 opacity-[0.35]" />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.18),transparent)]" />
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_60%_40%_at_100%_0%,rgba(16,185,129,0.06),transparent)]" />

      <LandingNavbar />

      {/* Hero */}
      <section id="hero" className="relative pt-32 pb-20 sm:pt-40 sm:pb-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid items-center gap-16 lg:grid-cols-2 lg:gap-12">
            <div>
              <motion.div
                {...fadeUp}
                transition={{ duration: 0.5 }}
                className="inline-flex items-center gap-2 rounded-full border border-accent/25 bg-accent/10 px-3 py-1 text-[11px] font-medium uppercase tracking-widest text-accent"
              >
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-60" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-accent" />
                </span>
                Enterprise reconciliation platform
              </motion.div>

              <motion.h1
                {...fadeUp}
                transition={{ duration: 0.5, delay: 0.08 }}
                className="mt-6 text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl lg:text-[3.25rem]"
              >
                Close every payment gap
                <span className="block bg-gradient-to-r from-white via-white to-white/50 bg-clip-text text-transparent">
                  before it becomes exposure.
                </span>
              </motion.h1>

              <motion.p
                {...fadeUp}
                transition={{ duration: 0.5, delay: 0.16 }}
                className="mt-6 max-w-lg text-base leading-relaxed text-muted sm:text-lg"
              >
                ReconcileIQ ingests platform and bank settlement files, runs multi-pass matching,
                classifies eleven gap types, and gives your ops team a production workbench to
                resolve exceptions — with a full immutable audit trail.
              </motion.p>

              <motion.div
                {...fadeUp}
                transition={{ duration: 0.5, delay: 0.24 }}
                className="mt-10 flex flex-wrap items-center gap-4"
              >
                <Link to="/dashboard">
                  <Button size="lg" className="gap-2 px-6 shadow-[0_0_30px_rgba(59,130,246,0.25)]">
                    Start reconciling
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link to="/exceptions">
                  <Button variant="ghost" size="lg" className="gap-2 border border-white/[0.08]">
                    View live exceptions
                  </Button>
                </Link>
              </motion.div>

              <motion.div
                {...fadeUp}
                transition={{ duration: 0.5, delay: 0.32 }}
                className="mt-12 flex flex-wrap items-center gap-6 border-t border-white/[0.06] pt-8"
              >
                <div className="flex items-center gap-2 text-xs text-muted">
                  <Lock className="h-3.5 w-3.5" />
                  SOC2-ready audit
                </div>
                <div className="flex items-center gap-2 text-xs text-muted">
                  <Globe className="h-3.5 w-3.5" />
                  INR-native · minor units
                </div>
                <div className="flex items-center gap-2 text-xs text-muted">
                  <Zap className="h-3.5 w-3.5" />
                  SSE live job progress
                </div>
              </motion.div>
            </div>

            <HeroMockup />
          </div>
        </div>
      </section>

      <StatsMarquee />

      {/* Trusted by */}
      <section className="py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <p className="text-center text-[11px] font-medium uppercase tracking-[0.2em] text-muted">
            Built for payment ops teams at scale
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-x-12 gap-y-4 opacity-40">
            {logos.map((name) => (
              <span key={name} className="text-sm font-medium tracking-wide text-foreground">
                {name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 sm:py-28">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Everything ops needs to trust the numbers
            </h2>
            <p className="mt-4 text-muted">
              From ingestion to exception resolution — one platform, zero spreadsheet drift.
            </p>
          </div>
          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="group rounded-2xl border border-white/[0.06] bg-[#0c1018]/80 p-6 transition-colors hover:border-accent/20 hover:bg-[#0c1018]"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/10 text-accent transition-colors group-hover:bg-accent/20">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 text-base font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{f.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="pb-24">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="relative overflow-hidden rounded-3xl border border-accent/20 bg-gradient-to-br from-accent/10 via-[#0c1018] to-[#0c1018] px-8 py-16 text-center sm:px-16">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(59,130,246,0.15),transparent_60%)]" />
            <div className="relative">
              <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                Ready to eliminate reconciliation blind spots?
              </h2>
              <p className="mx-auto mt-4 max-w-md text-muted">
                Upload platform and bank files, trigger a run, and review flagged gaps in minutes.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-4">
                <Link to="/login">
                  <Button size="lg">Get started free</Button>
                </Link>
                <Link to="/exceptions">
                  <Button variant="ghost" size="lg" className="border border-white/[0.1]">
                    Browse exceptions
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] py-10">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6 lg:px-8">
          <p className="text-sm text-muted">© 2024 ReconcileIQ · Payments gap detection</p>
          <div className="flex gap-6 text-sm text-muted">
            <Link to="/audit" className="hover:text-foreground transition-colors">Audit Log</Link>
            <Link to="/reports" className="hover:text-foreground transition-colors">Reports</Link>
            <Link to="/dashboard" className="hover:text-foreground transition-colors">Dashboard</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
