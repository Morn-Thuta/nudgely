-- Only accounts explicitly designated by a project administrator may read the shop.
-- app_metadata cannot be set by public sign-up or updateUser (unlike user_metadata).
-- Provision a team account in Supabase Auth, then set app_metadata.nudgely_team = true.
-- Keeps Thuta's service-role backend writes and migration 002's column grants unchanged.
drop policy if exists "signed-in can read customers" on public.customers;
drop policy if exists "signed-in can read messages" on public.messages;
drop policy if exists "signed-in can read tags" on public.tags;
drop policy if exists "signed-in can resolve handovers" on public.customers;
create policy "team can read customers" on public.customers for select to authenticated
  using ((select auth.jwt() -> 'app_metadata' ->> 'nudgely_team') = 'true');
create policy "team can read messages" on public.messages for select to authenticated
  using ((select auth.jwt() -> 'app_metadata' ->> 'nudgely_team') = 'true');
create policy "team can read tags" on public.tags for select to authenticated
  using ((select auth.jwt() -> 'app_metadata' ->> 'nudgely_team') = 'true');
create policy "team can resolve handovers" on public.customers for update to authenticated
  using ((select auth.jwt() -> 'app_metadata' ->> 'nudgely_team') = 'true')
  with check ((select auth.jwt() -> 'app_metadata' ->> 'nudgely_team') = 'true');
