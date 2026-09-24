import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const read = (relative) => readFileSync(join(root, relative), "utf8");
const checks = [];

function check(label, passed, detail) {
  checks.push({ label, passed: Boolean(passed), detail });
}

/**
 * Read the movie-header duration directly from an ISO Base Media / MP4 file.
 *
 * GitHub-hosted runners do not guarantee `ffprobe`, so the submission boundary
 * check must not depend on a system media binary. This handles the v0 and v1
 * `mvhd` layouts used by the checked-in demo and fails closed for malformed or
 * unsupported files.
 */
function mp4DurationSeconds(file) {
  const bytes = readFileSync(file);

  function boxAt(offset, limit) {
    if (offset + 8 > limit) return null;
    let size = bytes.readUInt32BE(offset);
    const type = bytes.toString("ascii", offset + 4, offset + 8);
    let header = 8;
    if (size === 1) {
      if (offset + 16 > limit) return null;
      size = Number(bytes.readBigUInt64BE(offset + 8));
      header = 16;
    } else if (size === 0) {
      size = limit - offset;
    }
    if (!Number.isSafeInteger(size) || size < header || offset + size > limit) return null;
    return { type, payload: offset + header, end: offset + size };
  }

  function child(parent, expectedType) {
    let offset = parent.payload;
    while (offset < parent.end) {
      const box = boxAt(offset, parent.end);
      if (!box) return null;
      if (box.type === expectedType) return box;
      offset = box.end;
    }
    return null;
  }

  const root = { payload: 0, end: bytes.length };
  const movie = child(root, "moov");
  const movieHeader = movie && child(movie, "mvhd");
  if (!movieHeader || movieHeader.payload + 20 > movieHeader.end) return Number.NaN;

  const version = bytes.readUInt8(movieHeader.payload);
  if (version === 0) {
    const timeScale = bytes.readUInt32BE(movieHeader.payload + 12);
    const duration = bytes.readUInt32BE(movieHeader.payload + 16);
    return timeScale > 0 ? duration / timeScale : Number.NaN;
  }
  if (version === 1 && movieHeader.payload + 32 <= movieHeader.end) {
    const timeScale = bytes.readUInt32BE(movieHeader.payload + 20);
    const duration = Number(bytes.readBigUInt64BE(movieHeader.payload + 24));
    return timeScale > 0 && Number.isSafeInteger(duration) ? duration / timeScale : Number.NaN;
  }
  return Number.NaN;
}

const readme = read("README.md");
const server = read("agent/alexa_mcp_server.py");
const core = read("agent/core.py");
const fixture = JSON.parse(read("data/demo_candidates.json"));
const app = read("app/page.tsx");
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
  "respond_to_request",
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
check(
  "MCP Streamable HTTP request and origin safeguards",
  server.includes("def _reject_invalid_origin")
    && server.includes("HTTPStatus.FORBIDDEN")
    && server.includes("HTTPStatus.METHOD_NOT_ALLOWED")
    && app.includes('Accept: "application/json, text/event-stream"')
    && app.includes('"MCP-Protocol-Version": "2025-11-25"'),
);
check(
  "Alexa+ web simulation accepts a natural-language prompt",
  app.includes('id="alexa-request"')
    && app.includes('name: "respond_to_request"')
    && server.includes('"name": "respond_to_request"'),
);
const amazonScenario = fixture.find((row) => row.source === "Amazon Developer Hackathon · Alexa+");
const namedExpiredRows = fixture.filter((row) =>
  ["Agents for Humans — Professional Agents", "Steve Agent Arena — highest individual prize"].includes(row.title),
);
check(
  "Amazon cash scenario discloses unmeasured probability and owner gates",
  amazonScenario?.status === "open"
    && amazonScenario?.payout_usd === 15000
    && amazonScenario?.base_probability === 0.01
    && /illustrative/i.test(amazonScenario?.probability_basis ?? "")
    && /no empirical/i.test(amazonScenario?.probability_basis ?? "")
    && /deadline_at/.test(JSON.stringify(amazonScenario)),
);
check(
  "past-deadline historical contests are closed in the fixture",
  namedExpiredRows.length === 2 && namedExpiredRows.every((row) => row.status === "closed"),
);
check(
  "scoring expires dated candidates and fails closed on invalid deadlines",
  core.includes('deadline_at.replace("Z", "+00:00")')
    && core.includes('status="unknown", deadline_days=None'),
);
check(
  "browser candidate expires after its official deadline",
  app.includes('deadlineAt: "2026-10-23T12:00:00-07:00"')
    && app.includes("expireByDeadline(item, now)"),
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

const duration = mp4DurationSeconds(demo);
check("demo is under three minutes", Number.isFinite(duration) && duration > 0 && duration < 180, Number.isFinite(duration) ? `${duration.toFixed(2)}s (MP4 metadata)` : "MP4 duration unavailable");

const selectedText = [readme, server, draft, friction, readiness].join("\n");
const secretPattern = /\b(?:sk|pk)_live_[A-Za-z0-9]+\b|-----BEGIN (?:RSA|EC|OPENSSH|PRIVATE) KEY-----|(?:wallet|seed phrase|private key|bank account)\s*[:=]\s*\S+/i;
check("no labeled live credentials or payout data", !secretPattern.test(selectedText));

const failed = checks.filter((item) => !item.passed);
console.log(JSON.stringify({ name: "amazon-submission-preflight", passed: checks.length - failed.length, failed: failed.length, duration_seconds: Number.isFinite(duration) ? Number(duration.toFixed(2)) : null, checks }, null, 2));
if (failed.length > 0) process.exitCode = 1;
