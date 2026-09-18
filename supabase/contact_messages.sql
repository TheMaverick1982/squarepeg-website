-- Square Peg Pizzeria website: Contact form messages
-- Run once in Supabase: Dashboard > SQL Editor > New query > paste > Run.
-- Safe to re-run: it only adds what's missing.

create table if not exists public.contact_messages (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz not null default now(),
  first_name  text,
  last_name   text,
  email       text not null,
  phone       text,
  topic       text,          -- e.g. 'Feedback about a visit', 'Gift cards', 'Jobs'
  location    text,          -- e.g. 'Glastonbury' (blank = not location-specific)
  message     text not null,
  page        text,
  status      text not null default 'new',   -- new / in progress / done / spam
  routed_to   text           -- filled in by the notify-contact function
);

-- The website may ADD messages. Nobody can read them with the public key.
alter table public.contact_messages enable row level security;

-- Rate limit: how many messages this email address sent in the last hour.
-- SECURITY DEFINER so the check can count rows the public key can't read.
create or replace function public.contact_recent_count(p_email text)
  returns int language sql security definer stable set search_path = public as $$
  select count(*)::int from public.contact_messages
  where lower(email) = lower(p_email) and created_at > now() - interval '1 hour'
$$;
revoke all on function public.contact_recent_count(text) from public;
grant execute on function public.contact_recent_count(text) to anon;

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
    -- at most 2 links in a message (spam blasts carry more)
    and (array_length(regexp_split_to_array(lower(message), 'https?://'), 1) - 1) <= 2
    -- no HTML in the message
    and message !~* '<\s*(script|iframe|a|img)\b'
    -- the website only ever creates new, unrouted messages
    and status = 'new' and routed_to is null
    -- at most 3 messages an hour from one address
    and public.contact_recent_count(email) < 3
  );

create index if not exists contact_messages_created_at_idx on public.contact_messages (created_at desc);
create index if not exists contact_messages_email_idx on public.contact_messages (lower(email), created_at desc);
