-- Square Peg Pizzeria website: Contact form messages
-- Run once in Supabase: Dashboard > SQL Editor > New query > paste > Run.

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
  status      text not null default 'new',   -- new / in progress / done
  routed_to   text           -- filled in by the notify-contact function
);

-- The website may ADD messages. Nobody can read them with the public key.
alter table public.contact_messages enable row level security;

drop policy if exists "website can insert contact messages" on public.contact_messages;
create policy "website can insert contact messages"
  on public.contact_messages for insert
  to anon
  with check (
    char_length(email) between 3 and 320
    and char_length(message) between 1 and 5000
    and status = 'new' and routed_to is null
  );

create index if not exists contact_messages_created_at_idx on public.contact_messages (created_at desc);
