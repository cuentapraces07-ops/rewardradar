"""Render a short, English Alexa+ prototype demo for the Amazon hackathon.

The video shows the local MCP/voice simulation and its disclosures. It does
not imply a live Alexa device connection or a prize. All visuals are generated
locally with original text and shapes.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import wave
from pathlib import Path

import imageio_ffmpeg
import edge_tts
from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1600, 900
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / "work" / "alexa-plus-video"
DEFAULT_OUTPUT = ROOT.parent / "outputs" / "AlexaPlus-demo-draft.mp4"
INK, PAPER, WHITE, ORANGE, GREEN, MUTED, RED = "#172a25", "#f3f0e9", "#fffdf8", "#ff5d24", "#2e9f50", "#69736e", "#a5372b"

NARRATION = [
    "RewardRadar is an evidence-first voice experience for Alexa Plus. Ask which opportunity is worth your next hour, and the system checks source state, competition, and payout signals before it answers.",
    "The project exposes a self-hosted MCP endpoint over Streamable HTTP using protocol version 2025-11-25. This local run is credential-free and reads a transparent fixture, so every claim can be reproduced.",
    "The voice request calls search rewards. RewardRadar ranks by payment-adjusted hourly value, not by the largest headline. The response keeps the source trail and labels planning assumptions.",
    "A follow-up calls plan pursuit with a time limit and minimum payout. It ranks only matching fixture evidence, reports the assumptions, and stops at a human confirmation gate. It never submits work, spends money, or claims guaranteed payment.",
    "A second question calls verify funding. Escrow, sponsor verification, and a payout rail are separate signals. Missing evidence lowers confidence; an advertised reward is never reported as money earned.",
    "The same project includes a focus-ready Fire TV web view and fail-closed Ring and Bee adapter boundaries. Fire TV still needs a simulator capture, Ring needs authorized API evidence, and Bee needs real Bee or Apple Watch data.",
    "This is a working Alexa Plus prototype, not a guarantee of a prize. It gives builders a faster, safer answer to one practical question: should I spend my next hour here?",
]


def font(size: int, bold: bool = False, mono: bool = False):
    root = Path("C:/Windows/Fonts")
    candidates = ([root / "consolab.ttf", root / "consola.ttf"] if mono else [root / ("segoeuib.ttf" if bold else "segoeui.ttf"), root / "arial.ttf"])
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def wrap(draw: ImageDraw.ImageDraw, value: str, max_width: int, chosen) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in value.split():
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=chosen)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def frame(number: int, kicker: str, title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 12), fill=ORANGE)
    draw.rectangle((58, 45, 116, 103), fill=ORANGE)
    draw.ellipse((73, 60, 101, 88), outline=WHITE, width=3)
    draw.text((137, 48), "RewardRadar", fill=INK, font=font(28, bold=True))
    draw.text((137, 82), "ALEXA+ PROTOTYPE", fill=MUTED, font=font(13, bold=True))
    draw.text((1500, 58), f"0{number}", fill=ORANGE, font=font(22, mono=True, bold=True))
    draw.text((70, 175), kicker.upper(), fill=ORANGE, font=font(18, bold=True))
    y = 220
    for line in wrap(draw, title, 1450, font(66, bold=True)):
        draw.text((70, y), line, fill=INK, font=font(66, bold=True))
        y += 73
    if subtitle:
        for line in wrap(draw, subtitle, 1380, font(24)):
            draw.text((72, y + 12), line, fill=MUTED, font=font(24))
            y += 34
    draw.line((70, 838, 1530, 838), fill="#c7c2b7", width=2)
    draw.text((70, 852), "Evidence visible. Assumptions disclosed.", fill=MUTED, font=font(17))
    return image, draw


def build_frames() -> list[Path]:
    WORK.mkdir(parents=True, exist_ok=True)
    frames: list[Image.Image] = []

    image, draw = frame(1, "Alexa+ · voice-first evidence", "ASK ONCE. HEAR THE EVIDENCE.", "A self-hosted MCP surface for deciding whether paid technical work is worth the next hour.")
    draw.rectangle((70, 520, 1530, 730), fill=INK)
    draw.text((108, 566), '"Which opportunity is worth my next two hours?"', fill=WHITE, font=font(32, bold=True))
    draw.text((108, 647), "Alexa+  →  RewardRadar  →  source-backed answer", fill="#ff9a73", font=font(23, mono=True))
    frames.append(image)

    image, draw = frame(2, "MCP transport", "A SMALL, INSPECTABLE SERVER.", "Streamable HTTP · MCP 2025-11-25 · no credentials in the demo")
    draw.rectangle((70, 475, 1530, 748), fill="#0e1b18")
    lines = [
        ("POST /mcp", ORANGE),
        ('{"method":"initialize","id":1}', WHITE),
        ('{"protocolVersion":"2025-11-25"}', GREEN),
        ('{"method":"tools/list","id":2}', WHITE),
        ('search_rewards · verify_funding · summarize_submission_status', "#b9ccc6"),
        ('plan_pursuit · read-only · owner confirmation required', "#ff9a73"),
    ]
    y = 515
    for text, color in lines:
        draw.text((110, y), text, fill=color, font=font(25, mono=True))
        y += 46
    frames.append(image)

    image, draw = frame(3, "Tool call · search_rewards", "THE LARGEST NUMBER IS NOT THE ANSWER.")
    draw.rectangle((70, 465, 760, 735), fill=WHITE, outline="#bbb6ac", width=2)
    draw.text((105, 500), "REQUEST", fill=MUTED, font=font(15, bold=True))
    draw.text((105, 548), "search_rewards", fill=INK, font=font(31, mono=True, bold=True))
    draw.text((105, 620), "query:  \"\"", fill=MUTED, font=font(22, mono=True))
    draw.text((105, 665), "limit:  3", fill=MUTED, font=font(22, mono=True))
    draw.rectangle((825, 465, 1530, 735), fill="#d8f6df", outline="#a8dfb5", width=2)
    draw.text((865, 500), "RESPONSE", fill=GREEN, font=font(15, bold=True))
    draw.text((865, 548), "$5,000 headline", fill=INK, font=font(35, mono=True, bold=True))
    draw.text((865, 615), "8% planning probability", fill=INK, font=font(24, mono=True))
    draw.text((865, 665), "Expected value: $400", fill=GREEN, font=font(25, mono=True, bold=True))
    frames.append(image)

    image, draw = frame(4, "Tool call · plan_pursuit", "A PLAN, NOT AN AUTOPILOT.", "Time-boxed ranking with an explicit human confirmation gate.")
    draw.rectangle((70, 475, 760, 735), fill=WHITE, outline="#bbb6ac", width=2)
    draw.text((105, 500), "REQUEST", fill=MUTED, font=font(15, bold=True))
    draw.text((105, 548), "plan_pursuit", fill=INK, font=font(31, mono=True, bold=True))
    draw.text((105, 620), "max_hours: 40", fill=MUTED, font=font(22, mono=True))
    draw.text((105, 665), "minimum_payout: $100", fill=MUTED, font=font(22, mono=True))
    draw.rectangle((825, 465, 1530, 735), fill="#fff0d8", outline="#e7bf84", width=2)
    draw.text((865, 500), "SAFE RESPONSE", fill=ORANGE, font=font(15, bold=True))
    draw.text((865, 548), "1 qualified match", fill=INK, font=font(30, mono=True, bold=True))
    draw.text((865, 615), "next: inspect source", fill=INK, font=font(23, mono=True))
    draw.text((865, 665), "owner confirmation required", fill=ORANGE, font=font(20, mono=True, bold=True))
    frames.append(image)

    image, draw = frame(5, "Tool call · verify_funding", "EVIDENCE GAPS STAY AUDIBLE.")
    draw.rectangle((70, 475, 1000, 735), fill=INK)
    checks = [("escrow", "not verified", RED), ("sponsor", "not verified", RED), ("payout rail", "owner setup", ORANGE)]
    y = 515
    for label, value, color in checks:
        draw.text((112, y), f"{label:<14}", fill="#b9ccc6", font=font(24, mono=True))
        draw.text((420, y), value, fill=color, font=font(24, mono=True, bold=True))
        y += 62
    draw.rectangle((1060, 475, 1530, 735), fill="#ffe0db", outline="#e4a99f", width=2)
    draw.text((1095, 515), "VOICE ANSWER", fill=RED, font=font(15, bold=True))
    draw.text((1095, 570), "NOT\nGUARANTEED", fill=RED, font=font(46, bold=True), spacing=4)
    draw.text((1095, 690), "headline ≠ income", fill=INK, font=font(20, mono=True, bold=True))
    frames.append(image)

    image, draw = frame(6, "One codebase · honest boundaries", "MORE DEVICES, NO FABRICATED EVIDENCE.")
    labels = [("ALEXA+", "MCP ready locally", GREEN), ("FIRE TV", "web view · capture pending", ORANGE), ("RING", "API token · device pending", ORANGE), ("BEE", "real export required", RED)]
    y = 475
    for label, value, color in labels:
        draw.rectangle((70, y, 1530, y + 54), fill=WHITE, outline="#d0cbc1", width=1)
        draw.text((105, y + 15), label, fill=INK, font=font(19, mono=True, bold=True))
        draw.text((440, y + 15), value, fill=color, font=font(19, mono=True))
        y += 64
    frames.append(image)

    image, draw = frame(7, "The product decision", "SHOULD I SPEND MY NEXT HOUR HERE?", "RewardRadar answers with traceable evidence, transparent uncertainty, and no promise of a prize.")
    draw.rectangle((70, 545, 1530, 730), fill=ORANGE)
    draw.text((110, 590), "WORKING ALEXA+ PROTOTYPE", fill=WHITE, font=font(34, bold=True))
    draw.text((110, 660), "search  ·  plan  ·  verify  ·  disclose", fill="#5a210e", font=font(24, mono=True, bold=True))
    frames.append(image)

    paths: list[Path] = []
    for index, item in enumerate(frames, start=1):
        path = WORK / f"frame-{index:02}.png"
        item.save(path)
        paths.append(path)
    return paths


VOICE = "en-US-GuyNeural"


def voice(text: str, destination: Path) -> None:
    """Render the narration with an explicitly male English voice.

    The checked-in video is a generated presentation asset, not a runtime
    dependency.  Fail loudly if the selected voice cannot be reached instead
    of silently falling back to a different voice.
    """
    compressed = destination.with_suffix(".mp3")
    asyncio.run(edge_tts.Communicate(text, VOICE).save(str(compressed)))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [ffmpeg, "-y", "-i", str(compressed), "-ar", "22050", "-ac", "1", str(destination)],
        capture_output=True,
        text=True,
    )
    compressed.unlink(missing_ok=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as source:
        return source.getnframes() / source.getframerate()


def run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def main() -> None:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    segments: list[Path] = []
    for index, (image, narration) in enumerate(zip(build_frames(), NARRATION, strict=True), start=1):
        audio = WORK / f"voice-{index:02}.wav"
        segment = WORK / f"segment-{index:02}.mp4"
        voice(narration, audio)
        seconds = duration(audio) + 0.8
        run([ffmpeg, "-y", "-loop", "1", "-framerate", "30", "-i", str(image), "-i", str(audio), "-t", f"{seconds:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(segment)])
        segments.append(segment)
    concat = WORK / "concat.txt"
    concat.write_text("\n".join(f"file '{path.as_posix()}'" for path in segments), encoding="utf-8")
    run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(output)])
    print(output)


if __name__ == "__main__":
    main()
