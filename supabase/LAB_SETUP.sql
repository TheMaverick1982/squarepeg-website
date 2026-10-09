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
  round       text,                                        -- e.g. '2026-11', set when it goes to a vote
  votes       integer     not null default 0,
  note        text                                         -- why it was rejected, for our own records
);

comment on table public.lab_entries is
  'Pizza Lab submissions. Nothing is shown on the website until status = approved.';

create index if not exists lab_entries_status_idx on public.lab_entries (status, round, created_at desc);

alter table public.lab_entries enable row level security;

-- The public may read approved entries and nothing else. Pending and rejected
-- rows — the ones that might contain something we would not publish — are not
-- readable with the anon key at all.
drop policy if exists "approved entries are public" on public.lab_entries;
create policy "approved entries are public"
  on public.lab_entries for select
  to anon, authenticated
  using (status = 'approved');

grant select on public.lab_entries to anon, authenticated;

-- No insert policy: submissions come through the lab-submit Edge Function,
-- which holds the service-role key. The anon key cannot write here.

-- A view for the public vote, so the site never selects columns it shouldn't.
create or replace view public.lab_public as
  select id, name, by_name, sauce, cheese, toppings, finish, round, votes
    from public.lab_entries
   where status = 'approved';

grant select on public.lab_public to anon, authenticated;

-- What's waiting to be read. Open this in the Table Editor to moderate.
create or replace view public.lab_pending as
  select id, created_at, name, by_name, sauce, cheese, toppings, finish
    from public.lab_entries
   where status = 'pending'
   order by created_at;
