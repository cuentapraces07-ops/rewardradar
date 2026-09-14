"use client";

import { ArrowLeft, ArrowRight, Check, CircleDollarSign, Play, Radar, ShieldCheck } from "lucide-react";
import { useState } from "react";

const cards = [
  { title: "Alexa+ MCP", amount: "$25K", note: "Voice-first evidence", color: "#ff7a45" },
  { title: "Fire TV build", amount: "$25K", note: "Focus-ready TV view", color: "#66d184" },
  { title: "Ring workflow", amount: "$12K", note: "Safety automation", color: "#75b8ff" },
  { title: "AWS Builder", amount: "$5K", note: "Strands + Bedrock", color: "#f6c85f" },
];

export default function TVMode() {
  const [selected, setSelected] = useState(0);
  const move = (delta: number) => setSelected((current) => (current + delta + cards.length) % cards.length);

  return (
    <main className="min-h-screen bg-[#071513] px-10 py-12 text-white" onKeyDown={(event) => {
      if (event.key === "ArrowRight" || event.key === "ArrowDown") move(1);
      if (event.key === "ArrowLeft" || event.key === "ArrowUp") move(-1);
    }} tabIndex={0}>
      <div className="mx-auto max-w-[1500px]">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-4"><div className="grid h-12 w-12 place-items-center bg-[#ff5d24] shadow-[4px_4px_0_#66d184]"><Radar size={26} /></div><div><p className="text-2xl font-black tracking-[-.04em]">RewardRadar TV</p><p className="text-xs font-bold uppercase tracking-[.2em] text-[#8da59c]">Fire TV / Vega focus mode</p></div></div>
          <div className="flex items-center gap-2 rounded-full border border-[#2b4b42] px-4 py-2 text-xs font-bold text-[#b5cbc3]"><span className="h-2 w-2 rounded-full bg-[#66d184]" />Remote-ready web view</div>
        </header>

        <section className="mt-16 max-w-4xl"><p className="text-sm font-bold uppercase tracking-[.2em] text-[#ff8b5f]">A calmer way to choose what to build</p><h1 className="mt-4 text-[clamp(3rem,7vw,7rem)] font-black leading-[.88] tracking-[-.07em]">Put the<br /><span className="text-[#ff7a45]">evidence</span> on screen.</h1><p className="mt-8 max-w-2xl text-xl leading-8 text-[#b8ccc4]">A ten-foot interface for scanning opportunities, opening source evidence, and choosing the next build without chasing a headline number.</p></section>

        <section className="mt-14"><div className="mb-5 flex items-center justify-between"><div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[.17em] text-[#8da59c]"><Play size={16} className="text-[#ff7a45]" />Opportunity carousel</div><p className="text-xs font-mono text-[#6f8c82]">Use ← → on a remote or keyboard</p></div><div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{cards.map((card, index) => <button key={card.title} type="button" onClick={() => setSelected(index)} className={`min-h-56 border p-6 text-left transition ${selected === index ? "border-[#ff7a45] bg-[#17332c] shadow-[6px_6px_0_#ff5d24]" : "border-[#2b4b42] bg-[#0d211d] hover:border-[#72968b]"}`}><div className="flex items-start justify-between"><span className="grid h-9 w-9 place-items-center bg-[#132c27]" style={{ color: card.color }}><CircleDollarSign size={19} /></span><span className="font-mono text-xs text-[#6f8c82]">0{index + 1}</span></div><p className="mt-8 text-xl font-black">{card.title}</p><p className="mt-3 font-mono text-4xl font-black" style={{ color: card.color }}>{card.amount}</p><p className="mt-2 text-sm text-[#9db5ac]">{card.note}</p></button>)}</div></section>

        <section className="mt-12 grid gap-5 lg:grid-cols-[1.35fr_.65fr]"><div className="border border-[#2b4b42] bg-[#0d211d] p-7"><div className="flex items-center gap-3 text-[#66d184]"><ShieldCheck size={21} /><span className="text-xs font-bold uppercase tracking-[.17em]">Selected evidence</span></div><h2 className="mt-5 text-3xl font-black tracking-[-.04em]">{cards[selected].title}</h2><p className="mt-3 max-w-2xl text-base leading-7 text-[#b8ccc4]">RewardRadar shows the payout headline beside its confidence, evidence gaps, and estimated effort. Selecting a card never submits work or treats a prize as earned.</p><div className="mt-7 grid gap-3 sm:grid-cols-3"><div className="border-l-2 border-[#66d184] pl-3"><p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#6f8c82]">Status</p><p className="mt-2 font-mono text-sm font-bold">source checked</p></div><div className="border-l-2 border-[#ff7a45] pl-3"><p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#6f8c82]">Payout</p><p className="mt-2 font-mono text-sm font-bold">not guaranteed</p></div><div className="border-l-2 border-[#75b8ff] pl-3"><p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#6f8c82]">Input</p><p className="mt-2 font-mono text-sm font-bold">public evidence</p></div></div></div><aside className="border border-[#2b4b42] bg-[#132c27] p-7"><p className="text-xs font-bold uppercase tracking-[.17em] text-[#8da59c]">Remote controls</p><div className="mt-6 grid grid-cols-2 gap-3"><button type="button" onClick={() => move(-1)} className="flex items-center justify-center gap-2 border border-[#4d6b62] px-3 py-3 text-sm font-bold hover:bg-[#1d4038]"><ArrowLeft size={16} />Previous</button><button type="button" onClick={() => move(1)} className="flex items-center justify-center gap-2 border border-[#4d6b62] px-3 py-3 text-sm font-bold hover:bg-[#1d4038]">Next<ArrowRight size={16} /></button></div><div className="mt-8 border-t border-[#355149] pt-5 text-sm text-[#b8ccc4]"><p className="flex items-center gap-2"><Check size={15} className="text-[#66d184]" />No calls or account actions</p><p className="mt-3 flex items-center gap-2"><Check size={15} className="text-[#66d184]" />Visible source trail</p></div></aside></section>
      </div>
    </main>
  );
}
