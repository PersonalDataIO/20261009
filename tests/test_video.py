import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from deckgen.video import HOST_URL, load_video_deck, prepare_story, render_preview, subtitles

ROOT = Path(__file__).resolve().parents[1]
STORY = ROOT / "content/videos/01-flair.yaml"


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.deck = load_video_deck(ROOT, STORY)

    def test_draft_uses_deck_titles_and_contiguous_timing(self):
        story = prepare_story(self.deck, STORY, draft=True)
        self.assertGreater(story["duration"], 52)
        self.assertEqual(story["scenes"][2]["text"], self.deck.by_id()["1T"].titre)
        self.assertEqual(len(story["cards"]), 8)
        for previous, current in zip(story["scenes"], story["scenes"][1:]):
            self.assertEqual(previous["end"], current["start"])
        self.assertIn("BROUILLON", render_preview(ROOT, story))
        self.assertIn(self.deck.by_id()["1L"].texte, subtitles(story))

    def test_storyboard_can_render_in_english(self):
        deck = load_video_deck(ROOT, STORY, "en")
        story = prepare_story(deck, STORY, draft=True, language="en")
        preview = render_preview(ROOT, story)
        self.assertEqual(story["theme"], "Intuition")
        self.assertEqual(story["scenes"][1]["label"], "Drivers and Mathematicians")
        self.assertEqual(story["scenes"][2]["text"], deck.by_id()["1T"].titre)
        self.assertIn('<html lang="en">', preview)
        self.assertIn("A shared Lever", preview)
        self.assertIn("A shared Lever:", subtitles(story))

    def test_public_export_requires_explicit_verification(self):
        self.deck.by_id()["1R"].a_verifier = True
        with self.assertRaisesRegex(ValueError, "1R requires editorial verification"):
            prepare_story(self.deck, STORY)

    def test_rights_storyboard_in_both_languages(self):
        path = ROOT / "content/videos/07-droits.yaml"
        for language, theme in [("fr", "Droits"), ("en", "Rights")]:
            with self.subTest(language=language):
                deck = load_video_deck(ROOT, path, language)
                story = prepare_story(deck, path, draft=True, language=language)
                self.assertEqual(story["theme"], theme)
                self.assertGreater(story["duration"], 52)
                self.assertEqual(len(story["scenes"]), 9)
                self.assertEqual(story["scenes"][2]["text"], deck.by_id()["7T"].titre)
                self.assertEqual(story["scenes"][-2]["card"], "7L")
                self.assertNotIn("7mQc", render_preview(ROOT, story))
                deck.by_id()["7R"].a_verifier = True
                with self.assertRaisesRegex(ValueError, "7R requires editorial verification"):
                    prepare_story(deck, path, language=language)

    def test_rights_action_requires_verification_too(self):
        path = ROOT / "content/videos/07-droits.yaml"
        deck = load_video_deck(ROOT, path)
        deck.by_id()["7L"].a_verifier = True
        source = yaml.safe_load(path.read_text(encoding="utf-8"))
        source["scenes"][2]["verified"] = True
        next(scene for scene in source["scenes"] if scene.get("card") == "7Qc")["verified"] = True
        with tempfile.TemporaryDirectory() as directory:
            edited = Path(directory) / "story.yaml"
            edited.write_text(yaml.safe_dump(source), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "7L requires editorial verification"):
                prepare_story(deck, edited)

    def test_opening_and_cta_use_configurable_host_url(self):
        for language in ["fr", "en"]:
            with self.subTest(language=language), patch.dict("os.environ", {}, clear=True):
                deck = load_video_deck(ROOT, STORY, language)
                story = prepare_story(deck, STORY, draft=True, language=language)
                self.assertEqual(story["url"], HOST_URL)
                self.assertEqual(story["scenes"][0]["kind"], "explanation")
                self.assertIn("Uber", story["scenes"][0]["detail"])
                self.assertEqual(story["scenes"][-1]["text"], "Explore the game!")
                self.assertEqual(story["scenes"][-1]["start"], story["duration"] - 12)
                self.assertIn(f'href="{HOST_URL}"', render_preview(ROOT, story))
                with patch.dict("os.environ", {"HOST_URL": "https://example.org/game/"}):
                    changed = prepare_story(deck, STORY, draft=True, language=language)
                    self.assertEqual(changed["url"], "https://example.org/game/")
                    self.assertIn('href="https://example.org/game/"', render_preview(ROOT, changed))
                with patch.dict("os.environ", {"HOST_URL": "javascript:alert(1)"}):
                    with self.assertRaisesRegex(ValueError, "HOST_URL"):
                        prepare_story(deck, STORY, draft=True, language=language)

    def test_closing_cta_has_separate_proposal_links_before_final_url(self):
        deck = load_video_deck(ROOT, STORY, "en")
        story = prepare_story(deck, STORY, draft=True, language="en")
        preview = render_preview(ROOT, story)
        closing_start = preview.rindex('<section class="scene cta')
        closing = preview[closing_start:preview.index("</section>", closing_start)]
        self.assertEqual(closing.count('>Contact us</a>'), 3)
        self.assertEqual(closing.count('class="proposal"'), 3)
        self.assertLess(closing.index("Want to hold a workshop in Geneva?"), closing.index(f">{HOST_URL}</a>"))
        self.assertEqual([proposal["text"] for proposal in story["scenes"][-1]["proposals"]], [
            "Want to play with Uber drivers in your city?",
            "Want to play with your math department?",
            "Want to hold a workshop in Geneva?",
        ])

    def test_verified_export_and_invalid_storyboards(self):
        self.deck.by_id()["1R"].a_verifier = True
        source = yaml.safe_load(STORY.read_text(encoding="utf-8"))
        source["scenes"][2]["verified"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "story.yaml"
            path.write_text(yaml.safe_dump(source), encoding="utf-8")
            self.assertFalse(prepare_story(self.deck, path)["draft"])
            for field, value in [("duration", 0), ("duration", float("nan")), ("card", "2T"), ("kind", "unknown")]:
                invalid = copy.deepcopy(source)
                invalid["scenes"][1][field] = value
                path.write_text(yaml.safe_dump(invalid), encoding="utf-8")
                with self.assertRaises(ValueError):
                    prepare_story(self.deck, path, draft=True)

    def test_complete_cards_echo_and_directed_questions(self):
        for filename, number in [("01-flair.yaml", "1"), ("07-droits.yaml", "7")]:
            for language in ["fr", "en"]:
                with self.subTest(filename=filename, language=language):
                    path = ROOT / "content/videos" / filename
                    deck = load_video_deck(ROOT, path, language)
                    story = prepare_story(deck, path, draft=True, language=language)
                    scenes = [scene for scene in story["scenes"] if scene.get("card")]
                    self.assertEqual([scene["card"] for scene in scenes[:5]],
                                     [number + code for code in ["T", "R", "E", "Qc", "Qm"]])
                    preview = render_preview(ROOT, story)
                    self.assertNotIn('class="card-id"', preview)
                    self.assertNotIn('class="overview"', preview)
                    for scene in scenes:
                        card = deck.by_id()[scene["card"]]
                        self.assertEqual(scene["text"], card.titre)
                        self.assertEqual(scene["detail"], card.texte)
                        self.assertEqual(scene["type_name"], deck.types[card.type]["nom"])
                        self.assertNotIn(card.id, preview)
                        word_count = len((card.titre + " " + card.texte).split())
                        self.assertGreaterEqual(scene["duration"], 3 + word_count / 2.5)
                    questions = [scene for scene in scenes if scene["kind"] == "question"]
                    self.assertEqual(len(questions), 2)
                    self.assertEqual(questions[0]["sender"], questions[1]["recipient"])
                    self.assertEqual(questions[0]["recipient"], questions[1]["sender"])
                    self.assertIn("Uber", questions[0]["sender"])

    def test_new_rights_question_requires_verification(self):
        path = ROOT / "content/videos/07-droits.yaml"
        deck = load_video_deck(ROOT, path)
        deck.by_id()["7Qc"].a_verifier = True
        source = yaml.safe_load(path.read_text(encoding="utf-8"))
        source["scenes"][2]["verified"] = True
        with tempfile.TemporaryDirectory() as directory:
            edited = Path(directory) / "story.yaml"
            edited.write_text(yaml.safe_dump(source), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "7Qc requires editorial verification"):
                prepare_story(deck, edited)


if __name__ == "__main__":
    unittest.main()