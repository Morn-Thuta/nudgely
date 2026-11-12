# Dythan: frontend handoff — 11 November 2026

Built from main at `bc7f6a5`, in `web/`. Existing Streamlit edits were preserved in their original working copy.

## Ready for review

- Next.js/TypeScript landing page with an original React Three Fiber grocery shop. Scroll opens the shop door, introduces customers and reveals an evidence chart across three story chapters. Warm cream/green design, bundled Outfit/DM Sans fonts, responsive layout, pause control, reduced-motion layout and SVG fallback.
- Connected product redesign: consistent navigation and surfaces, responsive inbox with a mobile back action, keyboard-accessible customer detail dialogs, three-step campaign review, clearer results, password visibility control, chat suggestions and Enter-to-send (Shift+Enter for a new line). Landing links directly to `/demo` and `/try`; the logo returns to `/`.
- `/try`: optional name, 500-character messages, stable browser-tab session, typing state, rate-limit errors, nullable replies, HUMAN/STOP/START backend semantics. Same-origin proxy to the existing Render API; no fake fallback when live requests fail.
- `/present`: phone QR code from the configured public URL or current origin. Local previews explicitly warn that localhost does not work on another device.
- Supabase team login, live conversations with evidence-linked tags, customer search and detail, campaign rehearsal, historical results. Public `/demo` routes read only committed fictional data.
- Campaign opt-outs, deterministic holdout, draft checks, review acknowledgement, repeat-run prevention on the current page, and a simulated CSV export. No live delivery is claimed.
- Current 57% / 1.9x / 38–85% figures used consistently. The old 30-customer scores are labelled separately from the newer transferable model.

## Supabase created and seeded

Project: **nudgely**, Singapore (`ap-southeast-1`). Project reference: `vpjhnagrxaqgodfiweui`.

Dashboard: https://supabase.com/dashboard/project/vpjhnagrxaqgodfiweui

API URL: `https://vpjhnagrxaqgodfiweui.supabase.co`

Migrations 001, 002 and the new 003 have been applied. Seeded **30 fictional customers, 87 chat messages and 45 distinct tags**. C014's explicit opt-out is preserved. Seed SQL can be regenerated with `node web/scripts/seed-sql.mjs`; it does not require downloading or exposing the service-role key.

Access verified using database roles: anonymous and non-team authenticated users see zero messages; designated team users can read all 87. `authenticated` cannot read `customers.key_hash`. Supabase security advisor reported no findings after migration.

### Team account provisioning (project administrator)

1. Create a team user in Supabase Authentication → Users. Do not share passwords in Git or chat. Use normal account/password management through Supabase.
2. After verifying the user, grant the team role in the SQL editor, substituting that user's UUID:

```sql
update auth.users
set raw_app_meta_data = coalesce(raw_app_meta_data, '{}'::jsonb)
  || '{"nudgely_team": true}'::jsonb
where id = '<verified-team-user-uuid>'::uuid;
```

3. Sign out and back in to refresh the JWT. Disable public sign-up for this team-only app if desired; migration 003 still prevents ordinary sign-ups from reading conversations.
4. Invite Thuta to the Supabase project through the organization's member settings. This has **not** been sent automatically.

Migration 003 changes the broad authenticated-user policies to an administrator-controlled team role without changing the agreed table columns. Thuta must include it in any fresh environment. Backend service-role access is unchanged.

## Remaining live dependencies

| Item | Owner / action |
|---|---|
| Vercel deployment | Team access authorization is required for the connected `cabinet-care` scope before a project/deployment can be created. See `web/README.md` for ready-to-use settings. |
| Dashboard login | Provision the first team account with the metadata role above. No account has been created or invited automatically. |
| Backend → new database | Latest team update (`e56cd7b`) reports Render now saves live chats to Supabase. Full signed-in frontend verification is still pending. The frontend never needs a service-role key or `KEY_SALT`. |
| End-to-end live proof | Judge web chat and WhatsApp → Render → Supabase → signed-in dashboard. Realtime and 15-second polling are implemented but this full deployed path remains unverified. |
| Campaign delivery | No delivery endpoint in `V1_ARCHITECTURE.md`; frontend is deliberately labelled rehearsal. Coordinate the endpoint with Thuta before adding sending. |
| Final pitch | Shareef's business slides and measured classmate-test results are pending. See `Dythan_Demo_Script.md`; record the backup once the deployed flow is verified. |

## Validation

Validation includes production build, lint, TypeScript, nine unit tests and desktop/mobile browser tests. Browser tests cover responsive layouts across product routes, landing-to-app navigation, customer dialogs and focus restoration, password visibility, reduced-motion and manual pause behavior, opt-out filtering, reviewed simulation, keyboard chat submission, handover/null replies, rate limits, stable chat sessions and signed-out redirects. Tests mock chat; they do not establish real AI quality, live delivery or cross-device Realtime behavior.

Feature freeze: **Friday 13 November, noon SGT**. Finals: **Saturday 14 November**. If the live path is not reliable by the freeze, use the team's Streamlit + Live WhatsApp fallback and label prerecorded or simulated sections clearly.
