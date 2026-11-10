// Supabase Edge Function: hand the Google Sheet the builds it hasn't seen.
//
// The spreadsheet is where the kitchen actually works -- one tab per bench,
// a column to tick when something gets picked. This is the only way rows get
// into it. Entries are deliberately unreadable with the public anon key, so
// reading them needs the service-role key, and that key stays in here rather
// than going anywhere near a Google account.
//
// Deploy:   supabase functions deploy lab-export --no-verify-jwt
// Secrets:  LAB_EXPORT_KEY   a long random string, different from LAB_DIGEST_KEY,
//                            sent as ?key= by the Apps Script
//
// Called by tools/lab_sheet.gs:
//   GET .../lab-export?key=<LAB_EXPORT_KEY>&since=<ISO8601>
//
// `since` is the newest created_at the sheet already holds. The script sends
// it so a weekly pull stays small; leave it off and you get everything, which
// is what you want the first time and after someone deletes a tab by accident.
// Rows are never updated or removed here, only read: the sheet owns the Picked
// column and nothing writes back, so there is nothing to keep in step.
import { createClient } from "npm:@supabase/supabase-js@2";

const MAX = 5000;

Deno.serve(async (req) => {
  const url = new URL(req.url);
  // Both sides trimmed: a secret pasted into a dashboard field very often
  // carries a trailing newline, and an exact comparison then fails in a way
  // that looks like the wrong key rather than invisible whitespace.
  const want = (Deno.env.get("LAB_EXPORT_KEY") ?? "").trim();
  const got = (url.searchParams.get("key") ?? "").trim();
  if (!want || got !== want) return new Response("forbidden", { status: 403 });

  const db = createClient(
    Deno.env.get("SUPABASE_URL") ?? "",
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
    { auth: { persistSession: false } },
  );

  let q = db.from("lab_entries")
    .select("id,created_at,kind,name,by_name,build")
    .order("created_at", { ascending: true })
    .limit(MAX);

  const since = (url.searchParams.get("since") ?? "").trim();
  // A bad date would silently return everything, every run, and the sheet
  // would grow a duplicate of itself. Only use it if it parses.
  if (since && !Number.isNaN(Date.parse(since))) q = q.gt("created_at", since);

  const { data, error } = await q;
  if (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500, headers: { "Content-Type": "application/json" },
    });
  }

  return new Response(JSON.stringify({ ok: true, entries: data ?? [] }), {
    headers: { "Content-Type": "application/json" },
  });
});
