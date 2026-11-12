import { NextResponse } from "next/server";

// Server-side calls to the Nudgely backend for signed-in team actions. The visitor's Supabase
// access token is passed through; the backend checks it and the team role itself.
export async function forwardToBackend(
  request: Request,
  path: string,
  method: "GET" | "POST",
) {
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin)
    return NextResponse.json({ error: "Forbidden." }, { status: 403 });
  const auth = request.headers.get("authorization");
  if (!auth?.startsWith("Bearer "))
    return NextResponse.json({ error: "Sign in first." }, { status: 401 });
  const body = method === "POST" ? await request.text() : undefined;
  if (body && body.length > 4096)
    return NextResponse.json({ error: "Message too long." }, { status: 413 });
  try {
    const base =
      process.env.NUDGELY_API_URL || "https://nudgely-api.onrender.com";
    const response = await fetch(new URL(path, base), {
      method,
      headers: { "Content-Type": "application/json", Authorization: auth },
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(55000),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok)
      return NextResponse.json(
        {
          error:
            typeof payload.detail === "string"
              ? payload.detail
              : "The backend refused the request.",
        },
        { status: response.status },
      );
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      {
        error:
          "The backend didn't answer in time. Check WhatsApp before trying again: it may already have sent.",
      },
      { status: 504 },
    );
  }
}
