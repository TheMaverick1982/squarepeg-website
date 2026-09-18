// Supabase Edge Function: email each new contact message to the right person.
// Trigger: Database Webhook on INSERT into public.contact_messages (see DEPLOY_VERCEL.md).
// Secrets needed:  RESEND_API_KEY   (or swap sendEmail() for your email provider)
//                  NOTIFY_FROM      e.g. "Square Peg Website <website@squarepegpizzeria.com>"
//                  WEBHOOK_SECRET   any long random string, also set as a header on the webhook
import { createClient } from "npm:@supabase/supabase-js@2";

// ---- Who gets the emails -----------------------------------------------------------
// Every website message goes to this whole list. To send certain topics to certain people
// instead, put addresses in BY_TOPIC / BY_LOCATION below and set ALWAYS_TO to the few who
// should still see everything.
const ALWAYS_TO = [
  "kelly@squarepegpizzeria.com",
  "maffefinancial@hotmail.com",
  "catering@squarepegpizzeria.com",
  "marketing@squarepegpizzeria.com",
  "hr@squarepegpizzeria.com",
];
// Optional extra recipients by topic (added to ALWAYS_TO, not instead of it).
const BY_TOPIC: Record<string, string> = {};
// Optional extra recipient for location-specific topics, e.g. "Glastonbury": "glastonbury@…"
const LOCATION_TOPICS = new Set(["General question", "Feedback about a visit"]);
const BY_LOCATION: Record<string, string> = {};
// -------------------------------------------------------------------------------------

function recipients(topic?: string, location?: string): string[] {
  const to = [...ALWAYS_TO];
  if (topic && BY_TOPIC[topic]) to.push(BY_TOPIC[topic]);
  if (location && BY_LOCATION[location] && (!topic || LOCATION_TOPICS.has(topic))) to.push(BY_LOCATION[location]);
  return [...new Set(to.map((a) => a.trim().toLowerCase()).filter(Boolean))];
}

// ---- Spam filter: score a message, email only the ones that look real ----------------
const SPAM_WORDS = [
  "seo", "backlink", "link building", "rank your", "guest post", "crypto", "bitcoin", "forex",
  "viagra", "casino", "loan offer", "increase your sales", "web design services", "digital marketing agency",
  "i can help you get more", "free trial of our", "telegram", "whatsapp me",
];

function spamScore(r: Record<string, unknown>): { score: number; why: string[] } {
  const msg = String(r.message ?? "");
  const low = msg.toLowerCase();
  const why: string[] = [];
  let score = 0;
  const links = (low.match(/https?:\/\//g) ?? []).length;
  if (links >= 2) { score += 2; why.push(`${links} links`); }
  else if (links === 1) { score += 1; why.push("1 link"); }
  for (const w of SPAM_WORDS) if (low.includes(w)) { score += 2; why.push(`phrase "${w}"`); }
  if (msg.length > 40 && msg === msg.toUpperCase()) { score += 1; why.push("all caps"); }
  if (!/[.!?]/.test(msg) && msg.length > 300) { score += 1; why.push("one long run-on"); }
  if (String(r.first_name ?? "").toLowerCase() === String(r.email ?? "").toLowerCase()) { score += 1; why.push("name is the email"); }
  if (/[\u0400-\u04FF\u4E00-\u9FFF]/.test(msg)) { score += 1; why.push("non-Latin script"); }
  return { score, why };
}

const esc = (s: unknown) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));

async function sendEmail(to: string[], replyTo: string, subject: string, html: string) {
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${Deno.env.get("RESEND_API_KEY")}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: Deno.env.get("NOTIFY_FROM"), to, reply_to: replyTo, subject, html }),
  });
  if (!r.ok) throw new Error(`Email failed: ${r.status} ${await r.text()}`);
}

Deno.serve(async (req) => {
  if (req.headers.get("x-webhook-secret") !== Deno.env.get("WEBHOOK_SECRET")) return new Response("forbidden", { status: 403 });
  const { record } = await req.json();
  if (!record) return new Response("no record", { status: 400 });

  const db0 = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const { score, why } = spamScore(record);
  if (score >= 3) {
    // Looks like spam: keep it in the table for review, but don't email anyone.
    await db0.from("contact_messages").update({ status: "spam", routed_to: `spam (${why.join(", ")})` }).eq("id", record.id);
    return new Response(JSON.stringify({ ok: true, skipped: "spam", why }), { headers: { "Content-Type": "application/json" } });
  }

  const to = recipients(record.topic, record.location);
  const name = [record.first_name, record.last_name].filter(Boolean).join(" ") || "Website visitor";
  const subject = `[Website] ${record.topic ?? "Message"}${record.location ? ` · ${record.location}` : ""} · ${name}`;
  const html = `
    <h2>New message from squarepegpizzeria.com</h2>
    <p><b>From:</b> ${esc(name)} &lt;${esc(record.email)}&gt;${record.phone ? ` · ${esc(record.phone)}` : ""}</p>
    <p><b>Topic:</b> ${esc(record.topic)}<br><b>Location:</b> ${esc(record.location || "Not location-specific")}</p>
    <p style="white-space:pre-wrap;border-left:4px solid #d61b24;padding-left:12px">${esc(record.message)}</p>
    <p style="color:#777">Reply to this email to answer ${esc(name)} directly.</p>
    ${score > 0 ? `<p style="color:#b5121b">Heads up, this message scored ${score} on the spam check (${esc(why.join(", "))}). It still looked real enough to send.</p>` : ""}`;

  await sendEmail(to, record.email, subject, html);

  await db0.from("contact_messages").update({ routed_to: to.join(", ") }).eq("id", record.id);
  return new Response(JSON.stringify({ ok: true, to }), { headers: { "Content-Type": "application/json" } });
});
