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

    def test_chatty_questions_with_no_topic_word(self):
        # Live 13 Nov: the full stock list was thrown away because "guys" wasn't in it.
        self.assertTrue(_engages_with("Right now we have oat milk, eggs and durian.", "So what do you guys have?"))
        self.assertTrue(_engages_with("In stock today: oat milk, kai lan and rice.", "what's in stock lah"))


class StockClaimTests(unittest.TestCase):
    def test_offering_to_say_what_is_in_stock_is_not_a_claim(self):
        from nudgely.verify import verify_message
        hi = "Hi Min, welcome to Kampung Fresh! How can I help you today? I can tell you what's in stock or how our delivery works."
        self.assertFalse([w for w in verify_message(hi, [], {}) if "in stock" in w])

    def test_unknown_item_in_stock_is_still_caught(self):
        from nudgely.verify import verify_message
        self.assertTrue([w for w in verify_message("Good news, it's back in stock!", [], {}) if "in stock" in w])
        self.assertFalse([w for w in verify_message("This information is for you.", [], {}) if "in stock" in w])


class AishaDemoTests(unittest.TestCase):
    """Live 13 Nov rehearsal: Aisha's follow-up got the canned handover twice."""

    def test_follow_up_pointing_back_counts_as_engaged(self):
        self.assertTrue(_engages_with("Yes, oat milk is back in stock now!", "Oh is it really available now?"))

    def test_products_being_ready_is_not_a_live_order(self):
        from nudgely.verify import verify_message
        ok = "Yes, oat milk is back in stock. Our party snack packs are ready too."
        self.assertFalse([w for w in verify_message(ok, [], {}) if "live order" in w])
        self.assertTrue([w for w in verify_message("Your order is ready for pickup!", [], {}) if "live order" in w])


if __name__ == "__main__":
    unittest.main()
