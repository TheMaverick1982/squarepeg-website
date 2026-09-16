// Supabase Edge Function: email each new contact message to the right person.
// Trigger: Database Webhook on INSERT into public.contact_messages (see DEPLOY_VERCEL.md).
// Secrets needed:  RESEND_API_KEY   (or swap sendEmail() for your email provider)
//                  NOTIFY_FROM      e.g. "Square Peg Website <website@squarepegpizzeria.com>"
//                  WEBHOOK_SECRET   any long random string, also set as a header on the webhook
import { createClient } from "npm:@supabase/supabase-js@2";

// ---- Routing: edit these addresses ------------------------------------------------
const DEFAULT_TO = "info@squarepegpizzeria.com";
const BY_TOPIC: Record<string, string> = {
  "Catering": "catering@squarepegpizzeria.com",
  "Large party reservation": "catering@squarepegpizzeria.com",
  "Food truck": "catering@squarepegpizzeria.com",
  "Fundraiser": "info@squarepegpizzeria.com",
  "Gift cards": "info@squarepegpizzeria.com",
  "Rewards / app help": "info@squarepegpizzeria.com",
  "Jobs": "info@squarepegpizzeria.com",
  "Media or partnership": "info@squarepegpizzeria.com",
};
// Location-specific topics (feedback, general questions) go to that store's manager.
const LOCATION_TOPICS = new Set(["General question", "Feedback about a visit"]);
const BY_LOCATION: Record<string, string> = {
  // "Glastonbury": "glastonbury@squarepegpizzeria.com",
  // "East Hartford": "easthartford@squarepegpizzeria.com",
};
// -------------------------------------------------------------------------------------

function routeFor(topic?: string, location?: string): string {
  if (topic && LOCATION_TOPICS.has(topic) && location && BY_LOCATION[location]) return BY_LOCATION[location];
  if (topic && BY_TOPIC[topic]) return BY_TOPIC[topic];
  if (location && BY_LOCATION[location]) return BY_LOCATION[location];
  return DEFAULT_TO;
}

const esc = (s: unknown) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));

async function sendEmail(to: string, replyTo: string, subject: string, html: string) {
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${Deno.env.get("RESEND_API_KEY")}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: Deno.env.get("NOTIFY_FROM"), to: [to], reply_to: replyTo, subject, html }),
  });
  if (!r.ok) throw new Error(`Email failed: ${r.status} ${await r.text()}`);
}

Deno.serve(async (req) => {
  if (req.headers.get("x-webhook-secret") !== Deno.env.get("WEBHOOK_SECRET")) return new Response("forbidden", { status: 403 });
  const { record } = await req.json();
  if (!record) return new Response("no record", { status: 400 });

  const to = routeFor(record.topic, record.location);
  const name = [record.first_name, record.last_name].filter(Boolean).join(" ") || "Website visitor";
  const subject = `[Website] ${record.topic ?? "Message"}${record.location ? ` · ${record.location}` : ""} · ${name}`;
  const html = `
    <h2>New message from squarepegpizzeria.com</h2>
    <p><b>From:</b> ${esc(name)} &lt;${esc(record.email)}&gt;${record.phone ? ` · ${esc(record.phone)}` : ""}</p>
    <p><b>Topic:</b> ${esc(record.topic)}<br><b>Location:</b> ${esc(record.location || "Not location-specific")}</p>
    <p style="white-space:pre-wrap;border-left:4px solid #d61b24;padding-left:12px">${esc(record.message)}</p>
    <p style="color:#777">Reply to this email to answer ${esc(name)} directly.</p>`;

  await sendEmail(to, record.email, subject, html);

  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  await db.from("contact_messages").update({ routed_to: to }).eq("id", record.id);
  return new Response(JSON.stringify({ ok: true, to }), { headers: { "Content-Type": "application/json" } });
});
