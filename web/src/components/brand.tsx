import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
export function Brand() {
  return (
    <Link href="/" className="brand" aria-label="Nudgely home">
      nudgely
      <span>
        <ArrowUpRight size={22} />
      </span>
    </Link>
  );
}
export function PublicHeader() {
  return (
    <header className="public-header wrap">
      <Brand />
      <nav aria-label="Main navigation">
        <Link href="/#how">How it works</Link>
        <Link href="/#evidence">The evidence</Link>
        <Link href="/login">
          Shop sign in <ArrowUpRight size={15} />
        </Link>
      </nav>
    </header>
  );
}
