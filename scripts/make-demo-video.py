"""Generate the submission demo video from repository-native assets.

The script intentionally avoids cloud video services. It creates nine 16:9 frames,
uses the local Windows speech engine, and muxes them with the ffmpeg binary bundled
by imageio-ffmpeg. Output is a standard H.264/AAC MP4 suitable for Devpost.
"""

from __future__ import annotations

import subprocess
import sys
import wave
from pathlib import Path

import imageio_ffmpeg
import pyttsx3
from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1600, 900
INK = "#172a25"
PAPER = "#f3f0e9"
WHITE = "#fffdf8"
ORANGE = "#ff5d24"
GREEN = "#2e9f50"
MUTED = "#69736e"
RED = "#a5372b"

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / "work" / "rewardradar-video"
DEFAULT_OUTPUT = ROOT.parent / "outputs" / "RewardRadar-demo.mp4"

NARRATION = [
    "A bounty feed shows advertised money. It does not show whether the work is still available, whether ten people already claimed it, or whether the payment mechanism can actually reach you. Reward Radar answers the professional question: should I spend my next hour here?",
    "In a time stamped September tenth evidence capture, repository scripts queried three public feeds. Of thirty advertised Opire rows, only eight canonical issues were open. Twenty two were eliminated before coding. Execution Market exposed twenty six tasks worth one dollar and seventy eight cents in total, while a separate Superteam capture found one then open agent eligible listing among twenty one rows.",
    "Reward Radar implements a real four node Strands Graph Builder pipeline. The credential free run uses Demo Model, a deterministic adapter that makes one prescribed tool call per node. It demonstrates executable orchestration and tool plumbing, not open ended model reasoning.",
    "The credential free demo runs each Strands node over the same disclosed fixture and prints each node's tool invocation and result. Judges can reproduce that deterministic run with one command. A separate entry point runs the same graph through Amazon Bedrock once A W S access is configured.",
    "One issue advertised more than three thousand dollars. But the canonical discussion was locked, ten claimers were already competing, and payment was not escrowed. Reward Radar cut the practical probability below one percent and said avoid. The highest payout is not always the best opportunity.",
    "The Superteam verifier found one live agent eligible competition with ten submissions and individual prizes from one hundred to two hundred fifty U S D C. But qualifying requires a public X post and at least five Solana mainnet trades. The sponsor was not marked verified, payment was sponsor direct, and the API deadline conflicts with the written close. Reward Radar said avoid: do not risk real capital on a headline.",
    "In the disclosed fixture, the Professional Agents track ranked first: a five thousand dollar gold prize, with a two thousand dollar podium floor. The eight percent payment probability is an explicit planning assumption, not a measured prediction. Deterministic arithmetic produces a four hundred dollar expected value before effort.",
    "In this demo, fixed Python formulas apply transparent risk multipliers and compute expected value from explicit fixture inputs. Demo Model does not perform open ended reasoning, and no hosted model run is claimed yet. Source links and payout gaps stay visible, and advertised money is never reported as earned.",
    "Reward Radar does not find more work. It finds the work worth doing. Four Strands agents, deterministic guardrails, transparent uncertainty, and one qualified pursuit. Stop chasing phantom bounties. Start verifying.",
]


def font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    windows = Path("C:/Windows/Fonts")
    if mono:
        candidates = [windows / "consolab.ttf", windows / "consola.ttf"]
    elif bold:
        candidates = [windows / "arialbd.ttf", windows / "segoeuib.ttf"]
    else:
        candidates = [windows / "segoeui.ttf", windows / "arial.ttf"]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


def wrap(draw: ImageDraw.ImageDraw, text: str, max_width: int, chosen: ImageFont.FreeTypeFont) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
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


def base_frame(index: int, kicker: str, title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 12), fill=ORANGE)
    draw.rectangle((58, 45, 116, 103), fill=ORANGE)
    draw.ellipse((73, 60, 101, 88), outline=WHITE, width=3)
    draw.ellipse((80, 67, 94, 81), outline=WHITE, width=2)
    draw.text((137, 48), "RewardRadar", fill=INK, font=font(28, bold=True))
    draw.text((137, 82), "STRANDS AGENT SYSTEM", fill=MUTED, font=font(13, bold=True))
    draw.text((1500, 58), f"0{index}", fill=ORANGE, font=font(22, mono=True, bold=True))
    draw.text((70, 176), kicker.upper(), fill=ORANGE, font=font(18, bold=True))
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


def card(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], label: str, value: str, note: str, accent: str = INK) -> None:
    draw.rectangle(xy, fill=WHITE, outline="#bbb6ac", width=2)
    x1, y1, x2, _ = xy
    draw.rectangle((x1, y1, x1 + 9, xy[3]), fill=accent)
    draw.text((x1 + 28, y1 + 24), label.upper(), fill=MUTED, font=font(15, bold=True))
    draw.text((x1 + 28, y1 + 63), value, fill=INK, font=font(44, mono=True, bold=True))
    draw.text((x1 + 28, y1 + 120), note, fill=MUTED, font=font(18))


def build_frames() -> list[Path]:
    WORK.mkdir(parents=True, exist_ok=True)
    frames: list[Image.Image] = []

    image, draw = base_frame(1, "The professional question", "DON’T CHASE THE HEADLINE PAYOUT.", "RewardRadar measures whether an opportunity is still real, payable, and worth the next hour.")
    draw.rectangle((70, 530, 1530, 770), fill=INK)
    draw.text((108, 570), "$3,280 advertised", fill=WHITE, font=font(47, mono=True, bold=True))
    draw.text((108, 646), "≠", fill=ORANGE, font=font(54, bold=True))
    draw.text((190, 650), "money earned", fill="#c8d8d3", font=font(42, bold=True))
    frames.append(image)

    image, draw = base_frame(2, "Time-stamped evidence capture", "PUBLIC FEEDS CAPTURED. RESULTS TIME-STAMPED.")
    card(draw, (70, 470, 410, 695), "Opire advertised", "30", "$518K displayed total", ORANGE)
    card(draw, (430, 470, 770, 695), "Canonical open", "8", "22 eliminated", GREEN)
    card(draw, (790, 470, 1130, 695), "Execution", "$1.78", "26 tasks", INK)
    card(draw, (1150, 470, 1530, 695), "Agent eligible", "1", "Superteam · 21 rows", ORANGE)
    frames.append(image)

    image, draw = base_frame(3, "Strands graph", "FOUR STRANDS NODES. ONE INSPECTABLE RANKING.")
    labels = [("01", "SCOUT", "normalize"), ("02", "VERIFIER", "source truth"), ("03", "RISK", "friction"), ("04", "ROI", "rank")]
    for idx, (number, name, note) in enumerate(labels):
        x = 70 + idx * 370
        draw.rectangle((x, 470, x + 310, 680), fill=INK)
        draw.text((x + 24, 492), number, fill=ORANGE, font=font(18, mono=True, bold=True))
        draw.text((x + 24, 545), name, fill=WHITE, font=font(34, bold=True))
        draw.text((x + 24, 605), note, fill="#b7cbc4", font=font(19))
        if idx < 3:
            draw.line((x + 316, 575, x + 354, 575), fill=ORANGE, width=5)
            draw.polygon([(x + 354, 575), (x + 340, 565), (x + 340, 585)], fill=ORANGE)
    frames.append(image)

    image, draw = base_frame(4, "Reproducible working demo", "FOUR NODES RUN. EVERY TOOL CALL IS VISIBLE.")
    draw.rectangle((70, 430, 1530, 760), fill="#0e1b18")
    draw.text((105, 456), "$ python -m agent.demo", fill="#ff9a73", font=font(23, mono=True, bold=True))
    console = [
        ("SCOUT", "4 disclosed audit representatives loaded", "#d6e2de"),
        ("VERIFIER", "canonical state + lock evidence preserved", "#d6e2de"),
        ("RISK", "locked · crowded · non-escrowed", "#ff9a73"),
        ("ROI", "PURSUE cash hackathon  ·  EXPECTED $400", "#66d184"),
    ]
    y = 520
    for role, line, color in console:
        draw.text((108, y), f"[{role:<8}]", fill=ORANGE, font=font(21, mono=True, bold=True))
        draw.text((300, y), line, fill=color, font=font(21, mono=True))
        y += 55
    draw.text((1190, 710), "exit 0  OK", fill="#66d184", font=font(18, mono=True, bold=True))
    frames.append(image)

    image, draw = base_frame(5, "Risk verdict", "A LARGE NUMBER CAN STILL BE A BAD BET.")
    draw.rectangle((70, 470, 1020, 715), fill=WHITE, outline="#bbb6ac", width=2)
    draw.text((104, 500), "Open-source issue", fill=MUTED, font=font(16, bold=True))
    draw.text((104, 545), "$3,280", fill=INK, font=font(56, mono=True, bold=True))
    draw.text((104, 630), "LOCKED   ·   10 CLAIMERS   ·   NOT ESCROWED", fill=RED, font=font(22, mono=True, bold=True))
    draw.rectangle((1060, 470, 1530, 715), fill="#ffe0db", outline="#e4a99f", width=2)
    draw.text((1094, 505), "VERDICT", fill=RED, font=font(16, bold=True))
    draw.text((1094, 555), "AVOID", fill=RED, font=font(64, bold=True))
    draw.text((1094, 645), "P(payment) < 1%", fill=INK, font=font(22, mono=True, bold=True))
    frames.append(image)

    image, draw = base_frame(6, "Capital-gated listing", "OPEN DOES NOT MEAN LOW-RISK.")
    card(draw, (70, 470, 410, 695), "Prize floor", "$100", "10 submissions", GREEN)
    card(draw, (430, 470, 770, 695), "Mainnet", "5 trades", "real capital", RED)
    card(draw, (790, 470, 1130, 695), "Social", "Public X", "required", RED)
    card(draw, (1150, 470, 1530, 695), "Payment", "Direct", "sponsor unverified", RED)
    draw.rectangle((70, 730, 1530, 792), fill="#ffe0db", outline="#e4a99f", width=2)
    draw.text((104, 747), "STRUCTURED DEADLINE ≠ WRITTEN CLOSE", fill=RED, font=font(21, mono=True, bold=True))
    frames.append(image)

    image, draw = base_frame(7, "Selected pursuit", "THE DISCLOSED FIXTURE RANKED THIS FIRST.")
    card(draw, (70, 470, 430, 705), "Gold prize", "$5,000", "cash", ORANGE)
    card(draw, (450, 470, 810, 705), "Podium floor", "$2,000", "cash", GREEN)
    card(draw, (830, 470, 1170, 705), "Planning assumption", "8%", "explicit", INK)
    card(draw, (1190, 470, 1530, 705), "Expected value", "$400", "before effort", ORANGE)
    frames.append(image)

    image, draw = base_frame(8, "Deterministic core", "GUARDRAILS, NOT VIBES.")
    draw.rectangle((70, 455, 1530, 740), fill="#132c27")
    code = [
        ('if status != "open":', WHITE),
        ('    probability = 0', "#66d184"),
        ('probability *= 1 / (1 + 0.24 * claimers)', "#ff9a73"),
        ('expected_value = payout * probability', WHITE),
        ('verdict = "pursue" | "watch" | "avoid"', "#66d184"),
    ]
    y = 486
    for text, color in code:
        draw.text((112, y), text, fill=color, font=font(25, mono=True))
        y += 46
    frames.append(image)

    image, draw = base_frame(9, "The outcome", "STOP CHASING. START VERIFYING.", "RewardRadar finds the work worth doing: transparent uncertainty, traceable evidence, and one qualified pursuit.")
    draw.rectangle((70, 550, 1530, 730), fill=ORANGE)
    draw.text((110, 585), "cuentapraces07-ops.github.io/rewardradar/", fill=WHITE, font=font(34, mono=True, bold=True))
    draw.text((110, 652), "STRANDS · PYTHON · REACT · MIT", fill="#5a210e", font=font(19, bold=True))
    frames.append(image)

    paths: list[Path] = []
    for index, frame in enumerate(frames, start=1):
        path = WORK / f"frame-{index:02}.png"
        frame.save(path, quality=95)
        paths.append(path)
    return paths


def voice_for(text: str, destination: Path) -> None:
    engine = pyttsx3.init()
    engine.setProperty("rate", 168)
    engine.setProperty("volume", 0.95)
    voices = engine.getProperty("voices")
    english = next((voice for voice in voices if "english" in voice.name.lower() or "zira" in voice.name.lower()), None)
    if english is not None:
        engine.setProperty("voice", english.id)
    engine.save_to_file(text, str(destination))
    engine.runAndWait()
    engine.stop()


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as source:
        return source.getnframes() / source.getframerate()


def run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    if completed.returncode:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise SystemExit(completed.returncode)


def main() -> None:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = build_frames()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    segments: list[Path] = []

    for index, (frame, narration) in enumerate(zip(frames, NARRATION, strict=True), start=1):
        audio = WORK / f"voice-{index:02}.wav"
        segment = WORK / f"segment-{index:02}.mp4"
        voice_for(narration, audio)
        duration = wav_duration(audio) + 0.8
        frames_count = max(1, int(duration * 30))
        run(
            [
                ffmpeg,
                "-y",
                "-loop",
                "1",
                "-framerate",
                "30",
                "-i",
                str(frame),
                "-i",
                str(audio),
                "-vf",
                f"zoompan=z='min(zoom+0.00018,1.025)':d={frames_count}:s=1600x900:fps=30,format=yuv420p",
                "-af",
                "apad=pad_dur=0.8",
                "-t",
                f"{duration:.3f}",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                str(segment),
            ]
        )
        segments.append(segment)

    concat_file = WORK / "concat.txt"
    concat_file.write_text("".join(f"file '{path.as_posix()}'\n" for path in segments), encoding="utf-8")
    run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    print(output)


if __name__ == "__main__":
    main()
