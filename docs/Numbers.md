# Numbers sheet: the single source of truth

Owner: Shareef · Checked 22 Oct 2026 against the repo data and the raw datasets.

Every number in the deck, video, brief, app and submission form must come from this page, using the wording given here. If a number changes, change it here first, then everywhere else.

## Headline numbers

| # | Say this | Exact value | Source |
|---|---|---|---|
| 1 | **Our model's top 30% captures about half (53%) of all extra visits, about 1.8x better than picking 30% at random.** | 52.9% vs 30%; ratio 1.76x | `data/uplift_summary.json` → `top30_capture_share`, Lenta test set |
| 2 | **This estimate is noisy: the 90% interval is 31% to 89%.** Always say this together with #1 in the brief and form; in the deck, put it as a footnote | 31.2% to 88.6% | `top30_capture_ci90`, `notebooks/check_capture.py` (300 bootstrap resamples) |
| 3 | **SMS lifted grocery visits from 10.3% to 11.0% (+7%)** across 687k customers | 10.26% → 11.01%; +7.4% | `visit_rate_no_msg`, `visit_rate_msg` (full Lenta dataset) |
| 4 | **Email lifted visits from 10.6% to 16.7% (+57%) and purchases from 0.57% to 1.07% (about 1.9x)** across 64k online shoppers | 10.62% → 16.70%; 0.573% → 1.068%; ratio 1.87x | Hillstrom dataset, both email groups vs no email. Recomputed from raw data |
| 5 | (optional) **The best email (men's merchandise) lifted visits +72% and purchases 2.2x** | 10.62% → 18.28%; 0.573% → 1.253%; ratio 2.19x | Hillstrom, men's email group vs no email only |

### Correction made on 22 Oct (please read, Dythan)

The brief and PRD used to say "Email vs no email, 64k shoppers: +72% visits, 2.2x purchases". Those two figures are for the **men's email group only**, not for all email. Hillstrom had three randomised groups:

| Group | Customers | Visited | Bought |
|---|---|---|---|
| Men's merchandise email | 21,307 | 18.3% | 1.25% |
| Women's merchandise email | 21,387 | 15.1% | 0.88% |
| No email | 21,306 | 10.6% | 0.57% |
| **Both emails combined** | **42,694** | **16.7%** | **1.07%** |

Use #4 as the headline. Use +72% / 2.2x only with the label "best email" or "men's email". A judge who knows the dataset will spot "+72% for email" straight away.

## Supporting numbers

| Topic | Value | Source |
|---|---|---|
| Lenta dataset size | 687,029 customers (say "687k") | scikit-uplift `fetch_lenta` docs |
| Lenta test set | 103,055 customers the model never saw | `n_test` |
| Training sample | 50% of Lenta, 70/30 train/test split | `notebooks/train_uplift.py` |
| Model | Two-model uplift, HistGradientBoosting (scikit-learn), scikit-uplift `TwoModels` | `train_uplift.py` |
| Features removed for fairness | gender, age, children | `features_dropped` |
| Uplift in the top 30% | messaged customers in the top 30% visited 1.3 points more than unmessaged ones | `uplift_at_30` = 0.0131 |
| Hillstrom size | 64,000 customers, 3 randomised groups, 2-week tracking | Hillstrom challenge description |
| Demo customers | 30 (10 Persuadable, 10 Sure Thing, 10 Lost Cause), real Lenta scores with fictional names and chats | `data/customers.csv` |
| Customer labels | Persuadable = top 30% uplift. Sure Thing = not Persuadable and top 30% chance of returning anyway. Lost Cause = everyone else | `TEAM.md`, `train_uplift.py` |
| Holdout group | 10% of chosen customers, random with a fixed seed | `app/lib.py` |
| Message rules | ≤ 300 characters · discount only for Persuadables, max 10% · ends "Reply STOP to opt out" | `nudgely/llm.py` `check_message` |
| Live regenerations | max 3 per session | `app/lib.py` `REGEN_LIMIT` |
| WhatsApp window | free text only within 24h of the customer's last message | Meta policy, `TEAM.md` |
| Opt-outs on file | 1 (C014, asked to be removed on 30 Jun 2026) | `data/consent.json` |

## Status numbers (will change, so re-check on Friday)

| Item | As of Thu 22 Oct, 11:40pm | Check |
|---|---|---|
| Chats with tags | 30 / 30 | `data/tags.json` |
| Message drafts | 15 / 30 (all 10 Persuadables + 5 Lost Causes) | `data/messages.json` |
| Real MantaGO message sent to a phone | Not yet confirmed | Thuta |

The deck and video should never claim "30 personalised messages" unless `messages.json` has all 30 and Jack has checked them.

## Do not say

| Don't say | Why | Say instead |
|---|---|---|
| "Email increased visits by 72%" (no label) | Only true for the men's email group | "+57% visits" (#4), or "+72% for the best email" |
| "Our model is 1.8x better", with no caveat | The 90% interval runs from 31% to 89% | "about 1.8x on a public test set; noisy, so a pilot is next" |
| "Kampung Fresh saw X% more visits" | No live test has run. Kampung Fresh is fictional | "On public grocery data…" |
| "Proven in Singapore" | Lenta is Russian grocery SMS (2020); Hillstrom is US online retail email (2008) | "Proven on public randomised tests overseas; a Singapore pilot is the next step" |
| "Names never reach the AI" | The chat scrubber removes names and phone numbers, but the message writer receives a first name to greet the customer | "Chats are scrubbed of names and phone numbers; the writer sees only a first name" |
| "Uses a paid LLM API" | Tags and drafts were made on free tiers (OpenRouter free models, Google Gemini) | "free-tier LLMs (Gemini, OpenRouter), fictional data only" |
| "Every tag quotes the customer" | The filter accepts any word-for-word quote from the chat, including store lines (3 of 46 tags) | "every tag quotes the chat word for word" |
| "Complaints get no sales pitch" | Not hard-checked; C002, C006 and C009 drafts offer a discount after the apology | "complaints get an apology first" (until Jack fixes those drafts) |
| "Each campaign measures its lift" | The app creates the holdout but doesn't record returns yet | "each campaign *can* measure its own lift" |
| "Sends through MantaGO and writes tags back" | Only the broadcast is wired into the app, and only to test phones. Tag write-back is in the client, not the app. No live send confirmed yet | "sends to our test phones; others simulated; tag write-back supported in the client" |
| "Deployed on Streamlit Cloud" (before it is) | Not deployed as of Thu night | "built for Streamlit Community Cloud", then add the link once live |
| "Only messages opted-in customers" (as a fact about the demo) | `consent.json` records opt-outs only. Live sends go only to the team's own opted-in phones | "Live sends go only to our own opted-in test phones; opt-outs like C014 are blocked automatically" |

## Stale copies to fix (not Shareef's files)

- `app/lib.py` lines 33–35: `HILLSTROM` still holds the men's-only figures (18.3%, 1.25%, +72%, 2.2x), labelled as plain "email". Nothing in the app uses it today, but whoever owns `app/` should update it to the combined figures or delete it, so it never reaches a slide. (Jayden / Thuta)
- `README.md`: still says there is "only one example message draft" and a partial extraction cache. There are now 15 drafts and 30 of 30 tags. (Jayden)
- `docs/PRD.md` LLM spec: says "via a paid API key"; the demo used free tiers. (Thuta)

## Spoken version for the video (about 20 seconds)

> "We tested the targeting on 103,000 real grocery customers the model had never seen. Messaging our top 30% would have captured about half of all the extra visits, roughly 1.8 times better than picking at random. The range is wide, so we treat it as an early signal, and the product itself keeps a no-message group so every campaign can prove its own result."

## Friday final check

Tick each place once every number matches this page.

- [ ] Deck (Dythan)
- [ ] Video script and captions (Dythan)
- [ ] One-page brief: `docs/One_Page_Brief.md` and the PDF (Shareef, ✅ done 22 Oct)
- [ ] App: Overview shows 53% and the 31–89% interval. Results shows 10.3%, 11.0%, +7%, 53%, 1.8x (✅ checked in code 22 Oct; re-check on the live link)
- [ ] Submission form (Shareef)
- [ ] PRD (✅ Hillstrom row corrected 22 Oct)

## How to reproduce

```bash
python notebooks/check_capture.py     # prints the 53% and the 31%-89% interval from data/lenta_scored_test.csv
```

Hillstrom figures were recomputed from the raw 64,000-row file (`Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv`) by grouping `visit` and `conversion` by `segment`. They match the published challenge write-up exactly.

Sources: [Hillstrom challenge write-up](https://www.stochasticsolutions.com/pdf/HillstromChallenge.pdf) · [scikit-uplift fetch_lenta](https://www.uplift-modeling.com/en/latest/api/datasets/fetch_lenta.html) · [scikit-uplift fetch_hillstrom](https://www.uplift-modeling.com/en/latest/api/datasets/fetch_hillstrom.html)
