import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
sys.path.insert(0, str(ROOT))
import lib


class AppTests(unittest.TestCase):
    def test_all_pages_load(self):
        for page in ['customers', 'customer_detail', 'campaign', 'results']:
            app = AppTest.from_file(str(ROOT / 'app' / 'views' / f'{page}.py'), default_timeout=30).run()
            self.assertEqual(len(app.exception), 0, page)

    def test_results_show_labelled_example_until_real_outcomes_exist(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(lib, 'CAMPAIGN_LOG', str(Path(temp) / 'none.csv')):
            app = AppTest.from_file(str(ROOT / 'app' / 'views' / 'results.py'), default_timeout=30).run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any('Example only' in w.value for w in app.warning))
            self.assertIn('Difference', [m.label for m in app.metric])

    def test_headline_is_one_figure_with_its_range(self):
        h = lib.headline()
        self.assertEqual(f"{h['capture']:.0%}", '57%')
        self.assertLess(h['low'], h['capture'])
        self.assertLess(h['capture'], h['high'])

    def test_lift_range_is_wide_on_small_groups_and_brackets_the_difference(self):
        low, high = lib.lift_range(5, 24, 2, 12)
        self.assertLess(low, 0)
        self.assertGreater(high, 0)
        low, high = lib.lift_range(400, 1000, 200, 1000)
        self.assertGreater(low, 0.15)
        self.assertLess(high, 0.25)
        self.assertIsNone(lib.lift_range(3, 10, 0, 0))

    def test_reviewed_simulation_and_changed_audience(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(lib, 'SEND_LOG', str(Path(temp) / 'log.csv')), patch.object(lib, 'mantago_client') as client:
            app = AppTest.from_file(str(ROOT / 'app' / 'views' / 'campaign.py'), default_timeout=30).run()
            self.assertTrue(app.button[0].disabled)
            app.slider[0].set_value(1).run()
            app.slider[1].set_value(0).run()
            app.checkbox[0].check().run()
            self.assertFalse(app.button[0].disabled)
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(app.button[0].disabled)
            self.assertEqual(app.session_state['send_log'].status.tolist(), ['simulated'])
            app.slider[0].set_value(2).run()
            self.assertFalse(app.checkbox[0].value)
            self.assertTrue(app.button[0].disabled)
            client.assert_not_called()
