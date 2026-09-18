// Supabase Edge Function: receive the website contact form, check it's a human, save it.
//
// Optional. Without it the form posts straight into the table (the table's own rules still apply).
// Use it when you want a Cloudflare Turnstile check, which can only be verified server-side.
//
// Deploy:  supabase functions deploy submit-contact --no-verify-jwt
// Secrets: TURNSTILE_SECRET_KEY   Cloudflare Turnstile secret (optional: without it the check is skipped)
//          ALLOWED_ORIGINS        comma-separated, e.g. "https://squarepegpizzeria.com,https://www.squarepegpizzeria.com"
// SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are provided by Supabase automatically.
//
// Then put the function URL in data/content.py as contact_endpoint, and the Turnstile
// site key as turnstile_site_key, and rebuild. See SUPABASE_SETUP.md.
import { createClient } from "npm:@supabase/supabase-js@2";

const ORIGINS = (Deno.env.get("ALLOWED_ORIGINS") ?? "").split(",").map((s) => s.trim()).filter(Boolean);

function cors(origin: string | null) {
  const allow = !ORIGINS.length || (origin && ORIGINS.includes(origin)) ? (origin ?? "*") : ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}

const str = (v: unknown, max: number) => (typeof v === "string" ? v.trim().slice(0, max) : "");

async function humanCheck(token: string, ip: string): Promise<boolean> {
  const secret = Deno.env.get("TURNSTILE_SECRET_KEY");
  if (!secret) return true;                      // check not set up: let it through
  const body = new FormData();
  body.append("secret", secret);
  body.append("response", token);
  if (ip) body.append("remoteip", ip);
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body });
  const out = await r.json().catch(() => ({ success: false }));
  return out.success === true;
}

Deno.serve(async (req) => {
  const origin = req.headers.get("origin");
  const headers = { ...cors(origin), "Content-Type": "application/json" };
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors(origin) });
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "POST only" }), { status: 405, headers });
  if (ORIGINS.length && origin && !ORIGINS.includes(origin)) {
    return new Response(JSON.stringify({ error: "forbidden" }), { status: 403, headers });
  }

  const b = await req.json().catch(() => null);
  if (!b) return new Response(JSON.stringify({ error: "bad request" }), { status: 400, headers });

  const email = str(b.email, 320);
  const message = str(b.message, 3000);
  if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(email) || message.length < 5) {
    return new Response(JSON.stringify({ error: "please check your email address and message" }), { status: 400, headers });
  }
  // Same traps as the page: a hidden field only bots fill, and an impossibly fast submit.
  if (str(b.company_website, 50)) return new Response(JSON.stringify({ ok: true }), { headers });
  if (typeof b.elapsed_ms === "number" && b.elapsed_ms >= 0 && b.elapsed_ms < 1500) {
    return new Response(JSON.stringify({ ok: true }), { headers });
  }

  const ip = (req.headers.get("x-forwarded-for") ?? "").split(",")[0].trim();
  if (!(await humanCheck(str(b.turnstile_token, 3000), ip))) {
    return new Response(JSON.stringify({ error: "the human check didn't pass, please try again" }), { status: 400, headers });
  }

  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  // Rate limit: 3 an hour per address, same as the table's own rule.
  const since = new Date(Date.now() - 60 * 60 * 1000).toISOString();
  const { count } = await db.from("contact_messages").select("id", { count: "exact", head: true })
    .ilike("email", email).gte("created_at", since);
  if ((count ?? 0) >= 3) {
    return new Response(JSON.stringify({ error: "that's a lot of messages in one hour, please call us instead" }), { status: 429, headers });
  }

  const { error } = await db.from("contact_messages").insert({
    first_name: str(b.first_name, 80) || null,
    last_name: str(b.last_name, 80) || null,
    email,
    phone: str(b.phone, 40) || null,
    topic: str(b.topic, 80) || null,
    location: str(b.location, 80) || null,
    message,
    page: str(b.page, 200) || null,
  });
  if (error) return new Response(JSON.stringify({ error: "could not save the message" }), { status: 500, headers });
  return new Response(JSON.stringify({ ok: true }), { headers });
});
