// Supabase Edge Function: accept one Pizza Lab submission into the moderation queue.
//
// Deploy:  supabase functions deploy lab-submit --no-verify-jwt
// Secrets: ALLOWED_ORIGINS      comma-separated site origins
//          TURNSTILE_SECRET_KEY optional; same fail-open behaviour as submit-contact
// SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are provided by Supabase.
//
// Then set lab_endpoint in data/content.py, flip LAB_LIVE to True, and rebuild.
//
// This endpoint writes a row with status 'pending' and nothing else. There is no
// path through this function that publishes anything. Approval happens by hand
// in the Supabase Table Editor, which is the point of the whole design: a name
// typed by a stranger does not appear on the restaurant's domain until one of us
// has read it.
//
// The ingredient values are checked against the same fixed list the page offers,
// written here by the build (scripts/sync_polls.py writes polls.json; the build
// writes ingredients.json), so a crafted request cannot smuggle free text into
// what looks like a structured field.
import { createClient } from "npm:@supabase/supabase-js@2";
// Generated from data/play.py by `python3 scripts/sync_polls.py --allowlist`.
// INGREDIENTS-START
const INGREDIENTS = {
  "sauce": [
    "Tomato",
    "White (garlic and oil)",
    "Vodka sauce",
    "Pesto",
    "No sauce"
  ],
  "cheese": [
    "Fresh mozzarella",
    "Shredded mozzarella",
    "Ricotta",
    "Goat cheese",
    "Parmesan",
    "Vegan cheese"
  ],
  "toppings": [
    "Pepperoni",
    "House pork meatballs",
    "Spicy capicola",
    "Prosciutto",
    "Italian sausage",
    "Grilled chicken",
    "Mushrooms",
    "Cherry peppers",
    "Roasted red peppers",
    "Caramelised onions",
    "Black olives",
    "Fresh basil",
    "Baby arugula",
    "Roasted tomatoes",
    "Garlic",
    "Jalape\u00f1os",
    "Eggplant",
    "Artichoke hearts"
  ],
  "finish": [
    "Hot honey",
    "Calabrian chili oil",
    "Balsamic glaze",
    "Maple",
    "Olive oil and sea salt",
    "Fresh basil",
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
  // from here — there is no request body that results in a published entry.
  const { error } = await db.from("lab_entries").insert({
    name, by_name: by || null, sauce, cheese, toppings, finish: finish || null,
  });

  if (error) {
    return new Response(JSON.stringify({ error: "could not save" }), { status: 500, headers });
  }
  return new Response(JSON.stringify({ ok: true }), { headers });
});
