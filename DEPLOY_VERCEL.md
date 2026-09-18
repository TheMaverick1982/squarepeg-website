# Put the site on Vercel for team review

You'll end up with a link like `square-peg-review.vercel.app` (or `preview.squarepegpizzeria.com`) that your team can open on any phone or computer. **Your live site isn't touched.**

The review site uses the **`dist-staging`** folder. It's the same site with a "do not index" tag, so Google won't list the review copy or confuse it with your real site.

---

## Recommended: GitHub → Vercel (auto-deploys on every change)

### What you do (one time, about 10 minutes)
1. **Create an empty private GitHub repo**, e.g. `squarepeg-website`. Leave "Add a README" unchecked.
2. **Upload the project folder.** The easiest way is **GitHub Desktop**:
   - Choose **File → Add Local Repository**, pick `~/Sites/squarepeg-site`, and click "create a repository" when asked.
   - Click **Publish repository**, choose your account, keep it **private**, and publish.
   - The included `.gitignore` leaves out the scratch folders and zip files.
3. **Create a new Vercel project for the review site:**
   - In Vercel, click **Add New → Project** and import `squarepeg-website`.
   - **Project name:** `square-peg-review`
   - **Framework Preset:** Other
   - **Root Directory:** click Edit and choose `dist-staging`
   - **Build Command / Output Directory:** leave empty (the site is prebuilt)
   - Click **Deploy**. You get `square-peg-review.vercel.app`.
4. **How updates flow:** I can't log in to GitHub or Vercel for you. Each time I make changes, I update the files in `~/Sites/squarepeg-site`, you click **Commit** then **Push** in GitHub Desktop, and Vercel redeploys in about 30 seconds.

### At launch
Create a second Vercel project from the **same repo** with Root Directory **`dist`** (the version Google can see), and attach `squarepegpizzeria.com` to that one. The review project stays as your staging site.

### No GitHub? Deploy from Terminal instead
```bash
cd ~/Sites/squarepeg-site/dist-staging
npx vercel          # first time: log in, create project "square-peg-review"
npx vercel --prod   # gives square-peg-review.vercel.app
```

---

## Optional: a nicer review address
In the Vercel project, go to **Settings → Domains → Add** and enter `preview.squarepegpizzeria.com`. Then, wherever your domain's DNS is managed, add:

| Type | Name | Value |
|---|---|---|
| CNAME | `preview` | `cname.vercel-dns.com` |

This doesn't affect the live site or the future `order.` subdomain.

## Optional: keep it private
In the Vercel project, go to **Settings → Deployment Protection**.
- **Vercel Authentication** (included on free plans) only lets people who are logged into your Vercel team see preview links.
- **Password Protection** gives one shared password for everyone, but it's a paid add-on.

---

## Forms

### Catering, large parties, food truck, fundraisers → Square Peg Connect
These pages embed your Connect forms (`connect.squarepegpizzeria.com/public/...`). The addresses and frame heights live in `EMBEDS` in `data/content.py`. Food Truck uses the catering form.

### Contact form → Supabase (with routed email notifications)
Full step-by-step, including reusing your existing Resend account and the optional Turnstile check: **`SUPABASE_SETUP.md`**.

In short: create the Supabase project, run `supabase/contact_messages.sql`, put the Project URL and anon key into `data/content.py`, deploy the `notify-contact` function with your Resend key, and add a Database Webhook on insert.

---

## When you're ready to launch
- Build the real version with `python3 build.py` and deploy the **`dist`** folder (it has no "do not index" tag).
- `dist/vercel.json` already contains every 301 redirect and the caching headers in Vercel's format.
- Then follow `LAUNCH_CHECKLIST.md`.
