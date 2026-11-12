"use client";
import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowUpRight, Check, Eye, EyeOff } from "lucide-react";
import { Brand } from "@/components/brand";
import { ShopFallback } from "@/components/landing/shop-fallback";
import { supabase } from "@/lib/supabase";
import { PENDING_SHOP, ownerApi, ownerToken } from "@/lib/owner";

// A shop owner creates an account and their shop in one go. If Supabase asks them to confirm their
// email first, the shop name is remembered and the shop is created on their first sign-in.
export default function Signup() {
  const router = useRouter();
  const client = supabase();
  const devToken = !client && process.env.NEXT_PUBLIC_OWNER_DEV_TOKEN;
  const [shop, setShop] = useState(""),
    [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [show, setShow] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [info, setInfo] = useState("");

  async function signup(e: FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    setInfo("");
    try {
      if (client) {
        const { data, error } = await client.auth.signUp({ email, password });
        if (error) {
          setError(error.message || "Couldn't create the account. Try again.");
          return;
        }
        if (!data.session) {
          try {
            localStorage.setItem(PENDING_SHOP, shop);
          } catch {
            /* the shop name is asked for again after sign-in */
          }
          setInfo("Check your email and click the link to confirm your account, then sign in. Your shop is set up then.");
          return;
        }
      } else if (!(await ownerToken())) {
        setError("Sign-up isn't connected on this copy of the site.");
        return;
      }
      await ownerApi("shop", { name: shop });
      router.replace("/shop");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <header className="auth-header">
        <Brand />
        <Link href="/">
          Back to the little shop <ArrowUpRight size={15} />
        </Link>
      </header>
      <div className="login-layout">
        <aside className="login-story">
          <p className="eyebrow">FOR YOUR OWN SHOP</p>
          <h2>
            Message the customers
            <br />a message would
            <br />
            <span>actually bring back.</span>
          </h2>
          <ShopFallback />
          <div className="login-promises">
            <p>
              <Check size={16} /> Upload your sales and see who is worth a message.
            </p>
            <p>
              <Check size={16} /> Keep some back, so you can see what really worked.
            </p>
          </div>
        </aside>
        <main id="main" className="login-card">
          <p className="eyebrow">Create your shop</p>
          <h1>Start with your sales.</h1>
          <p>One account per shop. You can upload your sales export as soon as you’re in.</p>
          {client || devToken ? (
            <form onSubmit={signup}>
              <label>
                Shop name
                <input
                  id="signup-shop"
                  required
                  minLength={2}
                  maxLength={40}
                  value={shop}
                  onChange={(e) => setShop(e.target.value)}
                  placeholder="Ah Seng Provision"
                />
              </label>
              {client && (
                <>
                  <label>
                    Email
                    <input
                      id="signup-email"
                      type="email"
                      autoComplete="username"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </label>
                  <div className="password-field">
                    <label htmlFor="signup-password">Password (at least 8 characters)</label>
                    <span className="password-input">
                      <input
                        id="signup-password"
                        type={show ? "text" : "password"}
                        autoComplete="new-password"
                        required
                        minLength={8}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                      />
                      <button
                        type="button"
                        className="icon-button"
                        aria-label={show ? "Hide password" : "Show password"}
                        aria-pressed={show}
                        onClick={() => setShow(!show)}
                      >
                        {show ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </span>
                  </div>
                </>
              )}
              {error && (
                <p role="alert" className="error">
                  {error}
                </p>
              )}
              {info && (
                <p role="status" className="notice">
                  {info}
                </p>
              )}
              <button className="button primary" disabled={busy}>
                {busy ? "Creating your shop…" : "Create my shop"}
              </button>
            </form>
          ) : (
            <p className="notice">Sign-up isn’t connected on this copy of the site.</p>
          )}
          <Link href="/login" className="text-link">
            Already have a shop? Sign in <ArrowUpRight size={16} />
          </Link>
          <p className="fine">Your customers’ phone numbers stay on our server and are never shown in full.</p>
        </main>
      </div>
    </div>
  );
}
