// Supabase Edge Function: the weekly Pizza Lab digest.
//
// Emails every submission waiting for review, once a week, so nobody has to
// remember to go and look in the dashboard.
//
// Why this runs inside Supabase rather than as a GitHub Action, which is where
// the site's other scheduled jobs live: pending submissions are deliberately
// unreadable with the public anon key — that is the whole point of the
// moderation queue — so reading them needs the service-role key. That key must
// never go into a GitHub workflow. Here it is injected by Supabase and never
// leaves the project.
//
// Deploy:   supabase functions deploy lab-digest --no-verify-jwt
//           (or paste it into the dashboard — it is a single file)
// Secrets:  RESEND_API_KEY   already set for the contact form
//           NOTIFY_FROM      already set, e.g. "Square Peg Website <website@squarepegpizzeria.com>"
//           LAB_DIGEST_TO    optional; comma-separated. Defaults to the three
//                            addresses below, so it works without setting it.
//           LAB_DIGEST_KEY   a long random string, sent as ?key= by the schedule,
//                            so nobody can trigger the mail by hitting the URL
//
// Schedule: the pg_cron block in supabase/LAB_DIGEST_SCHEDULE.sql.
// Project:  the website's own, ytkwogufrjffcgfpinrf, beside contact_messages.
import { createClient } from "npm:@supabase/supabase-js@2";

// Set LAB_DIGEST_TO to change this without redeploying — it takes a
// comma-separated list and wins over the default.
const DEFAULT_TO = [
  "brian@brianhardy.com",
  "plainville@squarepegpizzeria.com",
  "ehartford@squarepegpizzeria.com",
].join(",");

const TO = (Deno.env.get("LAB_DIGEST_TO") || DEFAULT_TO)
  .split(",").map((s) => s.trim()).filter(Boolean);

function esc(s: unknown): string {
  return String(s ?? "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c] as string));
}

type Entry = {
  id: string; created_at: string; name: string; by_name: string | null;
  sauce: string; cheese: string; toppings: string[]; finish: string | null;
};

// One entry, laid out as a build sheet. Sauce, cheese, toppings and finish get
// their own labelled rows rather than one run-on sentence, because the person
// reading this is deciding whether the kitchen can make it and then, if it
// wins, handing it to the line.
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
  const toppings = (e.toppings ?? []).filter(Boolean).join(", ");
  // "Nothing — leave it alone" is a real choice on the form, but printing it as
  // a finish reads like a mistake. An empty row just doesn't render.
  const finish = e.finish && !/^nothing/i.test(e.finish) ? e.finish : "";
  return `
    <tr><td style="padding:20px 0;border-bottom:1px solid #e2ddd8">
      <div style="font:700 12px/1 Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#b5121b">
        ${esc(when)}
      </div>
      <div style="font:800 22px/1.2 Georgia,serif;color:#1a1614;margin:7px 0 2px">${esc(e.name)}</div>
      <div style="font:400 14px/1.4 Arial,sans-serif;color:#655d57;margin:0 0 12px">
        built by ${e.by_name ? esc(e.by_name) : "someone who didn't leave a name"}
      </div>
      <table style="border-collapse:collapse">
        ${row("Sauce", e.sauce)}
        ${row("Cheese", e.cheese)}
        ${row("Toppings", toppings)}
        ${row("Finish", finish)}
      </table>
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
  const want = (Deno.env.get("LAB_DIGEST_KEY") ?? "").trim();
  const got = (new URL(req.url).searchParams.get("key") ?? "").trim();
  if (want && got !== want) {
    return new Response("forbidden", { status: 403 });
  }

  const db = createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
    { auth: { persistSession: false } },
  );

  // Everything still waiting, not just the last seven days: an entry nobody got
  // to last week should appear again rather than quietly fall off the list.
  const { data, error } = await db.from("lab_entries")
    .select("id,created_at,name,by_name,sauce,cheese,toppings,finish")
    .eq("status", "pending")
    .order("created_at", { ascending: true });

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500, headers: { "Content-Type": "application/json" },
    });
  }

  const entries = (data ?? []) as Entry[];

  // Nothing waiting means no email. A weekly "nothing to report" trains people
  // to ignore the thing, and this one needs to be read.
  if (!entries.length) {
    return new Response(JSON.stringify({ ok: true, sent: false, pending: 0 }), {
      headers: { "Content-Type": "application/json" },
    });
  }

  const n = entries.length;
  const subject = `Pizza Lab: ${n} ${n === 1 ? "pizza" : "pizzas"} waiting for review`;
  const html = `
  <div style="background:#f4f2f0;padding:28px 0;font-family:Arial,sans-serif">
    <div style="max-width:620px;margin:0 auto;background:#fff;padding:30px 28px">
      <div style="font:700 12px/1 Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#b5121b">
        The Square Peg Pizza Lab
      </div>
      <h1 style="font:800 28px/1.1 Georgia,serif;color:#1a1614;margin:10px 0 6px">
        ${n} ${n === 1 ? "pizza is" : "pizzas are"} waiting for you
      </h1>
      <p style="font:400 15px/1.55 Arial,sans-serif;color:#655d57;margin:0 0 6px">
        Customers built these on the website. Nobody but us ever sees them.
        Everything here is made from ingredients already on the menu, so any
        one of them is a pizza the line can put up.
      </p>
      <table style="width:100%;border-collapse:collapse">${entries.map(card).join("")}</table>
      <p style="font:400 14px/1.55 Arial,sans-serif;color:#655d57;margin:22px 0 0">
        These stay on this list until somebody clears them, so next week's email
        will show them again. To read them any time, open <b>lab_inbox</b> in the
        Supabase Table Editor. When you pick one, set its <b>status</b> to
        <b>approved</b> in <b>lab_entries</b> and set the ones you're passing on
        to <b>rejected</b>. That's only so the list stays short — neither word is
        shown to anyone.
      </p>
    </div>
  </div>`;

  await sendEmail(subject, html);
  return new Response(JSON.stringify({ ok: true, sent: true, pending: n }), {
    headers: { "Content-Type": "application/json" },
  });
});
