import { NextResponse } from "next/server";
export const maxDuration = 60;

// Forwards a shop's sales file to the backend's scorer (Model 2). Public, like /api/chat: the
// demo page uses it without a login. The backend rate-limits per visitor and stores nothing.
const MAX_BODY = 2_900_000; // a 2 MB file grows by a third as base64

export async function POST(request: Request) {
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin)
    return NextResponse.json({ error: "Please upload on this site." }, { status: 403 });
  const body = await request.text();
  if (body.length > MAX_BODY)
    return NextResponse.json(
      { error: "That file is over 2 MB. Export a shorter period (3 to 6 months is plenty)." },
      { status: 413 },
    );
  try {
    const base = process.env.NUDGELY_API_URL || "https://nudgely-api.onrender.com";
    const response = await fetch(new URL("/api/shop/score", base), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Forwarded-For": request.headers.get("x-forwarded-for") ?? "",
      },
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
              : "The scorer couldn't read that file. Check it has phone, date and amount columns.",
        },
        { status: response.status },
      );
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      {
        error:
          "The scorer took too long to answer. The free server may be waking up: wait 30 seconds and try again.",
      },
      { status: 504 },
    );
  }
}
