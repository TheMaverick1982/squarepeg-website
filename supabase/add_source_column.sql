-- ===========================================================================
-- Where a contact enquiry came from.
--
-- Run this in the SQL editor of the WEBSITE project (ytkwogufrjffcgfpinrf) --
-- the one with contact_messages in it, not the Playground project.
--
-- Safe to re-run. It adds one column and re-states the insert policy with a
-- length cap on that column, so a crafted request can't post a megabyte of
-- text into it. Everything the policy already checked is unchanged.
--
-- The column holds the referring site or our own campaign tags, plus the page
-- they landed on, captured when they arrive and carried through the visit. So
-- someone who finds us on Google, lands on /catering/ and then writes from
-- /contact/ is reported as Google rather than as our own catering page.
--
-- Nothing in here identifies a visitor. It is where the click came from, the
-- tags we put on our own links, and a page path.
-- ===========================================================================

alter table public.contact_messages
  add column if not exists source text;

comment on column public.contact_messages.source is
  'Referring site or campaign tags plus landing page, captured on arrival. No visitor identity.';


-- The policy has to be re-stated rather than patched: Postgres has no "add a
-- condition to an existing policy". This is the same policy as before with one
-- extra line in it, marked NEW below.
drop policy if exists "website can insert contact messages" on public.contact_messages;
create policy "website can insert contact messages"
  on public.contact_messages for insert
  to anon
  with check (
    -- looks like a real email address
    email ~* '^[^@[:space:]]+@[^@[:space:]]+\.[a-z]{2,}$'
    and char_length(email) between 6 and 320
    -- a real message, not a wall of text
    and char_length(message) between 5 and 3000
    -- names and phone stay short
    and char_length(coalesce(first_name, '')) <= 80
    and char_length(coalesce(last_name, '')) <= 80
    and char_length(coalesce(phone, '')) <= 40
    and char_length(coalesce(topic, '')) <= 80
    and char_length(coalesce(location, '')) <= 80
    and char_length(coalesce(page, '')) <= 200
    -- NEW: the page builds this line itself and caps it at 300 characters, so
    -- anything longer did not come from our own form.
    and char_length(coalesce(source, '')) <= 300
    -- at most 2 links in a message (spam blasts carry more)
    and (array_length(regexp_split_to_array(lower(message), 'https?://'), 1) - 1) <= 2
    -- no HTML in the message
    and message !~* '<\s*(script|iframe|a|img)\b'
    -- the website only ever creates new, unrouted messages
    and status = 'new' and routed_to is null
    -- at most 3 messages an hour from one address
    and public.contact_recent_count(email) < 3
  );


-- ===========================================================================
-- CHECK IT WORKED
-- ===========================================================================
-- The column exists:
--   select column_name from information_schema.columns
--    where table_name = 'contact_messages' and column_name = 'source';
--
-- The policy is back (one row, "website can insert contact messages"):
--   select policyname from pg_policies where tablename = 'contact_messages';
--
-- Then once a real message arrives:
--   select created_at, email, source from contact_messages
--    order by created_at desc limit 10;
--
-- Nobody can still READ messages with the public key. That was never granted
-- and this does not change it.
