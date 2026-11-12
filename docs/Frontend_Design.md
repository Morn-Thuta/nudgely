# Nudgely interface direction

The product should feel like a well-kept neighbourhood shop: welcoming at the door, organised behind the counter. The landing page is expressive; the workspace prioritises reading conversations and making a careful decision.

## Design system

- Organic, calm direction. Feasibility/impact score: 14 (impact 4, fit 5, feasibility 4, performance 4, consistency risk 3).
- Outfit headings give the shop a rounded, recognisable voice. DM Sans keeps forms and dense records readable. Both fonts are bundled locally.
- Cream surfaces, forest-green actions, sage context panels and a restrained warm accent. Shared tokens live in `web/src/app/app-ui.css`; the landing composition is scoped in `landing.css`.
- Spacing uses a small consistent rhythm, with 12–18 px card radii and controls at least 44 px where practical. Icons come from Lucide.
- The 3D shop is the memorable visual anchor. Only the landing has scroll-driven motion. The product uses stable layouts, clear active states and direct interactions.

## Navigation and tasks

1. Landing → Explore the app opens the fictional workspace; Try a conversation opens the shop chat.
2. Conversations → customer thread and evidence-linked memories. Phones show the inbox first, then a selected conversation with a clear back action.
3. Customers → search/filter → profile dialog. Native dialog behavior supports Escape, focus containment and focus restoration.
4. Campaign → choose audience → inspect drafts → acknowledge review → simulate. Opt-outs, invalid drafts and duplicate rehearsals remain guarded.
5. Results keeps historical evidence separate from live outcomes. The 57% headline uses normal digit spacing and tabular numerals.
6. Sign-in, QR presentation and chat reuse the same visual identity. No extra backend capability is implied by the redesign.

## Accessibility and verification

The site supports visible keyboard focus, labelled inputs, error/status announcements, reduced-motion preferences, a manual 3D pause control and a static WebGL fallback. The 3D scene is decorative; the story also exists as semantic text. Customer lists and tables scroll within their containers on narrow screens.

Automated checks exercise desktop and mobile routes, the main navigation flow, customer dialog dismissal/focus, password visibility, campaign guards, chat errors and auth redirects. Screenshots and manual browser inspection complement those checks. Real team sign-in and cross-device chat-to-dashboard behavior still depend on provisioned accounts and deployment configuration.

Design guidance: installed Frontend Design and UI/UX Pro Max skills. The generated palette suggestion was adapted to the existing Nudgely cream/green identity for continuity with the requested landing reference.
