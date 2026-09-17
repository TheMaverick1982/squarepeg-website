# Ranking in the towns around each store (15-mile plan)

**Goal:** show up in organic search for people in the towns within about 15 miles of each Square Peg, not just the store's own town.

**Short version:** the website now covers every nearby town honestly and usefully. The biggest remaining gains come from Google Business Profile, local links and reviews. Those need your team, not code.

## 1. What's built into the site

- **"Towns we serve" on every location page.** It lists every town within 15 miles, grouped under 5, 5–10 and 10–15 miles, under a heading like "Wood-fired pizza near Wethersfield, Rocky Hill, Portland & 31+ more towns". That's 23–40 towns per store.
- **A new `/areas-we-serve/` page.** It covers all 166 towns in CT, RI and South Florida. For each town it shows the closest Square Peg, how far it is, and one or two other nearby stores. It has a "type your town" search and a "use my location" button, and is linked from the footer and the Locations page.
- **Search data (schema).** Each restaurant now lists every nearby town as an area it serves, plus a 15-mile radius around the store.
- **llms.txt** (the file AI assistants read) lists each store's nearby towns.
- **The town list** lives in `data/service_areas.json`, built by `scripts/build_service_areas.py`. Rerun that script only when you add or move a location.
  - **Sources:** USPS town names (which include villages people actually use, like Mystic, Uncasville and Plantsville) and GeoNames town centers.
  - **Accuracy:** distances are straight-line, so they're shown in bands rather than exact miles.
  - **Preston:** its store coordinates are approximate until its exact location is added (see the launch checklist).

## 2. What we deliberately did *not* build

We did not build 160 near-identical "Pizza in [Town]" pages. Google's spam policies call this doorway abuse, giving "pages targeted at specific regions or cities that funnel users to one page" as an example ([Google spam policies](https://developers.google.com/search/docs/essentials/spam-policies)). Pages like that can pull the whole site down.

A town page is only worth making when it has content you can't find on the location page, such as:
- the real drive and parking
- game-day or event tie-ins
- group deals for local schools and teams
- photos from a local event

Good first candidates:

| Page | Store | Why |
|---|---|---|
| Pizza near UConn | Storrs | Students, parents, game days, reunions |
| Pizza near Mohegan Sun / Uncasville | Preston | Visitors looking for food off-property |
| Pizza near CCSU / New Britain | Berlin, Plainville | Students and campus events |
| Pizza near Boca Raton | Delray Beach | A big market next door |
| Pizza near Hartford / downtown offices | East Hartford, Glastonbury | Office lunch and catering pickup |
| Wood-fired food truck in [county] | Food truck | The truck really does travel to these towns |

Send a few facts per page (what locals ask, events you've done there, photos) and Claude will write each one.

## 3. Where the out-of-town rankings actually come from

### Google Business Profile (the map results)
- **Map results mostly depend on distance.** A store rarely appears in the map pack 15 miles away. Organic results (the website) and the signals below are how you reach further out.
- **Categories:**
  - Primary: *Pizza restaurant*.
  - Secondary, where true: *Italian restaurant*, *Caterer*, *Bar*.
- **Service areas:** a business that serves customers at its address and also delivers can list up to 20 service areas ([Google help](https://support.google.com/business/answer/9157481?hl=en)). Google doesn't say this affects ranking, but it helps people find you.
  - If a store delivers through Toast, add its biggest nearby towns.
- **Food truck:** if it doesn't have its own Business Profile, consider one set up as a service-area business with up to 20 towns. The truck really does go to customers.
- **Posts:** post weekly (events, specials, catering). Mention the town naturally when it's real, e.g. "Catered the Wethersfield Little League banquet this weekend".
- **Photos:** add photos regularly, including catering and truck events in nearby towns.
- **Reviews:**
  - Ask for them steadily, from the receipt, app and SMS.
  - Reviews that mention where people came from ("drove in from Manchester") help.
  - Reply to every review.
- **Links:** each profile's website link should go to its location page, and its menu and order links to the Toast subdomain (already in the launch checklist).

### Local links (the biggest organic lever)
- **Tuesday fundraisers are a built-in link machine.** Every school, PTO, team and nonprofit that books one should link to `/fundraisers/` or the store page from its website, newsletter or Facebook event. Add that ask to the confirmation email.
- **Sponsorships:** youth leagues, school programs and 5Ks in neighboring towns usually list sponsors with a link.
- **Chambers of commerce** in the regions around each store; members usually get a directory link.
- **Event listings:** food truck stops, pizza classes (Eventbrite), trivia and bingo nights. Post them to town event calendars, Patch, local news sites and brewery calendars.
- **Local press:** new store openings (Bolton), fundraiser totals and community events.

### Listings (consistency)
- **Same name, address, phone and hours everywhere:** Yelp, Apple Maps, Bing Places, Facebook, TripAdvisor, Slice, DoorDash, Uber Eats, Grubhub, ezCater.
- **Fix known mismatches first:** Shelton (310 vs 320 Howe Ave), Berlin (119 vs 151 Webster Square Rd) and East Hartford (Long Hill Rd vs St).
- **Bolton:** point old Parkside Pizza listings to Square Peg Bolton where possible.

## 4. How to measure

- **Search Console:**
  - Filter Performance → Queries by town names (e.g. "manchester", "wethersfield") and compare month over month.
  - Filter Pages to `/locations/…` and `/areas-we-serve/`.
- **Rank tracking:** a tracker such as Semrush, Ahrefs or a local grid-rank tool can check "pizza near me" style searches from points around each store. That shows how far out each store ranks.
- **Orders:** Toast delivery addresses and loyalty signups by ZIP show whether out-of-town customers are growing.

## 5. First 90 days

| When | What |
|---|---|
| Launch week | Location pages and Towns We Serve go live. Submit the sitemap and request indexing for the location pages and `/areas-we-serve/`. |
| Weeks 1–2 | Business Profiles: categories, service areas (delivering stores and the truck), website and order links, and fixing listing mismatches. |
| Weeks 2–4 | Add the link ask to fundraiser confirmations. List upcoming truck, class and trivia events on town calendars. |
| Month 2 | Write the first 2–3 town guides from section 2, with real local content. Start a weekly Business Profile post routine. |
| Month 3 | Review Search Console town queries and tracker results, then pick the next towns to push. |
