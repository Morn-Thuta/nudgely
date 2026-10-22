# Nudgely: message the right customers, say the right thing, prove it worked

**Team Nudgely** · AI-GNITION 2026 · Problem Statement 1 · Built on the MantaGO Open API (Eslitec)

Nudgely turns the purchase and chat data a business already holds into personal MantaGO messages. It sends them only to customers a message will actually bring back, and holds out a no-message group so the lift can be measured.

## Problem and target users

Small retailers and F&B businesses send the same "We miss you, 10% off" to everyone and cannot tell whether it brought anyone back. This causes three problems:
- Discounts are wasted on customers who would have returned anyway.
- Messages ignore what each customer has told the shop.
- Nobody measures whether the campaign worked.

**Target users:** owners and marketers of small businesses that talk to customers on WhatsApp, Instagram, Messenger or LINE through MantaGO. Our demo business is a fictional neighbourhood grocer in Tampines, Kampung Fresh.

## Solution and core workflow

Nudgely decides **who** to message and **what** to say, then proves the result.

1. **Smart Send (who):** an uplift model predicts how much more likely each customer is to return *because of* a message. It picks the top customers within the budget and skips those who would return anyway or won't be moved.
2. **Chat Memory (what):** an LLM reads each chosen customer's past chats and pulls out tags such as a restock request, a delivery complaint or an upcoming party. Every tag must quote the chat word for word.
3. **Personal message:** one short message per customer, built from those tags. Discounts are capped at 10%, complaints get an apology first, and every message has an opt-out line. The owner previews every message.
4. **Send via MantaGO:** approved messages go out through the MantaGO Open API on WhatsApp. In the demo, our own test phones get real messages and everyone else is simulated. Our API client also supports writing tags back to MantaGO.
5. **Prove it:** a random 10% of chosen customers is held out. Retention lift = return rate of messaged customers minus return rate of the held-out group.

## Evidence and expected impact

Randomised tests show messages bring customers back. Our model points a limited budget at the customers who respond most.

| Finding | Result | Source |
| --- | --- | --- |
| Email vs no email, 64k online shoppers | Visits 10.6% → 16.7% (+57%); purchases 0.57% → 1.07% (about 1.9x). Best email: +72% visits, 2.2x purchases | Hillstrom dataset |
| SMS vs no SMS, 687k grocery customers | Visits 10.3% → 11.0% (+7%) | Lenta dataset |
| Our model's top 30% vs a random 30% | Captures 53% of all extra visits vs 30% (about 1.8x). Noisy: 90% interval 31–89% | Lenta test set (103k customers), our analysis |

**Expected impact for a business:**
- More customers return per message sent.
- Fewer discounts are wasted on customers who would come back anyway.
- Fewer paid WhatsApp messages are sent.
- The owner gets a monthly retention-lift number measured against their own no-message group.

## Tools and technology

- **MantaGO Open API** (Eslitec): message delivery on WhatsApp; tag write-back supported in our client
- **Uplift model:** scikit-uplift two-model approach with scikit-learn HistGradientBoosting, trained offline on the Lenta dataset
- **LLM:** free-tier Google Gemini and OpenRouter models through a provider-swappable wrapper, for tag extraction and message drafts. Output is JSON, auto-checked against hard rules and cached. Only fictional data is sent
- **App:** Python and Streamlit, built for Streamlit Community Cloud

## Responsible AI

- **Consent:** live sends go only to our own opted-in test phones. Opt-outs are blocked automatically, and every message ends "Reply STOP to opt out".
- **Privacy:** chats are scrubbed of names and phone numbers before the LLM reads them, and the message writer sees only a first name. No API keys are in GitHub.
- **Fairness:** targeting uses behaviour only; gender, age and children are removed.
- **Human in control:** the owner previews every message and must confirm before anything is sent. Rehearsal mode is the default.
- **Singapore:** a real rollout adds recorded consent and DNC Register checks under the PDPA, in line with the Model AI Governance Framework's human-in-the-loop approach.

## Limitations and next steps

- **Demo data:** customer names and chats are fictional. Model results come from public overseas datasets (Russian grocery SMS, US online email), not a live Singapore business.
- **Noisy targeting estimate:** the true lift in visits is small, so the 53% figure has a wide interval. A real pilot needs 2 to 4 weeks with a holdout group.
- **Needs one past test:** uplift models learn from a campaign that had a message group and a no-message group. A new business starts with one random test month.

**Next steps:** pilot with one MantaGO business in Singapore, read reply events from MantaGO to track results automatically, and retrain the model monthly on the business's own campaign results.

---

Full details: [Numbers sheet](Numbers.md) · [Responsible AI](Responsible_AI.md) · [PRD](PRD.md)
