# Square Peg Pizzeria: Launch Checklist

The site in `dist/` is ready to deploy. Work through this list before pointing squarepegpizzeria.com at it.

## 1. Toast setup (do this first)
- [ ] Confirm with your Toast rep that you can switch from **Toast Websites** to **Toast Online Ordering Pro** (or keep both), and what it costs.
- [ ] In Toast, connect the subdomain **order.squarepegpizzeria.com**. Toast needs these DNS records:
  - `order` CNAME → `sites.toasttab.com`
  - `_acme-challenge.order` CNAME → the value Toast gives you
- [ ] Open `order.squarepegpizzeria.com/order/<slug>` for each location and confirm it loads.
- [ ] Confirm the URL pattern Toast uses on the subdomain. The redirects assume the same paths as today (`/order/<slug>`, `/menu/<slug>`). If Toast uses different paths, update `redirect_map()` in `build.py`.
- [ ] **The site is ready for the switch: it's one setting.** `TOAST_ON_SUBDOMAIN` at the top of `data/content.py` moves every Order, Menu and Gift Card button, the search data and `llms.txt` from `squarepegpizzeria.com/...` to `order.squarepegpizzeria.com/...`. The 301 redirects for old Toast URLs already point to the subdomain.
- [ ] If Toast uses different paths on the subdomain, or a different gift card link, change `TOAST_PATHS` (or `gift_cards_url`) in the same file.

### Launch day: switching Toast to the subdomain
1. **Connect the subdomain in Toast.** Toast connects `order.squarepegpizzeria.com` (DNS records above). Wait until it loads in a browser.
2. **Check the links.** In GitHub, go to **Actions → Check Toast links → Run workflow**. Every row should be ✅.
   - A ❌ with 403 can mean Toast blocks automated checks. Open that link yourself to confirm.
3. **Flip the switch.** In `data/content.py`, set `TOAST_ON_SUBDOMAIN = True`. Then rebuild and push:
   - `python3 build.py && python3 build.py --staging`, then push, or
   - ask Claude to do it.
4. **Move the main domain.** Point `squarepegpizzeria.com` and `www` to Vercel (section 8).
   - From then on, old links like `squarepegpizzeria.com/order/...` redirect (301) to the same page on the subdomain.
5. **Spot-check from a phone:**
   - an Order button
   - a Menu button
   - Gift Cards
   - one old `/order/...` link
   - one old `/menu-<town>` link

## 2. Fix these details (found during the build)
- [ ] **Turn on the Google hours sync** (`HOURS_SYNC.md`). After that, Google Business Profile is the only place to edit hours, and the "Hours: website vs Google" report shows every mismatch to fix first.
- [ ] **Hours don't match between your website and Toast ordering.** The new site uses the hours from your current /locations page. Confirm each location's hours (see the table below), then update `data/content.py`.
- [ ] **Storrs:** the Slice page (squarepegpizzeriastorrs.com) lists **(203) 220-4513** with 11am–9pm hours. Your site lists (860) 454-6038. Fix the Slice listing, or ask Slice to link to your site.
- [ ] **Storrs:** its Toast ordering slug is `squarepegwindsor`. It works, but consider renaming it in Toast (e.g. `square-peg-storrs`), then update `toast` in `content.py`.
- [ ] **East Hartford:** the Toast slug is misspelled (`square-peg-pizzera-east-hartford`). The address is "Long Hill **Rd**" on your current site and Yelp, but the US Census address database has no 130 Long Hill *Rd*; it matches **130 Long Hill St** (as Toast has it). The new site now uses **Long Hill St**. Fix Yelp and your Google Business Profile to match.
- [ ] **Shelton:** the address is **320** Howe Ave on your site but **310** in the Toast slug. Confirm which is right.
- [ ] **Berlin:** the Toast slug says **119** Webster Square Rd; the address is **151**. Confirm.
- [ ] **Rewards sign-up link:** the home page loyalty banner's "Sign up online" button uses `loyalty_signup` in `content.py` (currently `https://squarepegpizzeria.comosense.net/auth/signup`). Open it and confirm it's the right Como sign-up page, or paste the correct link. "Get the app" uses `app_link`.
- [ ] Map coordinates for 9 locations now come from the US Census geocoder and are included in each page's search data. **Preston** (353 CT-165) didn't match, so its search data has no coordinates. Copy its exact lat/lng from Google Maps into `content.py` and set `"geo_exact": True`.
- [ ] Review each location's blurb in `content.py`; they're written from what we know. Adjust local details freely.
- [ ] Confirm the best **catering phone number** (`catering_phone`; currently Glastonbury's) and the contact email (`email`: info@squarepegpizzeria.com).
- [ ] **Large parties:** if you have a minimum group size, deposit, or private-room details, add them to `LARGE_PARTY_FAQ` in `content.py`.
- [ ] Add your **Instagram** URL (`instagram`).
- [ ] Update the **monthly deal** in `DEAL` each month; the current one ends Sept 30.

| Location | Website hours (used) | Toast ordering hours (differ) |
|---|---|---|
| Storrs | Wed 10pm, Thu midnight, Fri–Sat 1am | Wed 9pm, Thu–Sat 10pm |
| Glastonbury | Mon 9pm, Wed 10pm, Fri 11:30am–midnight, Sun 9pm | Mon 10pm, Wed 9pm, Fri 11am–11pm, Sun 10pm |
| East Hartford | Wed 11am–8:30pm | Wed 8am–8:30pm |
| Berlin | Wed closed | Wed 4–10pm |
| Bolton | Wed–Sat 9pm | matches |

## 3. Brand assets
- [ ] The logo comes from your current site's logo file (transparent PNG). If you have an **SVG** version, send it; it will be sharper at every size. "PIZZERIA" is lightened on dark backgrounds so it stays readable.
- [ ] Send higher-res photos if you have them: interiors of each location, the team, the truck at events. Put them in `assets/img-src/` and set `photo` per location.
- [ ] Only use photos you own or have licensed. The "friends sharing pizza" and "friends at a holiday party" photos look like stock images; confirm you hold the license. The old site also had a watermarked Shutterstock thumbnail, which was left out.
- [ ] Review `/sms-terms/` against your current SMS terms page word for word; carriers check it.
- [ ] `/roll-the-dice/` says **appetizer only**. If drinks count too, update `DICE` in `content.py`.

## 4. Forms
- [x] Square Peg Connect forms are embedded: Catering (also used on Food Truck), Large Reservations, Tuesday Fundraisers.
- [ ] **Add `CONNECT_EMBED_SNIPPET.html` to the Connect app** (just before `</body>` in its `index.html`) and redeploy Connect. Each form then hides its logo inside the website and resizes itself on every step, with no extra white space. Until then, the site trims the logo and uses fixed heights (`EMBEDS` in `content.py`).
- [ ] **Catering is pickup-only.** The website never mentions catering delivery or setup. Note: the Fall catering campaign copy in this project (`Catering_Campaign_Suite_Fall_Holiday_2026.md`) still says "handles the count, the timing, and the setup". Update it to match.
- [ ] Review `/promotions/` and `/entertainment/`: the specials and weekly lineups were copied from the current site. Confirm they're still current, and whether any specials vary by location.
- [ ] In Connect, the location lists show 9 locations for large reservations and 8 for fundraisers. Confirm that's intended.
- [ ] **Contact form:** set up Supabase and email routing (see `DEPLOY_VERCEL.md`), then send a test message to every route.
- [ ] Have someone review the **privacy page** draft (`/privacy/`) before launch.

## 5. Tracking
- [ ] Add your GA4 ID (`ga4_id`) and Meta Pixel ID (`meta_pixel_id`) in `content.py`.
- [ ] Button clicks are already sent to `dataLayer`: `order_click`, `menu_click`, `call_click`, `directions_click`, `app_click`, `contact_submit`, `picker_open`. Each includes the location and source.
- [ ] Set up cross-domain measurement in GA4 for `squarepegpizzeria.com` + `order.squarepegpizzeria.com`, and verify both domains in Meta Business Manager so Toast purchases still attribute to ads.
- [ ] Re-check the `CateringFormSubmit` conversion event from your Meta campaigns: the catering URL changes from `/events-catering` to `/catering/` (a redirect is included).

## 6. Social sharing
- [x] Every page has its own branded 1200×630 share image (`/img/og/`) plus Open Graph and Twitter/X tags.
- [ ] After launch, paste a few URLs into the Facebook Sharing Debugger (developers.facebook.com/tools/debug) to refresh Facebook's cached previews.

## 7. Chatbot
- [ ] The Vendasta chat snippet is installed on every page, loaded about 2.5 seconds after the page finishes so it doesn't slow the first load. The URL contains `webchat-client..prod` (two dots), copied exactly as provided; confirm it matches your Vendasta dashboard.
- [ ] On phones, the bottom action bar leaves space on the right for the chat bubble. Check that they don't overlap once it's live.

## 8. Go live
- [ ] Deploy `dist/` (**not** `dist-staging/`, which is hidden from Google) to Vercel (see `DEPLOY_VERCEL.md`) or Netlify.
- [ ] Point the root domain and `www` to the host. **Don't touch the `order` records.** In Vercel, set `www.squarepegpizzeria.com` to **redirect (308) to `squarepegpizzeria.com`**, because Google still has old `www.` pages indexed (e.g. `/events/trivia-night`).
- [ ] **301 redirects are built in**: `dist/vercel.json` for Vercel, `dist/_redirects` for Netlify, with the full list in `REDIRECTS.csv`. Every URL in your current Toast sitemap is covered:
  - Toast pages move to the subdomain on the same path: `/order/*`, `/menu/*`, `/account/*`, `/checkout/*`, `/cart/*`, `/confirm/*` → `order.squarepegpizzeria.com/...`. App links, COMO emails, QR codes, Google "Order" buttons and the 400+ indexed menu-item URLs keep working and keep their search value.
  - Old content pages go to their new equivalents:
    - `/events-catering` and `/catering-*` → `/catering/`
    - `/party-requests` → `/large-party-reservations/`
    - `/tuesday-charity-night` → `/fundraisers/`
    - `/monthly-deals` and `/reward-program` → `/deals/`
    - `/gallery` → `/about/`
    - `/gift-card(s)` and the old `/popmenu-digital-gift-cards` → Toast gift cards
  - `/contact`, `/about`, `/entertainment`, `/food-truck`, `/locations`, `/private-events`, `/promotions`, `/roll-the-dice` and `/sms-terms` keep their URLs.
- [x] The redirects already set up in Toast (Website → Path redirects) are carried over: `/menu-<town>` goes straight to that store's ordering page, `/events/*` to Entertainment, `/party-request` to Large Parties, and `/popmenu-order` to the menu. Note: Toast currently sends `/menu-berlin` to the **Plainville** ordering page; the new site sends it to Berlin.
- [x] Vercel adds a trailing slash before redirects run, so every rule matches both `/old-page` and `/old-page/`.
- [ ] After launch, spot-check 5 old URLs (including one `/order/...` link and one `/menu/...` item link) and confirm each returns **301** and lands on the right page.
- [ ] Any other host: `REDIRECTS.csv` has the same list (Cloudflare Pages reads `_redirects` as-is).
- [ ] Google Search Console: verify the domain, submit `https://squarepegpizzeria.com/sitemap.xml`.
- [ ] Google Business Profile, for each location: set the website to that location's page (e.g. `/locations/glastonbury-ct/`), and set the order link to its Toast page.
- [ ] Update Yelp, Apple Maps, Facebook and Slice listings to the same name, address, phone and hours.
- [ ] Run PageSpeed Insights on the home page and one location page after launch.

## 9. Protect your Google rankings

**Ranking spot-check (Sept 17, 2026).** This was a rough check with an unlocalized search tool, not your real data.
- **Brand searches:** squarepegpizzeria.com shows up for "Square Peg Pizzeria + town", usually around positions 5–10. The Toast `/order/<slug>` pages rank for these the most, plus `/locations`, `/`, `/events-catering` and `/private-events`.
- **Generic searches:** for "pizza + town" and catering searches, the website itself doesn't appear. Those customers come through Google Maps (your Business Profiles), Yelp, Toast, DoorDash and Slice.
- **Takeaway:** the rebuild mainly has upside there, as long as the redirects and Business Profile links are right.

### Before launch
- [ ] **Get a baseline from Search Console.** Go to Performance → Search results → last 16 months → **Queries** and **Pages** tabs → Export, and also export the Pages (indexing) report. Send both to Claude, which will match every query and URL that gets clicks to its new page and redirect.
- [ ] **Confirm Toast keeps the same paths on `order.squarepegpizzeria.com`** (`/order/<slug>`, `/menu/<slug>`, item URLs). This is where most current brand rankings live.
- [ ] **Fix the unfinished page title on `vip.squarepegpizzeria.com`.** Google shows it as "{City} Appreciation Week | …". This is separate from the rebuild.
- [ ] **Bolton:** 4 of the top 10 results for "pizza bolton ct" still point to Parkside Pizza (Yelp, a Toast listing, parksidepizzact.com). Update or redirect those to Square Peg Bolton where you can.

### Launch week
- [ ] **Search Console:**
  - Submit the new sitemap.
  - Use URL Inspection → **Request indexing** for the home page and all 10 location pages.
- [ ] **Business Profiles:**
  - Website link → the location page.
  - Menu and order links → the Toast subdomain.
- [ ] **Request indexing** for `/areas-we-serve/` too, and work through `LOCAL_SEO_PLAN.md` (service areas, fundraiser link asks, event listings).

### First 4–6 weeks
- [ ] **Check Search Console → Pages → "Not found (404)" weekly.** Send any old URLs that show up there to Claude to add redirects.
- [ ] **Compare clicks and impressions with the baseline.** A dip for 2–4 weeks after a rebuild is normal; brand searches should recover first.
