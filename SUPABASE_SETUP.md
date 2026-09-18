# Supabase setup for the contact form

Everything the contact form needs, in order. About 30 minutes. Steps 1–3 are required; 4–6 are optional extras.

Only the contact form uses Supabase. Catering, large parties, fundraisers and the food truck go to Square Peg Connect; careers goes to Wingman; ordering, menus and gift cards stay in Toast.

---

## 1. Create the project and the table

1. Go to **supabase.com**, sign in, click **New project**.
   - **Name:** `square-peg-website`
   - **Region:** East US (closest to Connecticut)
   - **Database password:** let it generate one and save it in your password manager.
   - The free plan is enough. See "About the free plan" at the bottom.
2. Open **SQL Editor → New query**, paste the whole contents of `supabase/contact_messages.sql`, and click **Run**.
   - It creates the `contact_messages` table, the rules that block spam, and the 3-messages-an-hour limit.
   - It's safe to run again later if we change the rules.

## 2. Connect the website

1. Go to **Project Settings → API** and copy two values:
   - **Project URL** (looks like `https://abcdefgh.supabase.co`)
   - **anon public** key (a long string)
2. Send them both to me, or paste them into `data/content.py` yourself:
   - `"supabase_url": "https://abcdefgh.supabase.co",`
   - `"supabase_anon_key": "eyJhbGci…",`
3. Rebuild and push. The anon key is meant to be public: with the rules from step 1, it can only *add* a message, never read one.

**Test it:** open `/contact/` on the review site, send yourself a message, then look in Supabase under **Table Editor → contact_messages**.

## 3. Email notifications through your existing Resend account

Good news: because Resend already sends from your domain for the other app, **there are no DNS changes to make**. Domains are verified once per Resend account.

1. **In Resend:**
   - Check **Domains** and confirm `squarepegpizzeria.com` (or whichever domain you send from) shows as verified.
   - Go to **API Keys → Create API Key**:
     - **Name:** `Square Peg website contact form`
     - **Permission:** sending access
     - **Domain:** restrict it to your sending domain
   - Copy the key. A separate key means you can switch this one off later without touching the other app.
   - Decide the from-address, e.g. `website@squarepegpizzeria.com`. It must be on the verified domain. Replies go to the customer, not this address.
2. **Edit the routing** at the top of `supabase/functions/notify-contact/index.ts`, or tell me the addresses and I'll do it:
   - which address gets catering, large parties, food truck, fundraisers, gift cards, jobs, media
   - which manager gets feedback and general questions for each location
3. **Install the Supabase command line tool** on your Mac (one time):
   ```bash
   brew install supabase/tap/supabase
   supabase login
   supabase link --project-ref <your project ref>     # Settings → General → Reference ID
   ```
4. **Deploy the function and set its secrets:**
   ```bash
   supabase functions deploy notify-contact --no-verify-jwt
   supabase secrets set RESEND_API_KEY=re_xxx \
     NOTIFY_FROM="Square Peg Website <website@squarepegpizzeria.com>" \
     WEBHOOK_SECRET=<a long random string you make up>
   ```
5. **Tell the table to call it.** In Supabase: **Database → Webhooks → Create a new hook**
   - **Name:** `notify-contact`
   - **Table:** `contact_messages`
   - **Events:** Insert
   - **Type:** Supabase Edge Function → `notify-contact`
   - **HTTP Headers:** add `x-webhook-secret` with the same secret as above.
6. **Test:** send another message from the site. The email should arrive, and `routed_to` in the table should show who got it.

**What the function does besides emailing:** it scores each message for spam. Anything scoring 3 or more (several links, SEO or crypto phrases, all caps) is saved with the status `spam` and **nobody gets emailed**. Borderline messages are still sent, with a note at the bottom.

---

## 4. Optional: Cloudflare Turnstile (invisible "are you human" check)

Add this only if spam gets through. It needs a free Cloudflare account; your DNS doesn't have to move.

1. In Cloudflare: **Turnstile → Add widget**
   - **Domain:** `squarepegpizzeria.com`
   - **Widget mode:** Managed
   - Copy the **site key** (public) and the **secret key** (private).
2. Deploy the second function and give it the secret:
   ```bash
   supabase functions deploy submit-contact --no-verify-jwt
   supabase secrets set TURNSTILE_SECRET_KEY=0x_xxx \
     ALLOWED_ORIGINS="https://squarepegpizzeria.com,https://www.squarepegpizzeria.com"
   ```
3. In `data/content.py` set both, then rebuild:
   - `"contact_endpoint": "https://<project ref>.functions.supabase.co/submit-contact",`
   - `"turnstile_site_key": "0x_yyy",`

The form then goes through that function, which checks the Turnstile result, re-checks the honeypot and timing, enforces the 3-an-hour limit, and only then saves the message. Leave both settings blank and everything works as before.

## 5. Optional: weekly backup of the messages

Supabase's free plan takes no automatic backups, so `.github/workflows/backup-contact-messages.yml` exports the messages weekly and keeps the file for 90 days on GitHub.

In GitHub: **Settings → Secrets and variables → Actions → New repository secret**, twice:
- `SUPABASE_URL` — the Project URL from step 2
- `SUPABASE_SERVICE_KEY` — **Project Settings → API → service_role** key

The service key can read everything, so it only ever lives in GitHub secrets, never in the website.

## 6. Optional: who reads the messages

Anyone who should read messages in Supabase needs their own login: **Project Settings → Team → Invite**. Use individual accounts, not a shared one, and turn on two-factor authentication.

---

## About the free plan

- **Fine for this:** a contact form is a handful of rows a day.
- **Projects pause after a week of inactivity** on the free plan, which for a live form isn't an issue, but if the site is quiet for a long stretch, check that the project is still active.
- **No automatic backups** on free ([Supabase docs](https://supabase.com/docs/guides/platform/backups)); the Pro plan keeps the last 7 days. Step 5 covers this either way.

## What to send me when you're done

- the **Project URL** and **anon public** key (step 2)
- the email addresses for routing (step 3)
- the Turnstile **site key**, if you set that up (step 4)

Keep the service_role key, the Resend key, the Turnstile secret and the webhook secret to yourself: they go into Supabase secrets and GitHub secrets, never into the website files.
