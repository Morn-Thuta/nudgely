import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
sys.path.insert(0, str(ROOT))
import lib


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.customers = lib.load_customers()

    def test_holdout_and_explicit_opt_out(self):
        plan = lib.plan_campaign(self.customers, 30, 10)
        self.assertEqual(plan.loc[plan.customer_id == 'C014', 'group'].iloc[0], 'Skipped')
        self.assertEqual((plan.group == 'Held out').sum(), 3)
        self.assertEqual(len(plan.customer_id.unique()), 30)
        self.assertTrue(plan.equals(lib.plan_campaign(self.customers, 30, 10)))

    def test_sender_blocks_missing_drafts_before_contacting_provider(self):
        plan = lib.plan_campaign(self.customers, 10, 10)
        with patch.object(lib, 'mantago_client') as client:
            with self.assertRaises(ValueError):
                lib.send_campaign(plan, {}, simulate=False)
            client.assert_not_called()

    def test_simulation_does_not_contact_mapped_accounts(self):
        plan = lib.plan_campaign(self.customers, 1, 0)
        plan['mantago_client_id'] = 'test-account'
        msgs = lib.load_json('messages.json')
        with tempfile.TemporaryDirectory() as temp, patch.object(lib, 'SEND_LOG', str(Path(temp) / 'log.csv')), patch.object(lib, 'mantago_client') as client:
            log = lib.send_campaign(plan, msgs)
            self.assertEqual(log.status.tolist(), ['simulated'])
            client.assert_not_called()

    def test_live_whatsapp_uses_template_when_available(self):
        plan = lib.plan_campaign(self.customers, 2, 0)
        ids = plan.loc[plan.group == 'Will message', 'customer_id'].tolist()
        plan['mantago_client_id'] = 'test-account'
        msgs = lib.load_json('messages.json')
        with tempfile.TemporaryDirectory() as temp, patch.object(lib, 'SEND_LOG', str(Path(temp) / 'log.csv')), \
                patch.object(lib, 'mantago_client') as client, patch.object(lib, 'mantago_platform', return_value='whatsapp'), \
                patch.object(lib, 'whatsapp_templates', return_value={ids[0]: 'pack-1'}):
            client.return_value.send.return_value = {'success': True}
            log = lib.send_campaign(plan, msgs, simulate=False)
        self.assertEqual(log.status.tolist(), ['sent', 'queued (needs WhatsApp template)'])
        first, second = client.return_value.send.call_args_list
        self.assertEqual(first.kwargs['intent_id'], 'pack-1')
        self.assertIsNone(second.kwargs['intent_id'])

    def test_review_changes_with_draft_or_delivery_mode(self):
        plan = lib.plan_campaign(self.customers, 1, 0)
        msgs = lib.load_json('messages.json')
        original = lib.campaign_id(plan, msgs)
        self.assertNotEqual(original, lib.campaign_id(plan, msgs, False))
        edited = {cid: dict(msg) for cid, msg in msgs.items()}
        edited['C001']['message'] += ' edited'
        self.assertNotEqual(original, lib.campaign_id(plan, edited))

    def test_sender_rejects_stale_opt_out_plan(self):
        plan = lib.plan_campaign(self.customers, 30, 0)
        plan.loc[plan.customer_id == 'C014', 'group'] = 'Will message'
        with patch.object(lib, 'draft_problems', return_value={}):
            with self.assertRaisesRegex(ValueError, 'opted-out'):
                lib.send_campaign(plan, {})
