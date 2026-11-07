# How accurate is the tagging?

Measured against `data/examples/tagging_test_set.json`: 32 hand-written chats
with the tags they should produce. Reproduce with `python scripts/test_tagging.py`.

Run on 5 Nov 2026, whole-chat path, OpenRouter free models with no pinned
`LLM_MODEL`, so the exact model varies with whatever the free tier serves that
day. **Rerun this on the paid key before quoting it at finals**, because the
number currently belongs to a model we did not choose.

## The numbers

| | |
|---|---|
| Recall, all tags | **97%** (30 of 31 found) |
| Precision, all tags | **86%** |
| Exactly right, every tag and no extras | **72%** (23 of 32) |
| Right, allowing judgement calls | **84%** (27 of 32) |
| Sentiment correct | **75%** |
| Tags on the trap cases that must not appear | **0** |

| tag type | found | missed | invented | arguable | recall | precision |
|---|---|---|---|---|---|---|
| restock_request | 7 | 0 | 0 | 0 | 100% | 100% |
| complaint_delivery | 5 | 1 | 1 | 0 | 83% | 83% |
| complaint_price | 3 | 0 | 1 | 0 | 100% | 75% |
| upcoming_event | 6 | 0 | 2 | 0 | 100% | 75% |
| product_interest | 6 | 0 | 1 | 4 | 100% | 86% |
| loyal_regular | 3 | 0 | 0 | 1 | 100% | 100% |

**Recall** is how much it finds. Miss a complaint and the shop sends a promotion
to an angry customer. **Precision** is how much of what it finds is real. Invent
a tag and the message references something the customer never said.

**Arguable** is counted separately and not forgiven. Four cases produced
`product_interest` where the test set does not require it but the wording
defends it - "you got party snack packs?" really is product interest. Marking
those honestly is the difference between 86% precision and the 76% a stricter
reading gives. Both appear in the script's output; neither is hidden.

## A bug the test set found, and the fix

The shop announced a Deepavali promotion. The customer replied *"Ok"*. That came
back as an `upcoming_event` tag, so a customer who never mentioned Deepavali had
a festival on their record - and would have been sent a Deepavali message.

The cause: `extract_tags` checked that the quoted evidence existed **somewhere**
in the chat, including the shop's own messages. A shop advertising a festival is
not evidence that this customer has one coming up.

Evidence now has to come from a message the customer sent. That lifted precision
from 83% to 86%, cleared both trap cases, and is the kind of mistake no amount of
reading the output by eye would have caught - the tag looked perfectly well
evidenced.

## The failure that is left

**Sarcasm.** *"Three days for a carton of eggs, very efficient service"* is the
only missed tag in the set, and it is a delivery complaint - the worst kind to
miss, because the next thing the shop sends is a promotion. No rule fixes this;
it needs an example of sarcasm in the prompt.

## The pattern in the rest

Every remaining error is over-tagging, never under-tagging:

| case | what happened |
|---|---|
| T08 | "I need it for Sunday" became an `upcoming_event` |
| T29 | "Durian season started?" became an `upcoming_event` |
| T30 | "ordered Gardenia bread but got a different brand" became `complaint_price` |
| T11 | "Bread got stock? Last week sold out when I came" became `complaint_delivery` |

T30 is the one with teeth. A wrong item delivered is a fulfilment problem, and
tagging it as a price complaint sends the price-complaint template - an apology
about the wrong thing.

T11 is new since the previous run and nothing in the code changed to cause it.
Free models rotate, so **the numbers move a few points between runs**. Treat
anything inside about five points as noise, and rerun before quoting.

## What this is safe to claim

> "Across 32 hand-written chats the tagger finds 97% of the tags it should, and
> 86% of what it finds is supportable. It gets every tag exactly right on 72% of
> chats. It over-tags rather than under-tags, it misreads sarcasm, and the
> numbers come from a free model we did not pick, so they move a few points
> between runs."

Do not quote a single headline accuracy figure without the recall/precision
split. They fail in opposite directions and a shop cares about both.
