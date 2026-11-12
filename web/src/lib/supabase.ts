import { createClient, type SupabaseClient } from "@supabase/supabase-js";
let instance: SupabaseClient | null = null;
export function supabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL,
    key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) return null;
  if (!instance) instance = createClient(url, key);
  return instance;
}
// Explicit projection is required by migration 002; SELECT * includes private backend columns.
export const CUSTOMER_COLUMNS =
  "id,channel,name,label,uplift,p_no_msg,handover,opted_out,created_at,last_seen_at";
