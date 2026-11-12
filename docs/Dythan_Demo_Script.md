# Dythan's finals demo and pitch draft

Prepared 11 November. Source of numbers: `Numbers.md`. Rehearse after deployment; this document does not claim a completed live rehearsal or recording.

## Two-minute stage path

| Time | Screen and action | Say |
|---|---|---|
| 0:00–0:15 | Landing page | “A neighbourhood shop remembers its regulars. Its software should too. Nudgely connects what someone says with whether a thoughtful message could bring them back.” |
| 0:15–0:35 | `/present`; invite judges to scan | “This is Kampung Fresh, our fictional grocer. Try asking about oat milk, a birthday party, or speaking to a person. Please use fictional details: the conversation can appear on this screen.” |
| 0:35–1:05 | Signed-in `/dashboard`; select the judge's incoming conversation | “The same assistant handles this web chat and WhatsApp. Here is the conversation, and here are the tags with their exact supporting words. When it needs help, it hands over to a person.” |
| 1:05–1:20 | Ask a volunteer to type HUMAN, then show the flag | “You can always ask for a person. We don't promise the AI knows everything, and we don't hide a handover.” |
| 1:20–1:40 | Customers, then Campaign | “For outbound messages, uplift asks a different question: will the message change the outcome? We reserve a no-message group and review drafts. This frontend's campaign action is a rehearsal; live sending is a separate integration.” |
| 1:40–2:00 | Results | “On Lenta public grocery data, the top 30% captured 57% of extra visits on average, about 1.9 times random. It ranged from 38 to 85% across seven splits. That's an early signal, not a promise to a Singapore shop. The next proof is a local pilot with measured returns.” |

Do not move to the live dashboard segment unless a separate-device test has shown the complete path. If no chat arrives, say “The live connection is unavailable; here is our labelled recorded flow,” and switch to the backup. Never show the fictional `/demo` inbox as the judge's live conversation.

## Seven-minute presentation structure

| Time | Slide / screen | Content |
|---|---|---|
| 0:00–0:40 | 1 — A little nudge. A lasting connection. | Introduce the shop owner, the customer who asked about oat milk, and the gap between remembering a conversation and sending a generic broadcast. Use a fictional example, labelled as such. |
| 0:40–1:20 | 2 — Remember / choose / measure | Chat memory identifies context; uplift prioritises limited messages; holdout and return matching test impact. MantaGO/WhatsApp deliver; Nudgely adds selection and context. |
| 1:20–3:20 | 3 — Try it yourself | Follow the two-minute stage path above. Keep the public QR visible while moving to the signed-in dashboard on another display/tab. |
| 3:20–4:10 | 4 — Evidence, with uncertainty | 57% captured by top 30%; 1.9x random; 38–85% over seven splits. Explain overseas data, the missing recency feature, and why a local pilot is needed. Do not mix in the retired model headline. |
| 4:10–4:50 | 5 — Human judgement stays in the loop | Grounded tags, reply checks and handover; opt-outs; invited dashboard access; fictional demo data. Distinguish implemented checks from production compliance work. |
| 4:50–5:35 | 6 — A shop's first week | Proposed onboarding: sign up → connect WhatsApp → import purchase history → review the first campaign → compare returns over time. Label this as the intended onboarding journey, not a finished signup/import flow. |
| 5:35–6:20 | 7 — A business that can work | Insert Shareef's sourced customer/problem/pricing/cost/competitor slide. Do not invent pricing, owner quotes, classmate-test outcomes or unit economics before that handoff. |
| 6:20–7:00 | 8 — What happens next | State the pilot hypothesis: more incremental return visits per message. Explain the measured-outcome plan and known limitations, then return to the QR and invite questions. |

This is a timed run sheet, not a measured seven-minute recording. Rehearse aloud and shorten as needed. Shareef's business slide and Jack's verified live examples are required before the final deck can be called complete.

## Q&A cards

**Why uplift instead of churn scoring?** Churn estimates who may leave. Uplift estimates how much a message changes the chance of a return. A customer can be at risk but unlikely to respond; a regular may return anyway.

**Does 57% mean a 57% conversion rate?** No. It is the share of estimated extra visits captured by selecting the top 30%, averaged across seven historical test splits. It is not a customer's probability or a live revenue result.

**Why such a wide range?** The incremental signal is small relative to ordinary variation in visits. Seven splits expose the instability. The range is not a confidence interval, and we don't guarantee the mean for a shop.

**Is this proven locally?** No. The public evidence is overseas. The next step is a consented local pilot with a no-message comparison group and return tracking. A classmate chat test measures usability and response quality, not retention lift.

**What if it invents a price or gets confused?** The reply pipeline checks outputs and can hand over. HUMAN explicitly requests a person. These checks reduce errors but are not a guarantee; show a verified example Jack has approved.

**How does it know stock?** The current backend uses a fixed shop-information source. Mock POS stock integration is optional and must be demonstrated before being claimed.

**Can anyone view my conversation?** The judge is told it may appear on the team's dashboard. Anonymous and non-team accounts cannot read the database. For this demo, use fictional details; production retention and privacy processes still need review.

**What does it cost?** Shareef owns the verified unit-economics slide. State its assumptions and source date. Don't quote the provisional per-reply cost as a contracted price or a complete cost per shop.

**What if the internet fails?** Use the labelled backup recording. Streamlit + Live WhatsApp is the team's fallback if the new dashboard is not ready by feature freeze; it still needs working connectivity for new live messages.

## Recording checklist

- Use the final public URL and scan from a second phone, signed out.
- Verify the team login and new conversation/tag visibility before recording.
- Hide account settings, tokens, phone mappings and notification previews.
- Record the two-minute path once without edits, then a clear backup take.
- Show whether each action is live, simulated, historical or prerecorded.
- Use 57% / 1.9x / 38–85% consistently. Add Shareef's source footnotes.
- Keep audio understandable, the QR readable, and the screen capture large enough for phones.
- Save a local backup. Publish/share only after the team checks the final video and deck.
