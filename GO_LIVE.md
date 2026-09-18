# Go live: the short list

Everything left, in order, with who does what. Hosting stays on Brian's Vercel account for now; the transfer to a Square Peg team can happen any time afterwards with no downtime.

**Legend:** 🟥 blocks launch · 🟨 do soon after · ⬜ nice to have

---

## Step 1 — Accounts (Brian) 🟥

Create these on **Square Peg's own email**, not a personal one, so nothing has to move later:

- **Supabase** — free plan, no card needed. Make it under the restaurant's account from the start.
- **Resend** — already exists and already sends from your domain. Nothing new to create except one API key.
- **Google Cloud** (only for the hours sync) — can wait until after launch.

Turn on two-factor authentication on each, plus GitHub, Vercel and the domain registrar.

---

## Step 2 — Contact form: Supabase (Brian, ~15 min) 🟥

Full detail in `SUPABASE_SETUP.md`. The short version:

1. **New project** in Supabase: name `square-peg-website`, region East US. Save the database password.
2. **SQL Editor → New query** → paste all of `supabase/contact_messages.sql` → **Run**. That builds the table and every anti-spam rule.
3. **Project Settings → API** → send Claude:
   - **Project URL**
   - **anon public** key
4. Claude puts them in the site, rebuilds, and you push. Then send a test message from `/contact/` and check **Table Editor → contact_messages**.

---

## Step 3 — Notification emails through Resend (Brian + Claude, ~15 min) 🟥

1. **In Resend:** **API Keys → Create API Key**
   - Name: `Square Peg website contact form`
   - Permission: sending access
   - Domain: restrict to your sending domain
   - Copy the key. No DNS changes: the domain is already verified for the other app.
2. **Send Claude the routing list** (no key, just addresses): who gets catering, large parties, food truck, fundraisers, gift cards, jobs, media, and which manager gets feedback for each location. Claude puts them in the function.
3. **Deploy the function, in the browser, no Terminal needed:**
   - Supabase → **Edge Functions → Deploy a new function → Via Editor**
   - Name it `notify-contact`, paste the contents of `supabase/functions/notify-contact/index.ts`, click **Deploy function**.
   - Add the secrets under **Edge Functions → Secrets** (or Settings → Edge Functions):
     - `RESEND_API_KEY` — the key from step 1
     - `NOTIFY_FROM` — e.g. `Square Peg Website <website@squarepegpizzeria.com>`
     - `WEBHOOK_SECRET` — any long random string you make up
   - (If you'd rather use Terminal, the CLI commands are in `SUPABASE_SETUP.md`.)
4. **Database → Webhooks → Create a new hook**
   - Table `contact_messages`, event **Insert**, type **Supabase Edge Function** → `notify-contact`
   - Header: `x-webhook-secret` = the same string
5. **Test every route:** send one message per topic and confirm each lands with the right person.

---

## Step 4 — Toast on the subdomain (Brian + Toast, then Claude) 🟥

1. Toast connects `order.squarepegpizzeria.com`; confirm it loads in a browser.
2. GitHub → **Actions → Check Toast links → Run workflow**. Every row should be ✅.
3. Tell Claude, who flips `TOAST_ON_SUBDOMAIN` to `True` and rebuilds. Every Order, Menu and Gift Card button then points at the subdomain, and all old links redirect there.

---

## Step 5 — Facts to confirm (Brian) 🟥

Claude can't verify these; they're on the site now as best guesses.

- **Hours for all 10 locations** (the site's hours and Toast's don't match everywhere).
- **Preston's exact map pin** (its coordinates are approximate).
- **Addresses:** Shelton 310 vs 320 Howe Ave; Berlin 119 vs 151 Webster Square Rd; East Hartford Long Hill Rd vs St.
- **Rewards sign-up link** in the home banner (currently the Como sign-up page, unverified).
- **Catering phone number** and the contact email.
- **Instagram URL** (missing).
- **Privacy page** — a draft; have someone read it.
- **SMS terms** — compare word for word with your current page; carriers check it.
- **Photo licenses** for the two stock-looking photos.
- **Specials and entertainment** lineups: still current?

---

## Step 6 — Launch day (Brian + Claude) 🟥

1. Create the **production Vercel project** from the same repo with Root Directory `dist` (the review site keeps using `dist-staging`).
2. Point **squarepegpizzeria.com** and **www** at it. Set `www` to redirect to the main domain. Don't touch the `order` DNS records.
3. Watch the first deploy, then spot-check on a phone: an Order button, a Menu button, Gift Cards, one old `/order/...` link, one `/menu-<town>` link.
4. **Google Search Console:** verify the domain, submit `sitemap.xml`, request indexing for the home page, the 10 location pages, the menu page and the towns page.
5. **Google Business Profile, each location:** website link → that location's page; menu and order links → the Toast subdomain.
6. Change `SITE_URL` in `.github/workflows/site-health.yml` to the real domain.

---

## Step 7 — First week after launch 🟨

- **Check the strict content-security policy** in the browser console, then switch it from report-only to enforced.
- **Turn on the Google hours sync** (`HOURS_SYNC.md`), so hours come from Google Business Profile. Run "Find Google place IDs" first and fix any wrong hours in Google.
- **Weekly message backup:** add `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` as GitHub secrets.
- **Uptime monitor** (UptimeRobot or similar) pointed at the home page and one location page.
- **Search Console:** watch the Pages report for 404s and send Claude any old URLs that show up.
- **Refresh Facebook's link previews** with the Sharing Debugger.
- **Analytics:** add the GA4 and Meta Pixel IDs, then set up cross-domain tracking with the Toast subdomain.

---

## Step 8 — When the restaurant's card is ready ⬜

- Create the Square Peg Vercel team, upgrade to Pro, and transfer both projects (**Settings → General → Transfer Project**). Zero downtime, domains included.
- Re-add integrations, re-create the deploy hook if one exists, and update the GitHub secret for it.
- Consider a GitHub organization for the repo at the same time.

---

## What Claude needs from you, in one list

1. Supabase **Project URL** + **anon public** key
2. Email **routing addresses** (by topic and by location)
3. Confirmed **hours**, Preston's **map pin**, and the three **addresses**
4. **Instagram** URL, **catering phone**, **rewards sign-up** link
5. A yes on the **privacy** and **SMS terms** pages
6. A word when **Toast's subdomain** is live, and when you've **pushed** each update
