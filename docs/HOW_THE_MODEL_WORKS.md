# How the model works, in plain English

For anyone who has to explain Nudgely out loud. Figures here are repeated from
[Numbers.md](Numbers.md), which stays the single source of truth - if one
disagrees with the other, Numbers.md wins.

## One sentence

For each customer the model outputs a single number: **how much more likely
they are to come back if you message them.** That number, and nothing else, is
what the model contributes.

## The version you say out loud

You have 30 customers. You cannot message all of them - it costs money, and it
annoys people.

The model looks at each person's shopping history and asks one question: **if I
text this person, does anything change?** It answers by guessing twice.

| | Comes back if you say nothing | Comes back if you text them | Gap |
|---|---|---|---|
| **Aisha Rahman** | 28% | 39% | **+11** |
| **Amirah Salleh** | 68% | 63% | **-5** |
| **Ravi Kumar** | 2% | 3% | **+1** |

Text Aisha. It moves her 11 points.

Do not text Amirah. She is coming back anyway, and the message does not help -
you would be spending money to annoy your best customer.

Do not text Ravi either. Nothing is bringing Ravi back.

So you message Aisha, and leave alone both the customer who looks best and the
customer who looks worst. **It is not about who is likely to come back. It is
about who you can change.** That is the whole model: one gap number per person.

The *words* in the message - "sorry about your late delivery", "your green tea
is back in" - are not the model. That is the LLM reading their old chats. The
model only ever picks the names.

(Those three are real rows from `data/customers.csv`, with fictional names.)

## In, and out

**In** - ten numbers computed from a shop's own purchase history (phone, date,
amount), plus whether that customer has ever replied to a message:

| Feature | Plain words |
|---|---|
| `months_from_register` | how long they have been a customer |
| `k_var_days_between_visits_15d / 1m / 3m` | how irregular their visits are, over three windows |
| `stdev_days_between_visits_15d` | the spread of gaps between visits |
| `perdelta_days_between_visits_15_30d` | whether their visits are speeding up or slowing down |
| `k_var_cheque_15d / 3m` | how much their basket value jumps around |
| `response_sms`, `response_viber` | have they replied to a message before |

No gender, no age, no children - those are dropped on purpose, and the app says
so in its Limitations block.

**Out** - three numbers per customer:

- `p_no_msg` - chance they come back if you leave them alone
- `p_msg` - chance they come back if you message them
- `uplift` - the difference, `p_msg - p_no_msg`

`uplift` is the number everything else is built on.

## How it gets there

Two models, not one (scikit-uplift `TwoModels`, "vanilla" / T-learner, with
HistGradientBoosting underneath). One is trained only on customers who were
messaged, the other only on customers who were not. Score a customer through
both, subtract, and the gap is what the message is worth to that person.

This only works because the training data comes from a **randomised** test -
Lenta sent SMS to a random half of 687k grocery customers. Without the
randomisation you would just be measuring who was already likely to return.

## What the one number is used for

1. **Ranking the audience.** The campaign page sorts everyone by `uplift` and
   takes the top N you ask for.
2. **The labels.** Top 30% by `uplift` are **Persuadable**. Of the rest, anyone
   whose `p_no_msg` is in the top 30% of all customers is a **Sure Thing** -
   they are coming back anyway. Everyone else is a **Lost Cause**.
3. **"Extra visits expected"** - the `uplift` of every chosen recipient, added up.

## What the model does not do

**It does not write the messages, and it has no idea what they say.** The text
is written separately by the LLM from that customer's own chat history, cached
in `data/messages.json`. Marcus gets an apology because he complained about a
late delivery; Cheryl gets a restock note because she mentioned Pokka green tea.

The one place the two meet is a **permission check, not generation**: a discount
is only allowed on a customer the model labelled Persuadable, capped at 10%, and
`llm.check_message` fails the draft if an offer appears on anyone else.

**It cannot tell you which wording works.** Picking the best message *type* per
person would need uplift scored per message variant, which needs A/B data from
real sends. We do not have that yet.

So: **model = who. LLM = what to say. MantaGO = delivery. The campaign page =
a human approving it before anything goes out.**

## There are two trained models - know which one you are talking about

| | `notebooks/train_uplift.py` | `notebooks/train_transferable.py` |
|---|---|---|
| Features | all 190 Lenta columns | the 10 above |
| Used for | the demo's 30 customers and the Results charts | scoring a **real** shop (`nudgely/scoring.py`) |
| Output | `data/uplift_summary.json` | `data/uplift_transferable.json` |

The 190-column model can never score a real customer - it wants Russian
store-format codes no Singapore shop has. That is the whole reason the
transferable one exists.

The demo's `data/customers.csv` is 30 genuine Lenta test rows (10 per label)
with fictional Singaporean names attached. The scores are real; the people
are not.

## The numbers

- Messaged vs not, across all 687k: **10.3% came back, against 11.0%** - a real
  but small lift of about 0.75 of a point.
- Top 30% by the model captures **57% of all the extra visits**, against 30% for
  picking 30% at random. Averaged over seven random splits.
- **Always quote the spread.** It swings between 38% and 85% depending on the
  split: "57% on average across seven splits, swinging between 38 and 85" is the
  honest sentence. The direction is solid; the exact number is noisy.
- The older 190-feature model manages 44.8% on the same seven-split test, so
  dropping to ten shop-computable features did not cost accuracy - it gained.
- The Results tab's own figure (52.9%, 90% interval 31%-89%) is the 190-feature
  model on a single split. Different model, different method, so do not mix it
  with the 57%.

## Limitations, say them before a judge does

- **No recency feature.** Lenta exposes no "days since last purchase", so every
  lapsed customer in the sample scored Lost Cause. A win-back tool that refuses
  to message people who left is a design problem, and it is the first thing to
  fix.
- **The lift is small and the interval is wide.** Under one percentage point,
  with a spread you can drive a bus through. Honest framing beats a big number.
- **Trained on Russian grocery, not Singapore.** The features transfer; the
  behaviour may not. A real pilot needs 2 to 4 weeks with a holdout measured the
  same way.
- **The demo customers and chats are fictional.** The model scores behind them
  are not.

## If a judge asks

**"Is this just churn prediction?"** No. Churn prediction tells you who is
leaving. This tells you who a message would *change* - which is a different
group. A Sure Thing is very likely to come back, and gets skipped precisely
because of that. That is the entire point of the Skipped column.

**"How do you know it worked?"** The holdout. Every campaign deliberately holds
back a random share of the people it would have messaged, and writes them to
`data/campaign_log.csv` alongside the recipients. Messaged return rate minus
holdout return rate is the only number that proves anything, and it is the one
on the Results page.

**"Does the AI write to customers unsupervised?"** No. Drafts are written ahead
of time, rule-checked, and shown in full on the campaign page. A human ticks a
box before anything is sent, and practice mode is on by default.
