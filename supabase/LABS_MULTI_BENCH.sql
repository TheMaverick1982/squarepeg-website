-- ===========================================================================
-- Square Peg Labs: one table, five benches
--
-- Run in the SQL editor of the project the website posts to -- the one in
-- lab_endpoint in data/content.py (ytkwogufrjffcgfpinrf). Safe to re-run.
--
-- lab_entries was built for pizza and only pizza: sauce, cheese and toppings
-- are NOT NULL and toppings carries a 1..4 check. A drink has no sauce and no
-- toppings at all, so the TABLE would reject it before any of the application
-- code got a say. That is what this fixes.
--
-- The shape it moves to is one jsonb column, `build`, holding an ordered list
-- of label/value pairs exactly as the page asked for them:
--
--   [{"label":"Sauce","value":"Marinara"},
--    {"label":"Protein","value":"Meatballs"},
--    {"label":"Add-ins","value":["Garlic","Ricotta"]}]
--
-- The point of that is a sixth bench. Give every bench a column per
-- ingredient and each new one is a migration, an edge-function edit and a
-- rewrite of the weekly email. With this, the email and the spreadsheet
-- render whatever labels they are handed and nobody has to teach them what a
-- rim is. The original pizza columns stay and are still written for pizza
-- entries, so the existing view, the history and anything already built on
-- them keep working.
-- ===========================================================================

-- All or nothing. Without the transaction the ALTERs commit, a later step
-- fails, and the table is left half migrated with stale views on top of it.
begin;

alter table public.lab_entries
  add column if not exists kind  text not null default 'pizza-lab',
  add column if not exists build jsonb;

comment on column public.lab_entries.kind is
  'Which bench: pizza-lab, pasta-lab, sandwich-lab, salad-lab, bar-lab.';
comment on column public.lab_entries.build is
  'Ordered [{label,value}] of what they picked. value is a string or an array.';

-- The pizza-shaped constraints come off. Nothing is lost: the values are
-- still validated against the kitchen lists in lab-submit before they land,
-- which is the check that actually matters.
alter table public.lab_entries alter column sauce    drop not null;
alter table public.lab_entries alter column cheese   drop not null;
alter table public.lab_entries alter column toppings drop not null;

-- The toppings check was created without a name, so find it rather than
-- guessing what Postgres called it.
do $$
declare c text;
begin
  for c in
    select con.conname from pg_constraint con
      join pg_class rel on rel.oid = con.conrelid
      join pg_namespace ns on ns.oid = rel.relnamespace
     where ns.nspname = 'public' and rel.relname = 'lab_entries'
       and con.contype = 'c'
       and pg_get_constraintdef(con.oid) ilike '%toppings%'
  loop
    execute format('alter table public.lab_entries drop constraint %I', c);
  end loop;
end $$;

-- A cap still belongs in the database, because the database is the last thing
-- standing if a function is ever deployed with the wrong list. Eight is above
-- every bench's cap and below anything that is obviously junk.
alter table public.lab_entries drop constraint if exists lab_entries_toppings_check;
alter table public.lab_entries
  add constraint lab_entries_toppings_check
  check (toppings is null or array_length(toppings, 1) between 1 and 8);

alter table public.lab_entries drop constraint if exists lab_entries_kind_check;
alter table public.lab_entries
  add constraint lab_entries_kind_check
  check (kind in ('pizza-lab','pasta-lab','sandwich-lab','salad-lab','bar-lab'));

-- Everything already in the table is a pizza. Give those rows the same build
-- array the new ones get, so the email and the spreadsheet have one code path
-- and the back catalogue does not read differently from this week's.
update public.lab_entries
   set build = (
     select jsonb_agg(x)
       from (
         select jsonb_build_object('label','Sauce','value',sauce)    as x
         union all select jsonb_build_object('label','Cheese','value',cheese)
         union all select jsonb_build_object('label','Toppings','value',to_jsonb(toppings))
         union all select jsonb_build_object('label','Finish','value',finish)
                    where finish is not null and finish not ilike 'nothing%'
       ) s
   )
 where build is null and sauce is not null;

create index if not exists lab_entries_kind_idx
  on public.lab_entries (kind, created_at desc);

-- ---------------------------------------------------------------------------
-- The inbox view, now that there are five benches
-- ---------------------------------------------------------------------------
-- security_invoker is not optional. A view runs as its OWNER by default, which
-- quietly bypasses the row-level security on the table underneath: without it
-- the public anon key can read every submission through the view even though
-- it is correctly blocked from reading lab_entries directly.
-- CREATE OR REPLACE VIEW cannot drop or rename a column, and both views
-- change shape here: lab_inbox trades sauce/cheese/toppings/finish for one
-- build column, lab_pending gains kind. Replacing them in place errors with
-- "cannot drop columns from view", so they go first.
drop view if exists public.lab_inbox;
create view public.lab_inbox with (security_invoker = true) as
  select
    created_at::date                       as submitted,
    initcap(replace(kind, '-lab', ''))     as bench,
    name                                   as called,
    coalesce(by_name, '—')                 as built_by,
    -- The build as one readable line: "Sauce: Marinara · Protein: Meatballs".
    (select string_agg(
              (e->>'label') || ': ' ||
              case when jsonb_typeof(e->'value') = 'array'
                   then (select string_agg(v #>> '{}', ', ')
                           from jsonb_array_elements(e->'value') v)
                   else e->>'value' end, '  ·  ')
       from jsonb_array_elements(coalesce(build, '[]'::jsonb)) e
      where coalesce(e->>'value', '') <> ''
        and (e->>'value') not ilike 'nothing%')  as build,
    status,
    id
  from public.lab_entries
  order by
    -- Anything still waiting goes to the top, oldest first, because that is
    -- the one that has been waiting longest. Everything dealt with sinks
    -- below it, newest first, as a record.
    (status <> 'pending'),
    case when status = 'pending' then created_at end asc,
    created_at desc;

comment on view public.lab_inbox is
  'Square Peg Labs submissions, formatted to read. Pending first.';

revoke all on public.lab_inbox from anon, authenticated;

drop view if exists public.lab_pending;
create view public.lab_pending with (security_invoker = true) as
  select id, created_at, kind, name, by_name, build
    from public.lab_entries
   where status = 'pending'
   order by created_at;

revoke all on public.lab_pending from anon, authenticated;

commit;
