# WhatsApp templates to submit to Meta

Six sentences, one per tag type. Meta approves the **fixed text**; only the
numbered blanks change per customer. Nudgely fills the blanks and renders the
sentence mechanically, so the approved words cannot be altered by the model.

Submit all six as **Marketing** unless Meta pushes back, then retry the two
complaint ones as **Utility** - they answer a customer's issue rather than
promote anything.

The shop's name is part of the fixed text, so each shop submits its own copies.

## delivery_complaint

Used when the customer has a `complaint_delivery` tag.

```
Hi {{1}}, we're sorry about {{2}}. {{3}} Reply STOP to opt out
```

| Blank | Must contain |
|---|---|
| {{1}} | the customer's first name, exactly as given, nothing else |
| {{2}} | what actually went wrong, in a few words, taken from the chat. No excuses, no blame |
| {{3}} | one short sentence putting it right or asking how to, ending in a question. Do not argue, do not explain why the shop was right, do not push a sale |

## price_complaint

Used when the customer has a `complaint_price` tag.

```
Hi {{1}}, thanks for the honest feedback on our prices. {{2}} Reply STOP to opt out
```

| Blank | Must contain |
|---|---|
| {{1}} | the customer's first name, exactly as given, nothing else |
| {{2}} | one short sentence that takes the feedback seriously and ends in a question. Only mention an offer if it is in STORE_INFO current_offers and the label allows it |

## restock

Used when the customer has a `restock_request` tag.

```
Hi {{1}}, good news - the {{2}} you asked about is back in stock at Kampung Fresh. {{3}} Reply STOP to opt out
```

| Blank | Must contain |
|---|---|
| {{1}} | the customer's first name, exactly as given, nothing else |
| {{2}} | the item they asked about, named as the chat or STORE_INFO names it |
| {{3}} | one short sentence in the shop's voice that ends with a question inviting a reply. It must follow from the chat. No prices, dates or offers that are not in STORE_INFO |

## event

Used when the customer has a `upcoming_event` tag.

```
Hi {{1}}, you mentioned {{2}} coming up. {{3}} Reply STOP to opt out
```

| Blank | Must contain |
|---|---|
| {{1}} | the customer's first name, exactly as given, nothing else |
| {{2}} | the event they mentioned, in a few words, as the chat describes it |
| {{3}} | one short sentence in the shop's voice that ends with a question inviting a reply. It must follow from the chat. No prices, dates or offers that are not in STORE_INFO. Offer help with the event rather than a general promotion |

## product_interest

Used when the customer has a `product_interest` tag.

```
Hi {{1}}, we've got {{2}} in today. {{3}} Reply STOP to opt out
```

| Blank | Must contain |
|---|---|
| {{1}} | the customer's first name, exactly as given, nothing else |
| {{2}} | an item from STORE_INFO in_stock_now that they have shown interest in |
| {{3}} | one short sentence in the shop's voice that ends with a question inviting a reply. It must follow from the chat. No prices, dates or offers that are not in STORE_INFO |

## regular

Used when the customer has a `loyal_regular` tag.

```
Hi {{1}}, time for your usual {{2}}? {{3}} Reply STOP to opt out
```

| Blank | Must contain |
|---|---|
| {{1}} | the customer's first name, exactly as given, nothing else |
| {{2}} | what they usually buy, from the chat or their tags |
| {{3}} | one short sentence in the shop's voice that ends with a question inviting a reply. It must follow from the chat. No prices, dates or offers that are not in STORE_INFO |

## Example, filled

The restock template for a customer who asked about oat milk:

> Hi **Aisha**, good news - the **oat milk** you asked about is back in stock at Kampung Fresh. **Shall we set some aside for you?** Reply STOP to opt out

## Order of preference

A customer often has several tags. Nudgely picks the first of these that matches:

`delivery_complaint` → `price_complaint` → `restock` → `event` → `product_interest` → `regular`

Answering a complaint with a promotion is the worst message the shop can send,
which is why the two complaint templates come first.

## What is checked before anything sends

- The fixed text is copied from the template, never from the model
- Blank 1 must be the customer's exact first name
- No blank may contain a line break, template syntax, or over 140 characters
- No price, date, product or delivery term absent from the chat and STORE_INFO
- No discount unless the customer is Persuadable, and never above 10%
- No "free" anything that is not already one of the shop's terms
- No shouting in capitals
- Under 300 characters, ending with the opt-out line
- The message must ask a question, so the reply tells us whether they are returning

A customer whose blanks fail any of these is **skipped**, not sent a repaired
message. The code is `nudgely/templates.py`; fill them with
`python scripts/fill_templates.py`.
