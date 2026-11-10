import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nudgely.reply import _engages_with  # noqa: E402


class EngagesWithTests(unittest.TestCase):
    def test_typos_and_run_together_words_count(self):
        self.assertTrue(_engages_with("Yes, we have durian in stock today!", "Do you have durain?"))
        self.assertTrue(_engages_with("Oat milk is back in stock now.", "Is oakmilk back in stock?"))
        self.assertTrue(_engages_with("In stock now: oat milk, durian, kai lan.", "What items do you have instock?"))
        self.assertTrue(_engages_with("Yes, eggs are in.", "got egg?"))  # plural / singular

    def test_real_drift_is_still_caught(self):
        self.assertFalse(_engages_with("Our shop opens 8am to 9pm daily.", "Do you have durian?"))
        self.assertFalse(_engages_with("Thanks for shopping with us!", "Is oat milk back?"))

    def test_short_words_do_not_fuzzy_match(self):
        self.assertFalse(_engages_with("We sell tea.", "any pie?"))


if __name__ == "__main__":
    unittest.main()
