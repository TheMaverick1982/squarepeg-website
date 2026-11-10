// Supabase Edge Function: the weekly Square Peg Labs digest.
//
// Emails the week's builds, split by bench, so nobody has to remember to go
// and look. It used to send everything still marked pending, with a footer
// telling people to go and change a status in the Supabase Table Editor.
// Nobody was ever going to do that, so the queue only grew and the email got
// longer every week until it stopped being read. The spreadsheet is the
// working list now (see tools/lab_sheet.gs); this is the nudge, and it covers
// the last seven days whatever their status.
//
// Why this runs inside Supabase rather than as a GitHub Action, which is where
// the site's other scheduled jobs live: entries are deliberately unreadable
// with the public anon key -- that is the whole point -- so reading them needs
// the service-role key. That key must never go into a GitHub workflow. Here it
// is injected by Supabase and never leaves the project.
//
// Deploy:   supabase functions deploy lab-digest --no-verify-jwt
// Secrets:  RESEND_API_KEY   already set for the contact form
//           NOTIFY_FROM      already set, e.g. "Square Peg Website <website@squarepegpizzeria.com>"
//           LAB_DIGEST_TO    optional; comma-separated. Defaults to the list below.
//           LAB_DIGEST_KEY   a long random string, sent as ?key= by the schedule,
//                            so nobody can trigger the mail by hitting the URL
//           LAB_SHEET_URL    optional; the Google Sheet, linked at the bottom
//
// Schedule: the pg_cron block in supabase/LAB_DIGEST_SCHEDULE.sql.
import { createClient } from "npm:@supabase/supabase-js@2";

const DEFAULT_TO = [
  "brian@brianhardy.com",
  "plainville@squarepegpizzeria.com",
  "ehartford@squarepegpizzeria.com",
  "catering@squarepegpizzeria.com",
  "maffefinancial@hotmail.com",
].join(",");

const TO = (Deno.env.get("LAB_DIGEST_TO") || DEFAULT_TO)
  .split(",").map((s) => s.trim()).filter(Boolean);

// Reading order, and the heading each bench gets. A kind that is not in here
// still goes out -- under its own slug -- rather than being dropped silently.
const BENCH_NAMES: Record<string, string> = {
  "pizza-lab": "Pizzas",
  "pasta-lab": "Pastas",
  "sandwich-lab": "Sandwiches",
  "salad-lab": "Salads",
  "bar-lab": "Drinks",
};
const ORDER = Object.keys(BENCH_NAMES);

function esc(s: unknown): string {
  return String(s ?? "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c] as string));
}

type Pair = { label: string; value: string | string[] };
type Entry = {
  id: string; created_at: string; kind: string | null;
  name: string; by_name: string | null; build: Pair[] | null;
};

// One labelled row. Sauce, protein, add-ins and finish get their own line
// rather than one run-on sentence, because the person reading this is deciding
// whether the kitchen can make it and then, if it wins, handing it to the line.
function row(label: string, value: string): string {
  if (!value) return "";
  return `
    <tr>
      <td style="font:700 11px/1.5 Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#a09890;padding:2px 14px 2px 0;vertical-align:top;white-space:nowrap">${esc(label)}</td>
      <td style="font:400 15px/1.5 Arial,sans-serif;color:#1a1614;padding:2px 0">${esc(value)}</td>
    </tr>`;
}

function card(e: Entry): string {
  const when = new Date(e.created_at).toLocaleDateString("en-US",
    { weekday: "short", month: "short", day: "numeric", timeZone: "America/New_York" });
  const rows = (e.build ?? []).map((p) => {
    const v = Array.isArray(p.value) ? p.value.filter(Boolean).join(", ") : (p.value ?? "");
    // "Nothing — leave it alone" and "No rim" are real answers on the form, but
    // printed as a value they read like a mistake. An empty row doesn't render.
    if (!v || /^(nothing|no |straight up)/i.test(v)) return "";
    return row(p.label, v);
  }).join("");
  return `
    <tr><td style="padding:20px 0;border-bottom:1px solid #e2ddd8">
      <div style="font:700 12px/1 Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#b5121b">
        ${esc(when)}
      </div>
      <div style="font:800 22px/1.2 Georgia,serif;color:#1a1614;margin:7px 0 2px">${esc(e.name)}</div>
      <div style="font:400 14px/1.4 Arial,sans-serif;color:#655d57;margin:0 0 12px">
        built by ${e.by_name ? esc(e.by_name) : "someone who didn't leave a name"}
      </div>
      <table style="border-collapse:collapse">${rows}</table>
    </td></tr>`;
}

async function sendEmail(subject: string, html: string) {
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${Deno.env.get("RESEND_API_KEY")}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ from: Deno.env.get("NOTIFY_FROM"), to: TO, subject, html }),
  });
  if (!r.ok) throw new Error(`Email failed: ${r.status} ${await r.text()}`);
}

Deno.serve(async (req) => {
  // The schedule calls this with ?key=<LAB_DIGEST_KEY>. Without it, anyone who
  // learned the URL could send the kitchen an email whenever they liked.
  //
  // Both sides are trimmed. A secret pasted into a dashboard field very often
  // carries a trailing newline, and an exact comparison then fails in a way
  // that looks like the wrong key rather than invisible whitespace.
  const url = new URL(req.url);
  const want = (Deno.env.get("LAB_DIGEST_KEY") ?? "").trim();
  const got = (url.searchParams.get("key") ?? "").trim();
  if (want && got !== want) return new Response("forbidden", { status: 403 });

  // ?days=30 to catch up by hand after a missed week.
  const days = Math.min(90, Math.max(1, parseInt(url.searchParams.get("days") ?? "7", 10) || 7));
  const since = new Date(Date.now() - days * 86400_000).toISOString();

  const db = createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
    { auth: { persistSession: false } },
  );

  const { data, error } = await db.from("lab_entries")
    .select("id,created_at,kind,name,by_name,build")
    .gte("created_at", since)
    .order("created_at", { ascending: true });

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500, headers: { "Content-Type": "application/json" },
    });
  }

  const entries = (data ?? []) as Entry[];

  // A quiet week means no email. A weekly "nothing to report" trains people to
  // ignore the thing, and this one needs to be read.
  if (!entries.length) {
    return new Response(JSON.stringify({ ok: true, sent: false, entries: 0 }), {
      headers: { "Content-Type": "application/json" },
    });
  }

  const by: Record<string, Entry[]> = {};
  for (const e of entries) (by[e.kind || "pizza-lab"] ??= []).push(e);
  const kinds = [...ORDER.filter((k) => by[k]?.length),
                 ...Object.keys(by).filter((k) => !ORDER.includes(k))];

  const n = entries.length;
  const tally = kinds.map((k) => `${by[k].length} ${(BENCH_NAMES[k] ?? k).toLowerCase()}`).join(", ");
  const subject = `Square Peg Labs: ${n} new ${n === 1 ? "build" : "builds"} this week`;
  const sheet = (Deno.env.get("LAB_SHEET_URL") ?? "").trim();

  const sections = kinds.map((k) => `
      <div style="font:700 12px/1 Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#1a1614;border-top:3px solid #1a1614;padding:22px 0 2px;margin-top:10px">
        ${esc(BENCH_NAMES[k] ?? k)} &middot; ${by[k].length}
      </div>
      <table style="width:100%;border-collapse:collapse">${by[k].map(card).join("")}</table>`).join("");

  const html = `
  <div style="background:#f4f2f0;padding:28px 0;font-family:Arial,sans-serif">
    <div style="max-width:620px;margin:0 auto;background:#fff;padding:30px 28px">
      <div style="font:700 12px/1 Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#b5121b">
        Square Peg Labs
      </div>
      <h1 style="font:800 28px/1.1 Georgia,serif;color:#1a1614;margin:10px 0 6px">
        ${n} new ${n === 1 ? "build" : "builds"} this week
      </h1>
      <p style="font:400 15px/1.55 Arial,sans-serif;color:#655d57;margin:0 0 6px">
        ${esc(tally)}. Customers built these on the website and nobody but us
        ever sees them. Everything here is made from what is already on the
        menu and behind the bar, so any one of them is something the line can
        actually put up.
      </p>
      ${sections}
      <p style="font:400 14px/1.55 Arial,sans-serif;color:#655d57;margin:22px 0 0">
        This is the last seven days only. Every build ever sent is in
        ${sheet ? `<a href="${esc(sheet)}" style="color:#b5121b">the Labs spreadsheet</a>` : "the Labs spreadsheet"},
        one tab per bench &mdash; mark the ones you pick there.
      </p>
    </div>
  </div>`;

  await sendEmail(subject, html);
  return new Response(JSON.stringify({ ok: true, sent: true, entries: n }), {
    headers: { "Content-Type": "application/json" },
  });
});
