#!/usr/bin/env python3
"""Export a family storyboard as a deterministic vertical MP4."""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

from deckgen.video import load_video_deck, prepare_story, render_preview, subtitles

ROOT = Path(__file__).resolve().parent


def export_video(preview: Path, story: dict, width: int, fps: int) -> None:
    from playwright.sync_api import sync_playwright

    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is required for MP4 export")
    height = width * 16 // 9
    output = preview.with_suffix(".mp4")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            page.goto(preview.as_uri() + "?export=1", wait_until="networkidle")
            page.evaluate("() => document.fonts.ready")
            page.evaluate("window.renderFrame(1.5)")
            page.screenshot(path=str(preview.with_suffix(".png")))
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                       "-f", "image2pipe", "-framerate", str(fps), "-vcodec", "mjpeg", "-i", "-",
                       "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                       "-vf", "scale=in_range=full:out_range=tv", "-color_range", "tv",
                       "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
            with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
                try:
                    cached_scene = None
                    cached_image = None
                    for frame in range(math.ceil(story["duration"] * fps)):
                        seconds = frame / fps
                        scene = next(item for item in story["scenes"] if item["start"] <= seconds < item["end"])
                        holding = seconds >= scene["start"] + 0.65 and seconds <= scene["end"] - 0.25
                        if not holding or cached_scene != scene["start"]:
                            page.evaluate("window.renderFrame", seconds)
                            image = page.screenshot(type="jpeg", quality=95)
                            if holding:
                                cached_scene, cached_image = scene["start"], image
                        else:
                            image = cached_image
                        encoder.stdin.write(image)
                        if frame % (fps * 5) == 0:
                            print(f"Rendering {frame / fps:.0f}/{story['duration']:.0f}s", flush=True)
                finally:
                    encoder.stdin.close()
                if encoder.wait() != 0:
                    raise RuntimeError("FFmpeg failed to encode the video")
        finally:
            browser.close()
    print(f"Video: {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", type=Path, default=ROOT / "content/videos/01-flair.yaml")
    parser.add_argument("--all", action="store_true", help="export every family storyboard")
    parser.add_argument("--out", type=Path, default=ROOT / "dist/videos")
    parser.add_argument("--draft", action="store_true", help="mark unverified exports as drafts")
    parser.add_argument("--language", choices=["fr", "en", "both"], default="fr", help="storyboard language")
    parser.add_argument("--preview-only", action="store_true", help="build HTML and subtitles without Chromium")
    parser.add_argument("--width", type=int, choices=[540, 1080], default=1080)
    parser.add_argument("--fps", type=int, choices=[24, 30], default=24)
    args = parser.parse_args()
    try:
        args.out.mkdir(parents=True, exist_ok=True)
        paths = sorted((ROOT / "content/videos").glob("[0-9][0-9]-*.yaml")) if args.all else [args.story]
        languages = ["fr", "en"] if args.language == "both" else [args.language]
        for path in paths:
            for language in languages:
                story = prepare_story(load_video_deck(ROOT, path, language), path, args.draft, language)
                slug = story["slug"]
                if not isinstance(slug, str) or not slug or Path(slug).name != slug or slug in {".", ".."}:
                    raise ValueError("The storyboard slug must be a plain filename")
                preview = args.out / f"{slug}{'-en' if language == 'en' else ''}{'-draft' if args.draft else ''}.html"
                preview.write_text(render_preview(ROOT, story), encoding="utf-8")
                preview.with_suffix(".srt").write_text(subtitles(story), encoding="utf-8")
                preview.with_suffix(".json").write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"Preview: {preview}")
                if not args.preview_only:
                    export_video(preview.resolve(), story, args.width, args.fps)
    except (ValueError, RuntimeError, ImportError) as error:
        parser.exit(1, f"Video export: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())