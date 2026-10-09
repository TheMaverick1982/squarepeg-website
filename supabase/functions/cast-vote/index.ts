// Supabase Edge Function: record one vote from a /play/ page.
//
// Serves both The Great Pizza Debate and the Confession checklist — they are the
// same mechanic, so they share this one endpoint.
//
// Deploy:  supabase functions deploy cast-vote --no-verify-jwt
// Secrets: ALLOWED_ORIGINS   comma-separated, e.g. "https://squarepegpizzeria.com,https://www.squarepegpizzeria.com"
// SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are provided by Supabase automatically.
//
// Then put the function URL in data/content.py as vote_endpoint and rebuild.
//
// What this deliberately does NOT do:
//
//  * It does not store who voted. No IP, no cookie, no fingerprint reaches the
//    database — the IP is used for rate limiting in memory and then discarded.
//  * It does not use Turnstile. The contact form does, because a spam lead
//    wastes a human's time. A stuffed pineapple poll wastes nobody's time, and
//    making people solve a challenge to answer a joke question would kill the
//    page. The rate limit below is the whole defence, and that is proportionate.
//  * It does not accept arbitrary poll or option names. Both are checked against
//    a fixed list, so a script cannot create a poll called whatever it likes and
//    have the site render it.
import { createClient } from "npm:@supabase/supabase-js@2";

const ORIGINS = (Deno.env.get("ALLOWED_ORIGINS") ?? "").split(",").map((s) => s.trim()).filter(Boolean);

function cors(origin: string | null) {
  const allow = !ORIGINS.length || (origin && ORIGINS.includes(origin)) ? (origin ?? "*") : ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Vary": "Origin",
  };
}

// Which polls exist, and what may be voted on in each. Generated from
// data/play.py by `python3 scripts/sync_polls.py --allowlist`, which rewrites
// the block between the markers below — so this cannot drift from the site, and
// the whole function stays a single file you can paste into the dashboard.
// POLLS-START
const POLLS: Record<string, string[]> = {
  "confession": [
    "car",
    "ketchup",
    "frozen",
    "toppings",
    "breakfast",
    "crust",
    "box",
    "last-slice",
    "ordered-twice",
    "microwave",
    "pineapple",
    "lied",
    "hid",
    "floor",
    "whole-thing"
  ],
  "debate:cold-leftover-pizza": [
    "cold",
    "hot"
  ],
  "debate:fold-or-flat": [
    "fold",
    "flat"
  ],
  "debate:fork-and-knife": [
    "never",
    "sometimes"
  ],
  "debate:is-a-calzone-a-pizza": [
    "yes",
    "no"
  ],
  "debate:pineapple-on-pizza": [
    "yes",
    "no"
  ],
  "debate:ranch-with-pizza": [
    "yes",
    "no"
  ]
};
// POLLS-END

const validVote = (poll: string, option: string) =>
  Object.prototype.hasOwnProperty.call(POLLS, poll) &&
  (POLLS as Record<string, string[]>)[poll].includes(option);

// Rate limit: a sliding window per IP, held in memory. An Edge Function instance
// is short-lived and there may be several at once, so this is a speed bump
// rather than a wall — enough to stop a loop in a browser console or a trivial
// script, which is the realistic threat to a pizza poll.
const WINDOW_MS = 60_000;
const MAX_PER_WINDOW = 25;
const hits = new Map<string, number[]>();

function rateLimited(ip: string): boolean {
  if (!ip) return false;
  const now = Date.now();
  const recent = (hits.get(ip) ?? []).filter((t) => now - t < WINDOW_MS);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 5000) hits.clear();            // crude guard against unbounded growth
  return recent.length > MAX_PER_WINDOW;
}

// Coarse region for the Connecticut-vs-Florida split, from the edge's own
// geo header. Never asked of the visitor, never stored against them.
function region(req: Request): string {
  const r = (req.headers.get("x-vercel-ip-country-region") ??
             req.headers.get("cf-region-code") ?? "").toUpperCase();
  return r === "CT" || r === "FL" ? r : "other";
}

function db() {
  return createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
    { auth: { persistSession: false } },
  );
}

Deno.serve(async (req) => {
  const origin = req.headers.get("origin");
  const headers = { ...cors(origin), "Content-Type": "application/json" };
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors(origin) });

  // GET ?poll=<name> — current totals, so a page can show live numbers rather
  // than whatever the nightly build baked in. Cached briefly: these are vote
  // counts on a pizza poll, and a minute of staleness is worth not hitting the
  // database once per page view.
  if (req.method === "GET") {
    const poll = new URL(req.url).searchParams.get("poll") ?? "";
    if (!Object.prototype.hasOwnProperty.call(POLLS, poll)) {
      return new Response(JSON.stringify({ error: "unknown poll" }), { status: 400, headers });
    }
    const { data, error } = await db().from("poll_totals")
      .select("option,region,votes").eq("poll", poll);
    if (error) {
      return new Response(JSON.stringify({ error: "could not read totals" }), { status: 500, headers });
    }
    return new Response(JSON.stringify({ ok: true, totals: data ?? [] }), {
      headers: { ...headers, "Cache-Control": "public, max-age=30, s-maxage=60" },
    });
  }

  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "GET or POST only" }), { status: 405, headers });
  }
  if (ORIGINS.length && origin && !ORIGINS.includes(origin)) {
    return new Response(JSON.stringify({ error: "forbidden" }), { status: 403, headers });
  }

  const ip = (req.headers.get("x-forwarded-for") ?? "").split(",")[0].trim();
  if (rateLimited(ip)) {
    return new Response(JSON.stringify({ error: "slow down" }), { status: 429, headers });
  }

  const b = await req.json().catch(() => null);
  if (!b) return new Response(JSON.stringify({ error: "bad request" }), { status: 400, headers });

  const poll = typeof b.poll === "string" ? b.poll.slice(0, 80) : "";
  // The confession page sends several at once; the debate sends one.
  const raw = Array.isArray(b.options) ? b.options : [b.option];
  const options = raw
    .filter((o: unknown): o is string => typeof o === "string")
    .map((o: string) => o.slice(0, 80))
    .slice(0, 40);

  const good = options.filter((o: string) => validVote(poll, o));
  if (!poll || !good.length) {
    return new Response(JSON.stringify({ error: "unknown poll or option" }), { status: 400, headers });
  }

  const sb = db();
  const reg = region(req);
  for (const option of good) {
    const { error } = await sb.rpc("cast_vote", { p_poll: poll, p_option: option, p_region: reg });
    if (error) {
      return new Response(JSON.stringify({ error: "could not record vote" }), { status: 500, headers });
    }
  }

  // Hand back the fresh totals so the page can show results without a second
  // round trip, and without waiting for the nightly rebuild.
  const { data } = await sb.from("poll_totals").select("option,region,votes").eq("poll", poll);
  return new Response(JSON.stringify({ ok: true, totals: data ?? [] }), { headers });
});
