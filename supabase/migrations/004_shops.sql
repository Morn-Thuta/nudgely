-- Shops: a real shop signs up, uploads its sales, and runs its own campaign (nudgely/shops.py).
-- Run after 001-003. Additive only: nothing here touches the demo tables or the team dashboard.
--
-- Every shop table is written and read by the backend alone, with the service key. RLS is on with
-- no policies, so the publishable key (the browser) can read none of it: a shop's customers and
-- their phone numbers only reach the owner through the backend, after it checks who is signed in.

create table if not exists public.shops (
  id                text primary key default gen_random_uuid()::text,
  owner             uuid not null unique references auth.users(id) on delete cascade,  -- one shop per account
  name              text not null,
  offer             text not null default '',      -- e.g. "10% off your next basket"; fed to the AI's sentence
  note              text not null default '',      -- e.g. "Fresh durians came in this week"
  template_name     text,                          -- the shop's approved win-back template in Meta
  template_language text not null default 'en',
  created_at        timestamptz not null default now()
);

-- WhatsApp credentials live apart from everything else and are never returned by the API.
create table if not exists public.shop_secrets (
  shop_id            text primary key references public.shops(id) on delete cascade,
  wa_token           text,
  wa_phone_number_id text
);

create table if not exists public.shop_customers (
  id                 text primary key default gen_random_uuid()::text,
  shop_id            text not null references public.shops(id) on delete cascade,
  phone              text not null,                -- needed to send; never served to the browser
  ref                text not null,                -- what the owner sees: "•••• 3412"
  label              text not null,                -- Persuadable | Sure Thing | Lost Cause
  uplift             real,
  p_no_msg           real,
  p_msg              real,
  purchases          integer,
  avg_spend          real,
  months_as_customer real,
  days_since_last    integer,
  as_of              date,                         -- last date in the sales file that scored them
  scored_at          timestamptz,
  opted_out          boolean not null default false,
  unique (shop_id, phone)
);

create table if not exists public.shop_campaigns (
  id                    text primary key default gen_random_uuid()::text,
  shop_id               text not null references public.shops(id) on delete cascade,
  created_at            timestamptz not null default now(),
  size                  integer not null,
  holdout_pct           integer not null,
  status                text not null default 'draft' check (status in ('draft', 'sent')),
  mode                  text check (mode in ('rehearsal', 'live')),
  sent_at               timestamptz,
  expected_extra_visits real
);

create table if not exists public.campaign_rows (
  id           text primary key default gen_random_uuid()::text,
  campaign_id  text not null references public.shop_campaigns(id) on delete cascade,
  shop_id      text not null references public.shops(id) on delete cascade,
  phone        text not null,
  ref          text not null,
  label        text not null,
  uplift       real,
  "group"      text not null check ("group" in ('messaged', 'holdout')),
  since        text,                               -- template {{1}}, calculated
  blank        text,                               -- template {{2}}, AI-written or edited, checked
  message      text,                               -- the whole rendered template, for review
  source       text,                               -- ai | template | edited
  problems     jsonb not null default '[]'::jsonb,
  approved     boolean not null default false,
  status       text not null,                      -- draft | not messaged | simulated | sent | failed | skipped
  error        text,
  sent_at      timestamptz,
  returned     smallint check (returned in (0, 1)),
  returned_at  text
);
create index if not exists campaign_rows_campaign on public.campaign_rows (campaign_id);
create index if not exists shop_customers_shop on public.shop_customers (shop_id);

alter table public.shops          enable row level security;
alter table public.shop_secrets   enable row level security;
alter table public.shop_customers enable row level security;
alter table public.shop_campaigns enable row level security;
alter table public.campaign_rows  enable row level security;
revoke all on public.shops, public.shop_secrets, public.shop_customers, public.shop_campaigns,
              public.campaign_rows from anon, authenticated;
