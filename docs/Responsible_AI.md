# Responsible AI: Nudgely

Owner: Shareef · 22 Oct 2026 · For the deck (Dythan), the submission form and Q&A.

Every claim on this page was checked against the code. The "Where" column shows where a judge can see it.

## 1. Slide version (copy into the deck)

**Responsible by design**

- **Honest about the data.** All names and chats are fictional. Model results come from public randomised datasets, not a live Kampung Fresh test. We show the uncertainty (90% interval 31–89%), not just the headline.
- **Consent first.** Live sends go only to our own opted-in test phones. Opt-outs are blocked automatically, and every message ends "Reply STOP to opt out".
- **Private by default.** Chats are scrubbed of names and phone numbers before the AI reads them; the message writer sees only a first name. No API keys in GitHub.
- **Fair targeting.** The model uses shopping behaviour only. Gender, age and children are removed.
- **Human in control.** The owner reviews every message. Nothing sends until they confirm, and rehearsal mode is on by default.
- **Guardrails on the AI.** Every tag must quote the chat word for word. The writer is told to use only real stock and offers and to apologise first for complaints. Hard checks block discounts above 10% or for non-Persuadables, and any draft missing the opt-out line.

*Footer line:* Aligned with Singapore's PDPA (consent, Do Not Call) and the Model AI Governance Framework (human-in-the-loop).

## 2. Form version (about 150 words)

> All customer names and chats are fictional, and model results come from public randomised datasets (Lenta, Hillstrom); we report the uncertainty (90% interval 31–89%) alongside the headline. Live messages go only to our team's own opted-in test phones; opt-outs are blocked automatically, and every message ends with "Reply STOP to opt out". Chats are scrubbed of names and phone numbers before the LLM reads them (the message writer sees only a first name), and API keys stay out of GitHub. The targeting model uses behaviour only: gender, age and children are removed. Every AI tag must quote the chat word for word, the writer is instructed not to invent stock or prices, and discounts are hard-capped at 10%. The owner previews every message and must confirm before anything is sent; rehearsal mode is the default. Production adds DNC Register checks under Singapore's PDPA.

(143 words.)

## 3. What we do, and where to see it

| Principle | What Nudgely does | Where |
|---|---|---|
| **Disclosure** | The sidebar on every page says names and chats are fictional and results come from public datasets. The Results page lists the limitations. The Overview labels the chart "Historical evidence, not results from a live Kampung Fresh campaign" | `app/streamlit_app.py`, `app/views/results.py`, `app/views/overview.py` |
| **Honest uncertainty** | The 53% targeting figure is shown with its 90% bootstrap interval (31–89%), and labelled "noisy" | Overview and Results pages; `notebooks/check_capture.py` |
| **Consent and opt-out** | `data/consent.json` records opt-outs, and opted-out customers are skipped with the reason shown. The sender refuses a plan containing an opted-out customer. Every draft must end "Reply STOP to opt out", or Send is blocked | `app/lib.py` (`plan_campaign`, `send_campaign`); `nudgely/llm.py` (`check_message`) |
| **Live sends limited to test phones** | Only customers mapped to the team's own MantaGO test accounts get a real message; all others are simulated. The phone mapping is git-ignored | `app/lib.py` `test_accounts()`; `.gitignore` |
| **Privacy** | Phone numbers and the customer's name are replaced with `[phone]` and `[name]` before chat text is sent for tag extraction | `nudgely/llm.py` `scrub()` |
| **Cost and abuse control** | The app never calls the LLM on page load: it reads cached files. Live regeneration is capped at 3 per session | `app/lib.py` (`load_json`, `REGEN_LIMIT`) |
| **Security** | Keys live in `.env` locally and Streamlit secrets in the cloud; both are git-ignored. We searched the full commit history and found no keys or tokens | `.gitignore`, `.env.example` |
| **Fairness** | Gender, age and children are dropped before training, so targeting uses purchase behaviour only | `notebooks/train_uplift.py` (`DROP`); `features_dropped` in `data/uplift_summary.json` |
| **Grounded AI output** | Tags without a word-for-word quote from the chat are thrown away automatically | `nudgely/llm.py` `extract_tags()` |
| **Message guardrails** | Hard checks: ≤ 300 characters, opt-out line, at least one tag, discounts only for Persuadables, never above 10%. Prompt rules: don't invent stock, prices or offers; apologise first for complaints | `nudgely/llm.py` (`WRITE_SYSTEM`, `check_message`) |
| **Human in control** | The owner must tick "I've previewed every message; any live test recipients have opted in" before Send is enabled. The tick resets if recipients, drafts or delivery mode change. Rehearsal (simulate) mode is on by default | `app/views/campaign.py`, `app/lib.py` `campaign_id()` |
| **Explainability** | Every customer shows why they were chosen, held out or skipped (for example "Sure Thing: 34% likely to come back anyway"). Every draft carries a one-line reason for the owner | Campaign page; `messages.json` `reason` |
| **Measuring real impact** | A random 10% of chosen customers is held out, so lift can be measured against a real no-message group instead of assumed. Recording returns automatically is a next step | `app/lib.py` `plan_campaign()` |

## 4. Singapore alignment

**PDPA: consent obligation.** Customers' chat data is used only to serve them better messages from the same business, and they can withdraw at any time ("Reply STOP"). Opt-outs are honoured immediately in the plan, faster than the 21 days the DNC rules allow for stopping marketing messages.

**PDPA: Do Not Call provisions.** The DNC rules cover marketing messages sent through data apps such as WhatsApp to Singapore numbers. Before a business could send promotional messages, it would need either:
- a DNC Register check made within 21 days of sending, or
- clear and unambiguous consent recorded in written or other accessible form.

The message must also identify the sender and give contact details. In the demo, only our own consenting phones receive messages. In production, Nudgely would record consent per customer and check the DNC Register before each campaign.

**Model AI Governance Framework (PDPC/IMDA, 2nd edition, 2020).** It covers four areas:

| Framework area | Nudgely |
|---|---|
| Internal governance | Clear ownership: the business owner approves every campaign; the team owns model, prompts and checks |
| Level of human involvement | Human-in-the-loop: the AI recommends who and what, and a person approves before anything is sent |
| Operations management | Behaviour-only features; a fixed-seed random holdout; uncertainty reported; LLM output auto-checked |
| Stakeholder communication | A reason is shown for every decision. Data sources are disclosed. Every message carries an opt-out |

## 5. Data and AI tools disclosure

| Item | Detail |
|---|---|
| Lenta dataset | 687,029 grocery customers, randomised SMS vs no SMS. Source: BigTarget Hackathon by Lenta and Microsoft (2020), distributed through scikit-uplift. No explicit licence is published; we use it for non-commercial research and demonstration only |
| Hillstrom dataset | 64,000 online shoppers, randomised email vs no email (MineThatData, 2008). Released publicly by Kevin Hillstrom for analysis; distributed through scikit-uplift |
| Customer names and chats | Fictional, written by the team. Each demo customer's model scores come from a real anonymised Lenta row |
| LLM in the product | Free-tier LLMs through a provider-swappable wrapper: OpenRouter free models and Google Gemini for tag extraction, Google Gemini for message drafts (Anthropic and OpenAI also supported). Free-tier inputs may be used by the provider to improve its products; Gemini's free tier also allows human review. That is why only fictional data is sent. Production would use a paid tier where prompts are not used for training |
| AI coding assistant | The team used Claude (Anthropic) as a coding assistant during development; this is recorded in the commit history |
| Messaging | MantaGO Open API (Eslitec), WhatsApp channel |

## 6. Known gaps (we say these out loud)

| Gap | Why it matters | Fix in production |
|---|---|---|
| The message writer receives the customer's first name | Needed for the greeting, but it is personal data sent to the LLM | Fill the name in after generation using a `{first_name}` placeholder |
| The scrubber removes the customer's own name and phone numbers, not other people's names in the chat | Chats can mention family or friends | Add a named-entity check before sending to the LLM |
| `consent.json` records opt-outs only | No opt-out on file is not proof of consent | Store an explicit opt-in record with date and source |
| Not every draft names the store or gives contact details | Required for marketing messages under the DNC rules | Auto-append "Kampung Fresh, Tampines · [contact]" |
| Free-tier LLM | Inputs may be used for training | Paid tier or an enterprise agreement |
| Some complaint drafts (C002, C006, C009) apologise but then offer a discount | The prompt says to apologise first and not push a sale, but this is not hard-checked | Jack is fixing these drafts; add a hard check that complaint drafts contain no % offer |
| Tags can quote the store's lines as well as the customer's (3 of 46 do) | The evidence filter checks the whole chat | Restrict evidence to customer messages |
| Evidence comes from overseas datasets | Effects in Singapore may differ | 2–4 week pilot with one MantaGO business, with a holdout group |
| The 53% figure is noisy (31–89%) | The true targeting gain could be much smaller | Retrain monthly on the business's own campaign results |

## 7. Likely judge questions

**"Isn't this just spam with extra steps?"**
The opposite. The model's job is to message *fewer* people: it skips Sure Things who'd come back anyway and Lost Causes a message won't move. Every message is grounded in something the customer said, and every one has an opt-out.

**"What stops the AI making things up?"**
Three layers:
1. Tags without a word-for-word quote are deleted automatically.
2. The writer is told to use only the store's real stock and offers, and hard checks block bad discounts, over-long drafts or a missing opt-out.
3. The owner reads every message before it can be sent.

**"Is this legal in Singapore?"**
For the demo, only our own consenting phones receive messages. A real deployment needs recorded consent or a DNC Register check under the PDPA, plus sender identification. Those are on our production list.

**"Why remove gender and age? Wouldn't the model be more accurate?"**
Maybe slightly. But targeting offers by gender or age risks unfair treatment, and behaviour is what actually predicts response. We removed them and retrained; the 53% we report is the model without them.

**"Your 53% has a huge interval. Why should we trust it?"**
We don't ask you to. That's why the product holds out a random 10% in every campaign, so each business can measure its own lift instead of trusting our number.

Sources: [PDPC Advisory Guidelines on the Do Not Call Provisions (1 Feb 2021)](https://www.pdpc.gov.sg/-/media/Files/PDPC/PDF-Files/Advisory-Guidelines/Advisory-Guidelines-on-the-DNC-Provisions-1-Feb-2021.pdf) · [PDPC Model AI Governance Framework, 2nd edition](https://www.pdpc.gov.sg/help-and-resources/2020/01/model-ai-governance-framework) · [Gemini API Additional Terms of Service](https://ai.google.dev/terms) · [scikit-uplift fetch_lenta](https://www.uplift-modeling.com/en/latest/api/datasets/fetch_lenta.html) · [Hillstrom challenge write-up](https://www.stochasticsolutions.com/pdf/HillstromChallenge.pdf)
