-- ===========================================================================
-- Square Peg website: the Playground database
--
-- Run ONCE in the SQL editor of the WEBSITE project, ytkwogufrjffcgfpinrf --
-- the same project that holds contact_messages. Safe to re-run.
--
-- This supersedes PLAYGROUND_SETUP_COMBINED.sql, LAB_SETUP.sql,
-- LAB_NO_PUBLIC_VOTING.sql and lab_inbox_view.sql. Those were written for a
-- separate project and for a version of the Pizza Lab that published entries
-- and ran a public vote on them. Neither is true any more.
--
-- Everything the website stores now lives in one project. The poll tables were
-- originally created in the Connect app's project, which was a mistake: the
-- website should not be reading or writing anything in the system that runs
-- connect.squarepegpizzeria.com.
--
-- Two things get created:
--   1. poll_votes   -- the Great Pizza Debate and the confession checklist
--   2. lab_entries  -- Pizza Lab submissions, read only by you
-- ===========================================================================


-- ===========================================================================
-- PART 1 -- THE POLL ENGINE
-- ===========================================================================
--
-- The debate pages and the confession page are the same mechanic (pick an
-- option, we count it, we show percentages), so they share one table.
--
-- We store COUNTS, NEVER VOTERS. No cookie, no IP and no fingerprint is in
-- this table -- only "poll X option Y got one more vote today". A breach of
-- this table reveals nothing about anybody.

create table if not exists public.poll_votes (
  poll        text        not null,                -- 'debate:fold-or-flat', 'confession'
  option      text        not null,                -- 'fold', 'flat', 'ketchup', ...
  region      text        not null default 'other',
  day         date        not null default current_date,
  votes       integer     not null default 0,
  primary key (poll, option, region, day)
);

comment on table public.poll_votes is
  'Playground vote counts. Counts only - no voter is identifiable from this table.';

-- region is unused. It was built to compare Connecticut against Florida, using
-- a geo header that turns out never to reach a Supabase Edge Function, so every
-- row says 'other'. Left in place because dropping a column cannot be undone
-- and an empty column costs nothing.

create or replace view public.poll_totals with (security_invoker = true) as
  select poll, option, region, sum(votes)::bigint as votes
    from public.poll_votes
   group by poll, option, region;

-- Writes go through a function, not a table grant. The anon key is public --
-- it ships inside the website's JavaScript -- so if it could UPDATE poll_votes
-- directly, anyone could set any count to any number. This takes a vote as a
-- single operation the function controls, and the function is the only thing
-- with permission to write.
create or replace function public.cast_vote(p_poll text, p_option text, p_region text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.poll_votes (poll, option, region, day, votes)
  values (p_poll, p_option, coalesce(nullif(p_region, ''), 'other'), current_date, 1)
  on conflict (poll, option, region, day)
    do update set votes = public.poll_votes.votes + 1;
end;
$$;

-- Nobody calls this directly. The cast-vote Edge Function holds the
-- service-role key and calls it after checking the poll and option are real.
revoke all on function public.cast_vote(text, text, text) from public, anon, authenticated;

-- Results are public, which is the point -- the pages show them to everyone.
-- RLS is on with a select-only policy, so the anon key can read the counts and
-- can't write a single row.
alter table public.poll_votes enable row level security;

drop policy if exists "poll results are public" on public.poll_votes;
create policy "poll results are public"
  on public.poll_votes for select
  to anon, authenticated
  using (true);

grant select on public.poll_votes  to anon, authenticated;
grant select on public.poll_totals to anon, authenticated;


-- ===========================================================================
-- PART 2 -- THE PIZZA LAB
-- ===========================================================================
--
-- Customers build a pizza from the menu's own ingredients and name it. The
-- entries come to you, you pick one, it runs as a limited-time special.
--
-- Nothing anyone submits is ever shown on the website. That is why this table
-- has row-level security on and NO policies at all: the public key can read
-- nothing here. Submissions arrive through the lab-submit Edge Function, which
-- holds the service-role key. Reading is you, in the Table Editor, and the
-- weekly digest email.

create table if not exists public.lab_entries (
  id          uuid        primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  -- what they built
  name        text        not null check (length(name) between 1 and 40),
  by_name     text        check (length(by_name) <= 40),   -- optional: first name + initial
  sauce       text        not null,
  cheese      text        not null,
  -- coalesce matters: array_length('{}', 1) is NULL, not 0, and a CHECK passes
  -- on NULL -- so without it a pizza with no toppings is silently accepted.
  toppings    text[]      not null
              check (coalesce(array_length(toppings, 1), 0) between 1 and 4),
  finish      text,
  status      text        not null default 'pending'
                          check (status in ('pending', 'approved', 'rejected')),
  -- Unused, kept in case the Lab ever does run a public vote.
  round       text,
  votes       integer     not null default 0,
  note        text
);

comment on table public.lab_entries is
  'Pizza Lab submissions. Never shown on the website - these are for the kitchen to read.';

create index if not exists lab_entries_status_idx
  on public.lab_entries (status, created_at desc);

alter table public.lab_entries enable row level security;

-- If an older version of this was ever run, clear out what it left behind.
drop view   if exists public.lab_public;
drop policy if exists "approved entries are public" on public.lab_entries;
revoke select on public.lab_entries from anon, authenticated;


-- ---------------------------------------------------------------------------
-- Reading the entries
--
-- security_invoker is load-bearing on both views below. A Postgres view runs
-- as its OWNER unless told otherwise, which means it walks straight past the
-- row-level security on the table underneath it. Without this clause, these
-- views hand the public anon key every submission -- defeating the entire
-- reason lab_entries has no policies. Verified both ways against a real
-- Postgres 16: without it anon reads everything, with it anon is denied.
-- ---------------------------------------------------------------------------

-- The one to open: Table Editor -> lab_inbox. Pending first, oldest at the
-- top, toppings as a readable line instead of {Sausage,Garlic}.
create or replace view public.lab_inbox with (security_invoker = true) as
  select
    created_at::date                   as submitted,
    name                               as pizza,
    coalesce(by_name, '—')             as built_by,
    sauce,
    cheese,
    array_to_string(toppings, ', ')    as toppings,
    -- "Nothing — leave it alone" is a real answer on the form, but printed in
    -- a column it reads like a data error.
    case when finish is null or finish ilike 'nothing%' then '' else finish end
                                       as finish,
    status,
    id
  from public.lab_entries
  order by (status <> 'pending'),
           case when status = 'pending' then created_at end asc,
           created_at desc;

comment on view public.lab_inbox is
  'Pizza Lab submissions, formatted to read. Pending first. Open this one.';

-- What the weekly digest reads.
create or replace view public.lab_pending with (security_invoker = true) as
  select id, created_at, name, by_name, sauce, cheese, toppings, finish
    from public.lab_entries
   where status = 'pending'
   order by created_at;

revoke all on public.lab_inbox   from anon, authenticated;
revoke all on public.lab_pending from anon, authenticated;


-- ===========================================================================
-- CHECK IT WORKED
-- ===========================================================================
-- Four tables/views should exist: poll_votes, poll_totals, lab_entries,
-- lab_inbox, lab_pending.
--   select table_name from information_schema.tables
--    where table_schema = 'public' order by table_name;
--
-- Polls are readable by the public (this is correct, the pages show them):
--   select * from public.poll_totals;
--
-- The Lab queue is yours alone:
--   select * from public.lab_inbox;
--
-- Nothing here touches contact_messages.
