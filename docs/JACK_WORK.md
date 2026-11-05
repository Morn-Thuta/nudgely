# Jack's work, in plain English

What each piece does, and the one command that shows it working. Run everything
from the repo root with the virtual environment's Python
(`.venv/Scripts/python.exe` on Windows, `.venv/bin/python` elsewhere).

Most of this has no screen in the Streamlit app, which is why the app looks
unchanged. The commands below are how you see it.

---

## 1. Score a real shop's customers

A shop gives you a spreadsheet of purchases: phone, date, amount. This turns
that into a ranked list of who is worth messaging.

```
python scripts/score_shop.py --sales data/examples/sales_sample.csv --top 8
```

```
1,254 purchases from 48 customers in data/examples/sales_sample.csv
  Lost Cause: 18  Persuadable: 17  Sure Thing: 13

Top 8 by uplift - message these first:
  phone          uplift   if msg   if not  label
  92353412       +7.8%      16%       8%  Persuadable
  98818174       +7.4%      20%      13%  Persuadable
  92452821       +7.3%      15%       8%  Persuadable
  92499123       +6.5%      16%      10%  Persuadable
```

Read the first row as: this person has an 8% chance of coming back on their own,
16% if we message them, so the message is worth +7.8 points. That difference is
the whole point - not "will they return" but "does the message change anything".

`Persuadable` means message them. `Sure Thing` means they are coming back
anyway, so a discount is wasted. `Lost Cause` means the message will not move
them.

**Needs:** `data/model_transferable.pkl`. It is gitignored, so build it once with
`python notebooks/train_transferable.py` (about an hour).

**Don't have a real shop's file yet?** `python scripts/make_sample_sales.py`
writes a realistic fake one.

---

## 2. The model behind that

`notebooks/train_transferable.py` trains on ten numbers any shop can work out
from phone, date and amount alone - how long they have been a customer, how
irregular their visits are, how much their basket size jumps around, and whether
they have replied to a message before.

The old model needed all 190 columns of the Lenta dataset, including Russian
store-format codes. No Singapore shop has those, so the old model could never
score a real customer.

| | top 30% captures |
|---|---|
| all 190 Lenta features | 44.8% ± 10.5% |
| **10 shop-computable features** | **57.0% ± 14.2%** |
| random targeting | 30% by definition |

**Always quote the spread.** It swings between 38% and 85% depending on the
split. "57% on average across seven splits, swinging between 38 and 85" is the
honest sentence. The direction is solid; the exact number is noisy.

**Known gap:** the model has no "days since last purchase" feature, because
Lenta does not expose one. So every lapsed customer in the sample came out as
`Lost Cause`. A win-back tool that refuses to message people who left is a
design problem, and the team should know about it.

---

## 3. The reply bot

`nudgely/reply.py` answers an incoming WhatsApp message, or hands it to a person.
Nothing is hard-coded - the AI writes each reply - but it is checked before it
can be sent.

Two layers of protection:

**The prompt** tells the model to escalate when it is unsure.

**`review_reply`** catches it when it doesn't. Try it:

```
python -c "from nudgely.reply import review_reply; print(review_reply({'reply': 'Yes! Durian is \$3 a kilo today and we deliver free anywhere. Reply STOP to opt out'}, {'name':'Aisha','label':'Lost Cause'}, [], 'do you have durian?'))"
```

```
handover: True
reply   : Thanks for your message - someone from the shop will follow up shortly.
draft   : Yes! Durian is $3 a kilo today and we deliver free anywhere.
reason  : amount $3 appears in neither the chat nor STORE_INFO
```

The shop never said durian costs $3. The bot invented it, and the check caught
it. It also catches invented dates and delivery terms, discounts offered to the
wrong kind of customer, off-topic drift, and replies that are empty or too long.

### For whoever wires this into the backend

**`reply` is always safe to send.** On handover it is replaced with the holding
line above and the model's attempt is moved to `draft`, which is for the shop
owner to read and never to send. So if your code sends `reply` and forgets to
check `handover`, the customer gets a polite holding line rather than an invented
price. Check `handover` anyway - that is what tells you to put a person on it.

This applies even when the bot flags itself. A reply that says "let me check -
durian is $3 a kilo by the way" is a handover *and* an invention, so it gets the
same treatment; the model's own judgement is not trusted to make its text
sendable.

## 4. Reaching a real person

A customer can type `HUMAN` at any time. That is matched **before** the AI is
called, so no clever message can talk the bot out of handing over.

```
python -c "from nudgely.reply import asked_for_a_person as f; print(f('HUMAN'), f('can i speak to someone real'), f('thanks!'))"
```

```
True True False
```

The first reply to any customer advertises it, so they know the option exists.

---

## 5. Filling WhatsApp templates

WhatsApp will not let a shop start a conversation with free text. Meta approves a
fixed sentence with numbered blanks, and only the blanks may change. So the
first message to a customer cannot be written the way `write_messages.py` writes
it.

The six sentences, and everything checked before one sends, are in
[WHATSAPP_TEMPLATES.md](WHATSAPP_TEMPLATES.md) - that file is what Thuta submits
to Meta.

```
python scripts/fill_templates.py --only C001
```

```
C001 [restock] Hi Aisha, good news - the oat milk you asked about is back in
stock at Kampung Fresh. Shall we set some aside for you? Reply STOP to opt out
```

The model's job shrinks to filling blanks, and `render` substitutes them
mechanically - the approved words are copied from the template, never from
anything the model returned. A model that tries to rewrite the sentence cannot.

The blanks are still free text, so they get checked: no invented price, product,
date or delivery term, no discount to a customer who is not Persuadable, no
"free" anything that is not already a shop term, no shouting, and the message
must ask a question. A customer whose blanks fail is **skipped**, not sent a
patched-up message.

Replies are unaffected. Once a customer answers, WhatsApp allows 24 hours of free
text, which is what the reply bot above handles.

---

## 6. Tagging one message at a time

`extract_tags` re-reads a customer's whole chat. That suits a nightly batch but
is wrong for a live webhook: it costs more every time the conversation grows, and
it re-decides tags that were settled weeks ago.

`llm.tag_message` reads only the new message, with the existing tags passed in as
context so it does not repeat them. `llm.merge_tags` folds the result into what
the shop already remembers - same tag mentioned twice keeps the newer evidence,
and sentiment follows the newest message, because it describes where the customer
stands now.

This is the function Thuta's `POST /webhooks/mantago` calls:

```python
from nudgely.llm import merge_tags, tag_message

new = tag_message(customer_id, incoming_text, date=today, prior=stored_tags)
stored_tags = merge_tags(stored_tags, new)
```

---

## 7. How accurate is the tagging?

A judge will ask. Previously there was no answer. `data/examples/tagging_test_set.json`
is 32 hand-written chats with the tags they should produce, and ten of them are
traps - the shop mentions a festival the customer never did, a customer praises
the price, a customer asks to be left alone.

```
python scripts/test_tagging.py
```

See `docs/TAGGING_ACCURACY.md` for the current numbers and what they mean.

Two numbers, and they fail differently. **Recall** is how much it finds; miss a
complaint and the shop sends a promotion to an angry customer. **Precision** is
how much of what it finds is real; invent a tag and the message references
something the customer never said. Answers are cached, so a run cut short by a
quota limit is not wasted - run it again and it carries on.

Add `--per-message` to measure the live path instead of the batch one.

---

## 8. Run everything unattended

Right now someone has to run the scripts by hand. This chains them: tag new
chats, draft messages, verify them, close finished outcome windows.

```
python scripts/run_daily.py --dry-run
```

```
=== daily run === (dry run)
tags: nothing new to tag
messages: every tagged customer already has a draft
verify: checking every draft
returns: nothing past its window
=== done, all clear ===
```

Each step checks whether there is work before calling anything, so a quiet day
costs no API credit. Drop `--dry-run` to run it for real. Point Windows Task
Scheduler or cron at it and it runs itself.

---

## 6. The LLM never dies on one bad provider

Three fixes that are invisible until they save you:

- **Fallback chain** - try the configured model, then that provider's other
  models, then any other provider you have a key for. Only transient failures
  fall through; a bad prompt is not retried forever.
- **Timeouts** - a provider returning 503 used to hang for over five minutes,
  because Google's SDK retried it internally with backoff before our fallback
  got a turn. Now 30 seconds per call, 75 for the whole chain. Five minutes
  became eight.
- **Fresh model list** - every free OpenRouter model hard-coded during the
  hackathon now returns 404. Refreshed against the live list.

---

## 7. Measuring whether it actually worked

A real send writes one row per customer to `data/campaign_log.csv`, including
the ones deliberately held back. Rehearsals do not log, so the numbers stay
clean.

```
python scripts/record_returns.py --from-visits --close
```

Then the Results page in the Streamlit app charts messaged against holdout with
the measured lift. The holdout is the only honest comparison: without it you
cannot tell a good message from a customer who was coming back regardless.

---

## Still blocked on other people

- **The webhook** - MantaGO's documented API only sends. Until Eslitec confirms
  whether the callback delivers incoming message text, nothing two-way works.
  Blocked on Thuta, not on code.
- **WhatsApp templates** - broadcasts sit "Unsent" until Meta approves template
  sentences on a non-personal number.
- **A paid LLM key** - free tiers are 20 requests a day per model. Fine for
  testing, not for real customers.
