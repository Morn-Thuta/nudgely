"use client";
import { useEffect, useState } from "react";
import { Send } from "lucide-react";
import { supabase } from "@/lib/supabase";
import type { PlanRow } from "@/lib/campaign";
import type { Draft } from "@/lib/types";

async function token() {
  const { data } = (await supabase()?.auth.getSession()) ?? { data: null };
  return data?.session?.access_token ?? "";
}

async function call(path: string, init?: RequestInit) {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${await token()}`,
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || "Request failed.");
  return payload;
}

// Real delivery, one customer at a time, only to demo phones the backend allows
// (LIVE_RECIPIENTS). Everyone else in the plan stays a rehearsal.
export function LiveSend({
  plan,
  drafts,
}: {
  plan: PlanRow[];
  drafts: Record<string, Draft>;
}) {
  const [live, setLive] = useState<string[] | null>(null);
  useEffect(() => {
    call("/api/campaign/live")
      .then((p) => setLive(p.customer_ids ?? []))
      .catch(() => setLive([]));
  }, []);
  const rows = plan.filter((r) => live?.includes(r.customer.id));
  if (!rows.length) return null;
  return (
    <section className="panel review-panel live-send">
      <p className="eyebrow">Live</p>
      <h2>Send for real, on WhatsApp.</h2>
      <p>
        Only opted-in demo phones can be sent to. Read the message, change
        anything that’s out of date, then send. Everyone else above stays a
        rehearsal.
      </p>
      {rows.map((r) => (
        <LiveCard
          key={r.customer.id}
          row={r}
          draft={drafts[r.customer.id]?.message ?? ""}
        />
      ))}
    </section>
  );
}

function LiveCard({ row, draft }: { row: PlanRow; draft: string }) {
  const [text, setText] = useState(draft),
    [checked, setChecked] = useState(false),
    [busy, setBusy] = useState(false),
    [status, setStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const name = row.customer.name || row.customer.id;
  const held = row.group !== "Will message";
  async function send() {
    if (!window.confirm(`Send this WhatsApp message to ${name} now?`)) return;
    setBusy(true);
    setStatus(null);
    try {
      await call("/api/campaign/send", {
        method: "POST",
        body: JSON.stringify({ customer_id: row.customer.id, message: text }),
      });
      setStatus({ ok: true, text: `Sent to ${name} on WhatsApp.` });
      setChecked(false);
    } catch (e) {
      setStatus({ ok: false, text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="draft-card">
      <div>
        <h3>{name}</h3>
        <span className="pill">{row.customer.label}</span>
      </div>
      {held ? (
        <p className="fine">
          {name} is {row.group === "Held out" ? "in the comparison group" : "not selected"}{" "}
          in this plan, so no message goes out. Change the audience to include
          them.
        </p>
      ) : (
        <>
          <label className="fine" htmlFor={`live-${row.customer.id}`}>
            Message ({text.length}/600)
          </label>
          <textarea
            id={`live-${row.customer.id}`}
            className="live-text"
            value={text}
            maxLength={600}
            rows={4}
            onChange={(e) => {
              setText(e.target.value);
              setChecked(false);
            }}
          />
          <label className="check-row">
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
            />{" "}
            I’ve read this message and {name} has opted in.
          </label>
          <button
            className="button primary"
            disabled={!checked || busy || !text.trim()}
            onClick={send}
          >
            <Send size={16} /> {busy ? "Sending…" : "Send on WhatsApp"}
          </button>
          {status && (
            <p role="status" className={status.ok ? "notice" : "error"}>
              {status.text}
            </p>
          )}
        </>
      )}
    </article>
  );
}
