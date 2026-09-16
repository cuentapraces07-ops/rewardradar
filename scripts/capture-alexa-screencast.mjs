import { spawn } from "node:child_process";
import { mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { performance } from "node:perf_hooks";

const args = Object.fromEntries(process.argv.slice(2).map((part) => {
  const split = part.indexOf("=");
  return split < 0 ? [part.replace(/^--/, ""), "true"] : [part.slice(2, split), part.slice(split + 1)];
}));
const outputDir = resolve(args["frames-dir"] || "outputs/alexa-screencast");
const timeline = JSON.parse(await readFile(resolve(args.timeline), "utf8"));
const browserPath = args.chrome || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const pageUrl = new URL(args.url || "http://localhost:5173/");
if (args.endpoint) pageUrl.searchParams.set("mcpEndpoint", args.endpoint);
const url = pageUrl.toString();
const fps = 30;
const wait = (ms) => new Promise((resolveWait) => setTimeout(resolveWait, ms));

await mkdir(outputDir, { recursive: true });
const profile = await mkdtemp(join(tmpdir(), "rewardradar-chrome-"));
const browser = spawn(browserPath, [
  "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
  "--hide-scrollbars", "--window-size=1920,1080", "--force-device-scale-factor=1",
  "--remote-debugging-port=0", "--remote-allow-origins=*", `--user-data-dir=${profile}`, url,
], { stdio: "ignore", windowsHide: true });

let pageSocket;
let browserSocket;
let frameCount = 0;
let latestFrame;
let commandId = 0;
const pending = new Map();

function attachSocket(socket) {
  socket.addEventListener("message", (event) => {
    let message;
    try { message = JSON.parse(String(event.data)); } catch { return; }
    if (message.id && pending.has(message.id)) {
      const { resolve: resolveCommand, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) reject(new Error(message.error.message));
      else resolveCommand(message.result || {});
    }
    if (message.method === "Page.screencastFrame") {
      latestFrame = Buffer.from(message.params.data, "base64");
      socket.send(JSON.stringify({ id: ++commandId, method: "Page.screencastFrameAck", params: { sessionId: message.params.sessionId } }));
    }
  });
}

function command(socket, method, params = {}) {
  const id = ++commandId;
  return new Promise((resolveCommand, reject) => {
    pending.set(id, { resolve: resolveCommand, reject });
    socket.send(JSON.stringify({ id, method, params }));
    setTimeout(() => {
      if (pending.has(id)) {
        pending.delete(id);
        reject(new Error(`Timed out waiting for ${method}`));
      }
    }, 8000).unref();
  });
}

async function connect(webSocketUrl) {
  const socket = new WebSocket(webSocketUrl);
  attachSocket(socket);
  await new Promise((resolveOpen, reject) => {
    socket.addEventListener("open", resolveOpen, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });
  return socket;
}

async function localJson(path) {
  const response = await fetch(`http://127.0.0.1:${port}${path}`);
  if (!response.ok) throw new Error(`Chrome DevTools returned HTTP ${response.status}`);
  return response.json();
}

async function clickButton(label) {
  const expression = `(() => { const button = [...document.querySelectorAll('button')].find((item) => item.innerText.trim().includes(${JSON.stringify(label)})); if (!button) return false; button.click(); return true; })()`;
  const result = await command(pageSocket, "Runtime.evaluate", { expression, returnByValue: true });
  if (!result.result?.value) throw new Error(`Could not find the “${label}” demo button`);
  console.log(`[screencast] clicked ${label}`);
}

async function scrollToY(top) {
  if (!Number.isFinite(top) || top < 0) throw new Error(`Invalid scroll position: ${top}`);
  const expression = `(() => { window.scrollTo({ top: ${top}, behavior: "smooth" }); return true; })()`;
  const result = await command(pageSocket, "Runtime.evaluate", { expression, returnByValue: true });
  if (!result.result?.value) throw new Error(`Could not scroll the demo to ${top}px`);
  console.log(`[screencast] scrolled to ${top}px`);
}

let port;
try {
  const activePortPath = join(profile, "DevToolsActivePort");
  for (let attempt = 0; attempt < 100; attempt += 1) {
    try {
      port = Number((await readFile(activePortPath, "utf8")).split(/\r?\n/)[0]);
      if (port) break;
    } catch { await wait(100); }
  }
  if (!port) throw new Error("Chrome did not start its local DevTools endpoint");

  const page = (await localJson("/json/list")).find((target) => target.type === "page");
  const version = await localJson("/json/version");
  if (!page?.webSocketDebuggerUrl) throw new Error("Chrome did not expose a page target");
  pageSocket = await connect(page.webSocketDebuggerUrl);
  await command(pageSocket, "Page.enable");
  await command(pageSocket, "Runtime.enable");
  await command(pageSocket, "Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });

  let loaded = false;
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const probe = await command(pageSocket, "Runtime.evaluate", { expression: "document.body?.innerText?.includes('Money should') && [...document.querySelectorAll('button')].some((item) => item.innerText.includes('Run voice request'))", returnByValue: true });
    if (probe.result?.value) { loaded = true; break; }
    await wait(250);
  }
  if (!loaded) throw new Error("The local demo page did not become interactive");
  await wait(900);
  const initial = await command(pageSocket, "Page.captureScreenshot", { format: "jpeg", quality: 78, captureBeyondViewport: false });
  latestFrame = Buffer.from(initial.data, "base64");
  await command(pageSocket, "Page.startScreencast", { format: "jpeg", quality: 78, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });

  const actions = [...timeline.actions].sort((a, b) => a.at - b.at);
  for (const action of actions) {
    setTimeout(() => {
      void (async () => {
        if (action.button) await clickButton(action.button);
        if (Number.isFinite(action.scrollToY)) await scrollToY(action.scrollToY);
      })().catch((error) => { console.error(error); process.exitCode = 1; });
    }, action.at * 1000).unref();
  }

  const endAt = performance.now() + timeline.duration * 1000;
  const startAt = performance.now();
  while (performance.now() < endAt) {
    const elapsed = performance.now() - startAt;
    const target = join(outputDir, `frame_${String(frameCount + 1).padStart(6, "0")}.jpg`);
    await writeFile(target, latestFrame);
    frameCount += 1;
    const next = startAt + frameCount * (1000 / fps);
    await wait(Math.max(1, next - performance.now()));
  }
  await command(pageSocket, "Page.stopScreencast");
  console.log(JSON.stringify({ frames: frameCount, fps, seconds: frameCount / fps, outputDir }));

  browserSocket = await connect(version.webSocketDebuggerUrl);
  try { await command(browserSocket, "Browser.close"); } catch { /* Browser closes the socket with the command. */ }
} finally {
  pageSocket?.close();
  browserSocket?.close();
  if (browser.exitCode === null) browser.kill();
}
