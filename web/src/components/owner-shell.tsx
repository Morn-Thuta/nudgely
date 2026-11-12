"use client";
import { createContext, useCallback, useContext, useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ChartNoAxesCombined, ChevronRight, LogOut, Send, Settings, Users } from "lucide-react";
import { Brand } from "@/components/brand";
import { supabase } from "@/lib/supabase";
import { PENDING_SHOP, ownerApi, ownerToken, type OwnerShop } from "@/lib/owner";
import { cn } from "@/lib/utils";

// The signed-in shop owner's workspace: their own shop, not the demo one.
type OwnerState = { shop: OwnerShop; refresh: () => Promise<void> };
const Context = createContext<OwnerState | null>(null);
export function useOwner() {
  const c = useContext(Context);
  if (!c) throw new Error("Owner workspace missing");
  return c;
}

const NAV = [
  { href: "/shop", label: "Customers", icon: Users },
  { href: "/shop/campaign", label: "Campaign", icon: Send },
  { href: "/shop/results", label: "Results", icon: ChartNoAxesCombined },
  { href: "/shop/settings", label: "Settings", icon: Settings },
];

export function OwnerShell({ children }: { children: React.ReactNode }) {
  const path = usePathname(),
    router = useRouter();
  const [shop, setShop] = useState<OwnerShop | null>(null),
    [phase, setPhase] = useState<"loading" | "no-shop" | "ready">("loading"),
    [error, setError] = useState("");

  const refresh = useCallback(async () => {
    if (!(await ownerToken())) {
      router.replace("/login");
      return;
    }
    try {
      const { shop } = await ownerApi<{ shop: OwnerShop | null }>("shop");
      setShop(shop);
      setPhase(shop ? "ready" : "no-shop");
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, [router]);

  useEffect(() => {
    // Loads the owner's shop from the backend; state is set after the request resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  async function signOut() {
    await supabase()?.auth.signOut();
    router.replace("/login");
  }

  const current = NAV.find((n) => n.href === path)?.label ?? "Customers";
  const initials = (shop?.name ?? "Your shop")
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="workspace">
      <aside className="sidebar">
        <Brand />
        <div className="workspace-shop">
          <span className="shop-initial">{initials}</span>
          <div>
            <strong>{shop?.name ?? "Your shop"}</strong>
            <span>{shop ? `${shop.customers} customers scored` : "Shop owner"}</span>
          </div>
        </div>
        <p className="eyebrow sidebar-label">Your shop</p>
        <nav aria-label="Shop navigation">
          {NAV.map((n) => (
            <Link
              href={n.href}
              key={n.href}
              className={cn("sidebar-link", path === n.href && "active")}
              aria-current={path === n.href ? "page" : undefined}
            >
              <n.icon size={19} />
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          {supabase() && (
            <button onClick={() => void signOut()}>
              <LogOut size={18} /> Sign out
            </button>
          )}
          <p>Phone numbers stay on our server. You see the last four digits only.</p>
        </div>
      </aside>
      <div className="workspace-body">
        <header className="workspace-top">
          <div className="workspace-breadcrumb">
            {shop?.name ?? "Your shop"} <ChevronRight size={14} />
            <strong>{current}</strong>
          </div>
        </header>
        {error && (
          <div className="error workspace-error" role="alert">
            {error}
            <button onClick={() => void refresh()}>Retry</button>
          </div>
        )}
        <main id="main" className="workspace-content">
          {phase === "loading" ? (
            <div className="loading-state" role="status">
              Opening your shop…
            </div>
          ) : phase === "no-shop" ? (
            <CreateShop onCreated={refresh} />
          ) : (
            shop && <Context.Provider value={{ shop, refresh }}>{children}</Context.Provider>
          )}
        </main>
      </div>
    </div>
  );
}

function CreateShop({ onCreated }: { onCreated: () => Promise<void> }) {
  const [name, setName] = useState(() => {
    try {
      return localStorage.getItem(PENDING_SHOP) ?? "";
    } catch {
      return "";
    }
  });
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function create(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await ownerApi("shop", { name });
      try {
        localStorage.removeItem(PENDING_SHOP);
      } catch {
        /* nothing to clean up */
      }
      await onCreated();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel owner-narrow">
      <p className="eyebrow">One last step</p>
      <h2>Name your shop.</h2>
      <p>It appears in every message your customers get, so use the name they know you by.</p>
      <form onSubmit={create} className="owner-form">
        <label htmlFor="create-shop-name">Shop name</label>
        <input
          id="create-shop-name"
          required
          minLength={2}
          maxLength={40}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Ah Seng Provision"
        />
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button className="button primary" disabled={busy}>
          {busy ? "Creating…" : "Create my shop"}
        </button>
      </form>
    </section>
  );
}
