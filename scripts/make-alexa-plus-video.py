"""Backward-compatible entry point for the live, male-narrated video renderer."""

from pathlib import Path
import runpy
import sys


if __name__ == "__main__":
    renderer = Path(__file__).with_name("render-alexa-plus-video.py")
    runpy.run_path(str(renderer), run_name="__main__")
