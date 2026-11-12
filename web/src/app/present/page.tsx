import { Brand } from "@/components/brand";
import { QRPanel } from "@/components/qr-panel";
import Link from "next/link";
export const metadata = { title: "Scan to try" };
export default function Present() {
  return (
    <div className="dark-shell presentation">
      <header>
        <Brand />
        <div className="presentation-actions">
          <Link href="/demo">Explore the demo ↗</Link>
          <Link href="/dashboard">Live workspace ↗</Link>
        </div>
      </header>
      <main id="main">
        <p className="eyebrow">Your turn to try Nudgely</p>
        <h1>
          A conversation.
          <br />A little connection.
        </h1>
        <QRPanel large />
        <p className="fine">
          Fictional shop. Real AI in live mode. Your demo chat may appear on the
          team’s screen. Please don’t share private information.
        </p>
      </main>
    </div>
  );
}
