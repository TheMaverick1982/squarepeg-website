# Hours: edit them in Google only

The website copies each location's hours from its **Google Business Profile** every night. To change hours, including holiday hours, edit them in Google (Google Maps app, or business.google.com). The website catches up by the next morning.

## How it works

- **Every night (about 4am Eastern)**, a GitHub job (`.github/workflows/sync-hours.yml`) asks Google for each location's hours.
- **If anything changed**, it rebuilds the pages, commits them and pushes. Vercel then redeploys the site automatically.
- **Holiday and special hours** that you enter in Google show up on that location's page in a "Holiday & special hours" box. They also affect the "Open now" badges and the search data, and they appear about a week ahead, the same as on Google.
- **Nothing changed?** Then nothing is committed.
- **Need it sooner?** Go to GitHub, then **Actions → Sync hours from Google → Run workflow**.

### Safety rules

- **Google can't return a location** (an error, or no hours listed): the website keeps that location's last known hours.
- **Every lookup fails:** the job stops without changing anything, and GitHub emails you.
- **Google marks a location closed:** it's flagged in the job summary. Its hours are not removed from the site.
- **The sync isn't set up yet:** the website uses the hours in `data/content.py`, and the nightly job skips quietly.
- **Split hours** (e.g. lunch plus dinner): the site shows one window per day, from first open to last close, and the job summary flags it.

### Cost

The job makes one Google lookup per location per night, about 300 a month. Google's Place Details Enterprise tier includes 1,000 free lookups a month (Sept 2026 pricing), and GitHub Actions minutes are well within the free plan.

---

## One-time setup (about 15 minutes)

### Step 1: Google Cloud (creates the key)

Use the Google account that manages your business listings, or any account you control.

1. Go to **console.cloud.google.com** and sign in.
2. Create a project. At the top, open the project picker and choose **New project**.
   - **Name:** `Square Peg Website`
   - Click **Create**, then select the new project.
3. Turn on billing. Open **Billing** and link a billing account. Google requires a card even though this usage fits the free allowance.
4. Turn on the Places API. Open **APIs & Services → Library**, search for **Places API (New)**, and click **Enable**.
5. Create the key. Open **APIs & Services → Credentials → Create credentials → API key**. Then click the new key to edit it:
   - **Name:** `Website hours sync`
   - **Application restrictions:** None. GitHub's servers don't have fixed addresses.
   - **API restrictions:** Restrict key, then tick **Places API (New)** only.
   - Click **Save**, then copy the key.
6. Recommended safety nets:
   - **Budget alert:** open **Billing → Budgets & alerts** and create a budget of **$5** that emails you.
   - **Daily limit:** open **APIs & Services → Places API (New) → Quotas** and lower the daily request limits (e.g. to 200 per day).

Keep the key private. Don't paste it into email or chat. It only goes into GitHub (step 2).

### Step 2: GitHub (stores the key)

1. Open the repo **TheMaverick1982/squarepeg-website** on github.com.
2. Go to **Settings → Secrets and variables → Actions → New repository secret**.
   - **Name:** `GOOGLE_PLACES_API_KEY`
   - **Secret:** paste the key.
   - Click **Add secret**.
3. Open the **Actions** tab. If GitHub asks, click **I understand my workflows, go ahead and enable them**.

### Step 3: Match each location to its Google listing

1. Go to **Actions → Find Google place IDs → Run workflow**, then click the green **Run workflow** button.
2. Wait about 30 seconds, then open the run. Its summary shows two things:
   - **Place IDs:** each location and the Google listing it matched. Every row should say *matched* and show the right address. Any row that says *CHECK* or *NOT FOUND* needs attention; send me a screenshot.
   - **Hours: website vs Google:** every day where Google's hours differ from what the website shows now. **Fix anything wrong in Google first**, because the website will switch to Google's hours in step 4.

The job saves the IDs to `data/google_places.json` and pushes them.

### Step 4: Turn it on

1. Go to **Actions → Sync hours from Google → Run workflow**.
2. The summary lists every change it made. Vercel redeploys about a minute later.
3. **In GitHub Desktop, click Fetch origin, then Pull origin**, so your Mac has the bot's changes.

From then on, it runs by itself every night.

---

## Good to know

- **Pull before you commit.** The nightly job pushes to GitHub on its own. Before committing site changes in GitHub Desktop, click **Fetch origin** and **Pull** if it offers. Otherwise your push will be rejected until you pull.
- **When Claude updates the site**, it first copies `data/hours_google.json` from your Mac, so a rebuild never undoes Google's hours.
- **Vercel says "deployment blocked"?** The job commits as the repo owner to avoid this. If it still happens:
  1. In Vercel, open **Project → Settings → Git → Deploy Hooks** and create a hook for `main`.
  2. Save its URL as a GitHub secret named `VERCEL_DEPLOY_HOOK`.
  The job will call it after each push.
- **Toast ordering hours are separate.** Keep Toast in line with Google by hand.
- **Adding a location later:**
  1. Add it to `data/content.py`.
  2. Run **Find Google place IDs** again. Existing IDs are kept; use *force* to re-check them all.
- **Turning the sync off:** delete `data/hours_google.json` and rebuild, or disable the workflow under Actions. The site goes back to the hours in `content.py`.

## Files

| File | What it does |
|---|---|
| `scripts/find_google_place_ids.py` | Finds each location's Google listing (one time) |
| `scripts/sync_google_hours.py` | Nightly: reads Google hours into `data/hours_google.json` |
| `data/google_places.json` | Location → Google place ID |
| `data/hours_google.json` | Latest hours from Google (written by the job; don't edit) |
| `.github/workflows/sync-hours.yml` | The nightly job |
| `.github/workflows/find-place-ids.yml` | The one-time lookup |
