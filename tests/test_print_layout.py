import re
import unittest
from pathlib import Path

from deckgen.loader import load
from deckgen.render import build_html

ROOT = Path(__file__).resolve().parents[1]


class PrintLayoutTests(unittest.TestCase):
    def test_2x1_uses_landscape_sheets_with_matching_back_positions(self):
        deck = load(ROOT, "fr")
        html = build_html(ROOT, deck, "fr")
        pages = re.findall(r'<section class="page print-2x1">.*?</section>', html, re.DOTALL)
        self.assertGreaterEqual(len(pages), 2)

        first_sheet_ids = [card.id for card in deck.cards[:2]]
        back_aria = deck.config["ui"]["back_aria"]
        self.assertIn(".page.print-2x1{width:297mm;height:210mm;page:landscape-a4}", html)
        self.assertIn(".sheet.grid-2x1{grid-template-columns:repeat(2,148.5mm);grid-auto-rows:210mm}", html)
        verso_ids = re.findall(r'aria-label="' + re.escape(back_aria) + r' ([^"]+)"', pages[1])
        self.assertEqual(verso_ids, first_sheet_ids)
        self.assertEqual(pages[0].count('class="cell rotate-back"'), 0)
        self.assertEqual(pages[1].count('class="cell rotate-back"'), 2)
        self.assertIn(".sheet.grid-2x1 .rotate-back .card{transform:translate(148.5mm,210mm) rotate(180deg) scale(2.357143,2.386364)}", html)


if __name__ == "__main__":
    unittest.main()