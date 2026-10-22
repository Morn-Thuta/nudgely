# Submission form: draft answers

Owner: Shareef · Drafted 22 Oct 2026 · Deadline: **Fri 23 Oct 2026, 11:59 PM SGT**

These are ready-to-paste answers for the usual hackathon form fields. The real form's fields weren't available when this was drafted, so map each block to the closest field. Every number matches [Numbers.md](Numbers.md).

## 1. Basics

| Field | Answer |
|---|---|
| Team name | Nudgely |
| Problem statement | Problem Statement 1 |
| Project name | Nudgely |
| Tagline (≤ 12 words) | Message the right customers, say the right thing, prove it worked. |
| Partner platform | MantaGO Open API (Eslitec) |

| Member | Role |
|---|---|
| Min Thuta | Lead, MantaGO integration |
| Dythan Yong Jun An | Pitch and demo lead |
| Jack [full name] | Message quality (LLM) |
| Jayden [full name] | App and deployment |
| Shareef [full name] | Numbers, documentation, responsible AI |

Fill in full names exactly as registered.

## 2. Project summary (150 words)

> Small shops send the same "We miss you, 10% off" to every customer and never learn whether it worked. Nudgely fixes this in three steps on top of MantaGO. First, an uplift model picks the customers a message will bring back, skipping those who would return anyway. Second, an LLM reads each customer's past chats and writes a short personal message grounded in their own words, such as an oat milk restock or a son's birthday party, with capped discounts and an opt-out line. The owner previews every message before MantaGO sends it on WhatsApp. Third, a random 10% is held out, so every campaign measures its own lift. On 103,000 unseen grocery customers, our model's top 30% captured 53% of all extra visits, about 1.8x random: an early, noisy signal. Names and chats are fictional, gender and age are excluded, and live tests reach only our own opted-in phones.

## 3. Longer fields

**Problem**

> Small retail and F&B businesses send the same discount blast to every customer. Discounts are wasted on customers who would have returned anyway, messages ignore what customers have told the shop, and owners can't tell whether a campaign brought anyone back.

**Target users**

> Owners and marketers of small businesses that talk to customers on WhatsApp, Instagram, Messenger or LINE through MantaGO. Our demo business is Kampung Fresh, a fictional neighbourhood grocer in Tampines.

**Solution and how it works**

> 1. **Smart Send:** an uplift model predicts how much more likely each customer is to return because of a message, and picks the top customers within budget.
> 2. **Chat Memory:** an LLM extracts tags from past chats, such as restock requests, complaints and upcoming events. Each tag must quote the customer's own words.
> 3. **Personal message:** one short draft per customer, with a 10% discount cap, an apology first for complaints, and an opt-out line. The owner previews each one.
> 4. **Send:** the MantaGO Open API delivers each message on WhatsApp.
> 5. **Prove:** a random 10% of chosen customers is held out, so lift is measured against a real no-message group.

**How we use MantaGO**

> MantaGO is the delivery and customer layer. Nudgely's Open API client lists members and their clientIds, and sends a personalised broadcast to each chosen customer. The client also supports creating and assigning manual tags, so a business could see each customer's chat memory inside MantaGO. Nudgely decides who to message and what to say; MantaGO delivers it.

*Check with Thuta before submitting: if a live send or tag write-back hasn't worked by Friday, say "integration built and tested in simulation" instead.*

**Evidence and impact**

> - **Email vs no email (Hillstrom, 64k online shoppers):** visits 10.6% → 16.7% (+57%); purchases 0.57% → 1.07% (about 1.9x).
> - **SMS vs no SMS (Lenta, 687k grocery customers):** visits 10.3% → 11.0% (+7%).
> - **Our model on 103k unseen Lenta customers:** the top 30% captured 53% of all extra visits vs 30% for random (about 1.8x), with a 90% interval of 31–89%.
>
> For a business, this means more returns per message, fewer wasted discounts, fewer paid WhatsApp messages, and a retention-lift number measured against its own holdout group.

**Tech stack**

> Python, pandas, scikit-learn (HistGradientBoosting), scikit-uplift (two-model uplift), Google Gemini API (provider-swappable LLM wrapper), Streamlit on Streamlit Community Cloud, and the MantaGO Open API via `requests`.

**Datasets and licences**

> - **Lenta:** 687,029 customers, randomised SMS test, from the BigTarget Hackathon by Lenta and Microsoft (2020), distributed through scikit-uplift. No explicit licence is published; we use it for non-commercial research and demonstration only.
> - **Hillstrom:** 64,000 customers, randomised email test, released publicly by Kevin Hillstrom (MineThatData, 2008), distributed through scikit-uplift.
> - **Customer names and chats:** fictional, written by the team.

**Responsible AI** (148 words, from [Responsible_AI.md](Responsible_AI.md))

> Nudgely is honest, consent-first and human-controlled. All customer names and chats are fictional, and model results come from public randomised datasets (Lenta, Hillstrom); we report the uncertainty (90% interval 31–89%) alongside the headline. Live messages go only to our team's own opted-in test phones; opt-outs, such as a demo customer who asked to be removed, are blocked automatically, and every message ends with "Reply STOP to opt out". Chats are scrubbed of names and phone numbers before the LLM reads them, and API keys are kept out of GitHub. The targeting model uses behaviour only: gender, age and children are removed. Every AI tag must quote the customer's own words, messages may not invent stock or prices, and discounts are capped at 10%. The owner previews every message and must confirm before anything is sent; rehearsal mode is the default. Production adds DNC Register checks under Singapore's PDPA.

**AI use disclosure**

> - **In the product:** Google Gemini API (free tier) extracts tags from chats and drafts messages. Only fictional data is sent, because free-tier inputs may be used by Google to improve its products.
> - **In development:** the team used Claude (Anthropic) as a coding assistant; this is recorded in the commit history.
> - All AI output is checked automatically and reviewed by a person before use.

**Limitations and next steps**

> Names and chats are fictional, and the evidence comes from overseas public datasets, not a live Singapore business. The targeting estimate is noisy because the underlying lift is small. Uplift models also need one past campaign that had a message group and a no-message group.
>
> **Next steps:** a 2–4 week pilot with one MantaGO business in Singapore, with a holdout group; reading reply events from MantaGO automatically; retraining monthly on the business's own results; and recorded consent with DNC Register checks under the PDPA.

## 4. Links: every one must open in a signed-out (incognito) browser

| Link | URL | Status on Thu 22 Oct, 11:50pm | Owner and fix |
|---|---|---|---|
| Live app | _to add_ | ❌ Not deployed yet | **Jayden**: deploy, then set sharing to public |
| GitHub repo | https://github.com/Morn-Thuta/nudgely | ❌ **Private**: judges will get a 404 | **Thuta**: Settings → General → Danger Zone → Change visibility → Public. Safe to do: the full commit history was checked and has no keys or tokens, and `.env`, secrets and test phone numbers are git-ignored |
| Demo video | _to add_ | ❌ Not recorded yet | **Dythan**: YouTube unlisted, or Drive set to "Anyone with the link" |
| Pitch deck | _to add_ | ❌ Not shared yet | **Dythan**: set sharing to "Anyone with the link: Viewer" |
| One-page brief | `docs/One_Page_Brief.pdf` in the repo | ✅ Done; opens once the repo is public | **Shareef**: or upload the PDF to Drive with link sharing on |

**How to check a link:** open a new incognito window, paste the link, and confirm it opens without a sign-in or "Request access" screen. Re-check after every change to sharing settings.

## 5. Before pressing Submit (Friday)

- [ ] Everyone's full name filled in as registered
- [ ] All 5 links pass the incognito test
- [ ] Final number check done (deck, video, brief, app, form all match [Numbers.md](Numbers.md))
- [ ] Message count claims match reality (`data/messages.json` has 15 of 30 as of Thursday night)
- [ ] All 5 members have read the form
- [ ] Submit well before 11:59 PM SGT, and screenshot the confirmation
