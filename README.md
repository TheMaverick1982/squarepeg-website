# Square Peg Pizzeria website

A fast, static website for squarepegpizzeria.com. Ordering, menus and gift cards stay in **Toast** (on `order.squarepegpizzeria.com`); this site is everything around them. Its job is to get people to the right location's Toast page in as few taps as possible.

## What's in the folder

| Path | What it is |
|---|---|
| `dist/` | **The finished website.** Upload this folder to your host. |
| `data/content.py` | All the words, locations, hours, deals, links and settings. Most edits happen here. |
| `src/site.css`, `src/site.js` | Design and behavior. |
| `src/brand/` | Logo and favicon source files. |
| `assets/img-src/` | Original photos. Add new ones here. |
| `build.py` | Rebuilds `dist/` from the files above. |
| `dist-staging/` | Same site, hidden from Google, for team review on Vercel. |
| `supabase/` | Contact form table and the email-routing function. |
| `GO_LIVE.md` | **Start here:** the short, ordered list to get live, and who does what. |
| `LAUNCH_CHECKLIST.md` | The full detail behind it. |
| `DEPLOY_VERCEL.md` | GitHub → Vercel setup, forms, Supabase. |
| `REDIRECTS.csv` | Every old URL and where it now goes (301). |
| `HOURS_SYNC.md` | Hours come from Google Business Profile every night. Setup and how it works. |
| `scripts/`, `.github/workflows/` | The nightly Google hours sync, and the towns-within-15-miles builder. |
| `data/service_areas.json` | Towns within 15 miles of each store (used on location pages and `/areas-we-serve/`). |
| `LOCAL_SEO_PLAN.md` | How to rank in the towns around each store. |
| `SUPABASE_SETUP.md` | Contact form: Supabase, Resend emails, optional Turnstile and the weekly export. |
| `SECURITY_AND_BACKUPS.md` | Spam protection, security headers, what's backed up and how to restore. |

## Launch day: Toast moves to order.squarepegpizzeria.com
Set `TOAST_ON_SUBDOMAIN = True` at the top of `data/content.py`, rebuild and push. First run **Actions → Check Toast links** to confirm the subdomain works. Full steps are in `LAUNCH_CHECKLIST.md` section 1.

## Updating the site

1. In GitHub Desktop, click **Fetch origin** and **Pull** if it offers. The nightly hours job pushes changes on its own.
2. Edit `data/content.py` (for example, change the monthly `DEAL`).
   - **Hours:** once the Google sync is on, change them in Google, not here. See `HOURS_SYNC.md`.
3. Run `python3 build.py && python3 build.py --staging` (needs Python 3 and `pip3 install -r requirements.txt`).
4. Commit and push in GitHub Desktop; Vercel redeploys automatically.

## Pages

- `/`: home, with a quick "order from" picker, signature pies, all 10 locations with live open/closed status, catering, food truck, fundraisers, reviews and the app
- `/locations/` and `/locations/<town>/`: one page per location, each with its own hours, map, local story, FAQ and search data
- `/catering/`, `/large-party-reservations/`, `/food-truck/`: your booking-system form (embed)
- `/contact/`: contact form saved to Supabase, with emails routed by topic and location
- `/fundraisers/`: Tuesday Night Fundraiser requests (embed)
- `/our-menu/`: menu overview (pizza styles, pasta, parm sandwiches, salads, kids, desserts); live prices stay in Toast
- `/areas-we-serve/`: every town within 15 miles of a store, with its closest Square Peg
- `/deals/`: monthly deal and points shop
- `/roll-the-dice/`, `/about/`, `/sms-terms/`, `/privacy/`, `/thanks/`, `/404.html`

"Menu" and "Order" buttons open a location picker that sends guests to that location's Toast page.

## Built in

- **Speed:** no framework, CSS inlined, self-hosted fonts, AVIF/WebP images in several sizes, and a chat widget that loads after the page. Lighthouse (mobile): Performance 98–99, Accessibility 96–100, Best Practices 100, SEO 100.
- **SEO:** a unique title, description and H1 on every page; canonical URLs; Open Graph tags; structured data for Restaurant (one per location, with hours, address, order link and area served), Organization, FAQ and breadcrumbs; `sitemap.xml`, `robots.txt`, `llms.txt`; 301 redirects for every old URL.
- **Conversion:** a sticky Order button, a mobile action bar (Order / Call / Find us), the site remembering the guest's usual location, "closest to me" sorting, open-now badges, tap-to-call and directions, and click tracking sent to `dataLayer`.
- **Chatbot:** the Vendasta web chat on every page.
