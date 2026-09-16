# Square Peg Pizzeria: Launch Checklist

The site in `dist/` is ready to deploy. Work through this list before pointing squarepegpizzeria.com at it.

## 1. Toast setup (do this first)
- [ ] Confirm with your Toast rep that you can switch from **Toast Websites** to **Toast Online Ordering Pro** (or keep both), and what it costs.
- [ ] In Toast, connect the subdomain **order.squarepegpizzeria.com**. Toast needs these DNS records:
  - `order` CNAME → `sites.toasttab.com`
  - `_acme-challenge.order` CNAME → the value Toast gives you
- [ ] Open `order.squarepegpizzeria.com/order/<slug>` for each location and confirm it loads.
- [ ] Confirm the URL pattern Toast uses on the subdomain. The redirects assume the same paths as today (`/order/<slug>`, `/menu/<slug>`). If Toast uses different paths, update `redirect_map()` in `build.py`.
- [ ] In `data/content.py`, change:
  - `order_base` → `https://order.squarepegpizzeria.com/order/`
  - `menu_url` → the Toast menu or ordering URL on the subdomain
  - `gift_cards_url` → your Toast eGift card link
- [ ] Rebuild: `python3 build.py`

## 2. Fix these details (found during the build)
- [ ] **Hours don't match between your website and Toast ordering.** The new site uses the hours from your current /locations page. Confirm each location's hours (see the table below), then update `data/content.py`.
- [ ] **Storrs:** the Slice page (squarepegpizzeriastorrs.com) lists **(203) 220-4513** with 11am–9pm hours. Your site lists (860) 454-6038. Fix the Slice listing, or ask Slice to link to your site.
- [ ] **Storrs:** its Toast ordering slug is `squarepegwindsor`. It works, but consider renaming it in Toast (e.g. `square-peg-storrs`), then update `toast` in `content.py`.
- [ ] **East Hartford:** the Toast slug is misspelled (`square-peg-pizzera-east-hartford`). The address is "Long Hill **Rd**" on your current site and Yelp, but the US Census address database has no 130 Long Hill *Rd*; it matches **130 Long Hill St** (as Toast has it). The new site now uses **Long Hill St**. Fix Yelp and your Google Business Profile to match.
- [ ] **Shelton:** the address is **320** Howe Ave on your site but **310** in the Toast slug. Confirm which is right.
- [ ] **Berlin:** the Toast slug says **119** Webster Square Rd; the address is **151**. Confirm.
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
- [x] Square Peg Connect forms are embedded: Catering (also used on Food Truck), Large Reservations, Tuesday Fundraisers. Frame heights are set in `EMBEDS` in `content.py`.
- [ ] Walk through each embedded form on a phone and a laptop. If a step ever shows an inner scrollbar, raise that form's `mobile` / `desktop` height.
- [ ] In Connect, the location lists show 9 locations for large reservations and 8 for fundraisers. Confirm that's intended.
- [ ] If Connect has a way to post its height to the parent page, send the docs and the frames can auto-resize.
- [ ] **Contact form:** set up Supabase and email routing (see `DEPLOY_VERCEL.md`), then send a test message to every route.
- [ ] Have someone review the **privacy page** draft (`/privacy/`) before launch.

## 5. Tracking
- [ ] Add your GA4 ID (`ga4_id`) and Meta Pixel ID (`meta_pixel_id`) in `content.py`.
- [ ] Button clicks are already sent to `dataLayer`: `order_click`, `menu_click`, `call_click`, `directions_click`, `app_click`, `contact_submit`, `picker_open`. Each includes the location and source.
- [ ] Set up cross-domain measurement in GA4 for `squarepegpizzeria.com` + `order.squarepegpizzeria.com`, and verify both domains in Meta Business Manager so Toast purchases still attribute to ads.
- [ ] Re-check the `CateringFormSubmit` conversion event from your Meta campaigns: the catering URL changes from `/events-catering` to `/catering/` (a redirect is included).

## 6. Chatbot
- [ ] The Vendasta chat snippet is installed on every page, loaded about 2.5 seconds after the page finishes so it doesn't slow the first load. The URL contains `webchat-client..prod` (two dots), copied exactly as provided; confirm it matches your Vendasta dashboard.
- [ ] On phones, the bottom action bar leaves space on the right for the chat bubble. Check that they don't overlap once it's live.

## 7. Go live
- [ ] Deploy `dist/` (**not** `dist-staging/`, which is hidden from Google) to Vercel (see `DEPLOY_VERCEL.md`) or Netlify.
- [ ] Point the root domain and `www` to the host. **Don't touch the `order` records.**
- [ ] **301 redirects are built in**: `dist/vercel.json` for Vercel, `dist/_redirects` for Netlify, with the full list in `REDIRECTS.csv`. Every URL in your current Toast sitemap is covered:
  - Toast pages move to the subdomain on the same path: `/order/*`, `/menu/*`, `/account/*`, `/checkout/*`, `/cart/*`, `/confirm/*` → `order.squarepegpizzeria.com/...`. App links, COMO emails, QR codes, Google "Order" buttons and the 400+ indexed menu-item URLs keep working and keep their search value.
  - Old content pages go to their new equivalents: `/events-catering`, `/catering-*`, `/party-requests`, `/private-events` → `/catering/`; `/tuesday-charity-night` → `/fundraisers/`; `/monthly-deals`, `/promotions`, `/reward-program` → `/deals/`; `/gift-card(s)` → Toast gift cards; and so on.
  - `/contact`, `/about`, `/food-truck`, `/locations`, `/roll-the-dice` and `/sms-terms` keep their URLs. `/private-events` and `/party-requests` now point to the new **Large Party Reservations** page.
- [ ] After launch, spot-check 5 old URLs (including one `/order/...` link and one `/menu/...` item link) and confirm each returns **301** and lands on the right page.
- [ ] Any other host: `REDIRECTS.csv` has the same list (Cloudflare Pages reads `_redirects` as-is).
- [ ] Google Search Console: verify the domain, submit `https://squarepegpizzeria.com/sitemap.xml`.
- [ ] Google Business Profile, for each location: set the website to that location's page (e.g. `/locations/glastonbury-ct/`), and set the order link to its Toast page.
- [ ] Update Yelp, Apple Maps, Facebook and Slice listings to the same name, address, phone and hours.
- [ ] Run PageSpeed Insights on the home page and one location page after launch.
