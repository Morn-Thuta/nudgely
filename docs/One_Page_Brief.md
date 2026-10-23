# Nudgely: message the right customers, say the right thing, prove it worked

**Team Nudgely** · AI-GNITION 2026 · Problem Statement 1 · Built on MantaGO (Eslitec)

**Try it:** https://nudgely.streamlit.app · **Code:** https://github.com/Morn-Thuta/nudgely

Nudgely picks who to message, writes what to say from each customer's own chats, and holds back a no-message group to prove it worked.

| | Result | Source |
| --- | --- | --- |
| **Email vs no email** | +57% visits (10.6% → 16.7%), purchases about 1.9x | Hillstrom, 64k online shoppers, randomised |
| **SMS vs no SMS** | +7% visits (10.3% → 11.0%) | Lenta, 687k grocery customers, randomised |
| **Our top 30% vs random 30%** | Catches 53% of extra visits vs 30% (about 1.8x). Noisy: 90% interval 31–89% | Lenta test set, 103k customers |

## The problem

Small shops send the same "We miss you, 10% off" to everyone. Discounts go to people who'd return anyway, messages ignore what customers said, and nobody knows if it worked.

**For:** small retail and F&B owners who message customers through MantaGO. Demo shop: **Kampung Fresh**, a fictional grocer in Tampines.

## How it works

1. **Pick who.** An uplift model finds customers a message will actually bring back.
2. **Remember what.** An LLM pulls tags from past chats, each quoting the chat word for word.
3. **Write it.** One short message each: apology first for complaints, max 10% off, opt-out line.
4. **Approve and send.** The owner confirms; MantaGO delivers on WhatsApp (approved templates) and stores each customer's tags. Demo sends reach only our test phones.
5. **Prove it.** A random 10% gets no message, so the real lift can be measured.

> Hi Aisha! Planning your son's end-of-Oct birthday party? 🎉 We have party snack packs ($12/$20) for easy celebrations! Good news, your favourite oat milk is back in stock too! Enjoy 10% off your next order. Reply STOP to opt out

## Why it matters

- More customers return per message sent
- No discounts wasted on customers who'd come back anyway
- Fewer paid WhatsApp messages
- A lift number checked against the shop's own no-message group

## Responsible AI

- **Consent.** Live sends go only to our opted-in test phones. Every message ends "Reply STOP to opt out".
- **Privacy.** Names and phone numbers are scrubbed from chats; the writer sees only a first name.
- **Fairness.** No gender, age or children in the model.
- **Human in control.** Nothing sends until the owner confirms.
- **Singapore-ready.** Production adds PDPA consent records and DNC Register checks.

## Built with

MantaGO Open API · scikit-uplift · scikit-learn · Gemini and OpenRouter (free tiers) · Python · Streamlit

## Limitations and next steps

- Names and chats are fictional; evidence comes from overseas public datasets.
- The 53% is noisy, so a 2–4 week pilot with a holdout group is next.
- The model needs one past message vs no-message test to learn from.
- **Next:** pilot with one Singapore MantaGO business and retrain monthly.

---

Full details: [Numbers sheet](Numbers.md) · [Responsible AI](Responsible_AI.md) · [Submission draft](Submission_Draft.md)
