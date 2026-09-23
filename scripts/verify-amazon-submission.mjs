import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = fileURLToPath(new URL("..", import.meta.url));
const read = (relative) => readFileSync(join(root, relative), "utf8");
const checks = [];

function check(label, passed, detail) {
  checks.push({ label, passed: Boolean(passed), detail });
}

const readme = read("README.md");
const server = read("agent/alexa_mcp_server.py");
const draft = read("docs/AMAZON-SUBMISSION-DRAFT.md");
const friction = read("docs/AMAZON-FRICTION-LOG.md");
const fieldMap = read("docs/AMAZON-FIELD-MAP.md");
const readiness = read("docs/AMAZON-READINESS.md");
const alexaDocs = read("docs/ALEXA_PLUS.md");
const devpostCopy = read("submission/DEVPOST_V0.2_UPDATE_COPY.md");
const productFeedback = read("submission/AMAZON_PRODUCT_FEEDBACK.md");
const videoGenerator = read("scripts/make-alexa-plus-video.py");
const demo = join(root, "public", "media", "AlexaPlus-demo-v0.2.mp4");

const toolStart = server.indexOf("TOOL_DEFINITIONS:");
const toolEnd = server.indexOf("\ndef handle_rpc", toolStart);
const toolBlock = toolStart >= 0 && toolEnd >= toolStart ? server.slice(toolStart, toolEnd) : "";
const declaredTools = [...toolBlock.matchAll(/"name": "([^"]+)"/g)].map((match) => match[1]);
const expectedTools = [
  "search_rewards",
  "verify_funding",
  "summarize_submission_status",
  "plan_pursuit",
  "review_pursuit_case",
];
const exactToolSurface = declaredTools.length === expectedTools.length
  && declaredTools.every((tool, index) => tool === expectedTools[index]);

check("public repository reference", readme.includes("github.com/cuentapraces07-ops/rewardradar"));
check("open-source license file", existsSync(join(root, "LICENSE")));
check(
  "MCP protocol and exact read-only tool surface",
  server.includes("2025-11-25") && exactToolSurface,
  `declared tools: ${declaredTools.join(", ") || "none"}`,
);
check("local submission draft remains unsubmitted", /local submission draft/i.test(draft) && /owner-controlled/i.test(readiness));
check("friction log is local only", /not submitted/i.test(friction) && /up to a 10% bonus/i.test(friction));
check("field map covers owner gates", /GitHub username/i.test(fieldMap) && /Final submission/i.test(fieldMap) && /current state.*not verified/i.test(fieldMap));
const amazonMaterials = [draft, readiness, alexaDocs, devpostCopy, productFeedback].join("\n");
check(
  "Amazon materials do not advertise undeclared MCP tools",
  !/summarize_evidence_signals|simulate_x402_quote/i.test(amazonMaterials),
);
check(
  "video generator renders a local case reconnect",
  videoGenerator.includes("case_transcript")
    && videoGenerator.includes("review_pursuit_case")
    && videoGenerator.includes("handle_rpc"),
);
check("demo artifact exists", existsSync(demo) && statSync(demo).size > 100_000);

const ffprobe = spawnSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", demo], { encoding: "utf8" });
const duration = Number.parseFloat((ffprobe.stdout ?? "").trim());
check("demo is under three minutes", Number.isFinite(duration) && duration > 0 && duration < 180, Number.isFinite(duration) ? `${duration.toFixed(2)}s` : "ffprobe unavailable");

const selectedText = [readme, server, draft, friction, readiness].join("\n");
const secretPattern = /\b(?:sk|pk)_live_[A-Za-z0-9]+\b|-----BEGIN (?:RSA|EC|OPENSSH|PRIVATE) KEY-----|(?:wallet|seed phrase|private key|bank account)\s*[:=]\s*\S+/i;
check("no labeled live credentials or payout data", !secretPattern.test(selectedText));

const failed = checks.filter((item) => !item.passed);
console.log(JSON.stringify({ name: "amazon-submission-preflight", passed: checks.length - failed.length, failed: failed.length, duration_seconds: Number.isFinite(duration) ? Number(duration.toFixed(2)) : null, checks }, null, 2));
if (failed.length > 0) process.exitCode = 1;
