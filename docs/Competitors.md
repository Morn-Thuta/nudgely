# Competitors: who else helps a shop bring customers back, and where Nudgely differs

Researched 12 Nov 2026 from vendors' own sites and docs, plus a few third-party comparisons. Prices change
often and vendor pages sometimes disagree. **Check the live pricing page before quoting any price on a slide.**
Owner for the slide: Shareef. Used in [Pitch_Plan.md](Pitch_Plan.md) (Difference section and Q&A).

## The short version (say this on stage)

> WhatsApp tools are great at **sending**, but you pick who gets what by hand, and you see opens, not extra visits.
> Enterprise retention suites **measure lift**, but they're built for big brands with data and marketing teams.
> Nudgely is built for a corner shop: it picks **who a message actually changes**, writes it **from their own words**,
> and **proves it worked** against a group who got nothing.

## Four groups of competitors

### 1. The WhatsApp Business app (free, what Mei Ling uses today)

- **Does:** broadcast lists and labels from a phone.
- **Limits** (per vendor guides): **up to 256 contacts per broadcast list**, and recipients must have saved the shop's number. Labels are kept by hand, can't be combined in one send, and don't sync with anything. WhatsApp is also rolling out monthly broadcast limits in some countries. [WATI guide](https://www.wati.io/blog/whatsapp-broadcast-guide) · [SleekFlow guide](https://sleekflow.io/en-sg/blog/whatsapp-broadcast-list-guide)
- **Gap Nudgely fills:** no memory of what each person said, no idea who a message changes, no way to see if it worked.

### 2. WhatsApp marketing platforms (the "sending" layer)

| Platform | What it does well | Price signal (vendor, Nov 2026) | What it doesn't do |
|---|---|---|---|
| **SleekFlow** (HK/SG, Series A US$8M led by Tiger Global) | Shared inbox, broadcasts, automation, AI agents, Singapore presence | Plans from about **US$99–149/month**; vendor pages disagree. Meta's per-message fees billed on top. [Pricing](https://sleekflow.io/en-asean/pricing) · [Blog](https://sleekflow.io/en-sg/blog/sleekflow-vs-sinch.md) | Audiences are tags and rules you set; reports show sent/read/clicked, not extra visits vs a no-message group |
| **WATI** | Simple WhatsApp broadcasts and chatbot for small teams; partners with loyalty tools like Eber | Paid plans; pay-as-you-go in some markets ([comparison](https://wanotifier.com/compare/respond-io-vs-wati/)) | Same: rule/tag targeting, engagement metrics |
| **respond.io** | Multi-channel inbox, workflows, AI agents on higher plans | From about **US$99/month** (Starter), Growth US$199 ([respond.io](https://respond.io/wati-alternative)) | Same |
| **MantaGO** (Eslitec, Taiwan; the challenge platform) | Omnichannel chatbot, CRM, customer database, group messaging, event triggers ([G2](https://www.g2.com/products/mantago/reviews)) | Not public | In our tests its Open API returned no incoming chat text, and its WhatsApp broadcasts didn't reach phones (see [MANTAGO_API.md](MANTAGO_API.md)) |

**How Nudgely relates:** we're not another inbox. These platforms are **delivery partners**: Nudgely decides *who* and *what*; they (or WhatsApp's API directly, as today) send it.

Cost context everyone pays: Meta charges per WhatsApp message. A Singapore marketing message is listed at about **US$0.0732** (from 1 Jul 2026), and Meta's pricing changes again on 1 Oct 2026 ([SleekFlow on Meta pricing](https://sleekflow.io/en-us/blog/whatsapp-business-price)). **Every wasted message costs the shop money, which is the case for messaging fewer, better-chosen people.**

### 3. Loyalty and POS tools for Singapore retail

| Tool | What it does well | What it doesn't do |
|---|---|---|
| **Eber** (Singapore HQ) | Points, rewards and memberships for physical and online shops; **from $69/month billed annually**; WhatsApp only through partners (SleekFlow or WATI) ([Eber FAQ](https://eber.co/faqs/)) | Segments by points and rules; doesn't read chats; no per-campaign lift |
| **StoreHub** (POS) | SMS campaigns from the same system as the POS and online ordering ([StoreHub](https://www.storehub.com/sms-marketing/)) | We found no WhatsApp campaign feature; rule-based audiences; no chat memory |

**Gap:** these know what people **bought**, not what they **said**. Aisha's "can tell me when oat milk is back?" never reaches a points system.

### 4. Enterprise retention suites (the "measurement" layer)

| Tool | What it does well | Why it's not for Mei Ling |
|---|---|---|
| **Optimove** | Control groups on every campaign, automatic control-group sizing, "self-optimizing" campaigns that shift toward higher uplift per micro-segment ([Control groups](https://academy.optimove.com/hc/en-us/articles/8699001780893-Using-Control-Group-Optimization) · [Self-optimizing](https://www.optimove.com/?p=21142)) | Built for large brands with CRM teams and big customer bases; no public small-shop plan; not WhatsApp-chat-first. **Closest in thinking to Nudgely**, at the other end of the market |
| **Klaviyo** | Predicted churn risk, customer lifetime value and expected date of next order, for e-commerce email and SMS ([Klaviyo help](https://help.klaviyo.com/hc/en-us/articles/360020919731-Guide-to-Klaviyo-s-Predictive-Analytics)) | Predictions need **at least 500 customers who have ordered**; online-store data; **churn risk is not uplift**. Klaviyo itself advises against triggering on churn risk ([Klaviyo blog](https://www.klaviyo.com/blog/predicting-churn-risk-our-new-model)) |

**Key point for Q&A:** churn risk says *who might leave*. Uplift says *who a message changes*. A customer at high risk may ignore any message (*Lost Cause*); a regular may come anyway (*Sure Thing*). Messaging either wastes money. Only uplift skips both.

## Positioning (slide 7)

Two axes:

- **X: How it picks who to message.** Everyone / tags and rules → predicted risk → **causal uplift**.
- **Y: How it proves results.** None → opens and clicks → **extra visits vs a no-message group**.

| | Picks by rules/tags | Picks by predicted risk | Picks by uplift |
|---|---|---|---|
| **Proves with lift vs holdout** | | Optimove (enterprise) | **Nudgely (small shops)** |
| **Proves with opens/clicks** | SleekFlow, WATI, respond.io, MantaGO, Eber, StoreHub | Klaviyo (e-commerce) | |
| **No proof** | WhatsApp Business app | | |

## Nudgely's three differences (say exactly three)

1. **It messages only the people a nudge changes.** It uses an uplift model, not a blast, rules or churn risk. It runs on ten things any shop's receipts have.
2. **Every message comes from the customer's own words.** The AI keeps chat details as tags, each with the exact words as evidence, and drafts from them. The owner approves every send.
3. **Every campaign proves itself.** A random no-message group is built in, and lift is measured in extra return visits, not opens.

Plus: built for a 300-customer shop on WhatsApp, with no marketing team, and costs about $0.00025 per AI reply.

## Where competitors are stronger (be honest if asked)

- **Maturity and scale:** SleekFlow, WATI and respond.io run thousands of businesses, have official WhatsApp partner status, multi-agent inboxes, Instagram/Facebook/LINE channels and integrations. We have one channel and a prototype.
- **Proven local results:** our uplift evidence is a public overseas dataset (57% of extra visits from the top 30%, about 1.9x random, 38–85% across seven splits). Optimove and Klaviyo have years of customer results.
- **Loyalty mechanics:** Eber does points and memberships; we don't, and don't plan to.

**Answer if asked "why wouldn't SleekFlow just add this?":** They could add a model. The hard parts are the shop-sized uplift model on receipt data, the chat-memory tags with evidence, and putting measurement into every send. Our plan is to be the decision layer that plugs into them, not to fight them.

## Not checked yet (do before quoting)

- WATI's current Singapore price
- Whether SleekFlow's AI agents personalise from chat history automatically
- MantaGO pricing
- Any Singapore-specific player using uplift (we found none in this search; say "we found none", not "there are none")
