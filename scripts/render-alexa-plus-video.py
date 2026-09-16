"""Capture the running Alexa+ prototype, add male narration, and render a captioned demo."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
import tempfile
import wave
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

import edge_tts
import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "public" / "media" / "AlexaPlus-demo-v0.4.mp4"
DEFAULT_CAPTIONS = ROOT / "submission" / "VIDEO_NARRATION_EN_v0.4.srt"
VOICE = "en-US-AndrewNeural"
FPS = 30
SILENCE_SECONDS = 0.22
FADE_SECONDS = 0.35

SCENES = [
    (
        "search",
        "A reward headline is only the start of the story. Is the work still open? Is the sponsor verifiable? Can the payout actually reach you? RewardRadar is built to help answer one practical question before you commit your next hour.",
    ),
    (
        "search",
        "Here, the user asks whether any available work is worth pursuing. This is a voice-client simulation: the visual interface turns that request into a real tool call to RewardRadar's local Model Context Protocol server.",
    ),
    (
        "search",
        "The client negotiates MCP twenty twenty-five dash eleven dash twenty-five, discovers the available tools, and requests a search. The server ranks its timestamped demonstration records and returns structured results with the source, assumptions, and a planning verdict.",
    ),
    (
        "funding",
        "Now we inspect funding instead of trusting the headline. Escrow, sponsor verification, acceptance criteria, and payout setup are separate signals. Missing evidence remains visible. A listed reward is never described as money already earned.",
    ),
    (
        "status",
        "RewardRadar checks the submission record, too. The Alexa-plus Devpost entry is submitted. No award has been announced, and no payment has been received. Those are three different states, and the interface keeps them distinct.",
    ),
    (
        "status",
        "This prototype runs locally on a checked-in fixture. It is not connected to an Alexa device or a live rewards feed, and its planning estimates are not guarantees. RewardRadar makes the evidence easier to hear—and easier to inspect—before you decide what to do next.",
    ),
]


def run(command: list[str], *, cwd: Path | None = None, timeout: int = 180) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def ensure_services(endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1"}
        or parsed.path != "/mcp"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("The video renderer only accepts a local HTTP MCP endpoint ending in /mcp.")
    health_url = f"{parsed.scheme}://{parsed.netloc}/health"
    for url in ("http://localhost:5173/", health_url):
        try:
            with urlopen(url, timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError(f"Local service returned HTTP {response.status}: {url}")
        except Exception as exc:
            raise RuntimeError(
                "Start the website with `pnpm dev` and the MCP fixture with "
                "`python -m agent.alexa_mcp_server --port 8787`, then rerun this script."
            ) from exc


def srt_stamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def caption_chunks(text: str, max_words: int = 7) -> list[str]:
    pieces: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        words = sentence.split()
        for start in range(0, len(words), max_words):
            pieces.append(" ".join(words[start : start + max_words]))
    return pieces


async def synthesize(text: str, destination: Path) -> None:
    await edge_tts.Communicate(
        text,
        voice=VOICE,
        rate="-3%",
        pitch="-1Hz",
        volume="+0%",
    ).save(str(destination))


def write_combined_wav(paths: list[Path], destination: Path) -> tuple[list[float], list[float]]:
    durations: list[float] = []
    starts: list[float] = []
    with wave.open(str(paths[0]), "rb") as first:
        params = first.getparams()
        silence = b"\x00" * round(params.framerate * SILENCE_SECONDS) * params.nchannels * params.sampwidth
    cursor = 0.0
    with wave.open(str(destination), "wb") as output:
        output.setparams(params)
        for index, path in enumerate(paths):
            with wave.open(str(path), "rb") as source:
                if source.getparams()[:3] != params[:3]:
                    raise RuntimeError("Narration segments have incompatible audio formats")
                starts.append(cursor)
                duration = source.getnframes() / source.getframerate()
                durations.append(duration)
                output.writeframes(source.readframes(source.getnframes()))
                cursor += duration
            if index < len(paths) - 1:
                output.writeframes(silence)
                cursor += SILENCE_SECONDS
    return starts, durations


def write_captions(path: Path, starts: list[float], durations: list[float]) -> None:
    entries: list[str] = []
    cue = 1
    for (_, narration), start, duration in zip(SCENES, starts, durations, strict=True):
        chunks = caption_chunks(narration)
        total_words = sum(len(chunk.split()) for chunk in chunks)
        word_cursor = 0
        for chunk in chunks:
            words = len(chunk.split())
            cue_start = start + duration * word_cursor / total_words
            cue_end = start + duration * (word_cursor + words) / total_words
            entries.append(f"{cue}\n{srt_stamp(cue_start)} --> {srt_stamp(cue_end)}\n{chunk}\n")
            cue += 1
            word_cursor += words
    path.write_text("\n".join(entries), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--captions-output", type=Path, default=DEFAULT_CAPTIONS)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8787/mcp")
    args = parser.parse_args()
    output = args.output.resolve()
    captions_output = args.captions_output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    captions_output.parent.mkdir(parents=True, exist_ok=True)
    ensure_services(args.endpoint)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    with tempfile.TemporaryDirectory(prefix="rewardradar-video-") as temporary:
        workspace = Path(temporary)
        audio_dir = workspace / "audio"
        frames_dir = workspace / "frames"
        audio_dir.mkdir()
        frames_dir.mkdir()

        wavs: list[Path] = []
        for index, (_, narration) in enumerate(SCENES, start=1):
            mp3 = audio_dir / f"voice-{index:02d}.mp3"
            wav = audio_dir / f"voice-{index:02d}.wav"
            asyncio.run(synthesize(narration, mp3))
            run([ffmpeg, "-y", "-i", str(mp3), "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)])
            wavs.append(wav)

        narration_path = workspace / "narration.wav"
        starts, durations = write_combined_wav(wavs, narration_path)
        total_duration = starts[-1] + durations[-1]
        timeline = {
            "duration": round(total_duration, 3),
            "actions": [
                {"at": round(starts[1] + 0.12, 3), "button": "Run voice request"},
            {"at": round(starts[3] + 0.12, 3), "button": "Verify the money"},
            {"at": round(starts[4] + 0.12, 3), "button": "Check submission status"},
            {"at": round(starts[5] + 0.5, 3), "scrollToY": 430},
        ],
        }
        timeline_path = workspace / "timeline.json"
        timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
        capture_script = ROOT / "scripts" / "capture-alexa-screencast.mjs"
        capture_log = run([
            "node",
            str(capture_script),
            f"--frames-dir={frames_dir}",
            f"--timeline={timeline_path}",
            "--url=http://localhost:5173/",
            f"--endpoint={args.endpoint}",
        ], timeout=int(total_duration + 90))
        print(capture_log.strip())

        write_captions(captions_output, starts, durations)
        local_captions = workspace / "captions.srt"
        local_captions.write_bytes(captions_output.read_bytes())
        subtitles = (
            "subtitles=captions.srt:force_style="
            "'PlayResX=1920,PlayResY=1080,FontName=Arial,FontSize=25,PrimaryColour=&H00F7F7F3,"
            "BackColour=&HCC08130F,BorderStyle=4,Outline=1,Shadow=0,"
            "MarginV=42,Alignment=2'"
        )
        run([
            ffmpeg,
            "-y",
            "-framerate",
            str(FPS),
            "-start_number",
            "1",
            "-i",
            str(frames_dir / "frame_%06d.jpg"),
            "-i",
            str(narration_path),
            "-vf",
            subtitles,
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-t",
            f"{total_duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-metadata",
            "title=RewardRadar | Alexa+ Opportunity Scout",
            "-metadata",
            "artist=RewardRadar",
            "-metadata",
            "comment=Local MCP prototype using a timestamped fixture; no live Alexa device or payment claim.",
            str(output),
        ], cwd=workspace, timeout=600)

    print(f"Video: {output}")
    print(f"Narration: {VOICE} (male, natural U.S. English)")
    print(f"Runtime: {total_duration:.1f} seconds; captions burned in and saved to {captions_output}")


if __name__ == "__main__":
    main()
