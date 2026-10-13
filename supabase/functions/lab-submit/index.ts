// Supabase Edge Function: accept one Pizza Lab submission into the moderation queue.
//
// Deploy:  supabase functions deploy lab-submit --no-verify-jwt
// Secrets: ALLOWED_ORIGINS      comma-separated site origins
//          TURNSTILE_SECRET_KEY optional; same fail-open behaviour as submit-contact
// SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are provided by Supabase.
//
// Then set lab_endpoint in data/content.py, flip LAB_LIVE to True, and rebuild.
//
// This endpoint writes a row and nothing else. Nothing a member of the public
// submits is ever shown on squarepegpizzeria.com: entries go to the kitchen, we
// pick one, it runs as an LTO. So there is no path through this function that
// publishes anything, and no API that reads these rows back out.
//
// Only two fields are free text — the pizza's name and the submitter's name —
// and both are read by a person before they go anywhere. Everything else is
// checked against the same fixed list the page offers, generated from
// data/play.py by `python3 scripts/sync_polls.py --allowlist` into the marked
// block below, so a crafted request cannot smuggle free text into what looks
// like a structured field, and the lists cannot drift from the menu.
import { createClient } from "npm:@supabase/supabase-js@2";
// Generated from data/play.py by `python3 scripts/sync_polls.py --allowlist`.
// INGREDIENTS-START
const INGREDIENTS = {
  "sauce": [
    "House-made red sauce",
    "Parm Cream sauce"
  ],
  "cheese": [
    "Shredded mozzarella",
    "Fresh mozzarella",
    "Parmesan",
    "Ricotta",
    "Goat cheese",
    "Fontina",
    "Bleu cheese crumbles",
    "Vegan cheese"
  ],
  "toppings": [
    "Meatballs",
    "Sausage",
    "Bacon",
    "Pepperoni",
    "Prosciutto",
    "Chicken cacciatore",
    "Spicy capicola",
    "Olives",
    "Roasted red peppers",
    "Mushrooms",
    "Red onion",
    "Hot cherry peppers",
    "Garlic",
    "Hot pepper relish",
    "Pineapple",
    "Broccolini"
  ],
  "finish": [
    "Hot honey",
    "Chili oil",
    "Maple",
    "Parm Cream drizzle",
    "Ranch drizzle",
    "Fresh basil",
    "Baby arugula",
    "Olive oil",
    "Nothing \u2014 leave it alone"
  ],
  "max": 4
};
// INGREDIENTS-END

const ORIGINS = (Deno.env.get("ALLOWED_ORIGINS") ?? "").split(",").map((s) => s.trim()).filter(Boolean);
const LIST = INGREDIENTS as unknown as { sauce: string[]; cheese: string[]; toppings: string[]; finish: string[]; max: number };

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

// Same fail-open posture as the contact form: we only turn someone away when
// Cloudflare actively says the token is bad. Unset the secret to disable.
async function humanCheck(token: string, ip: string): Promise<boolean> {
  const secret = Deno.env.get("TURNSTILE_SECRET_KEY");
  if (!secret || !token) return true;
  try {
    const body = new FormData();
    body.append("secret", secret);
    body.append("response", token);
    if (ip) body.append("remoteip", ip);
    const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST", body, signal: AbortSignal.timeout(4000),
    });
    if (!r.ok) return true;
    return (await r.json())?.success === true;
  } catch {
    return true;
  }
}

Deno.serve(async (req) => {
  const origin = req.headers.get("origin");
  const headers = { ...cors(origin), "Content-Type": "application/json" };
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors(origin) });
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "POST only" }), { status: 405, headers });
  }
  if (ORIGINS.length && origin && !ORIGINS.includes(origin)) {
    return new Response(JSON.stringify({ error: "forbidden" }), { status: 403, headers });
  }

  const b = await req.json().catch(() => null);
  if (!b) return new Response(JSON.stringify({ error: "bad request" }), { status: 400, headers });

  const ip = (req.headers.get("x-forwarded-for") ?? "").split(",")[0].trim();
  if (!(await humanCheck(str(b.turnstile_token, 2048), ip))) {
    return new Response(JSON.stringify({ error: "could not verify" }), { status: 400, headers });
  }

  const name = str(b.name, 40);
  const by = str(b.by, 40);
  const sauce = str(b.sauce, 60);
  const cheese = str(b.cheese, 60);
  const finish = str(b.finish, 60);
  const toppings = (Array.isArray(b.toppings) ? b.toppings : [])
    .filter((t: unknown): t is string => typeof t === "string")
    .map((t: string) => t.trim().slice(0, 60));

  // Everything except the two free-text fields must come from our own lists.
  const ok =
    name.length > 0 &&
    LIST.sauce.includes(sauce) &&
    LIST.cheese.includes(cheese) &&
    (!finish || LIST.finish.includes(finish)) &&
    toppings.length >= 1 && toppings.length <= LIST.max &&
    toppings.every((t: string) => LIST.toppings.includes(t)) &&
    new Set(toppings).size === toppings.length;

  if (!ok) {
    return new Response(JSON.stringify({ error: "that isn't a pizza we can make" }), { status: 400, headers });
  }

  const db = createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
    { auth: { persistSession: false } },
  );

  // status defaults to 'pending' in the schema and is deliberately not settable
  // from here. status is only ever changed by hand, and only to keep the inbox
  // short — it does not control whether anything is shown, because nothing is.
  const { error } = await db.from("lab_entries").insert({
    name, by_name: by || null, sauce, cheese, toppings, finish: finish || null,
  });

  if (error) {
    return new Response(JSON.stringify({ error: "could not save" }), { status: 500, headers });
  }
  return new Response(JSON.stringify({ ok: true }), { headers });
});
