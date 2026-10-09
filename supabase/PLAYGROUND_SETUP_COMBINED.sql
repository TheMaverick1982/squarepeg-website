-- ===========================================================================
-- Square Peg Playground — database setup
-- Run this ONCE in the Supabase SQL editor (SQL Editor → New query → Run).
-- Safe to re-run: everything is "if not exists" or "create or replace".
--
-- Creates two things:
--   1. poll_votes   — the Great Pizza Debate + the confession checklist
--   2. lab_entries  — Pizza Lab submissions, with a moderation queue
-- ===========================================================================


-- ===========================================================================
-- PART 1 — THE POLL ENGINE
-- ===========================================================================
--
-- The debate and the confession page are the same mechanic (pick an option,
-- we count it, we show percentages), so they share one table.
--
-- We store COUNTS, NEVER VOTERS. No cookie, no IP, no fingerprint is in this
-- table — only "poll X option Y got one more vote, in this region, on this
-- day". A breach of this table reveals nothing about anyone.
--
-- region is coarse ('CT' / 'FL' / 'other') and comes from the edge's own geo
-- header, not from asking the visitor. It exists so we can run the
-- Connecticut-vs-Florida comparison.

create table if not exists public.poll_votes (
  poll        text        not null,                 -- 'debate:pineapple-on-pizza', 'confession'
  option      text        not null,                 -- 'yes', 'no', 'car', 'ketchup', ...
  region      text        not null default 'other'
                          check (region in ('CT', 'FL', 'other')),
  day         date        not null default (now() at time zone 'America/New_York'),
  votes       bigint      not null default 0,
  primary key (poll, option, region, day)
);

comment on table public.poll_votes is
  'Aggregate vote counts for the /play/ pages. Counts only - no voter identity of any kind is stored.';

-- Rolled up for the website and the nightly build.
create or replace view public.poll_totals as
  select poll, option, region, sum(votes)::bigint as votes
    from public.poll_votes
   group by poll, option, region;

-- One atomic upsert, called only by the cast-vote Edge Function (which holds
-- the service-role key). Taking writes as a function means the public anon key
-- can never insert an arbitrary row.
create or replace function public.cast_vote(p_poll text, p_option text, p_region text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_poll is null or p_option is null
     or length(p_poll) > 80 or length(p_option) > 80 then
    raise exception 'bad poll or option';
  end if;

  insert into public.poll_votes (poll, option, region, votes)
  values (p_poll, p_option,
          case when p_region in ('CT', 'FL') then p_region else 'other' end,
          1)
  on conflict (poll, option, region, day)
  do update set votes = public.poll_votes.votes + 1;
end;
$$;

revoke all on function public.cast_vote(text, text, text) from public, anon, authenticated;

-- Results are public (they're printed on the page), so anon may READ the
-- totals. RLS is on with no insert/update/delete policy, so the anon key
-- cannot write here at all.
alter table public.poll_votes enable row level security;

drop policy if exists "poll results are public" on public.poll_votes;
create policy "poll results are public"
  on public.poll_votes for select
  to anon, authenticated
  using (true);

grant select on public.poll_votes  to anon, authenticated;
grant select on public.poll_totals to anon, authenticated;

-- Nothing is seeded. A poll showing 50/50 on two votes is honest; one showing
-- 57/43 because we typed it in is not, and real numbers are the whole appeal.
-- The site copy handles the empty state ("Nobody has voted yet. Go on.").


-- ===========================================================================
-- PART 2 — THE PIZZA LAB
-- ===========================================================================
--
-- One rule drives this design: nothing a member of the public types appears on
-- squarepegpizzeria.com until a person has read it. Names are the real risk —
-- a pizza called something defamatory, obscene, or just somebody's phone
-- number — and no word filter catches that reliably.
--
-- Moderation happens in the Supabase Table Editor, not a custom admin page on
-- the website. An admin page would mean bolting authentication onto a static
-- site, which is a far bigger attack surface than this problem deserves.
-- Supabase already has accounts, passwords and an audit trail.
--
-- TO MODERATE: open the lab_pending view, read the rows, then set status on
-- that row in lab_entries to 'approved' or 'rejected'.

create table if not exists public.lab_entries (
  id          uuid        primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  -- what they built
  name        text        not null check (length(name) between 1 and 40),
  by_name     text        check (length(by_name) <= 40),    -- optional: first name + initial
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
  round       text,                                          -- e.g. '2026-11', set when it goes to a vote
  votes       integer     not null default 0,
  note        text                                           -- why it was rejected, for our records
);

comment on table public.lab_entries is
  'Pizza Lab submissions. Nothing is shown on the website until status = approved.';

create index if not exists lab_entries_status_idx
  on public.lab_entries (status, round, created_at desc);

alter table public.lab_entries enable row level security;

-- The public may read APPROVED entries and nothing else. Pending and rejected
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

-- What the website reads, so it never selects a column it shouldn't.
create or replace view public.lab_public as
  select id, name, by_name, sauce, cheese, toppings, finish, round, votes
    from public.lab_entries
   where status = 'approved';

grant select on public.lab_public to anon, authenticated;

-- What's waiting to be read. Open THIS in the Table Editor to moderate.
create or replace view public.lab_pending as
  select id, created_at, name, by_name, sauce, cheese, toppings, finish
    from public.lab_entries
   where status = 'pending'
   order by created_at;


-- ===========================================================================
-- CHECK IT WORKED — run these after, they should return rows / no error.
-- ===========================================================================
-- select * from public.poll_totals;        -- empty is correct, nobody has voted
-- select * from public.lab_pending;        -- empty is correct, nothing submitted
