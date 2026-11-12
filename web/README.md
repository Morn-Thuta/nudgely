# Nudgely frontend

Dythan's Next.js frontend for the 14 November finals. The landing page uses an original procedural 3D neighbourhood shop, scroll-driven storytelling, a cream/green palette and locally bundled Outfit/DM Sans fonts. See [frontend handoff](../docs/Frontend_Handoff.md) and [stage script](../docs/Dythan_Demo_Script.md).

## Run

Node 20.9+ (Node 24 used for validation).

```powershell
cd web
npm ci
Copy-Item .env.example .env.local
# Fill in the public Supabase URL and publishable key for team sign-in.
npm run dev
```

Open http://localhost:3000. The public demo works without Supabase. Chat defaults to the existing Render backend; set `NUDGELY_CHAT_MODE=mock` for an explicitly labelled offline rehearsal. Do not put a Supabase service-role key or an LLM key in this frontend.

| Route | Purpose |
|---|---|
| `/` | Scrolling 3D shop story, evidence, demo entry points and QR |
| `/try` | Mobile judge chat through the same-origin `/api/chat` proxy |
| `/present` | Large QR view for the stage |
| `/login` | Email/password sign-in for provisioned team accounts |
| `/dashboard` | Authenticated live conversations; Realtime + 15-second fallback refresh |
| `/dashboard/customers` | Customer labels, uplift and evidence-linked tags |
| `/dashboard/campaign` | Reviewed campaign simulation; no delivery endpoint exists in the contract |
| `/dashboard/results` | Historical evidence; no fabricated live campaign results |
| `/demo` and its subpages | Public, explicitly fictional data; no live database reads |

## Data and access

- `npm run data:sync` exports allowlisted fields from committed fictional data. It never reads test-account phone mappings or runtime inboxes. Run it after changes to the source artifacts and commit the generated JSON.
- The 30 legacy demo profiles and the 48 synthetic sales-sample customers are different populations. The current headline is **57%, about 1.9x random, range 38–85% over seven splits**. Source: `docs/Numbers.md` and `data/uplift_transferable.json`.
- The browser uses Supabase's publishable key and signed-in session. Every live query is protected by RLS. `customers` uses an explicit column projection because `key_hash` must remain unreadable.
- Apply migrations `001`, `002`, then `003_team_dashboard_access.sql`. Migration 003 requires the administrator-controlled `app_metadata.nudgely_team` boolean. An ordinary public sign-up cannot grant itself dashboard access.
- Realtime listens to customers, messages and tags; a refresh failure is shown without substituting fictional data. The demo view never pretends to be live.
- Conversations are read-only. Handover resolution, live campaign sending, and live return tracking require backend integration beyond today's contract.

## Checks

The landing scene loads dynamically near the viewport and renders only when needed. The pause control and system reduced-motion preference replace 3D with an original SVG illustration and show all three story chapters in a normal layout. A WebGL failure also falls back to the illustration. No external models or textures are downloaded. The visual reference was [CabinetCare](https://cabinetcare-landing.vercel.app/); Nudgely's scene, illustrations and copy are original.

```powershell
npm run lint
npm run typecheck
npm test
npm run build
npm run test:e2e
```

Browser checks use Microsoft Edge and mobile viewport emulation. Install Edge or change `channel` in `playwright.config.ts` to an installed Chromium browser. `test:e2e` starts the built app on port 3100 in explicit mock mode; chat responses are intercepted and no real messages or paid model requests are sent. Windows sandbox restrictions may require these commands to run outside the sandbox.

## Vercel

Import `Morn-Thuta/nudgely`, framework **Next.js**, root directory **web**, Node **24.x**, install `npm ci`, build `npm run build`. Deploy the frontend branch for review before merging.

Set the values from `.env.example` in Vercel settings. `NEXT_PUBLIC_SITE_URL` should be the public frontend URL so stage QR codes work on phones. Use `NUDGELY_CHAT_MODE=live` only for the real demo. Public Supabase variables are embedded at build time: redeploy after changing them. Keep `/try` publicly reachable; the database remains behind team authentication.

The backend URL is server-side, so browser CORS does not block the chat proxy. No API keys or Supabase service keys are required by that proxy. Backend rate limits remain authoritative. It does not retry a timed-out message, because delivery may already have happened.

References used: [Next.js installation](https://nextjs.org/docs/app/getting-started/installation), [Supabase auth guidance](https://supabase.com/docs/guides/auth/server-side/advanced-guide). This dashboard uses a browser Supabase client with `getUser()` and database RLS; it does not authorize from client-provided session data alone.
