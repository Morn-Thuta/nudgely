# Nudgely: message the right customers, say the right thing, prove it worked

**Team:** [Team name] · **Project:** Nudgely · **AI-GNITION 2026, Problem Statement [1/2]**

Nudgely turns the purchase and chat data a business already holds into personal, automated MantaGO messages, sent only to customers a message will actually bring back, and measures the lift against a no-message group.

## Problem and target users

Small retail and F&B businesses send the same "We miss you, 10% off" to everyone and cannot tell whether it brought anyone back. Discounts are wasted on customers who would return anyway, messages ignore what each customer has said, and nobody measures the effect.

**Target users:** owners and marketers of small businesses that talk to customers on WhatsApp, Instagram, Messenger or LINE through MantaGO.

## Solution and core workflow

Nudgely decides **who** to message and **what** to say, then proves the result.

1. **Smart Send (who):** an uplift model predicts how much more likely each customer is to return *because* of a message, and picks the top ones within the budget.
2. **Chat Memory (what):** an LLM reads each chosen customer's past chats and pulls out evidence-backed tags such as a restock request, a delivery complaint or an upcoming event.
3. **Personal message:** the LLM writes one short message per customer from those tags, with a discount cap, an apology first for complaints, and an opt-out line. The owner previews every message.
4. **Send via MantaGO:** the MantaGO Open API delivers each message and stores the tags on the customer.
5. **Prove it:** a random 10% of chosen customers is held out. Retention lift = return rate of messaged customers minus return rate of the held-out group.

## Evidence and expected impact

Real randomised tests show messaging brings customers back, and our uplift model directs a limited message budget to the customers who respond most.

| Finding | Result | Source |
| --- | --- | --- |
| Email vs no email, 64k online shoppers | Visits 10.6% to 18.3% (+72%); purchases 0.57% to 1.25% (about 2.2x) | Hillstrom dataset |
| SMS vs no SMS, 687k grocery customers | Visits 10.3% to 11.0% (+7%) | Lenta dataset |
| Our model's top 30% vs a random 30% | Captures 45% of all extra visits vs 30% (about 1.5x) | Lenta test set, our analysis |

**Expected impact for a business:** more customers return per message sent, fewer discounts wasted on customers who would come back anyway, lower per-message cost on paid channels such as WhatsApp, and a monthly retention-lift number the owner can trust.

## Tools and technology

- **MantaGO Open API** (Eslitec): message delivery and customer tags
- **Uplift model:** scikit-uplift two-model approach with scikit-learn gradient boosting, trained on the Lenta dataset
- **LLM via paid API:** tag extraction and message writing, JSON output, cached
- **App:** Python and Streamlit, deployed on Streamlit Community Cloud

## Limitations and next steps

- **Demo data:** customer chats and names are fictional; model results come from public datasets, not a live business.
- **No live test yet:** the held-out comparison is shown on Lenta data; a real pilot needs 2 to 4 weeks.
- **Needs one past test:** uplift models learn from a campaign with a message and no-message group; a new business starts with one random test month.
- **Responsible AI:** opt-in customers only, opt-out in every message, names and phone numbers removed before text reaches the LLM, gender excluded from targeting, owner approves every send.

**Next steps:** pilot with one MantaGO business, read reply events from MantaGO to track results automatically, and retrain the model monthly on its own campaign results.
