"use client";
import { useSyncExternalStore } from "react";
import { QRCodeSVG } from "qrcode.react";
import Link from "next/link";
const subscribe = () => () => {};
const getOrigin = () =>
  process.env.NEXT_PUBLIC_SITE_URL || window.location.origin;
const getServerOrigin = () => process.env.NEXT_PUBLIC_SITE_URL || "";
export function QRPanel({ large = false }: { large?: boolean }) {
  const origin = useSyncExternalStore(subscribe, getOrigin, getServerOrigin);
  const url = origin ? new URL("/try", origin).toString() : "";
  const local = url && /localhost|127\.0\.0\.1/.test(new URL(url).hostname);
  return (
    <div className={large ? "qr-panel qr-large" : "qr-panel"}>
      {url ? (
        <div className="qr-code">
          <QRCodeSVG
            value={url}
            size={large ? 280 : 160}
            marginSize={3}
            level="M"
            title="Open the Nudgely demo chat"
          />
        </div>
      ) : (
        <div className="qr-loading">Preparing QR code…</div>
      )}
      <div>
        <h3>Meet your new regular.</h3>
        <p>
          Scan to chat with Kampung Fresh. Ask about oat milk, plan a party, or
          ask for a person.
        </p>
        <Link href="/try" className="text-link">
          Open the chat instead ↗
        </Link>
        {local ? (
          <p className="fine">
            Local preview: this QR works on this computer only. A public site
            URL is needed for phones.
          </p>
        ) : (
          <p className="fine">{url}</p>
        )}
      </div>
    </div>
  );
}
