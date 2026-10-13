-- ===========================================================================
-- The Pizza Lab inbox
--
-- Run in the SQL editor of the PLAYGROUND project (tsrnpmkipdbtwyrlfbuy).
-- Safe to re-run.
--
-- The weekly email is the reminder. This is the thing you open when you want
-- to look without waiting for Monday: Table Editor -> lab_inbox.
--
-- It reads as a build sheet rather than as raw table columns. toppings is a
-- Postgres array, which the Table Editor shows as {Sausage,Garlic} -- true,
-- but not what you want to read at 9am while deciding what goes on the menu.
-- ===========================================================================

-- security_invoker is not optional here. A Postgres view runs as its OWNER by
-- default, which means it quietly bypasses the row-level security on the table
-- underneath it: without this line the public anon key can read every
-- submission through the view even though it is correctly blocked from reading
-- lab_entries directly. Tested both ways -- without it, anon sees everything.
create or replace view public.lab_inbox with (security_invoker = true) as
  select
    created_at::date                                   as submitted,
    name                                               as pizza,
    coalesce(by_name, '—')                             as built_by,
    sauce,
    cheese,
    array_to_string(toppings, ', ')                    as toppings,
    -- "Nothing — leave it alone" is a real answer on the form, but it reads
    -- like a data error in a column. Blank it out.
    case when finish is null or finish ilike 'nothing%' then '' else finish end
                                                       as finish,
    status,
    id
  from public.lab_entries
  order by
    -- Anything still waiting goes to the top, oldest first, because that is
    -- the one that has been waiting longest. Everything already dealt with
    -- sinks below it, newest first, as a record.
    (status <> 'pending'),
    case when status = 'pending' then created_at end asc,
    created_at desc;

comment on view public.lab_inbox is
  'Pizza Lab submissions, formatted to read. Pending first. Open this rather than lab_entries.';

-- Belt and braces: even with security_invoker set, don't hand the public roles
-- a grant on it in the first place.
revoke all on public.lab_inbox from anon, authenticated;

-- Same bug, same fix, on the view that was already there. lab_pending was
-- created without security_invoker, so until this runs the anon key can read
-- the whole moderation queue through it. Nothing has been exposed yet -- the
-- Lab is not live and the table is empty -- but this has to go in before it is.
create or replace view public.lab_pending with (security_invoker = true) as
  select id, created_at, name, by_name, sauce, cheese, toppings, finish
    from public.lab_entries
   where status = 'pending'
   order by created_at;

revoke all on public.lab_pending from anon, authenticated;


-- ===========================================================================
-- HOW TO USE IT
-- ===========================================================================
-- Read:      Table Editor -> views -> lab_inbox
-- Just the queue:
--   select * from public.lab_inbox where status = 'pending';
--
-- When you pick one (copy the id from the inbox):
--   update public.lab_entries set status = 'approved' where id = '<paste-id>';
--
-- Clear the rest of a month so next week's email is short:
--   update public.lab_entries set status = 'rejected'
--    where status = 'pending' and created_at < date '2026-11-01';
--
-- Count what's waiting:
--   select count(*) from public.lab_entries where status = 'pending';
