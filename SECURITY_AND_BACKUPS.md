# Security, spam and backups

Plain-language guide to how the site is protected, what's backed up, and what still needs a decision from you.

## 1. Why this site is a small target

The website is **static**: plain HTML files on Vercel's network. There's no WordPress, no plugins, no admin login and no database behind the pages, so the usual restaurant-website break-ins (a plugin exploit, a stolen admin password) don't apply here.

The parts that do accept input are:

| Part | Who runs it | What it accepts |
|---|---|---|
| Contact form | Us, into Supabase | Name, email, phone, message |
| Catering / large party / fundraiser forms | Square Peg Connect (embedded) | Their own forms |
| Careers form | Wingman (embedded) | Applications |
| Ordering, menus, gift cards | Toast | Orders and payments |
| Chat | Vendasta | Chat messages |

Payments and card details never touch this site: they happen in Toast.

## 2. Contact form: spam protection

Four layers, so a bot has to beat all of them:

1. **Honeypot field.** A hidden field only a bot fills in. If it's filled, the message is silently dropped and the visitor sees the thank-you page.
2. **Timing check.** A form submitted within 2.5 seconds of loading is held back and sent a moment later, which breaks fast-fire scripts without ever losing a real person's message.
3. **Database rules** (in `supabase/contact_messages.sql`), which apply even to a bot posting straight to the database:
   - the email must look like an email
   - the message must be 5–3,000 characters
   - at most 2 links per message
   - no HTML tags (`<script>`, `<iframe>`, `<a>`, `<img>`)
   - names, phone, topic and location capped at sensible lengths
   - **at most 3 messages an hour from one email address**
4. **Spam scoring before anyone gets emailed** (in `supabase/functions/notify-contact/index.ts`). Messages that score 3 or more (multiple links, SEO/crypto spam phrases, all caps, non-Latin blasts) are saved with the status `spam` and **no email goes out**. Borderline ones are still emailed with a note at the bottom.

The public Supabase key in the site is meant to be public: it can only *add* messages, never read them. Reading requires a Supabase login.

**If spam still gets through,** Cloudflare Turnstile (a free, invisible "are you human" check) is already built and waiting: deploy the `submit-contact` function and fill in two settings. Steps are in `SUPABASE_SETUP.md`, section 4.

## 3. Security headers

Every page is served with:

| Header | In plain words |
|---|---|
| `Strict-Transport-Security` | Browsers must use https, always |
| `X-Content-Type-Options` | Stops a file being treated as something it isn't |
| `X-Frame-Options` / `frame-ancestors` | Nobody can load your site inside their own page |
| `Referrer-Policy` | Other sites don't see the full page address people came from |
| `Permissions-Policy` | Camera and microphone are off; location only for "find my closest" |
| `Content-Security-Policy` | Limits what the page may load |
| `Cross-Origin-Opener-Policy` | Keeps other tabs from touching this one |

**One thing to finish:** the strict version of the Content-Security-Policy currently runs in **report-only** mode (`Content-Security-Policy-Report-Only` in `build.py`), so it reports what it would block without breaking anything. After launch, open the site with the browser console open, visit the home page, a location page, catering (the embedded form), careers and the chat widget, and look for "Content Security Policy" messages. If there are none, move that value into the enforced policy. Ask me and I'll make the change.

## 4. Backups: what's actually protected

**Vercel doesn't back up your website, and it doesn't need to.** The site is rebuilt from your GitHub repository, so GitHub is the backup.

| What | Where it lives | Backup |
|---|---|---|
| The website (pages, photos, code) | GitHub repo, and your Mac | **Every version, forever.** Every commit is a restore point. Your Mac is a second copy. |
| The live site | Vercel | Vercel keeps your previous deployments, so you can put an earlier version back in a click. Confirm how long they're kept on your plan. |
| Contact form messages | Supabase | **On the free plan, Supabase does not take automatic daily backups** ([Supabase docs](https://supabase.com/docs/guides/platform/backups)). The Pro plan includes the last 7 days. The weekly export job below covers this either way. |
| Orders, menus, gift cards, customers | Toast | Toast's systems, under their own backup policy |
| Catering / party / fundraiser requests | Square Peg Connect | Your own system |
| Job applications | Wingman | Their system |
| Photos (originals) | `assets/img-src/` in the repo | Same as the website |

### Restoring
- **Bad change on the site:** in Vercel, open Deployments and promote the previous one. Then fix the files and push.
- **Something deleted from the repo:** GitHub keeps every version; tell me what and when, and I'll restore it.
- **Whole repo gone:** your Mac folder is a full copy; it can be pushed to a new repo.

### The weekly message backup (new)
`.github/workflows/backup-contact-messages.yml` exports every contact message to a CSV once a week and keeps it as a downloadable file on the run page for 90 days. It is **not** committed to the repo, because it contains customer contact details.

To switch it on, add two repository secrets in GitHub (**Settings → Secrets and variables → Actions**):
- `SUPABASE_URL` — your project URL
- `SUPABASE_SERVICE_KEY` — Supabase → Project Settings → API → `service_role` key. Keep this private; it can read everything.

Without those secrets the job skips quietly.

## 5. Daily health check (new)

`.github/workflows/site-health.yml` runs every morning and checks:
- every main page and all 10 location pages return a normal page
- the home page still has its title, structured data, and no accidental "hide from Google" tag
- the security headers are present
- sample old links still redirect correctly
- the sitemap lists pages and robots.txt isn't blocking Google

If anything fails, the job fails and GitHub emails you. Run it any time from **Actions → Site health check → Run workflow**.

**At launch:** change `SITE_URL` at the top of that file from the review site to `https://squarepegpizzeria.com`.

**Worth adding:** a free uptime monitor (UptimeRobot, Better Stack) that texts someone if the site or ordering goes down at 7pm on a Friday. The GitHub check runs once a day; an uptime monitor checks every few minutes.

## 6. Accounts: the part software can't do

- **Two-factor authentication on GitHub, Vercel, Supabase, your domain registrar, Toast and Google Business Profile.** The domain registrar matters most: whoever controls the domain controls the website and the email.
- **Keep the domain locked** at the registrar and the renewal on auto-pay.
- **Least access:** give staff their own logins rather than sharing one, and remove people when they leave.
- **Email sending:** when you set up Resend for contact form notifications, add its SPF and DKIM records, and a DMARC record for the domain, so your mail doesn't land in spam and nobody can spoof your address.
- **Keep the repo private.**
