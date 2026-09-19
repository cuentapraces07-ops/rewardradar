"use client";

import {
  AlertTriangle,
  ArrowRight,
  Bot,
  Check,
  ChevronRight,
  CircleDollarSign,
  Clock3,
  Code2,
  ExternalLink,
  Filter,
  GitBranch,
  Radar,
  RefreshCw,
  Server,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type Verdict = "pursue" | "watch" | "avoid";

type Opportunity = {
  id: number;
  source: string;
  title: string;
  kind: string;
  payout: number;
  probability: number;
  hours: number;
  confidence: number;
  competition: string;
  deadline: string;
  verdict: Verdict;
  reason: string;
  url: string;
  signals: string[];
};

const opportunities: Opportunity[] = [
  {
    id: 1,
    source: "Devpost",
    title: "Agents for Humans — Professional Agents",
    kind: "Hackathon",
    payout: 5000,
    probability: 8,
    hours: 34,
    confidence: 84,
    competition: "High",
    deadline: "Sep 14",
    verdict: "pursue",
    reason: "Cash prize, open eligibility and a product already grounded in verified market evidence.",
    url: "https://agentsforhumans.devpost.com/",
    signals: ["Cash payout", "$2k floor for podium", "Deadline Sep 14", "Build in progress"],
  },
  {
    id: 2,
    source: "Execution Market",
    title: "Published microtask inventory",
    kind: "Agent tasks",
    payout: 1.78,
    probability: 72,
    hours: 2.5,
    confidence: 84,
    competition: "Low",
    deadline: "Open",
    verdict: "avoid",
    reason: "Payment rail is concrete, but the entire current inventory is below the $100 objective.",
    url: "https://execution.market/",
    signals: ["26 live tasks at capture", "USDC on-chain rail", "Escrow references", "Insufficient upside"],
  },
  {
    id: 3,
    source: "Opire",
    title: "Godot issue #70796",
    kind: "Code bounty",
    payout: 3280,
    probability: 1,
    hours: 45,
    confidence: 64,
    competition: "10 claimers",
    deadline: "No deadline",
    verdict: "avoid",
    reason: "The issue is locked and crowded; the headline value overstates the practical chance of payment.",
    url: "https://github.com/godotengine/godot/issues/70796",
    signals: ["Locked issue", "10 claimers", "Long-running", "No escrow guarantee"],
  },
  {
    id: 4,
    source: "Opire",
    title: "Udio API wrapper issue #7",
    kind: "Code bounty",
    payout: 120,
    probability: 3,
    hours: 12,
    confidence: 64,
    competition: "13 claimers",
    deadline: "No deadline",
    verdict: "avoid",
    reason: "Thirteen people are already trying; expected return per hour falls below the guardrail.",
    url: "https://github.com/flowese/UdioWrapper/issues/7",
    signals: ["13 claimers", "Small repository", "Unclear acceptance", "No escrow guarantee"],
  },
  {
    id: 5,
    source: "Algora census",
    title: "Open GitHub bounty inventory",
    kind: "Code bounty",
    payout: 0,
    probability: 10,
    hours: 4,
    confidence: 64,
    competition: "Unknown",
    deadline: "Open",
    verdict: "watch",
    reason: "Only one plausibly open item remained after stale and already-awarded labels were removed.",
    url: "https://github.com/AsherKasper/bounty-census",
    signals: ["1 plausible item", "Amount unknown", "Labels are noisy", "Needs sponsor check"],
  },
  {
    id: 6,
    source: "Superteam Earn",
    title: "Steve Agent Arena — highest individual prize",
    kind: "Agent competition",
    payout: 250,
    probability: 3,
    hours: 12,
    confidence: 74,
    competition: "10 submissions",
    deadline: "Sep 19*",
    verdict: "avoid",
    reason: "The listing is open and agent-eligible, but payout is sponsor-direct, the sponsor is not marked verified, and qualification requires capital at risk plus a public X post.",
    url: "https://superteam.fun/earn/listing/steve-agent-arena-launch-your-agent-and-win-500-usdc",
    signals: ["Sponsor not verified", "5 mainnet trades + public X", "Agents explicitly allowed", "$100 third-place floor"],
  },
];

const agents = [
  { name: "Scout", icon: Radar, text: "Finds reward inventory", status: "Sep 10 capture" },
  { name: "Verifier", icon: ShieldCheck, text: "Checks the source of truth", status: "Recorded checks" },
  { name: "Risk", icon: AlertTriangle, text: "Flags manipulation & friction", status: "Social + capital gates" },
  { name: "ROI", icon: TrendingUp, text: "Ranks expected value", status: "1 pursue" },
];

const alexaTurns = [
  {
    prompt: "Which opportunity is worth my next two hours?",
    tool: "search_rewards",
    response: "The strongest match has the best payment-adjusted hourly return. I checked source state, competition, and payment signals before recommending it.",
    evidence: "fixture replay · ranking by expected hourly value",
  },
  {
    prompt: "Is that money actually funded?",
    tool: "verify_funding",
    response: "I will not treat it as income. The evidence separates escrow, verified sponsor, and payout rail; if a signal is missing, I say so.",
    evidence: "escrow + sponsor + payout rail · no guarantees",
  },
  {
    prompt: "Has my Alexa+ project been submitted?",
    tool: "summarize_submission_status",
    response: "Honest status: local prototype; registration and external submission require owner confirmation; no payout has been awarded.",
    evidence: "owner confirmation required · payout not awarded",
  },
  {
    prompt: "Plan a $100-plus opportunity I can finish in 40 hours.",
    tool: "plan_pursuit",
    response: "I can prepare a bounded pursuit brief, but I will not submit work, contact a sponsor, spend money, or claim a payout without the owner's confirmation.",
    evidence: "minimum_payout_usd: 100 · max_hours: 40 · read-only plan",
  },
];

const verdictStyles: Record<Verdict, string> = {
  pursue: "bg-[#d8f6df] text-[#12622f] border-[#a8dfb5]",
  watch: "bg-[#fff1cd] text-[#7a4a00] border-[#efd28a]",
  avoid: "bg-[#ffe0db] text-[#972c22] border-[#efb1a8]",
};

function money(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: value < 10 ? 2 : 0,
  }).format(value);
}

function expectedValue(item: Opportunity) {
  return item.payout * (item.probability / 100);
}

export default function Home() {
  const [selectedId, setSelectedId] = useState(1);
  const [filter, setFilter] = useState<"all" | Verdict>("all");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(100);
  const [alexaTurn, setAlexaTurn] = useState(0);

  const selected = opportunities.find((item) => item.id === selectedId) ?? opportunities[0];
  const visible = useMemo(
    () => opportunities.filter((item) => filter === "all" || item.verdict === filter),
    [filter],
  );

  const startReplay = () => {
    setProgress(12);
    setRunning(true);
  };

  useEffect(() => {
    if (!running) return;
    const checkpoints = [31, 58, 79, 100];
    const timers = checkpoints.map((next, index) =>
      window.setTimeout(() => {
        setProgress(next);
        if (next === 100) {
          setRunning(false);
        }
      }, 430 * (index + 1)),
    );
    return () => timers.forEach(window.clearTimeout);
  }, [running]);

  return (
    <main className="min-h-screen bg-[#f3f0e9] text-[#18211f]">
      <header className="sticky top-0 z-40 border-b border-[#d9d6cf] bg-[#f8f6f1]/95 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-5 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center bg-[#ff5d24] text-white shadow-[3px_3px_0_#192824]">
              <Radar size={20} strokeWidth={2.5} />
            </div>
            <div>
              <p className="font-display text-lg font-bold leading-none tracking-[-0.03em]">RewardRadar</p>
              <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#68736e]">Strands agent system</p>
            </div>
          </div>
          <div className="hidden items-center gap-7 text-xs font-semibold text-[#5d6864] md:flex">
            <span className="flex items-center gap-2"><span className="h-2 w-2 bg-[#32a852]" />Captured sources</span>
            <span>Snapshot ledger</span>
            <span>Guardrails</span>
            <a className="flex items-center gap-1 hover:text-[#ff5d24]" href="https://github.com/cuentapraces07-ops/rewardradar" target="_blank" rel="noreferrer">
              <GitBranch size={15} /> Source <ExternalLink size={12} />
            </a>
          </div>
          <button
            type="button"
            disabled={running}
            onClick={startReplay}
            className="flex items-center gap-2 border border-[#18211f] bg-[#18211f] px-4 py-2.5 text-xs font-bold text-white shadow-[3px_3px_0_#ff5d24] transition hover:-translate-y-0.5 disabled:cursor-wait disabled:opacity-70"
          >
            <RefreshCw size={14} className={running ? "animate-spin" : ""} />
            {running ? "Replaying saved trace…" : "Replay saved trace"}
          </button>
        </div>
        {running && <div className="h-0.5 bg-[#dedad0]"><div className="h-full bg-[#ff5d24] transition-all duration-500" style={{ width: `${progress}%` }} /></div>}
      </header>

      <div className="mx-auto max-w-[1500px] px-5 py-6 lg:px-8">
        <section className="mb-6 grid gap-5 xl:grid-cols-[1.45fr_.85fr]">
          <div className="relative overflow-hidden border border-[#cfcac0] bg-[#132c27] p-7 text-white shadow-[6px_6px_0_#c8c2b6] md:p-9">
            <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full border-[38px] border-[#1d4038]" />
            <div className="relative max-w-3xl">
              <div className="mb-7 flex flex-wrap items-center gap-3">
                <span className="border border-[#6f8a83] bg-[#1d4038] px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#cde8df]">Evidence snapshot · Sep 10, 2026</span>
                <span className="text-xs text-[#b9ccc6]">Static snapshot · no live refresh</span>
              </div>
              <h1 className="font-display text-[clamp(2.25rem,5vw,5rem)] font-black leading-[.91] tracking-[-0.055em]">
                Don’t chase the<br /><span className="text-[#ff7a45]">headline payout.</span>
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-7 text-[#c8d8d3] md:text-lg">
                Four cooperating agents separate payable opportunities from stale issues, manipulated totals and expensive dead ends—then rank the work by expected return.
              </p>
            </div>
          </div>

          <aside className="border border-[#cfcac0] bg-[#fffdf8] p-6 shadow-[6px_6px_0_#dfd9cc]">
            <div className="flex items-start justify-between">
              <div>
                <p className="label">Current mission</p>
                <h2 className="mt-2 font-display text-3xl font-black tracking-[-0.04em]">$100 cash floor</h2>
              </div>
              <Target className="text-[#ff5d24]" size={30} />
            </div>
            <div className="mt-7 border-y border-[#ded9cf] py-5">
              <div className="flex items-end justify-between">
                <span className="text-sm font-semibold text-[#59655f]">Best qualified upside</span>
                <span className="font-mono text-3xl font-bold">$5,000</span>
              </div>
              <div className="mt-3 border-l-4 border-[#ff5d24] bg-[#f2efe8] px-3 py-2 text-[11px] font-semibold text-[#59655f]">
                3 PUBLICATION GATES REMAIN: HOSTED DEMO · AWS · DEVPOST
              </div>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="bg-[#edf5ef] p-4"><p className="label">Floor prize</p><p className="mt-2 font-mono text-xl font-bold">$2,000</p></div>
              <div className="bg-[#fff0e8] p-4"><p className="label">Deadline</p><p className="mt-2 font-mono text-xl font-bold">SEP 14</p></div>
            </div>
          </aside>
        </section>

        <section className="mb-6 grid grid-cols-2 border border-[#cfcac0] bg-[#fffdf8] shadow-[4px_4px_0_#ded8cc] lg:grid-cols-4">
          {[
            ["Opire advertised", "30", "$518K displayed total", CircleDollarSign],
            ["Canonical open", "8", "22 eliminated", ShieldCheck],
            ["Agent-eligible", "1", "Superteam · 10 submissions", Target],
            ["Microtask inventory", "$1.78", "Execution · 26 rows", Zap],
          ].map(([label, value, note, Icon], index) => {
            const MetricIcon = Icon as typeof CircleDollarSign;
            return (
              <div key={String(label)} className={`p-5 md:p-6 ${index < 3 ? "border-r border-[#ded9cf]" : ""} ${index === 1 ? "max-lg:border-r-0" : ""} ${index < 2 ? "max-lg:border-b" : ""}`}>
                <div className="flex items-center justify-between"><p className="label">{String(label)}</p><MetricIcon size={17} className="text-[#7d8781]" /></div>
                <p className="mt-3 font-mono text-3xl font-bold tracking-[-0.04em]">{String(value)}</p>
                <p className="mt-1 text-xs font-medium text-[#737d78]">{String(note)}</p>
              </div>
            );
          })}
        </section>

        <section className="mb-6 border border-[#cfcac0] bg-[#fffdf8] p-5 shadow-[4px_4px_0_#ded8cc] md:p-6">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
            <div><p className="label">Decision engine</p><h2 className="mt-1 font-display text-2xl font-black tracking-[-0.035em]">Four recorded stages, one inspectable ranking</h2></div>
            <div className="flex items-center gap-2 text-xs font-semibold text-[#5f6a65]"><Sparkles size={15} className="text-[#ff5d24]" />Recorded Strands GraphBuilder run</div>
          </div>
          <div className="grid gap-2 lg:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] lg:items-stretch">
            {agents.map((agent, index) => (
              <div className="contents" key={agent.name}>
                <div className="group border border-[#d8d2c8] bg-[#f5f2eb] p-4 transition hover:border-[#ff5d24] hover:bg-[#fff8f4]">
                  <div className="flex items-center justify-between"><div className="grid h-9 w-9 place-items-center bg-[#18211f] text-white"><agent.icon size={18} /></div><span className="font-mono text-xs font-bold text-[#ff5d24]">0{index + 1}</span></div>
                  <h3 className="mt-5 font-display text-lg font-black">{agent.name}</h3>
                  <p className="mt-1 text-xs leading-5 text-[#6a746f]">{agent.text}</p>
                  <p className="mt-4 border-t border-[#ddd8ce] pt-3 font-mono text-xs font-bold">{agent.status}</p>
                </div>
                {index < agents.length - 1 && <div className="hidden items-center px-1 text-[#9b9e96] lg:flex"><ArrowRight size={18} /></div>}
              </div>
            ))}
          </div>
        </section>

        <section className="mb-6 grid gap-5 border border-[#cfcac0] bg-[#fffdf8] p-5 shadow-[4px_4px_0_#ded8cc] md:p-6 xl:grid-cols-[.92fr_1.08fr]">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[.15em] text-[#ff5d24]"><Bot size={16} />Alexa+ simulated experience</div>
            <h2 className="mt-2 font-display text-2xl font-black tracking-[-0.035em]">Ask once. Hear the evidence.</h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-[#65716b]">This local replay shows how an Alexa+-style client calls RewardRadar’s self-hosted MCP endpoint. The response never turns an advertised amount into a promised payout.</p>
            <div className="mt-5 flex flex-wrap items-center gap-2 text-[10px] font-bold uppercase tracking-[.12em] text-[#69736e]"><span className="flex items-center gap-1 border border-[#d5d0c7] bg-[#f2efe8] px-2 py-1"><Server size={13} /> POST /mcp</span><span className="border border-[#d5d0c7] bg-[#f2efe8] px-2 py-1">MCP 2025-11-25</span><span className="border border-[#a8dfb5] bg-[#edf8ef] px-2 py-1 text-[#12622f]">Fixture only</span></div>
            <button type="button" onClick={() => setAlexaTurn((current) => (current + 1) % alexaTurns.length)} className="mt-6 flex items-center gap-2 border border-[#18211f] bg-[#18211f] px-4 py-2.5 text-xs font-bold text-white shadow-[3px_3px_0_#ff5d24] transition hover:-translate-y-0.5"><Sparkles size={14} />Replay next voice turn</button>
            <figure className="mt-6 border border-[#d5d0c7] bg-[#f2efe8] p-3"><video className="aspect-video w-full bg-[#18211f]" controls preload="metadata" aria-label="RewardRadar Alexa Plus demonstration video"><source src="media/AlexaPlus-demo-v0.2.mp4" type="video/mp4" />Your browser does not support the demo video.</video><figcaption className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[10px] font-bold uppercase tracking-[.1em] text-[#69736e]"><span>94.89 s · male narration</span><span>local fixture · no payout claim</span></figcaption></figure>
          </div>
          <div className="border border-[#d5d0c7] bg-[#132c27] p-4 text-white md:p-5">
            <div className="flex items-center justify-between border-b border-[#355149] pb-3"><span className="text-[10px] font-bold uppercase tracking-[.14em] text-[#9db0aa]">Turn 0{alexaTurn + 1} / 04</span><span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-[.1em] text-[#66d184]"><span className="h-2 w-2 rounded-full bg-[#66d184]" />MCP response</span></div>
            <div className="mt-4 flex gap-3"><div className="grid h-8 w-8 shrink-0 place-items-center bg-[#ff5d24] text-white"><Bot size={16} /></div><div><p className="text-[10px] font-bold uppercase tracking-[.12em] text-[#ff9a73]">Alexa+</p><p className="mt-1 text-sm font-semibold leading-6 text-[#f8f6f1]">“{alexaTurns[alexaTurn].prompt}”</p></div></div>
            <div className="my-4 ml-11 border-l-2 border-[#ff5d24] pl-3"><p className="font-mono text-[10px] font-bold uppercase tracking-[.1em] text-[#ff9a73]">tool · {alexaTurns[alexaTurn].tool}</p></div>
            <div className="flex gap-3"><div className="grid h-8 w-8 shrink-0 place-items-center bg-[#1d4038] text-[#cde8df]"><ShieldCheck size={16} /></div><div><p className="text-[10px] font-bold uppercase tracking-[.12em] text-[#9db0aa]">RewardRadar</p><p className="mt-1 text-sm leading-6 text-[#c8d8d3]">{alexaTurns[alexaTurn].response}</p><p className="mt-3 font-mono text-[10px] text-[#8fa39d]">{alexaTurns[alexaTurn].evidence}</p></div></div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.55fr_.7fr]">
          <div className="border border-[#cfcac0] bg-[#fffdf8] shadow-[4px_4px_0_#ded8cc]">
            <div className="flex flex-col gap-4 border-b border-[#ded9cf] p-5 md:flex-row md:items-center md:justify-between">
              <div><p className="label">Opportunity queue</p><h2 className="mt-1 font-display text-2xl font-black tracking-[-0.035em]">Ranked by payment-adjusted value</h2></div>
              <div className="flex items-center gap-1 border border-[#d5d0c7] bg-[#f2efe8] p-1">
                <Filter size={14} className="mx-2 text-[#737c77]" />
                {(["all", "pursue", "watch", "avoid"] as const).map((choice) => (
                  <button key={choice} type="button" onClick={() => setFilter(choice)} className={`px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-[0.1em] ${filter === choice ? "bg-[#18211f] text-white" : "text-[#65706a] hover:bg-white"}`}>{choice}</button>
                ))}
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] border-collapse text-left">
                <thead className="bg-[#efebe3] text-[10px] uppercase tracking-[0.13em] text-[#69736e]">
                  <tr><th className="px-5 py-3">Opportunity</th><th className="px-4 py-3">Payout</th><th className="px-4 py-3">Planning P(pay)</th><th className="px-4 py-3">Expected</th><th className="px-4 py-3">Effort</th><th className="px-4 py-3">Verdict</th><th className="w-10" /></tr>
                </thead>
                <tbody>
                  {visible.map((item) => (
                    <tr key={item.id} onClick={() => setSelectedId(item.id)} className={`cursor-pointer border-t border-[#e2ded5] transition hover:bg-[#fff7ef] ${selectedId === item.id ? "bg-[#fff4e9]" : ""}`}>
                      <td className="px-5 py-4"><p className="font-semibold">{item.title}</p><p className="mt-1 text-xs text-[#738079]">{item.source} · {item.kind}</p></td>
                      <td className="px-4 py-4 font-mono text-sm font-bold">{money(item.payout)}</td>
                      <td className="px-4 py-4"><span className="font-mono text-sm font-bold">{item.probability}%</span><div className="mt-1.5 h-1 w-14 bg-[#dedad1]"><div className="h-full bg-[#ff5d24]" style={{ width: `${item.probability}%` }} /></div></td>
                      <td className="px-4 py-4 font-mono text-sm font-bold">{money(expectedValue(item))}</td>
                      <td className="px-4 py-4 font-mono text-sm">{item.hours}h</td>
                      <td className="px-4 py-4"><span className={`inline-flex border px-2 py-1 text-[10px] font-black uppercase tracking-[.1em] ${verdictStyles[item.verdict]}`}>{item.verdict}</span></td>
                      <td className="pr-4 text-[#7a847f]"><ChevronRight size={17} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <aside className="border border-[#18211f] bg-[#18211f] p-6 text-white shadow-[5px_5px_0_#ff5d24]">
            <div className="flex items-center justify-between"><p className="text-[10px] font-bold uppercase tracking-[.17em] text-[#9db0aa]">Recorded verdict</p><span className={`inline-flex border px-2 py-1 text-[10px] font-black uppercase tracking-[.1em] ${verdictStyles[selected.verdict]}`}>{selected.verdict}</span></div>
            <p className="mt-5 text-xs font-semibold text-[#ff8b5f]">{selected.source}</p>
            <h2 className="mt-1 font-display text-2xl font-black leading-tight tracking-[-0.035em]">{selected.title}</h2>
            <p className="mt-4 text-sm leading-6 text-[#b9c9c4]">{selected.reason}</p>
            <div className="my-6 grid grid-cols-2 border-y border-[#354b45] py-5">
              <div className="border-r border-[#354b45]"><p className="text-[10px] uppercase tracking-[.12em] text-[#8fa39d]">Scorer confidence</p><p className="mt-2 font-mono text-2xl font-bold">{selected.confidence}%</p></div>
              <div className="pl-5"><p className="text-[10px] uppercase tracking-[.12em] text-[#8fa39d]">Competition</p><p className="mt-2 font-mono text-lg font-bold">{selected.competition}</p></div>
            </div>
            <div className="space-y-3">
              {selected.signals.map((signal, index) => (
                <div key={signal} className="flex items-center gap-3 text-xs font-semibold text-[#cedbd7]">
                  {selected.verdict === "avoid" && index < 2 ? <X size={15} className="text-[#ff806f]" /> : <Check size={15} className="text-[#66d184]" />}{signal}
                </div>
              ))}
            </div>
            <a href={selected.url} target="_blank" rel="noreferrer" className="mt-7 flex w-full items-center justify-between border border-[#62756f] px-4 py-3 text-xs font-bold transition hover:border-[#ff7a45] hover:bg-[#213833]">
              Inspect source evidence <ExternalLink size={14} />
            </a>
          </aside>
        </section>

        <footer className="flex flex-col gap-3 py-8 text-xs text-[#66716b] md:flex-row md:items-center md:justify-between">
          <p>RewardRadar makes recommendations—not payment guarantees. Source links remain visible; probabilities are disclosed planning assumptions.</p>
          <div className="flex items-center gap-4 font-mono"><span className="flex items-center gap-1"><Code2 size={13} />MIT</span><span className="flex items-center gap-1"><Clock3 size={13} />Audit v0.2.0</span></div>
        </footer>
      </div>
    </main>
  );
}
