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
        for page in ['overview', 'customers', 'customer_detail', 'campaign', 'results']:
            app = AppTest.from_file(str(ROOT / 'app' / 'views' / f'{page}.py'), default_timeout=30).run()
            self.assertEqual(len(app.exception), 0, page)

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
