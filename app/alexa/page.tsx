"use client";

import {
  Activity,
  ArrowUpRight,
  AudioLines,
  Bot,
  Check,
  ChevronDown,
  CircleDollarSign,
  ExternalLink,
  Fingerprint,
  LoaderCircle,
  Mic2,
  Radio,
  Radar,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Workflow,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

type Json = Record<string, unknown>;
type RpcResult = { result?: { structuredContent?: Json; content?: Array<{ text?: string }> }; error?: { message?: string } };
type Trace = { method: string; id: number | string; state: "done" | "active" | "error"; note: string };
type Opportunity = {
  candidate?: { title?: string; source?: string; url?: string; payout_usd?: number; status?: string; escrowed?: boolean; sponsor_verified?: boolean; payout_rail_ready?: boolean };
  expected_value_usd?: number;
  expected_hourly_usd?: number;
  payment_probability?: number;
  verdict?: string;
  reasons?: string[];
};

const scenarios = [
  { id: "search", label: "Find worthwhile work", prompt: "Is any of this worth spending time on?", tool: "search_rewards", icon: Radar },
  { id: "funding", label: "Verify the money", prompt: "Is the advertised reward actually funded?", tool: "verify_funding", icon: ShieldCheck },
  { id: "status", label: "Check submission status", prompt: "Has RewardRadar been submitted, and has it earned anything?", tool: "summarize_submission_status", icon: CircleDollarSign },
] as const;

const defaultTools = ["search_rewards", "verify_funding", "summarize_submission_status"];
const DEFAULT_MCP_ENDPOINT = "http://127.0.0.1:8787/mcp";

function subscribeToLocationSearch(onChange: () => void) {
  window.addEventListener("popstate", onChange);
  return () => window.removeEventListener("popstate", onChange);
}

function getLocationSearch() {
  return window.location.search;
}

function getServerLocationSearch() {
  return "";
}

function localEndpointOverride(search: string) {
  const requested = new URLSearchParams(search).get("mcpEndpoint");
  if (!requested) return null;
  try {
    const parsed = new URL(requested);
    if (
      parsed.protocol === "http:" &&
      ["localhost", "127.0.0.1"].includes(parsed.hostname) &&
      parsed.pathname === "/mcp" &&
      !parsed.username &&
      !parsed.password &&
      !parsed.search &&
      !parsed.hash
    ) return parsed.toString();
  } catch {
    // Ignore malformed or non-local overrides.
  }
  return null;
}

function amount(value: unknown) {
  const number = typeof value === "number" ? value : Number(value ?? 0);
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: number < 10 ? 2 : 0 }).format(number);
}

function pickStructured(response: RpcResult): Json {
  if (response.error) throw new Error(response.error.message || "MCP request failed");
  const result = response.result;
  if (!result) throw new Error("The MCP server returned no result");
  if (result.structuredContent) return result.structuredContent;
  const text = result.content?.find((item) => item.text)?.text;
  if (text) return JSON.parse(text) as Json;
  return {};
}

export default function AlexaStudio() {
  const locationSearch = useSyncExternalStore(subscribeToLocationSearch, getLocationSearch, getServerLocationSearch);
  const [manualEndpoint, setManualEndpoint] = useState(DEFAULT_MCP_ENDPOINT);
  const [endpointEdited, setEndpointEdited] = useState(false);
  const endpoint = !endpointEdited ? localEndpointOverride(locationSearch) || manualEndpoint : manualEndpoint;
  const [connection, setConnection] = useState<"idle" | "connecting" | "connected" | "error">("idle");
  const [scenario, setScenario] = useState<(typeof scenarios)[number]["id"]>("search");
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(0);
  const [reply, setReply] = useState<Json | null>(null);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [error, setError] = useState("");
  const [tools, setTools] = useState<string[]>([]);
  const rpcId = useRef(0);
  const sessionId = useRef<string | null>(null);
  const runningRef = useRef(false);
  const autoplayedRef = useRef(false);

  const rpc = useCallback(async (method: string, params: Json = {}, notification = false): Promise<{ id: number; payload: RpcResult }> => {
    const id = notification ? undefined : ++rpcId.current;
    if (method === "initialize") sessionId.current = null;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
      "MCP-Protocol-Version": "2025-11-25",
    };
    if (method !== "initialize" && sessionId.current) headers["Mcp-Session-Id"] = sessionId.current;
    const response = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({ jsonrpc: "2.0", ...(id ? { id } : {}), method, ...(Object.keys(params).length ? { params } : {}) }),
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok && response.status !== 202) throw new Error(`MCP server responded ${response.status}`);
    if (notification) return { id: 0, payload: { result: { structuredContent: {} } } };
    const payload = await response.json() as RpcResult;
    if (payload.error) throw new Error(payload.error.message || "MCP request failed");
    if (method === "initialize") {
      const negotiatedSession = response.headers.get("Mcp-Session-Id");
      if (!negotiatedSession) throw new Error("MCP server did not return a session ID");
      sessionId.current = negotiatedSession;
    }
    return { id: id!, payload };
  }, [endpoint]);

  const appendTrace = (method: string, id: number | string, state: Trace["state"], note: string) => {
    setTraces((current) => [...current, { method, id, state, note }]);
  };

  const connect = useCallback(async () => {
    if (connection === "connecting") return;
    setConnection("connecting");
    setError("");
    setTraces([]);
    sessionId.current = null;
    try {
      const init = await rpc("initialize", { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "RewardRadar Voice Demo", version: "0.2.0" } });
      appendTrace("initialize", init.id, "done", "Negotiated MCP 2025-11-25");
      await rpc("notifications/initialized", {}, true);
      const listed = await rpc("tools/list");
      const available = (listed.payload.result as { tools?: Array<{ name: string }> } | undefined)?.tools;
      setTools((available || []).map((item) => item.name));
      appendTrace("tools/list", listed.id, "done", `${available?.length || 0} read-only tools discovered`);
      setConnection("connected");
      return true;
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Could not reach the local MCP server";
      setError(message.includes("fetch") ? "Can't reach the local demo server. Start it with: python -m agent.alexa_mcp_server --port 8787" : message);
      setConnection("error");
      return false;
    }
  }, [connection, rpc]);

  const callTool = useCallback(async (name: string, args: Json) => {
    const call = await rpc("tools/call", { name, arguments: args });
    appendTrace(`tools/call · ${name}`, call.id, "done", "Read-only tool result returned");
    return pickStructured(call.payload);
  }, [rpc]);

  const runScenario = useCallback(async (requested = scenario) => {
    if (runningRef.current || busy) return;
    runningRef.current = true;
    setBusy(true);
    setStep(1);
    setReply(null);
    setTraces([]);
    setError("");
    try {
      const ready = connection === "connected" || await connect();
      if (!ready) return;
      const chosen = scenarios.find((item) => item.id === requested) || scenarios[0];
      setStep(2);
      let result: Json;
      if (chosen.id === "status") {
        result = await callTool("summarize_submission_status", { track: "Alexa+" });
      } else {
        const search = await callTool("search_rewards", { query: chosen.id === "funding" ? "" : "", limit: 5 });
        const rows = (search.results || []) as Opportunity[];
        if (chosen.id === "funding") {
          const candidate = rows.find((row) => row.candidate?.title);
          result = candidate?.candidate?.title ? await callTool("verify_funding", { title: candidate.candidate.title }) : search;
        } else {
          result = search;
        }
      }
      setReply(result);
      setStep(3);
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "The tool call failed";
      setError(message);
      setConnection("error");
      setTraces((current) => [...current, { method: "MCP request", id: "—", state: "error", note: message }]);
    } finally {
      setBusy(false);
      runningRef.current = false;
    }
  }, [busy, callTool, connect, connection, scenario]);

  useEffect(() => {
    const requested = new URLSearchParams(window.location.search).get("demo");
    if (requested && scenarios.some((item) => item.id === requested)) {
      const chosen = requested as (typeof scenarios)[number]["id"];
      const timer = window.setTimeout(() => {
        if (autoplayedRef.current) return;
        autoplayedRef.current = true;
        setScenario(chosen);
        void runScenario(chosen);
      }, 350);
      return () => window.clearTimeout(timer);
    }
  }, [runScenario]);

  const selected = scenarios.find((item) => item.id === scenario) || scenarios[0];
  let endpointHost = "custom endpoint";
  try {
    endpointHost = new URL(endpoint).host;
  } catch {
    // Keep a safe label while the user edits an incomplete endpoint.
  }
  const statusView = scenario === "status";
  const fundingView = scenario === "funding";

  return (
    <main className="min-h-screen overflow-hidden bg-[#08130f] text-[#f4f6ee] selection:bg-[#baf16a] selection:text-[#10200e]">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_48%_-15%,rgba(123,210,116,.15),transparent_48%),radial-gradient(ellipse_at_90%_85%,rgba(255,126,73,.09),transparent_34%)]" />
      <header className="relative z-10 border-b border-white/[.08] bg-[#08130f]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-[76px] max-w-[1440px] items-center justify-between px-5 lg:px-10">
          <Link className="flex items-center gap-3" href="/">
            <span className="grid h-10 w-10 place-items-center rounded-2xl bg-[#baf16a] text-[#18310e] shadow-[0_0_28px_rgba(186,241,106,.2)]"><Radar size={21} /></span>
            <span><span className="block text-[15px] font-bold tracking-[-.03em]">RewardRadar</span><span className="mt-1 block text-[9px] font-bold uppercase tracking-[.22em] text-[#8d9b91]">Alexa+ voice lab</span></span>
          </Link>
          <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/[.04] px-3 py-2 text-[10px] font-semibold tracking-wide text-[#a7b4aa] md:flex"><span className={`h-1.5 w-1.5 rounded-full ${connection === "connected" ? "bg-[#baf16a] shadow-[0_0_8px_#baf16a]" : connection === "error" ? "bg-[#ff705c]" : "bg-[#839087]"}`} />{connection === "connected" ? "MCP SERVER CONNECTED" : connection === "connecting" ? "NEGOTIATING MCP SESSION" : connection === "error" ? "SERVER NOT REACHED" : "LOCAL MCP DEMO"}</div>
          <a className="flex items-center gap-2 rounded-full border border-white/10 px-4 py-2.5 text-[11px] font-semibold text-[#d7dfd8] transition hover:border-[#baf16a]/50 hover:text-[#baf16a]" href="https://github.com/cuentapraces07-ops/rewardradar" target="_blank" rel="noreferrer">View source <ExternalLink size={13} /></a>
        </div>
      </header>

      <div className="relative z-10 mx-auto max-w-[1440px] px-5 pb-16 pt-10 lg:px-10 lg:pt-14">
        <section className="grid items-center gap-9 lg:grid-cols-[1.12fr_.88fr] lg:gap-14">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#baf16a]/20 bg-[#baf16a]/[.06] px-3 py-1.5 text-[9px] font-bold uppercase tracking-[.2em] text-[#c6ed9e]"><Sparkles size={12} /> Voice-first · Evidence-led · Fixture replay</div>
            <h1 className="max-w-[760px] text-[clamp(3.4rem,8vw,7.2rem)] font-semibold leading-[.86] tracking-[-.085em] text-[#f4f6ee]">Money should<br /><span className="text-[#baf16a]">pass a test.</span></h1>
            <p className="mt-7 max-w-[590px] text-[15px] leading-7 text-[#a7b5ab] md:text-[17px] md:leading-8">Ask what is worth your next hour. RewardRadar calls a real local MCP server, checks the evidence in its fixture, and answers without passing a headline prize off as income.</p>
            <div className="mt-8 flex flex-wrap gap-2.5">
              {scenarios.map((item) => { const Icon = item.icon; return <button key={item.id} type="button" onClick={() => { setScenario(item.id); void runScenario(item.id); }} disabled={busy} className={`flex items-center gap-2 rounded-full border px-4 py-3 text-[11px] font-semibold transition disabled:opacity-60 ${scenario === item.id ? "border-[#baf16a]/60 bg-[#baf16a] text-[#16280d] shadow-[0_0_24px_rgba(186,241,106,.12)]" : "border-white/10 bg-white/[.035] text-[#d0d8d1] hover:border-white/25 hover:bg-white/[.07]"}`}><Icon size={14} />{item.label}</button>; })}
            </div>
            <div className="mt-8 flex items-center gap-4 text-[10px] text-[#839188]"><span className="flex items-center gap-1.5"><ShieldCheck size={13} className="text-[#baf16a]" />No payment actions</span><span className="h-1 w-1 rounded-full bg-[#55635a]" /><span className="flex items-center gap-1.5"><Workflow size={13} />Read-only tools</span><span className="h-1 w-1 rounded-full bg-[#55635a]" /><span className="flex items-center gap-1.5"><Fingerprint size={13} />No credentials</span></div>
          </div>

          <div className="relative mx-auto w-full max-w-[570px]">
            <div className="absolute -inset-8 rounded-[50%] bg-[#baf16a]/[.06] blur-3xl" />
            <div className="relative overflow-hidden rounded-[30px] border border-white/[.12] bg-[#101e18] shadow-[0_40px_130px_rgba(0,0,0,.4)]">
              <div className="flex items-center justify-between border-b border-white/[.08] px-5 py-4 md:px-6"><div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#baf16a]/10 text-[#baf16a]"><AudioLines size={17} /></span><span><span className="block text-[11px] font-semibold">Alexa+ simulation</span><span className="mt-1 block text-[9px] text-[#819087]">Not connected to an Alexa device</span></span></div><span className="rounded-full border border-white/10 px-2.5 py-1 text-[8px] font-bold uppercase tracking-[.14em] text-[#93a198]">MCP · 2025-11-25</span></div>
              <div className="min-h-[322px] px-5 py-6 md:px-7">
                <div className="flex gap-3"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-white/[.07] text-[#eff5ee]"><Mic2 size={15} /></span><div><p className="text-[9px] font-bold uppercase tracking-[.18em] text-[#77877b]">You ask</p><p className="mt-1.5 text-[15px] font-medium leading-6 text-[#eff5ee]">“{selected.prompt}”</p></div></div>
                <div className="ml-4 mt-4 space-y-0 border-l border-[#34443a] pl-5">
                  {[
                    [1, "Initialize protocol", "MCP handshake · 2025-11-25"],
                    [2, selected.tool, selected.id === "search" ? "Rank source-backed candidates" : selected.id === "funding" ? "Inspect escrow & sponsor signals" : "Check submission and payment separately"],
                    [3, "Shape a careful reply", "Planning estimate ≠ earned money"],
                  ].map(([index, title, note]) => <div key={String(index)} className="relative flex gap-3 pb-4 last:pb-0"><span className={`absolute -left-[25px] top-0.5 grid h-[11px] w-[11px] place-items-center rounded-full ring-[5px] ring-[#101e18] ${step >= Number(index) ? "bg-[#baf16a] text-[#16280d]" : "bg-[#526158]"}`}>{step === Number(index) && busy && <LoaderCircle size={17} className="animate-spin" />}</span><div><p className={`font-mono text-[10px] font-semibold ${step >= Number(index) ? "text-[#d9f2c2]" : "text-[#6f7e73]"}`}>{String(title)}</p><p className="mt-1 text-[9px] text-[#7d8b81]">{String(note)}</p></div></div>)}
                </div>
                <div className="mt-5 rounded-2xl border border-white/[.07] bg-[#0a1510] p-4">
                  <div className="flex items-center justify-between"><span className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[.15em] text-[#91a096]"><Bot size={12} /> RewardRadar</span><span className={`text-[8px] font-bold uppercase tracking-wider ${reply ? "text-[#baf16a]" : "text-[#738077]"}`}>{busy ? "Thinking" : reply ? "Evidence returned" : "Ready"}</span></div>
                  {error ? <p className="mt-3 text-[11px] leading-5 text-[#ff9887]">{error}</p> : reply ? <div className="mt-3 text-[11px] leading-5 text-[#d0dbd1]">{statusView ? <p>Submitted to the Alexa+ track. <strong className="text-[#f5f7f1]">No award announced; no payment received.</strong></p> : fundingView ? <p>Funding check complete: <strong className="text-[#f5f7f1]">{reply.verified ? "signals verified" : "not verified"}</strong>. Advertised prize is not income.</p> : <p>Checked {((reply.results as unknown[]) || []).length} fixture records. The largest headline is not automatically the best bet.</p>}<p className="mt-2 text-[9px] text-[#819087]">{statusView ? "Entry status as of Sep 14, 2026" : `Historical fixture · snapshot ${String(reply.data_as_of || "Sep 10, 2026")}`} · no live marketplace feed</p></div> : <p className="mt-3 text-[10px] leading-5 text-[#809087]">Run a request to see the actual MCP tool response here.</p>}
                  <p className="mt-3 flex items-center gap-1.5 text-[9px] font-semibold text-[#9dac9f]"><AudioLines size={12} />Video narration: natural male English voice</p>
                </div>
                <button type="button" onClick={() => void runScenario()} disabled={busy} className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-[#baf16a] px-4 py-3 text-[11px] font-bold text-[#16280d] transition hover:bg-[#cdf5a5] disabled:cursor-wait disabled:opacity-70">{busy ? <><LoaderCircle size={14} className="animate-spin" />Running verified tool calls</> : <><Radio size={14} />{reply ? "Run request again" : "Run voice request"}<ArrowUpRight size={13} /></>}</button>
              </div>
              <div className="border-t border-white/[.08] bg-white/[.025] px-5 py-3 text-center text-[9px] text-[#7d8b81]">This is a visual client simulation—not an Alexa skill or device connection.</div>
            </div>
          </div>
        </section>

        <section className="mt-10 grid gap-5 lg:grid-cols-[.8fr_1.2fr]">
          <div className="rounded-3xl border border-white/[.09] bg-white/[.035] p-5 md:p-6">
            <div className="flex items-center justify-between"><div><p className="text-[9px] font-bold uppercase tracking-[.18em] text-[#829087]">Source-aware response</p><h2 className="mt-1 text-[15px] font-semibold">Result card</h2></div><Activity size={17} className="text-[#baf16a]" /></div>
            {!reply ? <div className="mt-5 flex min-h-[146px] items-center justify-center rounded-2xl border border-dashed border-white/10 px-4 text-center text-[10px] leading-5 text-[#849187]">Run a request. The interface renders live structuredContent returned by the local MCP endpoint.</div> : statusView ? <div className="mt-5 rounded-2xl border border-white/[.08] bg-[#0a1510] p-4"><div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wide text-[#baf16a]"><Check size={13} />Submission confirmed</div><p className="mt-3 text-[13px] font-semibold">{String(reply.project || "RewardRadar")}</p><div className="mt-3 grid grid-cols-2 gap-2 text-[9px]"><span className="rounded-lg bg-white/[.04] p-2 text-[#acb8ae]">Status <strong className="block mt-1 text-[#edf4ed]">{String(reply.submission || "unknown")}</strong></span><span className="rounded-lg bg-white/[.04] p-2 text-[#acb8ae]">Prize <strong className="block mt-1 text-[#edf4ed]">{String(reply.award || "not awarded")}</strong></span><span className="col-span-2 rounded-lg bg-white/[.04] p-2 text-[#acb8ae]">Cash received <strong className="block mt-1 text-[#ff947e]">{String(reply.payment || "not received")}</strong></span></div>{typeof reply.submission_url === "string" && <a href={reply.submission_url} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1.5 text-[9px] font-semibold text-[#baf16a]">Inspect public entry <ExternalLink size={11} /></a>}</div> : fundingView ? <div className="mt-5 rounded-2xl border border-white/[.08] bg-[#0a1510] p-4"><div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wide text-[#ffac87]"><TriangleAlert size={13} />Funding not verified</div><p className="mt-3 text-[12px] font-semibold">{String(reply.title || "Selected opportunity")}</p><div className="mt-3 grid grid-cols-2 gap-2 text-[9px]">{[["Escrow", reply.escrowed ? "Verified" : "No evidence"], ["Sponsor", reply.sponsor_verified ? "Verified" : "No evidence"], ["Acceptance", reply.acceptance_clear ? "Clear" : "Ambiguous"], ["Payout rail", reply.payout_rail_ready ? "Ready" : "Owner setup"]].map(([label, value]) => <span key={String(label)} className="rounded-lg bg-white/[.04] p-2 text-[#93a096]">{String(label)}<strong className={`block mt-1 ${String(value).includes("Verified") || value === "Ready" || value === "Clear" ? "text-[#baf16a]" : "text-[#e9b095]"}`}>{String(value)}</strong></span>)}</div>{typeof reply.source_url === "string" && <a href={reply.source_url} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1.5 text-[9px] font-semibold text-[#baf16a]">Inspect canonical source <ExternalLink size={11} /></a>}</div> : <div className="mt-5 space-y-2">{((reply.results as Opportunity[]) || []).slice(0, 3).map((row, index) => <div key={`${row.candidate?.title}-${index}`} className="flex items-center justify-between gap-3 rounded-2xl border border-white/[.07] bg-[#0a1510] p-3"><div className="min-w-0"><p className="truncate text-[10px] font-semibold text-[#e9efe9]">{row.candidate?.title}</p><p className="mt-1 text-[9px] text-[#8e9b91]">{row.candidate?.source} · {row.candidate?.status}</p></div><div className="shrink-0 text-right"><p className="font-mono text-[10px] font-bold">{amount(row.candidate?.payout_usd)}</p><p className="mt-1 text-[8px] text-[#91a08e]">{row.verdict || "unscored"} · planning only</p></div></div>)}</div>}
          </div>

          <div className="rounded-3xl border border-white/[.09] bg-white/[.035] p-5 md:p-6">
            <div className="flex items-start justify-between gap-3"><div><p className="text-[9px] font-bold uppercase tracking-[.18em] text-[#829087]">MCP transport</p><h2 className="mt-1 text-[15px] font-semibold">A trace you can inspect</h2></div><details className="group relative"><summary className="flex cursor-pointer list-none items-center gap-1 rounded-full border border-white/10 px-3 py-1.5 text-[9px] font-semibold text-[#adb9ae]">Endpoint <ChevronDown size={11} className="transition group-open:rotate-180" /></summary><div className="absolute right-0 top-9 z-20 w-[min(360px,80vw)] rounded-xl border border-white/10 bg-[#17271e] p-3 shadow-2xl"><label className="block text-[9px] text-[#b9c5ba]" htmlFor="mcp-endpoint">Local MCP endpoint</label><input id="mcp-endpoint" value={endpoint} onChange={(event) => { setManualEndpoint(event.target.value); setEndpointEdited(true); setConnection("idle"); }} className="mt-2 w-full rounded-lg border border-white/10 bg-[#08130f] px-3 py-2 font-mono text-[9px] text-[#d8e4d8] outline-none focus:border-[#baf16a]/50" /></div></details></div>
            <div className="mt-5 overflow-hidden rounded-2xl border border-white/[.075] bg-[#07100c]">
              <div className="flex items-center justify-between border-b border-white/[.07] px-4 py-2.5"><span className="flex items-center gap-1.5 text-[9px] font-semibold text-[#a7b4a8]"><span className={`h-1.5 w-1.5 rounded-full ${connection === "connected" ? "bg-[#baf16a]" : connection === "error" ? "bg-[#ff705c]" : "bg-[#748178]"}`} />{endpointHost}</span><span className="text-[8px] text-[#728077]">JSON-RPC · read only</span></div>
              <div className="min-h-[146px] space-y-3 p-4 font-mono text-[9px]">
                {traces.length ? traces.map((trace, index) => <div key={`${trace.id}-${index}`} className="flex gap-3"><span className={trace.state === "error" ? "text-[#ff796b]" : "text-[#baf16a]"}>{trace.state === "error" ? "×" : "✓"}</span><div className="min-w-0"><p className="text-[#d9e3d9]">{trace.method}<span className="ml-2 text-[#819087]">id:{trace.id}</span></p><p className="mt-1 truncate text-[#819087]">{trace.note}</p></div></div>) : <div className="flex h-[112px] flex-col items-center justify-center text-center text-[9px] leading-5 text-[#77847a]"><Workflow size={20} className="mb-2 text-[#64736a]" />Initialize → discover tools → call a structured resource</div>}
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-2 text-[8px] font-semibold uppercase tracking-[.1em] text-[#7e8b81]">{(tools.length ? tools : defaultTools).map((tool) => <span key={tool} className="rounded-full border border-white/10 px-2.5 py-1">{tool}</span>)}</div>
          </div>
        </section>

        <section className="mt-5 grid gap-3 sm:grid-cols-3">
          {[["01", "Find", "Rank the transparent fixture by payment-adjusted value.", Radar], ["02", "Verify", "Separate funded escrow from sponsor and payout-rail signals.", ShieldCheck], ["03", "Disclose", "Keep “submitted,” “awarded,” and “paid” distinct.", Check]].map(([number, title, description, Icon]) => { const StageIcon = Icon as typeof Radar; return <article key={String(number)} className="rounded-2xl border border-white/[.08] bg-white/[.025] p-4"><div className="flex items-center justify-between"><span className="font-mono text-[9px] text-[#baf16a]">{String(number)} / {String(title).toUpperCase()}</span><StageIcon size={15} className="text-[#91a48f]" /></div><p className="mt-3 max-w-[300px] text-[10px] leading-5 text-[#93a095]">{String(description)}</p></article>; })}
        </section>

        <div className="mt-7 flex flex-col gap-3 rounded-2xl border border-[#e59650]/20 bg-[#e59650]/[.055] p-4 text-[9px] leading-5 text-[#b2aaa0] md:flex-row md:items-center md:justify-between md:px-5"><span className="flex items-start gap-2"><TriangleAlert size={14} className="mt-0.5 shrink-0 text-[#e6a16a]" />Demo uses a checked-in fixture, not fresh listings. Planning probabilities are estimates; no reward, eligibility, or payment is guaranteed.</span><a href="https://github.com/cuentapraces07-ops/rewardradar" target="_blank" rel="noreferrer" className="shrink-0 font-semibold text-[#d9e3d8] hover:text-[#baf16a]">Inspect source &amp; fixture <ArrowUpRight size={11} className="inline" /></a></div>
      </div>
    </main>
  );
}
