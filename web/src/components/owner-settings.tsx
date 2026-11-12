"use client";
import { useState, type FormEvent } from "react";
import { useOwner } from "./owner-shell";
import { ownerApi, type OwnerShop } from "@/lib/owner";

export function OwnerSettings() {
  const { shop, refresh } = useOwner();
  const [offer, setOffer] = useState(shop.offer),
    [note, setNote] = useState(shop.note),
    [pnid, setPnid] = useState(""),
    [token, setToken] = useState(""),
    [template, setTemplate] = useState(shop.template_name),
    [lang, setLang] = useState(shop.template_language || "en"),
    [busy, setBusy] = useState(""),
    [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function save(e: FormEvent, which: "words" | "whatsapp") {
    e.preventDefault();
    setBusy(which);
    setMsg(null);
    try {
      const body =
        which === "words"
          ? { offer, note }
          : {
              whatsapp: {
                template_name: template,
                template_language: lang,
                ...(token ? { wa_token: token } : {}),
                ...(pnid ? { wa_phone_number_id: pnid } : {}),
              },
            };
      await ownerApi<{ shop: OwnerShop }>("settings", body);
      setToken("");
      await refresh();
      setMsg({ ok: true, text: which === "words" ? "Saved. New messages use these words." : "WhatsApp details saved." });
    } catch (err) {
      setMsg({ ok: false, text: (err as Error).message });
    } finally {
      setBusy("");
    }
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Settings</p>
          <h1>What your messages may say.</h1>
          <p>The AI only uses what you write here. It never invents a product, price or offer.</p>
        </div>
      </div>
      {msg && (
        <p className={msg.ok ? "fine owner-ok" : "error"} role={msg.ok ? "status" : "alert"}>
          {msg.text}
        </p>
      )}

      <section className="panel">
        <p className="eyebrow">Your words</p>
        <form className="owner-form" onSubmit={(e) => void save(e, "words")}>
          <label htmlFor="set-offer">Offer for customers worth messaging (optional, 10% at most)</label>
          <input
            id="set-offer"
            maxLength={60}
            value={offer}
            onChange={(e) => setOffer(e.target.value)}
            placeholder="10% off your next basket"
          />
          <label htmlFor="set-note">What’s new at the shop (optional)</label>
          <input
            id="set-note"
            maxLength={140}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Fresh durians came in this week"
          />
          <button className="button primary" disabled={!!busy}>
            {busy === "words" ? "Saving…" : "Save"}
          </button>
        </form>
      </section>

      <section className="panel">
        <p className="eyebrow">WhatsApp</p>
        <h2>{shop.whatsapp_connected ? "Connected." : "Not connected yet."}</h2>
        <p>
          WhatsApp only lets a shop start a conversation with a template Meta has approved. Submit this one in
          your WhatsApp Business account (category Marketing), with its two blanks:
        </p>
        <blockquote className="owner-template">{shop.template_text}</blockquote>
        <p className="fine">
          {"{{1}}"} is how long since their last visit, worked out from your sales. {"{{2}}"} is the one sentence
          the AI writes, from your offer and note.
        </p>
        <form className="owner-form" onSubmit={(e) => void save(e, "whatsapp")}>
          <label htmlFor="set-pnid">Phone number ID (from Meta, not the phone number)</label>
          <input
            id="set-pnid"
            value={pnid}
            onChange={(e) => setPnid(e.target.value)}
            placeholder={shop.whatsapp_connected ? "Saved. Enter a new one to replace it" : "1412073635325460"}
          />
          <label htmlFor="set-token">Access token</label>
          <input
            id="set-token"
            type="password"
            autoComplete="off"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder={shop.whatsapp_connected ? "Saved. Enter a new one to replace it" : "EAAG…"}
          />
          <label htmlFor="set-template">Approved template name</label>
          <input id="set-template" value={template} onChange={(e) => setTemplate(e.target.value)} placeholder="win_back" />
          <label htmlFor="set-lang">Template language code</label>
          <input id="set-lang" value={lang} onChange={(e) => setLang(e.target.value)} placeholder="en" />
          <button className="button primary" disabled={!!busy}>
            {busy === "whatsapp" ? "Saving…" : "Save WhatsApp details"}
          </button>
          <p className="fine">The token is stored on our server and never shown again.</p>
        </form>
      </section>
    </>
  );
}
