import json
import re
import unittest
from pathlib import Path

from deckgen.loader import load
from deckgen.render import build_html
from deckgen.video import load_video_deck, prepare_story, render_preview

ROOT = Path(__file__).resolve().parents[1]


class VideoDownloadTests(unittest.TestCase):
    def test_all_family_downloads_match_language(self):
        for language in ["fr", "en"]:
            html = build_html(ROOT, load(ROOT, language), language)
            data = json.loads(re.search(r'<script id="deck-data" type="application/json">(.*?)</script>', html, re.S).group(1))
            families = [section for section in data["sections"] if section["video"]]
            self.assertEqual(len(families), 8)
            for section in families:
                self.assertTrue(section["video"].startswith("videos/" if language == "fr" else "../videos/"))
                self.assertTrue(section["video"].endswith("-en.mp4" if language == "en" else ".mp4"))
                self.assertIn(f'href="{section["video"]}" download', html)

    def test_all_storyboards_export_without_draft(self):
        paths = sorted((ROOT / "content/videos").glob("[0-9][0-9]-*.yaml"))
        self.assertEqual(len(paths), 8)
        for path in paths:
            for language in ["fr", "en"]:
                story = prepare_story(load_video_deck(ROOT, path, language), path, language=language)
                self.assertFalse(story["draft"])
                self.assertIn('class="type-box"', render_preview(ROOT, story))