import { supabase } from "./supabase";

// The shop owner's side of Nudgely: types for /api/owner/* and one helper to call it.

export type OwnerShop = {
  id: string;
  name: string;
  offer: string;
  note: string;
  template_name: string;
  template_language: string;
  whatsapp_connected: boolean;
  template_text: string;
  customers: number;
  persuadable: number;
  scored_up_to: string | null;
};

export type OwnerCustomer = {
  id: string;
  ref: string;
  label: "Persuadable" | "Sure Thing" | "Lost Cause";
  uplift: number;
  p_no_msg: number;
  p_msg: number;
  purchases: number;
  avg_spend: number;
  months_as_customer: number;
  days_since_last: number;
  opted_out?: boolean;
};

export type CampaignRow = {
  id: string;
  ref: string;
  label: string;
  uplift: number;
  group: "messaged" | "holdout";
  since: string;
  blank: string;
  message: string;
  source: "ai" | "template" | "edited" | null;
  problems: string[];
  approved: boolean;
  status: string;
  error: string | null;
  returned: 0 | 1 | null;
  returned_at: string | null;
};

export type CampaignResults = {
  messaged: number;
  messaged_back: number;
  kept_back: number;
  kept_back_back: number;
  waiting: number;
  difference: number | null;
  low: number | null;
  high: number | null;
  rate_messaged?: number;
  rate_kept_back?: number;
  verdict: "worked" | "did not help" | "too early to call" | "waiting";
};

export type CampaignSummary = {
  id: string;
  created_at: string;
  size: number;
  holdout_pct: number;
  status: "draft" | "sent";
  mode: "rehearsal" | "live" | null;
  sent_at: string | null;
};

export type Campaign = CampaignSummary & {
  expected_extra_visits: number;
  rows: CampaignRow[];
  results: CampaignResults;
  upload?: { purchases: number; unreadable_rows: number; updated: number };
};

// Signed in with Supabase, or, on a laptop without Supabase, a dev token the local backend accepts
// only when NUDGELY_DEV_AUTH=1 and Supabase is not configured.
export async function ownerToken() {
  const client = supabase();
  if (client) {
    const { data } = await client.auth.getSession();
    return data.session?.access_token ?? "";
  }
  return process.env.NEXT_PUBLIC_OWNER_DEV_TOKEN ?? "";
}

export async function ownerApi<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api/owner/${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${await ownerToken()}` },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || "Something went wrong. Try again.");
  return payload as T;
}

export function fileToBase64(file: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.onerror = () => reject(new Error("Couldn't read that file."));
    reader.readAsDataURL(file);
  });
}

export const MAX_UPLOAD = 2_000_000;
// The shop name typed at sign-up, kept until the owner confirms their email and signs in.
export const PENDING_SHOP = "nudgely.pendingShop";
export const pct = (n: number | null | undefined) => (n == null ? "–" : `${Math.round(n * 100)}%`);
export const points = (n: number | null | undefined) =>
  n == null ? "–" : `${n >= 0 ? "+" : ""}${(n * 100).toFixed(1)} pts`;
export const when = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString("en-SG", { day: "numeric", month: "short", year: "numeric" }) : "–";
