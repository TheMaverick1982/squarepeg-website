-- The Pizza Lab: customer-invented pizzas, moderated before anyone sees them.
--
-- Run this once in the Supabase SQL editor, alongside POLLS_SETUP.sql.
--
-- The whole design turns on one rule: nothing a member of the public types
-- appears on squarepegpizzeria.com until a person has read it. Names are the
-- risk here — a pizza called something defamatory, obscene or just somebody's
-- phone number would otherwise be published automatically on our own domain,
-- and no word filter catches that reliably.
--
-- Moderation happens in the Supabase Table Editor rather than in a custom admin
-- page on the website. That is a deliberate trade: an admin page would mean
-- building authentication onto a static site, which is a much larger attack
-- surface than the problem deserves. Supabase already has accounts, passwords
-- and an audit trail, and Brian already uses it.
--
-- To moderate: open lab_entries, read the pending rows, set status to
-- 'approved' or 'rejected'. Only 'approved' rows are ever readable by the site.

create table if not exists public.lab_entries (
  id          uuid        primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  -- what they built
  name        text        not null check (length(name) between 1 and 40),
  by_name     text        check (length(by_name) <= 40),   -- optional, first name + initial
  sauce       text        not null,
  cheese      text        not null,
  -- coalesce matters: array_length('{}', 1) is NULL, not 0, and a CHECK passes
  -- on NULL — so the bare version silently accepts a pizza with no toppings.
  toppings    text[]      not null
              check (coalesce(array_length(toppings, 1), 0) between 1 and 4),
  finish      text,
  -- moderation
  status      text        not null default 'pending'
                          check (status in ('pending', 'approved', 'rejected')),
  -- Unused. Kept in case the Lab ever does run a public vote; empty columns
  -- cost nothing and dropping one cannot be undone.
  round       text,
  votes       integer     not null default 0,
  note        text                                         -- why it was rejected, for our own records
);

comment on table public.lab_entries is
  'Pizza Lab submissions. Nothing is shown on the website until status = approved.';

create index if not exists lab_entries_status_idx on public.lab_entries (status, round, created_at desc);

alter table public.lab_entries enable row level security;

-- No policies at all, deliberately. Nothing from the Lab is ever shown on the
-- website: entries come to the kitchen, you pick one, it runs as an LTO. So the
-- public key can read nothing here -- not pending, not approved, not rejected --
-- and with RLS on and no policy, that is exactly what it gets.
--
-- Submissions come through the lab-submit Edge Function, which holds the
-- service-role key. Reading is you in the Table Editor and the weekly digest.

-- What's waiting to be read. Open this in the Table Editor to moderate.
create or replace view public.lab_pending as
  select id, created_at, name, by_name, sauce, cheese, toppings, finish
    from public.lab_entries
   where status = 'pending'
   order by created_at;


-- ===========================================================================
-- WEEKLY DIGEST — run this after deploying the lab-digest Edge Function
-- ===========================================================================
--
-- Emails everything waiting for review to plainville@squarepegpizzeria.com
-- every Monday at 9am Eastern, so nobody has to remember to check the queue.
--
-- This is scheduled inside Supabase rather than as a GitHub Action because
-- pending entries cannot be read with the public anon key — that is the point
-- of the queue — and the service-role key must never go into a workflow file.
--
-- Before running, replace BOTH placeholders:
--   <PROJECT>         your project ref, e.g. tsrnpmkipdbtwyrlfbuy
--   <LAB_DIGEST_KEY>  the same long random string you set as the function's
--                     LAB_DIGEST_KEY secret, so only this schedule can fire it

create extension if not exists pg_cron;
create extension if not exists pg_net;

-- 13:00 UTC is 9am Eastern in summer, 8am in winter. Postgres cron has no
-- time zone, so rather than chase the clock twice a year this stays put — an
-- hour either way does not matter for a weekly digest.
select cron.schedule(
  'pizza-lab-weekly-digest',
  '0 13 * * 1',
  $$
  select net.http_post(
    url := 'https://<PROJECT>.supabase.co/functions/v1/lab-digest?key=<LAB_DIGEST_KEY>',
    headers := '{"Content-Type": "application/json"}'::jsonb
  );
  $$
);

-- Check it:    select * from cron.job;
-- Last runs:   select * from cron.job_run_details order by start_time desc limit 5;
-- Remove it:   select cron.unschedule('pizza-lab-weekly-digest');
