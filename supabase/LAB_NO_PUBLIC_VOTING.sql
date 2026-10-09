-- ===========================================================================
-- Pizza Lab: no public voting
--
-- Run this in the SQL editor of the Playground project (tsrnpmkipdbtwyrlfbuy).
-- Safe to re-run.
--
-- The Lab was built expecting approved entries to be published and voted on,
-- so the public key could read anything marked 'approved'. That is no longer
-- how it works: entries come to the kitchen, you pick one, it runs as an LTO.
-- Nothing from the Lab is ever shown on the website.
--
-- Which means the public needs no read access to lab_entries at all. This
-- removes it. After running, the anon key cannot read a single row of that
-- table — not pending, not approved, not rejected. Submissions still work:
-- they go through the lab-submit Edge Function, which holds the service-role
-- key, and reading stays with you in the Table Editor and the weekly digest.
--
-- This only tightens access. Nothing that currently works stops working.
-- ===========================================================================

-- The view that served approved entries to the website. Nothing reads it now.
drop view if exists public.lab_public;

-- The policy that let the public read approved rows.
drop policy if exists "approved entries are public" on public.lab_entries;

-- And the grant underneath it.
revoke select on public.lab_entries from anon, authenticated;

-- lab_pending stays: it is how you moderate in the Table Editor, and it is
-- readable only with your own login, never with the public key.

-- ---------------------------------------------------------------------------
-- The votes and round columns are left in place. They are empty and unused,
-- and dropping a column cannot be undone. If the Lab ever does get a public
-- vote they are already there; if not, they cost nothing.
-- ---------------------------------------------------------------------------

-- ===========================================================================
-- CHECK IT WORKED
-- ===========================================================================
-- Should return no rows (the view is gone):
--   select table_name from information_schema.views
--    where table_schema = 'public' and table_name = 'lab_public';
--
-- Should return no rows (no policy left on the table):
--   select policyname from pg_policies
--    where schemaname = 'public' and tablename = 'lab_entries';
--
-- Should still list your pending submissions:
--   select * from public.lab_pending;
