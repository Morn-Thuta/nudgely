-- Backend state, so the API keeps nothing on disk (Render restarts, Vercel) and Supabase is the source of truth.
-- Run after 001_init.sql.

alter table public.customers
  add column if not exists key_hash  text unique,                 -- HMAC of the WhatsApp number / web session; never the number itself
  add column if not exists replied   boolean not null default false,
  add column if not exists memory    jsonb   not null default '{}'::jsonb,  -- merged AI tags, sentiment, best hook
  add column if not exists seen_ids  text[]  not null default '{}',         -- WhatsApp message ids already answered
  add column if not exists msg_count integer not null default 0;            -- for the per-visitor message cap

-- The dashboard must not see key_hash. Column-level grants on top of RLS:
revoke select on public.customers from authenticated, anon;
grant select (id, channel, name, label, uplift, p_no_msg, handover, opted_out, created_at, last_seen_at, memory, msg_count)
  on public.customers to authenticated;
revoke update on public.customers from authenticated, anon;
grant update (handover) on public.customers to authenticated;   -- "Mark resolved" on the dashboard
