# WhatsApp Cloud API: how Nudgely sends and receives

Tested end to end on 10 Nov 2026. We call Meta's WhatsApp Cloud API directly, because on our
MantaGO link broadcasts never deliver and no chat text is available (see `MANTAGO_API.md`).

## What works

| | Status |
|---|---|
| Send an approved template with blanks filled by our code | ✅ arrived on Thuta's phone |
| Receive a customer's message **with its text** on our webhook | ✅ |
| Reply with free text inside the 24-hour window | ✅ (`--echo`) |
| Delivery statuses (sent, delivered, read) on the webhook | ✅ |
| AI bot: tag each message, answer or hand over, STOP/START (`--bot`) | ✅ about 6–10 s per reply |

## Setup (already done)

- Meta app **Nudgely** (app id `3646880675488329`), owner Thuta, **published**
- Free test number **+1 555-164-9508**, phone number id `1412073635325460`, WhatsApp Business account id `1453007670136566`
- Test recipients (max 5 on the test number): Thuta, Dythan, Jack. Add more under Use cases → WhatsApp → Step 1 → Recipient
- Webhook fields subscribed: `messages`, template status, phone quality
- **Nudgely subscribed to the WhatsApp Business account** (`POST /{waba-id}/subscribed_apps`). Without this, messages go only to Meta's dashboard viewer and never reach us
- Privacy policy: https://raw.githubusercontent.com/Morn-Thuta/nudgely/main/docs/PRIVACY.md (Meta's checker can't read `github.com/blob` pages)

`.env` needs: `WA_TOKEN`, `WA_PHONE_NUMBER_ID`, `WA_GRAPH_VERSION=v25.0`, `WA_VERIFY_TOKEN`, `WA_APP_SECRET`. Ask Thuta for the values privately. Never commit them.

## Run it

```bash
python scripts/whatsapp_webhook.py --bot         # the real thing: AI tags + replies (customers in data/wa_customers.json)
python scripts/whatsapp_webhook.py --echo        # simple test: replies "Got it: ..."
cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8788   # gives https://xxx.trycloudflare.com
```

The quick-tunnel address changes every time. After restarting it, update **Callback URL** in
Meta (Use cases → WhatsApp → Step 2 → Configure Webhooks) to `https://<new>.trycloudflare.com/whatsapp`
with the same verify token, then **Verify and save**.

Send tests:

```bash
python scripts/test_whatsapp.py template --to 65XXXXXXXX --yes      # hello_world
python scripts/test_whatsapp.py text --to 65XXXXXXXX --message "Hi" --yes   # only within 24h of their last message
```

Incoming messages are appended to `data/wa_inbox.jsonl` (git-ignored: real customer messages).

## AI model

`LLM_PROVIDER=openrouter`, `LLM_MODEL=anthropic/claude-haiku-5.5` (paid credit, about $0.00025 per reply, 6 s).
The free models stay as automatic fallbacks but take 1–2 minutes, too slow for a live demo.

The bot only answers confidently about items in `STORE_INFO` (nudgely/llm.py). Anything else, such as
"do you have Monster Energy?", is handed to a person on purpose: it must never invent stock.

## Jack: how the bot is wired (done, for reference)

`on_message(wa, msg)` in `scripts/whatsapp_webhook.py` runs once per incoming message.
`msg = {"id", "from" (digits), "name", "timestamp", "type", "text"}`.

```python
from nudgely.llm import tag_message, merge_tags
from nudgely import reply

new = tag_message(customer_id, msg["text"], date=today, prior=stored_tags)
stored_tags = merge_tags(stored_tags, new)
out = reply.answer(customer, chat, msg["text"], tags=stored_tags)
wa.send_text(msg["from"], out["reply"])          # always safe to send (see reply.py)
if out.get("handover"):
    ...  # flag the conversation for a person
```

Map `msg["from"]` (the WhatsApp number) to a customer record; for the demo, create the customer
on first message.

## Before the finals (Thuta)

- [x] **Long-lived token.** A 60-day **user** token, valid until **9 Jan 2027**: Graph API Explorer → app Nudgely → User Token →
  `whatsapp_business_messaging` + `whatsapp_business_management` → Generate, then exchanged with the app secret
  (`GET /oauth/access_token?grant_type=fb_exchange_token`).
  **Don't use a system-user token on the test number**: every send fails with
  `(#10) Viewer cannot access the provided Paid Message Account`, even with full access. Once a system user exists,
  the API Setup page's *Generate token* also gives system-user tokens, so use Graph API Explorer instead.
- [x] **`WA_APP_SECRET`** set, so the receiver checks Meta's signature on every request
- [ ] **Audience demo needs a real number.** The test number only reaches 5 registered phones. For the audience, add a real number in Step 2 (Production setup), which also needs a payment method on the WhatsApp account
- [ ] Decide where the receiver runs on the day (demo laptop + tunnel is fine)
