-- The Playground poll engine: one table for every vote on the site.
--
-- Powers both The Great Pizza Debate (/play/debate/<slug>/) and the Confession
-- checklist (/play/confessions/). They are the same mechanic underneath — a
-- visitor picks an option, we count it, we show percentages — so they share one
-- table and one Edge Function rather than growing two of everything.
--
-- Run this once in the Supabase SQL editor.
--
-- Design notes worth keeping in mind before changing anything here:
--
--  * We store counts, never voters. There is no cookie, no account, no IP and
--    no fingerprint in this table — only "poll X option Y got one more vote, in
--    this region, on this day". That keeps the page out of scope for most of the
--    privacy policy and means a breach of this table reveals nothing about anyone.
--  * One vote per browser is enforced in localStorage, and a rate limit in the
--    Edge Function stops the obvious scripted stuffing. Neither is bulletproof.
--    That is an accepted trade: this is a pineapple poll, not an election. But
--    if we are going to publish "Connecticut says X", the number should not be
--    a lie, so the limits exist.
--  * region is coarse on purpose ('CT', 'FL', 'other'). It comes from the
--    Cloudflare/Vercel edge header, not from asking the visitor. It exists so we
--    can run the Connecticut-vs-Florida comparison, which is the genuinely
--    interesting thing this data produces.

-- ---------------------------------------------------------------- the table

create table if not exists public.poll_votes (
  poll        text        not null,              -- e.g. 'debate:pineapple-on-pizza', 'confession'
  option      text        not null,              -- e.g. 'yes', 'no', 'car', 'ketchup'
  region      text        not null default 'other'  -- 'CT' | 'FL' | 'other'
                          check (region in ('CT', 'FL', 'other')),
  day         date        not null default (now() at time zone 'America/New_York'),
  votes       bigint      not null default 0,
  primary key (poll, option, region, day)
);

comment on table public.poll_votes is
  'Aggregate vote counts for the /play/ pages. Counts only - no voter identity of any kind is stored.';

-- Rolled up for the website and for the nightly build.
create or replace view public.poll_totals as
  select poll, option, region, sum(votes)::bigint as votes
    from public.poll_votes
   group by poll, option, region;

-- ---------------------------------------------------------------- the writer
--
-- A single atomic upsert. Called only by the Edge Function, which holds the
-- service-role key. Taking this as a function rather than letting the client
-- insert means the anon key can never write an arbitrary row.

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

-- ---------------------------------------------------------------- read access
--
-- Results are public — they are printed on the page — so anon may read the
-- totals and nothing else. Row-level security is on with no insert, update or
-- delete policy, which means the anon key cannot write here at all. Writes go
-- through the Edge Function.

alter table public.poll_votes enable row level security;

drop policy if exists "poll results are public" on public.poll_votes;
create policy "poll results are public"
  on public.poll_votes for select
  to anon, authenticated
  using (true);

grant select on public.poll_votes to anon, authenticated;
grant select on public.poll_totals to anon, authenticated;

-- ---------------------------------------------------------------- seeding
--
-- Nothing is seeded. A poll showing 50/50 with two votes is honest; a poll
-- showing 57/43 because we typed it in is not, and the whole appeal of this
-- page is that the numbers are real. The site copy handles the empty state by
-- saying how few votes there are so far.
