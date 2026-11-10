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
python scripts/whatsapp_webhook.py --echo        # receiver on 127.0.0.1:8788, path /whatsapp
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

## The bot: tagging and replies (done, Jack)

`scripts/whatsapp_webhook.py` now tags every incoming message and answers it with the reply bot.
The logic is in `nudgely/conversation.py` so the FastAPI backend can call the same `handle()`.

```bash
python scripts/whatsapp_webhook.py              # tag + reply for real
python scripts/whatsapp_webhook.py --dry-run    # tag + print the draft reply, send nothing (no WA keys needed)
python scripts/whatsapp_webhook.py --echo       # old pipe test: "Got it: <text>", no AI
python scripts/whatsapp_webhook.py --clear-handover 6591234567   # let the bot talk to them again
```

What happens to each message:

1. **Meta gets its 200 straight away.** The AI takes seconds and Meta retries slow deliveries, so the
   work happens on one background worker, and a message id already seen is ignored. No double replies.
2. **STOP / UNSUBSCRIBE** is handled without the AI: one confirmation, then no tagging and no replies
   until they send START.
3. **Tagged** with `llm.tag_message`, merged into what we remember with `merge_tags`.
4. **Answered** with `reply.answer`, which hands over to a person when it is unsure, asked for a
   person (HUMAN), a refund or a complaint, or when the checker catches an invented price. On handover
   the customer gets the holding line and **the bot stays quiet for 12 hours** so it does not repeat
   "someone will follow up" on every message. Clear it early with `--clear-handover`.
5. A voice note or photo hands over (the bot cannot read it) instead of being ignored.

Each conversation (chat, tags, handover state) is kept in `data/wa_conversations.json`, git-ignored.
A number not seen before becomes a new customer with **no label, so no discount is ever offered**.

**Demo trick:** to make a teammate's phone start as a demo customer with their chat history and tags,
put `{"65XXXXXXXX": "C001"}` in `data/wa_contacts.json` (git-ignored, it holds phone numbers).

Not done yet, and needed before real customers: a **paid LLM key** (the bot sends their messages to
the model; free tiers are for testing), and a place for the shop owner to see handovers. Today they
are only printed in the console and saved in the conversations file.

## Before the finals (Thuta)

- [ ] **Permanent token.** The current token expires after 24 hours. Business settings → System users → add a system user → assign the Nudgely app and the WhatsApp account → generate a token with `whatsapp_business_messaging` and `whatsapp_business_management`
- [ ] **`WA_APP_SECRET`** from App settings → Basic, so the receiver checks Meta's signature
- [ ] **Audience demo needs a real number.** The test number only reaches 5 registered phones. For the audience, add a real number in Step 2 (Production setup), which also needs a payment method on the WhatsApp account
- [ ] Decide where the receiver runs on the day (demo laptop + tunnel is fine)
