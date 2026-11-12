# Shops: a real shop runs its own campaign

Until now Nudgely ran on one fictional shop. This adds the multi-shop version of the whole loop.
Branch `jack/shop-campaigns`. Nothing here touches the demo shop, `/demo` or the team dashboard.

| Step | Where | What happens |
|---|---|---|
| 1. Sign up | `/signup` | Any email account can create one shop. Team accounts still go to `/dashboard` from `/login`; everyone else goes to `/shop` |
| 2. Own data | Supabase, migration 004 | Five new tables. RLS on with no policies, so the browser can read none of it; the backend serves each owner only their own shop |
| 3. Upload sales | `/shop` (Customers) | CSV or Excel, scored with Model 2 and kept. Phones stay on the server; the page shows `•••• 3412` |
| 4. Plan | `/shop/campaign` | Top Persuadables by uplift, with a random share kept back (0–30%) |
| 5. Write | `/shop/campaign` | The shop's win-back template has two blanks: `{{1}}` how long since their last visit (calculated) and `{{2}}` one sentence the AI writes from the owner's offer and note. A sentence that invents a number, price or discount is thrown away for a plain one. Written 6 at a time with a 28 s limit, so no request runs long |
| 6. Send | `/shop/campaign` | Rehearsal (nothing leaves) or live through the shop's own WhatsApp number and Meta-approved template (`/shop/settings`) |
| 7. Results | `/shop/results` | Upload sales from the send date: messaged vs kept back, the range the difference could be, and a verdict |

Code: `nudgely/shops.py` (all the logic, storage-agnostic), `api/owner.py` (`/api/owner/*`), `web/src/components/owner-*.tsx`,
`web/src/app/{signup,shop}`, `web/src/app/api/owner/[...path]/route.ts`. Tests: `tests/test_owner.py`.

## Going live (Thuta)

1. Run `supabase/migrations/004_shops.sql` in the Supabase SQL editor. It only adds tables.
2. In Supabase Auth, decide on email confirmation. With it on, the owner confirms their email, signs in, and names the shop then.
3. Merge to `main`. Render rebuilds the backend (the scoring libraries are already in `api/requirements.txt`) and Vercel the site.

## Running it on a laptop without Supabase

`NUDGELY_DEV_AUTH=1` in `.env` and `NEXT_PUBLIC_OWNER_DEV_TOKEN=dev-yourname` in `web/.env.local`. Shops are kept in
`data/shops.json` (git-ignored). The dev sign-in refuses to work when Supabase is configured.

## Not done

- **A shop's own WhatsApp number** needs Meta to approve the number and the win-back template; until then live sends fail with Meta's reason and rehearsals work.
- **Replies and STOP on a shop's own number**: the webhook still answers the team's test number only.
- **Retraining on the shop's own results.** Scores come from Model 2, trained on Lenta. Each campaign's messaged and kept-back customers, with who came back, are exactly the data to train the shop's own pair of models once there are a few hundred.
