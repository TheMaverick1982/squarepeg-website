"""
Square Peg Pizzeria — site content.
Everything the site says lives here. Edit this file, run `python3 build.py`, redeploy.
"""

import os

# ------------------------------------------------------------------ TOAST GO-LIVE SWITCH
# Today Toast serves ordering and menus on the main domain (squarepegpizzeria.com/order/...).
# At launch this website takes over the main domain and Toast moves to the order subdomain.
# On launch day set TOAST_ON_SUBDOMAIN = True, rebuild, push. That one change moves every
# Order / Menu / Gift card button, the search data and llms.txt to the subdomain.
# (The 301 redirects from old main-domain Toast URLs always point to the subdomain.)
# For a test build without editing this file: SP_TOAST_ON_SUBDOMAIN=1 python3 build.py --staging
TOAST_ON_SUBDOMAIN = True
TOAST_MAIN_DOMAIN = "https://squarepegpizzeria.com"          # where Toast lives today
TOAST_SUBDOMAIN = "https://order.squarepegpizzeria.com"      # where Toast lives after launch
# Paths on the Toast site. The redirects assume Toast keeps the same paths on the subdomain;
# confirm with Toast (LAUNCH_CHECKLIST.md) and change these if its paths differ.
TOAST_PATHS = {"order": "/order/", "picker": "/order", "menu": "/menu", "gift_cards": "/gift-cards"}
if os.environ.get("SP_TOAST_ON_SUBDOMAIN") in ("1", "0"):
    TOAST_ON_SUBDOMAIN = os.environ["SP_TOAST_ON_SUBDOMAIN"] == "1"
TOAST_HOST = TOAST_SUBDOMAIN if TOAST_ON_SUBDOMAIN else TOAST_MAIN_DOMAIN

SITE = {
    "name": "Square Peg Pizzeria",
    "domain": "https://squarepegpizzeria.com",
    # Where "Order" buttons go: TOAST_HOST + /order/<location's toast slug>. Set by the switch above.
    "order_base": TOAST_HOST + TOAST_PATHS["order"],
    "order_picker_toast": TOAST_HOST + TOAST_PATHS["picker"],
    # Menus live in Toast (per location, with live prices). "Menu" buttons open the location
    # picker and send guests to that location's Toast page. This is the fallback link.
    "menu_url": TOAST_HOST + TOAST_PATHS["menu"],
    # Toast eGift cards. If Toast gives you a different gift card link (e.g. https://www.toasttab.com/<slug>/giftcards),
    # replace this line with that full URL.
    "gift_cards_url": TOAST_HOST + TOAST_PATHS["gift_cards"],
    "email": "info@squarepegpizzeria.com",
    "app_link": "https://onelink.to/squarepeg-app",
    # "Sign in" in the header: the Toast ordering account (saved cards, past orders).
    # TODO confirm this is the right Toast account page once ordering is on the subdomain.
    "toast_account_path": "/account",
    "loyalty_signin": "https://squarepegpizzeria.comosense.net/auth/signin?callbackUrl=%2Fmember%2Frewards",
    # Rewards sign-up and sign-in are the same Como page.
    "loyalty_signup": "https://squarepegpizzeria.comosense.net/auth/signin?callbackUrl=%2Fmember%2Frewards",
    "careers": "/careers/",
    "careers_external": "https://jobs.squarepegpizzeria.com/careers",
    "careers_embed_src": "https://www.joinwingman.app/careers/square-peg-pizzeria?embed=1",
    # Pizza-making classes: tickets and upcoming dates (Eventbrite).
    "events_calendar_url": "https://www.eventbrite.com/o/square-peg-pizzeria-40036949473",
    "facebook": "https://www.facebook.com/squarepegpizzeria/",
    "instagram": "https://www.instagram.com/SquarePegPizzeria/",
    # No dedicated catering line: the catering form is the fastest route, or guests call their location.
    "catering_phone": "",
    "founded": "2020",
    # Chatbot (Vendasta web chat) — pasted verbatim from Square Peg.
    "chat_src": "https://cdn.apigateway.co/webchat-client..prod/sdk.js",
    "chat_widget_id": "c8ba1e1a-1e32-11f1-a953-6241c47b1fa1",
    # Contact form → Supabase (see supabase/contact_messages.sql and DEPLOY_VERCEL.md).
    # The anon key is public by design; the table only allows inserts.
    # Optional: send the contact form through the submit-contact Edge Function instead of
    # straight to the table, so a Cloudflare Turnstile check can be verified server-side.
    # Fill in both to switch it on (see SUPABASE_SETUP.md); leave blank to post to the table.
    "contact_endpoint": "",        # e.g. https://abcdefgh.functions.supabase.co/submit-contact
    "turnstile_site_key": "",      # Cloudflare Turnstile site key (public)
    "supabase_url": "https://ytkwogufrjffcgfpinrf.supabase.co",
    "supabase_anon_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl0a3dvZ3VmcmpmZmNnZnBpbnJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk3MDM5MDIsImV4cCI6MjEwNTI3OTkwMn0.TBUjxGEnpo-sv7Yinb1GKIKOW14R2o1sYq5B_5viDPA",
    # The Playground (/play/). Leave blank and the pages still render and still
    # read correctly — they just don't record anything, which is the right
    # failure mode. See supabase/POLLS_SETUP.sql.
    #
    # The Playground has its own Supabase project, separate from the one above
    # (which holds the contact form and its customer submissions). That split
    # is worth keeping: cast-vote is a public, unauthenticated endpoint, and
    # Everything the website stores lives in the website's own project, the
    # same one as supabase_url above. The polls spent their first weeks in
    # tsrnpmkipdbtwyrlfbuy, which is the Connect app's project — the system
    # behind connect.squarepegpizzeria.com. That was a mistake: the public
    # website should not read or write anything in there, and a function in
    # that project is handed that project's service-role key. Moved Oct 2026,
    # votes carried across.
    "vote_endpoint": "https://ytkwogufrjffcgfpinrf.supabase.co/functions/v1/cast-vote",
    "lab_endpoint": "https://ytkwogufrjffcgfpinrf.supabase.co/functions/v1/lab-submit",
    # Analytics — fill in to activate (left blank = nothing loads)
    "ga4_id": "G-REQKJC1SBJ",
    "meta_pixel_id": "",
}

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def h(mon, tue, wed, thu, fri, sat, sun):
    """Hours helper: each arg is ("11:30","21:00") or None for closed. Close past midnight = "01:00"."""
    return dict(zip(DAYS, [mon, tue, wed, thu, fri, sat, sun]))

# Hours below come from squarepegpizzeria.com/locations (Sept 2026).
# Several differ from the hours shown in Toast ordering — see LAUNCH_CHECKLIST.md.
LOCATIONS = [
    {
        "slug": "glastonbury-ct", "review_url": "https://g.page/r/CZzu2KdNLF0JEAE/review",
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Wed": "21:00", "Thu": "21:00", "Fri": "23:00"}, "name": "Glastonbury", "region": "Greater Hartford",
        "street": "1001 Hebron Ave", "city": "Glastonbury", "state": "CT", "zip": "06033",
        "phone": "(860) 286-0415", "toast": "square-peg-pizzeria",
        "lat": 41.717186, "lng": -72.574051, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","22:00"),("11:30","22:00"),("11:00","00:00"),("11:00","23:00"),("11:00","21:00"))),
        "tag": "Where it all started",
        "blurb": "Our first Square Peg. Glastonbury is where the wood-fired oven got lit in 2020, and it’s still where regulars come for date nights, team dinners, and the same pie they’ve ordered since day one.",
        "nearby": ["Wethersfield", "Rocky Hill", "Portland", "Hebron", "Marlborough"],
        "same_as": ["https://www.yelp.com/biz/square-peg-pizzeria-glastonbury-2"],
        "photo": "oven-pizza",
    },
    {
        "slug": "east-hartford-ct", "review_url": "https://g.page/r/CdU-gccb2zW6EAE/review", "menu_extra": ["Breakfast on weekends from 7am: omelettes and the Pegg & Cheese", "Brunch cocktails like mimosas, Bloody Marys and Aperol spritzes"], "name": "East Hartford", "region": "Greater Hartford",
        "street": "130 Long Hill St", "city": "East Hartford", "state": "CT", "zip": "06108",
        "phone": "(860) 509-4221", "toast": "square-peg-pizzera-east-hartford",
        "lat": 41.790362, "lng": -72.594171, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("11:00","22:00"),("11:00","20:30"),("11:00","20:30"),("11:00","22:00"),("11:00","20:30"),("07:00","20:30"),("07:00","22:00"))),
        "tag": "Breakfast on weekends",
        "blurb": "East Hartford is the one Peg serving breakfast: omelettes and the Pegg & Cheese from 7am on weekends. The rest of the week it’s the full Square Peg — wood-fired pizza, handmade pasta, parm sandwiches and a bar — on Long Hill Street, an easy stop off Route 2 or the Charter Oak Bridge.",
        "nearby": ["Hartford", "Manchester", "South Windsor", "Wethersfield", "Glastonbury"],
        "same_as": ["https://www.yelp.com/biz/square-peg-pizzeria-east-hartford"],
        "photo": "dough",
    },
    {
        "slug": "vernon-ct", "review_url": "https://g.page/r/Ca9plvDsyye4EAE/review",
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Wed": "21:00", "Thu": "21:00", "Fri": "23:00"}, "name": "Vernon", "region": "Greater Hartford",
        "street": "226 Talcottville Rd", "city": "Vernon", "state": "CT", "zip": "06066",
        "phone": "(860) 926-0088", "toast": "square-peg-pizzeria-vernon-226-talcottville-rd",
        "lat": 41.836661, "lng": -72.491494, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("12:00","20:00"),("12:00","20:00"),("12:00","21:00"),("12:00","21:00"),("12:00","23:00"),("11:00","23:00"),("11:00","20:00"))),
        "tag": "Open till midnight Fridays",
        "blurb": "Right on Talcottville Road (Route 83), Vernon is the easy stop for Rockville, Ellington and Tolland: pickup on the way home, or a late one on Friday when the oven runs until midnight.",
        "nearby": ["Rockville", "Ellington", "Tolland", "Manchester", "South Windsor"],
        "photo": "margherita-board",
    },
    {
        # "bar": False = no beer/wine/cocktails yet (liquor license pending); "detroit": False = no Detroit-style pizza yet. Remove each once available.
        # "wood": False = this is the one kitchen that is not wood-fired, so no page here says wood-fired.
        "slug": "bolton-ct", "review_url": "https://g.page/r/CWYf9GcLXaLlEBM/review", "bar": False, "detroit": False, "wood": False, "pastas": ["Chicken Parmesan", "Pasta alla Vodka", "Spaghetti & Meatballs", "The Bella Parmigiana"], "menu_extra": ["Burgers"], "name": "Bolton", "region": "Greater Hartford",
        "street": "270 West St", "city": "Bolton", "state": "CT", "zip": "06043",
        "phone": "(860) 791-7109", "toast": "square-peg-pizzeria-bolton-270-west-street",
        "lat": 41.742106, "lng": -72.436706, "geo_exact": True,  # US Census geocoder
        "hours": h(*(None,("11:00","20:00"),("11:00","21:00"),("11:00","21:00"),("11:00","21:00"),("11:00","21:00"),("11:00","20:00"))),
        "tag": "Newest Peg",
        "blurb": "Our newest Peg, on West Street in Bolton. Dough made fresh from scratch, never frozen, plus handmade pasta, parm sandwiches, wings and salads. A straightforward neighborhood spot — weeknight dinner with the family, or a pickup on the way through town.",
        "nearby": ["Manchester", "Coventry", "Andover", "Vernon", "Hebron"],
        "photo": "pizza-boxes",
    },
    {
        "slug": "storrs-ct", "review_url": "https://g.page/r/CVgVzNCipW3ZEAE/review", "sunday_ticket": True,
        # UConn campus payment, Storrs only. Flagged per location so no other
        # Peg ever advertises something it cannot take.
        "husky_bucks": True,
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Sun": "21:00", "Wed": "21:00", "Thu": "22:00", "Fri": "23:00", "Sat": "23:00"}, "name": "Storrs", "region": "Eastern CT",
        "street": "9 Dog Ln", "city": "Storrs", "state": "CT", "zip": "06268",
        "phone": "(860) 454-6038", "toast": "squarepegwindsor",
        "lat": 41.804999, "lng": -72.243305, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","21:00"),("11:30","00:00"),("11:00","00:00"),("11:00","23:00"),("11:00","21:00"))),
        "tag": "Steps from UConn",
        "blurb": "Our founders are UConn alumni, so Storrs Center feels like coming home. Dog Lane is where Husky fans land after the game and alumni reunions come together, and the kitchen runs late Thursday through Saturday.",
        "nearby": ["Mansfield", "Coventry", "Willington", "Ashford", "Tolland"],
        "photo": "friends-holiday",
    },
    {
        "slug": "preston-ct", "review_url": "https://g.page/r/CdzzsjM-nYI5EAE/review", "sunday_ticket": True,
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Wed": "21:00", "Thu": "21:00"}, "name": "Preston", "region": "Eastern CT",
        "street": "353 CT-165", "city": "Preston", "state": "CT", "zip": "06365",
        "phone": "(860) 319-0930", "toast": "square-peg-new-preston-353-connecticut-165",
        "lat": 41.528840, "lng": -71.982108, "geo_exact": True,  # exact pin from Google Maps
        "hours": h(*(("16:00","20:00"),("16:00","20:00"),("11:30","21:00"),("11:30","21:00"),("11:30","22:00"),("11:30","22:00"),("11:30","20:00"))),
        "tag": "Southeastern CT",
        "blurb": "On Route 165, Preston brings wood-fired pies to Norwich, Ledyard and the rest of the southeast corner of the state. It’s an easy dinner stop before or after a night at the casinos.",
        "nearby": ["Norwich", "Ledyard", "Griswold", "Lisbon", "North Stonington"],
        "photo": "table-spread",
    },
    {
        "slug": "plainville-ct", "review_url": "https://g.page/r/CRm0rKa4S61lEAE/review",
        "sunday_ticket": True,   # added Oct 2026 — Brian
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Wed": "21:00", "Thu": "21:00"}, "name": "Plainville", "region": "Central CT",
        "street": "400 New Britain Ave", "city": "Plainville", "state": "CT", "zip": "06062",
        "phone": "(860) 996-0363", "toast": "square-peg-plainville-400-new-britain-avenue",
        "lat": 41.671493, "lng": -72.833556, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("11:30","21:00"),("11:30","21:00"),("11:30","21:00"),("11:30","21:00"),("11:00","23:00"),("11:00","23:00"),("11:00","20:00"))),
        "tag": "Central Connecticut",
        "blurb": "Plainville is our Central CT kitchen, close to New Britain, Southington and Farmington. Drop in, pick up on the way home, or plan a party we can feed.",
        "nearby": ["New Britain", "Southington", "Farmington", "Bristol", "Berlin"],
        "same_as": ["https://www.yelp.com/biz/square-peg-pizzeria-plainville"],
        "photo": "oven-fire",
    },
    {
        "slug": "berlin-ct", "review_url": "https://g.page/r/CaLinkTYNBDbEBM/review", "pastas": ["Chicken Parmesan", "Pasta alla Vodka", "Pasta Bolognese", "Spaghetti & Meatballs"], "menu_extra": ["Hot dogs"], "kids_menu": False, "salads": False, "parm_line": "meatball parm and Italian combo sandwiches", "name": "Berlin Truck Bar", "short": "Berlin", "region": "Central CT",
        "street": "151 Webster Square Rd", "city": "Berlin", "state": "CT", "zip": "06037",
        "phone": "(860) 505-4072", "toast": "square-peg-pizza-berlin-119-webster-square-road",
        "lat": 41.628734, "lng": -72.745911, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("16:00","21:00"),None,None,("16:00","22:00"),("11:00","23:00"),("11:00","23:00"),("11:00","19:00"))),
        "tag": "The Truck Bar",
        "blurb": "Berlin is our Truck Bar on Webster Square Road: brick-oven pizza, sandwiches, wings and a bar with an easy, hang-out feel. Come in for a weekend afternoon or a game night.",
        "nearby": ["Kensington", "New Britain", "Cromwell", "Newington", "Meriden"],
        "photo": "truck-tent",
    },
    {
        "slug": "shelton-ct", "review_url": "https://g.page/r/CSSSW9EazyNFEAE/review", "sunday_ticket": True,
        # Kitchen closes before the bar on these days (from the store hours).
        "kitchen": {"Wed": "21:00", "Thu": "21:00", "Fri": "22:00", "Sat": "22:00"}, "name": "Shelton", "region": "Fairfield & New Haven",
        "street": "320 Howe Ave, Unit 6", "city": "Shelton", "state": "CT", "zip": "06484",
        "phone": "(203) 538-5044", "toast": "square-peg-shelton-310-howe-avenue-unit-6",
        "lat": 41.314898, "lng": -73.091125, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("16:00","21:00"),("16:00","21:00"),("16:00","21:00"),("16:00","21:00"),("12:00","23:00"),("11:30","22:00"),("11:30","20:00"))),
        "tag": "Downtown Shelton",
        "blurb": "Our Fairfield County outpost on Howe Avenue, a short walk from the Riverwalk. Shelton brings the Square Peg oven to Derby, Stratford and the Valley.",
        "nearby": ["Derby", "Ansonia", "Stratford", "Trumbull", "Monroe"],
        "photo": "friends-sharing",
    },
    {
        "slug": "delray-beach-fl", "review_url": "https://g.page/r/CdcNVlETKllxEAE/review", "sunday_ticket": True, "name": "Delray Beach", "region": "Florida",
        "street": "4957 W Atlantic Ave", "city": "Delray Beach", "state": "FL", "zip": "33445",
        "phone": "(561) 566-8828", "toast": "square-peg-delray-beach-4957-west-atlantic-avenue",
        "lat": 26.457838, "lng": -80.12169, "geo_exact": True,  # US Census geocoder
        "hours": h(*(("12:00","21:00"),("12:00","21:00"),("12:00","21:00"),("12:00","21:00"),("12:00","22:00"),("12:00","22:00"),("12:00","20:00"))),
        "tag": "Connecticut pizza in Florida",
        "blurb": "Connecticut pizza, Florida sunshine. Delray Beach has its own kitchen making dough and sauce from scratch, the same way East Hartford does for our Connecticut Pegs. On West Atlantic Avenue, our Delray Peg feeds snowbirds who missed their Glastonbury pie and locals who are just finding out what the fuss is about.",
        "nearby": ["Boynton Beach", "Boca Raton", "Lake Worth Beach", "Highland Beach"],
        "photo": "kid-slice",
    },
]

# "Sal" — the pairing assistant. The widget is a third-party embed (same SDK as the
# floating chat, different widget id), so the page suppresses the floating one to
# avoid two instances of the SDK on one page. Everything below the widget is real
# content: the page has to be worth landing on even if the widget fails to load.
PAIRING = {
    "widget_id": "ea5ec150-73e8-11f1-b4c7-6291690b83e2",
    "lede": "Tell Sal what you\u2019re ordering, who\u2019s at the table, or just what kind of night "
            "it is. You\u2019ll get a drink that actually fits \u2014 not a list of everything we pour.",
    "asks": [
        "What should I drink with a pepperoni pizza?",
        "We\u2019re splitting a white pizza and wings \u2014 one bottle for the table?",
        "Something that isn\u2019t beer, but isn\u2019t sweet either.",
        "First date. Don\u2019t let me order wrong.",
        "What goes with the fried eggplant?",
        "I like bourbon. Build me a dinner around that.",
    ],
    "steps": [
        ("Tell Sal what\u2019s on the table",
         "A pizza, a pasta, a whole order for four. However you\u2019d say it out loud."),
        ("Get a real recommendation",
         "One or two options, with the reason behind them \u2014 not a wine list dumped on your lap."),
        ("Order it",
         "Bring the answer to your server, or start an order online and work from there."),
    ],
    # House pairings, written as guidance rather than specific bottles, because the
    # list varies by location. Keep these honest — they are the SEO content here.
    "classics": [
        ("Pepperoni", "A hoppy IPA",
         "Pepperoni renders out a lot of fat and a fair amount of heat. Hop bitterness scrubs the "
         "fat off your palate between bites, so the last slice tastes like the first one did."),
        ("Margherita", "A dry Italian red, or a dry ros\u00e9",
         "A simple pie lives or dies on the tomato. You want acid to meet acid \u2014 a wine with "
         "some bite keeps the sauce bright instead of flattening it out."),
        ("A white pizza", "A crisp, unoaked white",
         "No tomato means no acid on the plate, so the glass has to bring it. Something lean and "
         "cold cuts through the cream and cheese rather than piling richness on richness."),
        ("Anything with chili or hot honey", "An off-dry white, or a cold lager",
         "A touch of sweetness takes the edge off capsaicin. High alcohol does the opposite \u2014 "
         "it makes heat burn hotter, which is why a big red is the wrong move here."),
        ("Wings", "A cold lager",
         "Carbonation and cold are doing the work. You want something that resets your mouth and "
         "gets out of the way, not a beer that competes with the sauce."),
        ("Handmade pasta", "A medium-bodied red",
         "Enough structure to stand next to a long-cooked sauce, enough acidity to keep a heavy "
         "bowl from turning into a nap."),
    ],
}

# The link-in-bio page. Ordered by what actually earns a tap from a social profile:
# ordering first, then the thing being promoted right now, then the booking paths.
# Keep this under about a dozen rows — a long list gets scrolled past, not read.
# ("Label", "destination", "sub-label or empty", "accent" True for the primary rows)
# Rows are (label, destination, subtitle, highlight) — or six, adding
# (show_from, show_until) as ISO dates to make a row seasonal. The browser hides
# it outside that window against Eastern time, so a dated row drops off by
# itself without anyone rebuilding or remembering to take it down. Either date
# may be None.
LINKS = [
    ("Order Online", "ORDER", "Pickup or delivery from any location", True),
    # The costume contest. Live now so the Instagram bio link works through the run-up,
    # and gone by itself the morning after Halloween. HALLOWEEN is defined
    # further down this file so it can't be referenced here — instead there is
    # an assert below its definition that fails the build if these two dates
    # ever drift apart.
    ("Square Peg Costume Contest", "/halloween/", "Win a $25 gift card at your location",
     True, None, "2026-10-31"),
    # The holiday gift card bonus. Live from today so the bio link works through
    # the run-up — the page carries its own "Starts November 1" notice until the
    # buy window opens — and gone by itself on New Year's Day, when the offer
    # retires. The end date is checked against GIFT_BOUNCE further down.
    ("Holiday Gift Card Bonus", "/gift-card-bonus/", "Buy $100 in store, get a $20 voucher",
     True, None, "2026-12-31"),
    ("Find a Location", "/locations/", "Ten spots across CT and Delray Beach", False),
    ("This Month\u2019s Specials", "/monthly-specials/", "The limited-time menu, gone at the end of the month", True),
    ("Ask Sal: What Should I Drink?", "/pairing/", "Our pairing guide, free to use", False),
    ("Deals & Rewards", "/deals/", "Join free and start with $5 off", True),
    ("Gift Card Giveaway", "https://go.squarepegpizzeria.com/GC", "Enter this month\u2019s $50 drawing", False),
    ("Ongoing Promotions", "/promotions/", "Pasta, wings, wine and happy hour", False),
    ("Catering", "/catering/", "Office lunches, parties, game days", False),
    ("Tuesday Night Fundraisers", "/fundraisers/", "20% back to your school, team or cause", False),
    ("Large Party Reservations", "/large-party-reservations/", "Tables for eight or more", False),
    ("Food Truck Rentals", "/food-truck/", "Wood-fired pizza at your event", False),
    ("Gift Cards", "GIFT", "Send one in a minute", False),
    ("We\u2019re Hiring", "/careers/", "Every location, every shift", False),
]

# Pizza calculator. Sizes and slice counts come from MENU["pizza_styles"] — keep them
# in step. The math is area-based rather than a flat "3 slices each" rule, because an
# 18" slice is roughly 1.7x the area of a 12" slice and a flat rule badly under-orders
# for big pies. Appetite values are in square inches of pizza per person.
CALC = {
    "sizes": [
        # label, diameter/description, slices, area in square inches
        ("18\u2033 large round", "18\u2033", 8, 254),
        ("12\u2033 small round", "12\u2033", 6, 113),
        ("Detroit-style pan", "10\u00d714\u2033", 6, 140),
    ],
    "appetites": [
        ("light", "Light \u2014 a slice or two", 48),
        ("normal", "Normal \u2014 most people", 70),
        ("hearty", "Hearty \u2014 teenagers, game day", 95),
    ],
    "kid_area": 36,          # a child eats roughly half an adult portion
    "sides_discount": 0.80,  # apps, salads and wings take ~20% off the pizza needed
    "catering_threshold": 20,
    "notes": [
        ("Rounds come two ways", "A 12\u2033 round cuts into 6 slices, an 18\u2033 into 8. The large isn\u2019t "
         "just two more slices \u2014 it\u2019s more than twice the pizza, because area grows with the square "
         "of the diameter."),
        ("Detroit sits in between", "The 10\u00d714\u2033 pan is 6 thick, crispy-edged squares. It eats heavier "
         "than a round of the same area, so it goes further than the numbers suggest. Available at every "
         "location except Bolton."),
        ("Order one more than feels right", "Leftover pizza is a feature. Running out in front of your "
         "guests is not, and a second round of ordering adds half an hour to the night."),
        ("Mixed crowds round up", "Kids eat about half an adult portion, but they also eat unpredictably. "
         "If the split is close, take the larger number."),
    ],
}

# FAQ hub. Every answer has to be true for US — sizes come from MENU["pizza_styles"],
# food-safety numbers from USDA guidance. Generic pizza-blog filler loses to pizza blogs;
# the only edge here is answering as the people who actually make it.
PIZZA_FAQ = [
    ("Sizes & servings", [
        ("How many slices are in a large pizza?",
         "Ours is an 18\u2033 round cut into 8 slices. The 12\u2033 round is cut into 6, and the Detroit-style "
         "pan is 6 squares. Slice counts vary wildly between pizzerias \u2014 always ask by diameter, not by "
         "the word \u201clarge.\u201d"),
        ("How many people does a large pizza feed?",
         "Three to five adults if pizza is the whole meal, and more if there are appetizers on the table. "
         "An 18\u2033 pie is about 254 square inches, so each of its 8 slices is roughly 70% bigger than a "
         "slice off a 12\u2033. Our <a href=\"/pizza-calculator/\">pizza calculator</a> does the arithmetic."),
        ("Is a large pizza twice the size of a small?",
         "No \u2014 it\u2019s more than twice. Area grows with the square of the diameter, so going from a "
         "12\u2033 to an 18\u2033 gives you about 2.25 times the pizza, not 1.5 times. Two smalls are less "
         "food than one large."),
    ]),
    ("Reheating & leftovers", [
        ("Can you reheat wood-fired pizza?",
         "Yes, and a skillet beats a microwave every time. Put the slice in a dry pan over medium heat for "
         "about three minutes, then add a few drops of water to the pan away from the slice and cover it for "
         "another minute. The base re-crisps while the steam melts the cheese. A microwave does the opposite: "
         "it steams the crust soft."),
        ("How long does leftover pizza keep?",
         "USDA guidance for cooked leftovers is three to four days refrigerated, within two hours of coming "
         "off the table. Pizza is no exception, however convincing it looks on the counter the next morning."),
        ("Can you freeze pizza?",
         "You can. Wrap slices individually so they don\u2019t fuse, and reheat from frozen in a skillet or a "
         "hot oven rather than thawing first \u2014 thawed crust goes limp."),
    ]),
    ("Cheese, sauce & styles", [
        ("What\u2019s the difference between mozzarella and fresh mozzarella?",
         "Low-moisture mozzarella is aged and drier, so it browns, stretches and behaves predictably under "
         "high heat. Fresh mozzarella is packed in water or brine, has a milkier flavor and a softer texture, "
         "and releases moisture as it melts \u2014 which is why a Margherita made with it has those wet, "
         "creamy pools rather than an even blanket. Neither is better; they do different jobs."),
        ("What is a white pizza?",
         "A pizza built without tomato sauce. The base is usually cheese, cream, oil or garlic, which means "
         "there\u2019s no acidity on the plate to cut the richness \u2014 worth knowing when you pick a drink "
         "to go with it."),
        ("What is Detroit-style pizza?",
         "A thick rectangular pan pizza with cheese taken right to the edges, so it caramelizes against the "
         "hot pan and forms a crisp, chewy border. Ours is a 10\u00d714\u2033 pan cut into 6, available at "
         "every location except Bolton."),
        ("What does wood-fired actually change?",
         "Heat and speed. A wood-fired oven runs far hotter than a home oven and cooks a pie in minutes rather "
         "than tens of minutes, which puts char on the crust before the inside dries out. That\u2019s where the "
         "leopard-spotting and the chew come from."),
    ]),
    ("Ordering", [
        ("Do you have gluten-free pizza?",
         "We make a 12\u2033 gluten-free crust, and vegan cheese can go on any pizza. One honest caveat: our "
         "kitchens handle wheat flour all day, so we can\u2019t promise a coeliac-safe environment. If you "
         "have a serious allergy, tell your server and they\u2019ll walk you through what we can and can\u2019t "
         "guarantee."),
        ("How far ahead should I order for a party?",
         "For a handful of pies, the same day is usually fine. For a crowd, or anything on a Friday or "
         "Saturday evening, give us a day \u2014 and for twenty people or more, <a href=\"/catering/\">catering</a> "
         "is normally cheaper and arrives hot together rather than in waves."),
        ("Can I order a half-and-half pizza?",
         "On a round, yes \u2014 ask when you order. The Detroit pan is built differently and doesn\u2019t "
         "split as cleanly."),
    ]),
]

# Pizza trivia. Where a well-known story is disputed, say so — being the page that gets it
# right is more useful than being the hundredth page repeating the myth.
PIZZA_TRIVIA = {
    "facts": [
        ("The word is older than the dish you\u2019re picturing",
         "\u201cPizza\u201d turns up in a Latin document from Gaeta, in southern Italy, dated 997 AD \u2014 "
         "nearly eight centuries before tomatoes appeared on one. It referred to a flatbread.",
         True),
        ("Naples got UNESCO status for it",
         "In 2017 UNESCO added the art of the Neapolitan \u201cpizzaiuolo\u201d to its list of intangible "
         "cultural heritage \u2014 protecting the craft of making it, not the recipe.",
         True),
        ("Tomatoes were considered dangerous",
         "Europeans grew tomatoes as ornamental plants for two centuries before eating them, partly because "
         "the acid leached lead out of pewter plates and poisoned wealthy diners. The poor ate off wood, and "
         "ate tomatoes.",
         True),
        ("Pepperoni is an American invention",
         "Order pepperoni in Italy and you may get peppers \u2014 \u201cpeperoni\u201d is the Italian for "
         "bell peppers. The spicy cured sausage is Italian-American, and it is comfortably the most ordered "
         "topping in the United States.",
         True),
    ],
    "myths": [
        ("Queen Margherita inspired the Margherita",
         "The story \u2014 that Raffaele Esposito built a red, white and green pizza for Queen Margherita of "
         "Savoy in 1889 \u2014 is repeated everywhere, including by us until we looked into it. The supporting "
         "document has been challenged by historians as a likely forgery, and pizzas with those toppings were "
         "already being sold in Naples. Lovely story. Probably not history."),
        ("Pineapple is an Italian outrage",
         "Hawaiian pizza was invented in Ontario, Canada, in 1962, by a Greek-born restaurateur. Italy was "
         "never consulted and has nothing to do with it either way."),
        ("Authentic pizza must be thin and crispy",
         "A true Neapolitan base is soft and foldable in the middle with a puffed, blistered rim \u2014 not "
         "cracker-crisp. The crisp-throughout style is a later, largely American development."),
    ],
}

# "What pizza are you?" — results map to real menu items only, so every result can link
# straight to an order. Each answer carries a score for each result key.
QUIZ = {
    "results": {
        "spicy-margherita": ("Spicy Margherita", "pie-spicy-margherita",
            "You like a little trouble. Cherry peppers, spicy capicola, fresh mozzarella and basil \u2014 "
            "familiar enough to be comforting, hot enough to keep you honest."),
        "margherita": ("Margherita", "pie-margherita",
            "You have nothing to prove. Fresh mozzarella, tomato and basil, fire-kissed. The one that exposes "
            "a bad pizzeria and rewards a good one."),
        "prince": ("Prince of Paramus", "pie-prince-of-paramus",
            "You order like you mean it. House pork meatballs, mushrooms, mozzarella and tomato sauce \u2014 "
            "dinner, not a snack."),
        "bianco": ("Bianco", "pie-bianco",
            "You read the whole menu before deciding. Goat cheese, ricotta, garlic, maple and Calabrian chili "
            "oil \u2014 sweet, sharp and a bit contrary."),
        "detroit": ("Detroit-style", "pie-detroit",
            "You\u2019re in it for the edges. A thick 10\u00d714\u2033 pan with the cheese taken right to the "
            "rim so it caramelizes against the metal. At every location except Bolton."),
    },
    "questions": [
        ("It\u2019s Friday at 7pm. Where are you?", [
            ("At the bar, ordering a second one", {"spicy-margherita": 2, "detroit": 1}),
            ("A corner table with one other person", {"margherita": 2, "bianco": 1}),
            ("At home, box on the coffee table", {"detroit": 2, "prince": 1}),
            ("Somewhere loud with six friends", {"prince": 2, "spicy-margherita": 1}),
        ]),
        ("Pick a problem with most pizza.", [
            ("Not enough heat", {"spicy-margherita": 3}),
            ("Too much going on", {"margherita": 3}),
            ("Not enough food", {"prince": 2, "detroit": 1}),
            ("Too predictable", {"bianco": 3}),
        ]),
        ("The best part of the slice is\u2026", [
            ("The crust", {"detroit": 2, "margherita": 1}),
            ("The cheese pull", {"detroit": 1, "bianco": 2}),
            ("Whatever\u2019s on top", {"prince": 2, "spicy-margherita": 1}),
            ("The char", {"margherita": 2, "spicy-margherita": 1}),
        ]),
        ("Your drink order says a lot.", [
            ("Cold lager, no thinking required", {"detroit": 2, "prince": 1}),
            ("Whatever the bartender suggests", {"bianco": 2, "margherita": 1}),
            ("A red with some backbone", {"prince": 2, "margherita": 1}),
            ("Something with a kick in it", {"spicy-margherita": 2}),
        ]),
        ("Someone suggests splitting a pizza. You\u2026", [
            ("Agree, then order your own anyway", {"prince": 2, "detroit": 1}),
            ("Suggest two and leftovers", {"detroit": 2, "prince": 1}),
            ("Happily \u2014 you want room for dessert", {"margherita": 2, "bianco": 1}),
            ("Only if they let you pick", {"spicy-margherita": 2, "bianco": 1}),
        ]),
        ("Last one. A night out should be\u2026", [
            ("Easy", {"margherita": 2, "detroit": 1}),
            ("Interesting", {"bianco": 3}),
            ("Loud", {"spicy-margherita": 2, "prince": 1}),
            ("Filling", {"prince": 3}),
        ]),
    ],
}

# Date night page. Everything here is true of our own rooms — no recommending other
# businesses, which is what makes a local guide a maintenance burden and a liability.
DATE_NIGHT = {
    "lede": "No reservation anxiety, no tasting menu, no performance. A fire, a bottle and "
            "something that came out of the oven four minutes ago.",
    "reasons": [
        ("The oven does the talking",
         "Wood-fired pies cook in minutes, so food arrives while you\u2019re still on the first drink \u2014 "
         "not forty minutes into a conversation that had started to flag."),
        ("Splitting is the point",
         "A pizza, a pasta and something fried in the middle of the table beats two plates and a silence. "
         "Order three things and share all of them."),
        ("It costs what it costs",
         "You can have a very good night here for the price of two entr\u00e9es somewhere with a tasting menu, "
         "and nobody has to pretend to be impressed."),
        ("Nobody is rushing you",
         "The kitchen runs late most nights, and longer on football days. Stay for dessert."),
    ],
    "order": [
        ("Start", "Something fried to share while you look at the rest of the menu. It buys you ten minutes "
                  "of not deciding anything."),
        ("Middle", "One round pizza between two is plenty if you\u2019ve started with an appetizer. Pick one "
                   "red and one white if you\u2019re getting two \u2014 they taste different enough to be worth it."),
        ("Drink", "Friday is half-price bottles after 5pm. Happy hour runs 2\u20136pm every day at every "
                  "location with a bar. Not sure what goes with what? "
                  "<a href=\"/pairing/\">Ask Sal</a>."),
        ("End", "Dessert, and the argument about who\u2019s paying."),
    ],
}

REGIONS = ["Greater Hartford", "Central CT", "Eastern CT", "Fairfield & New Haven", "Florida"]

# Monthly member deal. Each entry is date-gated in the browser (Eastern time,
# both ends inclusive), so next month's promo can be staged ahead of its start
# date and swaps itself in overnight. Keep them in chronological order and make
# sure the windows don't overlap — two live at once would both render.
import datetime as _dt

DEALS = [
    {
        "eyebrow": "Loyalty members only",
        "headline": "$6 off when you spend $36+",
        "detail": "Monday–Friday, dine-in. One use per member. Not valid with other offers. Tax & gratuity not included.",
        "starts": "2000-01-01",
        "expires": "2026-09-30",
        "expires_label": "Ends Sept 30",
    },
    {
        "eyebrow": "Loyalty members only",
        "headline": "$8 off when you spend $38+",
        "detail": "Monday–Friday, dine-in. One use per member. Not valid with other offers. Tax & gratuity not included.",
        "starts": "2026-10-01",
        "expires": "2026-10-31",
        "expires_label": "Ends Oct 31",
    },
    # November: back to the September offer, which outperformed October's.
    {
        "eyebrow": "Loyalty members only",
        "headline": "$6 off when you spend $36+",
        "detail": "Monday–Friday, dine-in. One use per member. Not valid with other offers. Tax & gratuity not included.",
        "starts": "2026-11-01",
        "expires": "2026-11-30",
        "expires_label": "Ends Nov 30",
    },
]
# Legacy single-deal reference. Resolves to whichever deal is live today rather
# than DEALS[0], which is the September one and has been expired since 1 Oct:
# no template uses this now, but one that did would have shown a dead offer.
_today = _dt.date.today().isoformat()
DEAL = next((d for d in DEALS if d["starts"] <= _today <= d["expires"]), DEALS[-1])

POINTS = [
    (100, "Free cookie"), (200, "$5 off"), (300, "Free appetizer", "excludes wings"),
    (350, "Any pasta dish"), (400, "Any small pizza"), (500, "Large specialty pizza"),
    (600, "$25 reward card"), (1000, "$50 reward card"),
]

APP_PERKS = ["$5 off your next order", "Exclusive in-app deals", "Flash promos", "Rewards every visit"]

SIGNATURES = [
    ("Spicy Margherita", "Cherry peppers, spicy capicola, fresh mozzarella, basil", "pie-spicy-margherita"),
    ("Margherita", "Fresh mozzarella, tomato sauce & basil. The classic, fire-kissed", "pie-margherita"),
    ("Prince of Paramus", "House pork meatballs, mushrooms, mozzarella, tomato sauce", "pie-prince-of-paramus"),
    ("Bianco", "Goat cheese, ricotta, garlic, maple & Calabrian chili oil", "pie-bianco"),
]

# Menu overview for /our-menu/ and location pages. Taken from the Toast online menus (Sept 2026).
# No prices here: Toast has the live menu and prices for each location.
MENU = {
    "pizza_styles": [
        ("Neo-Neapolitan rounds", "12″ (6 slices) or 18″ (8 slices), red or white. Wood-fired at every location except Bolton."),
        ("Detroit-style", "Thick, crispy-edged 10×14″ pan pizza (6 slices). At every location except Bolton."),
        ("Gluten-free", "12″ gluten-free crust on any round pie. Vegan cheese on any pizza."),
    ],
    "sections": [
        ("Pasta", "pasta", [
            ("Chicken Parmesan", "Breaded chicken, house-made sauce and mozzarella over pasta."),
            ("Pasta alla Vodka", "Rigatoni in a garlic tomato cream sauce with vodka and basil, finished with Calabrian chili oil."),
            ("Pasta Bolognese", "Pappardelle in a traditional beef and pork tomato cream sauce."),
            ("Shrimp Scampi", "Sautéed shrimp and spaghetti in a creamy white wine, lemon and garlic sauce."),
            ("Spaghetti & Meatballs", "Two jumbo house-made pork meatballs, marinara and parmesan."),
            ("The Bella Parmigiana", "Crispy eggplant over spaghetti with parmesan and marinara."),
        ]),
        ("Parm sandwiches & Italian subs", "sandwiches", [
            ("Chicken Parm", "Crispy chicken, marinara and mozzarella on toasted bread."),
            ("Meatball Parm", "House-made pork meatballs, marinara, mozzarella and parmesan."),
            ("Eggplant & Ham Parm", "Crispy eggplant and ham with marinara and mozzarella."),
            ("Italian Combo", "Prosciuttini, ham, spicy capicola, fresh mozzarella and red wine vinaigrette."),
            ("The Hot Honey Eggplant", "Crispy eggplant with a sweet-heat hot honey finish."),
        ]),
        ("Starters & wings", "starters", [
            ("House-made pork meatballs", "Two jumbo meatballs with pecorino romano and our sauce."),
            ("Calamari", "Plain or loaded."),
            ("Honey bruschetta", "A sweet-and-savory take on the classic."),
            ("Fried mozzarella & garlic bread", "The two starters every table fights over."),
            ("Wood-fired wings", "Sauced (BBQ, hot honey, buffalo, Carolina gold) or dry-rubbed."),
        ]),
        ("Salads", "salads", [
            ("Caesar", "Romaine, croutons, shaved pecorino, Caesar dressing."),
            ("House", "Romaine, cucumber, red onion, fennel, roasted tomatoes, parmesan, red wine vinaigrette."),
            ("Chef, market greens & more", "Add chicken, shrimp, salmon or prosciutto."),
        ]),
        ("Kids' meals", "kids", [
            ("Kids pasta, spaghetti & meatballs, pasta alla vodka", "Smaller portions of the grown-up favorites."),
            ("Chicken fingers & mac and cheese", "The reliable ones."),
        ]),
        ("Beer, wine & cocktails", "drinks", [
            ("Cocktails", "Margaritas, spritzes and house specialties, shaken to go with pizza and pasta."),
            ("Beer", "Draft and bottled beer, including local picks."),
            ("Wine", "Reds and whites by the glass or bottle."),
        ]),
        ("Desserts", "desserts", [
            ("New York-style cheesecake", "In a graham cracker crust."),
            ("Gelato sandwiches & Italian sorbet", "A cool finish after the wood-fired oven."),
            ("Fried dough, brownies & warm cookies", "Chocolate chip cookies topped with sea salt."),
        ]),
    ],
    "drinks_note": "Beer, wine and cocktails are served at every Square Peg except Bolton.",
    "note": "Menus vary a little by location and change with the seasons. Your Square Peg’s online menu always has the current items and prices.",
}

# Real reviews shown on the current squarepegpizzeria.com homepage.
REVIEWS = [
    ("I’m not a big fan of pizza, but I will tell you this pizza, I can eat a whole small one by myself. That’s how good it is. My kids absolutely love their food.", "Cliff"),
    ("The crust was exactly what I love: thin and airy but had a great bite and chew. It wasn’t greasy, and the mozzarella was tasty.", "Olga"),
    ("Best vegan cheese pizza I’ve ever had. Life changing for someone who can’t have dairy!", "Jessica"),
]

FUNDRAISER_FAQ = [
    ("Does takeout count?", "Yes, as long as supporters phone the order through to the restaurant. Dine-in and called-in pickup both count. An order placed on our website doesn’t — it never gets attached to your group — and nor does anything through a third-party delivery app like DoorDash, Uber Eats or Grubhub. Worth putting in your own invite in those words."),
    ("How do supporters make their purchase count?", "They order from the location you booked, on your Tuesday, any time from 4pm to close — dining in, or calling the restaurant to arrange a pickup — and tell whoever takes the order that they’re supporting your organization. Pickup has to be phoned in; an order placed on our website can’t be credited to you."),
    ("How much does our organization earn?", "20% of qualifying food sales, excluding tax and alcohol. We total everything at the end of the night and send the donation after the event."),
    ("How many organizations can book a night?", "One organization per location per Tuesday. If your date is taken, we’ll add you to our priority waiting list."),
    ("What do we get to promote it?", "A custom digital flyer and social-ready graphics made by our team. Server tracking and sales reporting are handled by us."),
]

# ---------------------------------------------------------------- Catering
# Square Peg does NOT deliver and does NOT set up. Everything is pickup, from any
# of the ten locations. Nothing on the site may imply otherwise — see
# Catering_Launch_Runbook_Fall2026.md, where the ads were rewritten for the same
# reason. The food truck is the one exception: it travels, and it is booked
# through the same form.
# The three ways a group can eat with us, and the honest basis for choosing one.
# This table is the most useful thing on any of the event pages: most people
# arrive not knowing which of the three they actually want.
EVENT_ROUTES = [
    ("Come to us", "Large party reservation",
     "Ten or more at one of our tables. We save the seats and plan the food so it "
     "lands together instead of in waves.", "/large-party-reservations/"),
    ("We cook, you collect", "Pickup catering",
     "Trays of pasta, wings, salads, sandwiches and dessert, plus pizza. Ready "
     "boxed at the time you agreed. No minimum.", "/catering/"),
    ("We come to you", "The food truck",
     "A real wood-fired oven on wheels, cooking pies in front of your guests. "
     "The only one of the three where we turn up.", "/food-truck/"),
    ("Your cause, our Tuesday", "Tuesday fundraiser",
     "Come in on a Tuesday and 20% of food sales goes back to your school, "
     "team or cause.", "/fundraisers/"),
]

# The Pizza Lab at /play/pizza-lab/. Launched Oct 2026: the ingredient lists
# were rebuilt from the 10.12.26 menu, submissions go to lab-submit in the
# website's own Supabase project, and the three of us get a digest every Monday.
#
# Setting this False again pulls it from the nav, the Playground hub and the
# sitemap and puts noindex back on the page, without touching anything that has
# already been submitted.
# Live Oct 2026: on the main menu, in the sitemap, indexable, and on the
# Playground hub. Brian is promoting it.
LAB_LIVE = True

TRUCK = {
    "party_min": "10 or more",
    "season": "May through October",
    # PRIVATE EVENTS ONLY. Square Peg no longer carries itinerant vending licenses,
    # so the truck cannot sell to the public at festivals, markets or brewery
    # events — Carla, Oct 2026. Nothing on the site may imply otherwise.
    "private_only": "The truck does private events only. We don\u2019t carry the vending "
                    "licence to sell to the public at festivals, markets or brewery "
                    "events, so every booking is a private party, school, company or "
                    "wedding.",
    "events": ["Weddings and rehearsal dinners", "Graduation parties",
               "School and team events", "Corporate days and office parties",
               "Block parties and backyard birthdays", "Anniversaries and reunions"],
    # NO PER-PERSON PRICING ON THE SITE — Brian, Oct 2026. The packages are listed by
    # what is on them so a guest can picture the event; the numbers come from the
    # catering manager's estimate after the form, which is also how leads stay in our
    # system. The $1,000 minimum is the one figure Brian approved publishing, because
    # it saves everyone a conversation that was never going to work.
    "min_guests": "50",
    "small_min": "20",
    "small_charge": "$1,000",
    "packages": [
        ("2 hours",
         "A house or Caesar salad, meatballs, and an all-you-can-eat buffet of three "
         "pizza varieties."),
        ("3 hours",
         "A salad, a charcuterie board and meatballs, and four pizza varieties."),
        ("3\u00bd hours",
         "Both salads, charcuterie, meatballs, caprese and shrimp skewers, and four "
         "pizza varieties."),
        ("4 hours",
         "All of the above plus two pastas \u2014 marinara, alla vodka, Bolognese or mac "
         "and cheese \u2014 and bite-size sea salt chocolate chip cookies."),
    ],
    "small_party": "Under 50 guests we run a 20-guest package with a $1,000 minimum "
                   "charge: a salad and an all-you-can-eat pizza buffet \u2014 cheese, "
                   "pepperoni, margherita and one specialty of your choice.",
    "addons": "Meatballs, crostini, wings and bite-size cookies.",
    "price_note": "Pricing is per person and depends on the package, the headcount and "
                  "the date. Send the form and our catering manager will come back with "
                  "the menus and a written estimate.",
    "custom": "Don\u2019t see something you like? We can customize anything.",
    "steps": [
        ("Send the form",
         "Date, where it is, and roughly how many people. Choose Food truck "
         "private service when the form asks."),
        ("We email you the menus",
         "Our catering manager sends the packages and the pizza list first, so you "
         "have the detail in front of you before anyone picks up the phone."),
        ("We plan it, then the oven rolls up",
         "We go through the package, the timing and any dietary needs, then we park, "
         "fire up and cook in front of your guests."),
    ],
    # The comparison people actually need. Both columns are true, which is the point.
    "vs": [
        ("Where the food is made", "In our kitchen", "In front of your guests"),
        ("How it arrives", "You collect it, boxed and hot", "We drive it to you"),
        ("What\u2019s on it", "The full tray menu plus pizza",
         "Set packages, customizable"),
        ("Minimum", "None", "50 guests, or 20 with a $1,000 minimum"),
        ("Best for", "Offices, parties, anything on a schedule",
         "Weddings, graduations and private parties where the food is part of the show"),
    ],
}

# Only questions we can answer honestly. Radius, minimums, deposits and weather
# are all decided job by job, so they route to the conversation rather than to a
# number we would end up breaking.
TRUCK_FAQ = [
    ("How far ahead should I book the food truck?",
     "As early as you have a date. May through October is the busy stretch and "
     "Saturdays go first — summer weekends are often spoken for months out. Off "
     "season there is usually more room, so it is always worth asking."),
    ("Can you come to a festival, a market or a brewery?",
     "No. The truck is for private events only — we don’t carry the vending license "
     "needed to sell to the public, so we can’t take a spot at a public event. A "
     "private party at that venue is a different thing, and that we can do."),
    ("How far will the truck travel?",
     "It depends on the date and the job, so we would rather not publish a radius "
     "we would have to break. Send the form with where you are and when, and we "
     "will give you a straight answer."),
    ("Is there a minimum number of guests?",
     "Yes. The standard packages start at 50 guests. Below that we run a 20-guest "
     "package with a $1,000 minimum charge, so a smaller party is still possible — "
     "it just has a floor."),
    ("What is on the truck menu?",
     "Set packages, from a two-hour buffet with a salad, meatballs and three pizza "
     "varieties up to a four-hour spread with charcuterie, skewers, pastas and "
     "dessert. Pizza is wood-fired Neo-Neapolitan, red or white, and we can "
     "customize anything — our catering manager emails you the full menus when "
     "you send the form."),
    ("Can you handle gluten-free or vegan guests?",
     "Yes. We have a 12″ gluten-free crust and vegan cheese. Tell us the numbers "
     "when we talk and we will plan for them properly rather than improvising on "
     "the day."),
    ("What do you need from us on the day?",
     "Somewhere to park and set up — a driveway, a lot or a flat piece of lawn. "
     "We go through space and access with you before the date so there are no "
     "surprises when the truck pulls in."),
    ("Can we book the truck and pickup catering together?",
     "Yes, and for bigger events it is often the right answer: the truck cooks "
     "pizza in front of your guests while trays of salad, pasta and dessert come "
     "from the kitchen. Mention both on the form."),
]

# The guest-facing half of the fundraiser program.
#
# /fundraisers/ sells the idea to the organiser: how it works, how to book a
# Tuesday. The people that organiser then emails are supporters, and they need a
# completely different page — what to do on the night, and what does and doesn't
# count. This is the URL that goes in their newsletter and on their website,
# which also makes it the page that collects the local backlinks.
#
# Rules here must stay identical to FUNDRAISER_FAQ. If one changes, change both.
FUNDRAISER_NIGHT = {
    "share": "20%",
    "window": "4pm to close",
    "steps": [
        ("Come in on their Tuesday",
         "The one date and the one Square Peg your group named — not just any "
         "Tuesday, and not whichever location is closest. Any time from 4pm to "
         "close. No ticket, flyer or reservation needed."),
        ("Dine in or take it home",
         # No HTML in here: the step body is rendered with {{ }}, which escapes it,
         # so a <b> comes out as literal &lt;b&gt; on the page. Say it in words.
         "Both count, with one catch. A pickup order has to be phoned through to "
         "the restaurant — an order placed on our website never gets attached to "
         "the group, so it won’t count. Nor will anything through DoorDash, Uber "
         "Eats, Grubhub and the like."),
        ("Say who you’re with",
         "Tell your server, the person at the counter, or whoever picks up the "
         "phone. That’s the whole mechanism — nobody can credit an order to your "
         "group unless somebody is told."),
    ],
    "counts": ["Food eaten in, or picked up when the order was phoned through",
               "The one Tuesday your group booked, 4pm to close",
               "The Square Peg they named — each location runs its own night",
               "Any size order — a table of twenty or one pizza"],
    "excluded": ["Pickup ordered on the website instead of over the phone",
                 "DoorDash, Uber Eats, Grubhub and other delivery apps",
                 "A different Tuesday, or a different Square Peg",
                 "Alcohol",
                 "Tax and tip"],
    "faq": [
        ("Do I need a flyer or a code?",
         "No. Just say which group you’re supporting when you order."),
        ("Does takeout count?",
         "Yes — but call the restaurant to place it. Dine-in and phoned-in pickup "
         "both count. A pickup order put through the website doesn’t, because that "
         "order never gets attached to the group, and nor does anything booked "
         "through a delivery app."),
        ("What time should we come?",
         "Any time from 4pm to close, on the specific Tuesday the group booked. "
         "Earlier is usually quieter if you’re bringing small children."),
        ("What if I go on a different Tuesday, or to another location?",
         "It won’t count. Each Square Peg hosts one organization per Tuesday, so "
         "the donation is tied to that date at that restaurant. Check the invite "
         "for which one before you set off."),
        ("Does my drink count?",
         "Soft drinks are food sales and count. Alcohol doesn’t, and neither does "
         "tax or tip."),
        ("How much goes to the group?",
         "20% of qualifying food sales across the whole night. We total it "
         "up after close and send the donation to the organization."),
        ("Can I come if I’m not part of the group?",
         "Yes, and please do. Anyone who orders that night and mentions the group "
         "adds to their total."),
    ],
}

CATERING = {
    # ⚠ CONFIRM BEFORE PUSHING. Worked from the real tray prices on the catering
    # sheet, not guessed: a full tray feeds 40–50, so pasta ($151) + salad ($116)
    # + wings ($151) + cookies ($203) is $621, i.e. $12.42–15.53 a head. Swap the
    # pasta for chicken parm and it is $13.64–17.05. A lighter spread — pasta,
    # salad, garlic bread — comes in at $7.20–9.00.
    "per_head": "$12–18",
    "per_head_note": "That is a full spread — a pasta, a salad, wings and dessert. "
                     "Keep it lighter and it lands nearer $8.",
    "lead_time": "48 hours",
    "tray_half": "20–25",
    "tray_full": "40–50",
    "steps": [
        ("Send the form",
         "Date, headcount, which Square Peg, and anything we should know — allergies, "
         "a vegetarian table, a crowd of teenagers."),
        ("Our catering manager calls you",
         "One person, for all ten locations. They go through the menu with you, size "
         "the trays to your headcount and send an estimate."),
        ("Pick it up hot",
         "Boxed and waiting at the time you agreed, at the location you chose. "
         "Nothing to set up, nothing to send back."),
    ],
    # His own sheet: HALF TRAY serves 20–25, FULL TRAY serves 40–50.
    "feeds": [
        ("20–25", "Half trays", "Two or three dishes plus a dessert covers it"),
        ("40–50", "Full trays", "Same spread, one size up"),
        ("75–100", "Two full trays of each", "Worth a call — this one we plan properly"),
    ],
    "menu": [
        ("Starters", "Bone-in wings and boneless tenders in six flavours, cheesy garlic "
                     "bread, fried mozzarella, house-made pork meatballs, shrimp cocktail."),
        ("Salads", "House, Caesar, chef, market greens, and the Beet Dropper with goat "
                   "cheese, pistachios and crispy prosciutto."),
        ("Pastas", "Pasta alla vodka, spaghetti & marinara, Bolognese, shrimp scampi, "
                   "macaroni & cheese."),
        ("Add a protein", "Chicken parm, eggplant parm, roasted or fried chicken, "
                          "meatballs, salmon, shrimp — on top of any pasta tray."),
        ("Sandwich platters", "Ten or twenty on toasted rolls, up to four kinds: chicken "
                              "parm, Italian combo, meatball parm, turkey, BLT, hot honey "
                              "eggplant and more."),
        ("Desserts", "Cookie platters, fudge brownies, New York cheesecake, and fried "
                     "dough bites with Nutella."),
        ("Pizza", "Added from the regular menu. One 18″ round feeds about three and a "
                  "half adults, so a crowd of 50 is around fourteen pies."),
    ],
    "wing_flavors": "BBQ · Hot Honey · Buffalo · Peg Seasoning (garlic parm) · "
                    "Sweet & Smoky Dry Rub · Carolina Gold Mustard",
    "truck": "The food truck is the one thing that does come to you. Same form, "
             "choose Food truck as the event type.",
}

CATERING_FAQ = [
    ("How far ahead should I book catering?", "The earlier the better, especially October through December. Send the form with your date and headcount and we’ll confirm availability."),
    ("Can you cater at every location?", "Yes. Catering is available from all Square Peg locations. Choose the one closest to you, and your order will be ready for pickup there."),
    ("Do you have gluten-free or dairy-free options?", "Yes. We offer a 12″ gluten-free crust and vegan cheese. Tell us in the notes and we’ll plan for it."),
    ("Can the food truck come to our event?", "Yes. Book the Square Peg food truck for parties, schools, corporate events and fundraisers using the same form. Choose “Food truck” as the event type."),
    ("Do you deliver catering?", "No. Every catering order is pickup, from the Square Peg you choose. We’d rather tell you that up front than promise a van and a chafing dish we don’t have. If you need us on site, book the food truck instead — that one really does come to you."),
    ("Is there a minimum order?", "No minimum and no headcount floor. Ten people or a hundred, we’ll size it with you."),
    ("What’s the largest order you can do?", "There’s no hard ceiling with enough notice. Tell us the date and the number and we’ll tell you straight away whether that kitchen can take it on that day."),
    ("How many pizzas do I need?", "About one 18″ pie for every three and a half adults, which is where the table on this page comes from. If it’s a teenage or game-day crowd, work on two and a half. Our pizza calculator will do the arithmetic for you."),
    ("What does catering cost?", "Most orders land somewhere around $12–18 a head once you add wings, salad and dessert; pizza on its own is closer to $7. Your estimate comes from our catering manager after you send the form, so you see a real number before you commit to anything."),
    ("How do I pay?", "Our catering manager goes through it with you when they send the estimate."),
    ("Can I change the headcount after I book?", "Yes, within reason and with notice. Numbers move — tell us as soon as you know and we’ll adjust the order."),
]

SMS_TERMS = [
    ("Program", "Square Peg Pizzeria offers a recurring SMS messaging program to keep you informed about exclusive promotions and deals, upcoming events and entertainment, order confirmations, and loyalty and rewards updates."),
    ("Program name", "Square Peg Pizzeria SMS Alerts."),
    ("Message frequency", "Message frequency varies. You may receive up to 8 messages per month depending on your activity and location."),
    ("Message and data rates", "Message and data rates may apply. Check with your mobile carrier for details on your messaging plan."),
    ("How to opt out", "You may opt out of our SMS program at any time. Reply STOP, CANCEL, END, QUIT, or UNSUBSCRIBE to any message from us. You will receive one final confirmation message confirming your opt-out. No further messages will be sent after that."),
    ("How to get help", "Reply HELP to any message for assistance. You may also contact us directly at info@squarepegpizzeria.com or (860) 286-0415."),
    ("Supported carriers", "Available on all major US carriers. Carrier availability may vary."),
    ("Consent is not required for purchase", "Opting into our SMS program is never required to make a purchase, use our services, or participate in our rewards program."),
    ("Data sharing", "No mobile information will be shared with third parties or affiliates for marketing or promotional purposes. All categories exclude text messaging originator opt-in data and consent. This information will not be shared with any third party."),
    ("Privacy", "For full details on how we handle your personal information, see our Privacy Policy at squarepegpizzeria.com/privacy/."),
]

DICE = {
    "headline": "Roll doubles. Win pizza.",
    "when": "Monday–Thursday, until 4:00 PM, at every Square Peg",
    "how": [
        ("Order any full-price appetizer", "Monday through Thursday, before 4pm."),
        ("Roll two dice at your table", "Your server brings the dice. You roll."),
        ("Match them and win", "Any double wins a free small cheese pizza, right then. Double sixes win a $20 gift card for your next visit."),
    ],
    "odds": "Your odds of rolling a double are one in six.",
    "terms": "One roll per guest, per visit, with the purchase of any full-price appetizer. Free small cheese pizza is one per loyalty member and must be redeemed on the same visit; not transferable, no substitutions. Gift card is issued on the spot for use on a future visit. Valid Monday–Thursday until 4:00 PM at participating Square Peg Pizzeria locations. Not valid with any other offer, discount, or loyalty reward. House dice only; a team member must witness the roll. Employees and immediate family are not eligible. Management may end the promotion at any time.",
}

# ---------------------------------------------------------------------------
# Embedded forms from Square Peg Connect (connect.squarepegpizzeria.com).
# Once Connect has the embed snippet (CONNECT_EMBED_SNIPPET.html), each form reports its own
# height and resizes itself on every step, with no logo and no extra white space.
# Until then: "crop" hides Connect's logo header, and "mobile"/"desktop" are fixed frame
# heights (px) that fit the tallest step.
EMBEDS = {
    "catering": {"src": "https://connect.squarepegpizzeria.com/public/catering",
                 "title": "Square Peg catering request form", "crop": 196, "mobile": 1230, "desktop": 1210},
    "large_party": {"src": "https://connect.squarepegpizzeria.com/public/large-reservations",
                    "title": "Square Peg large reservation request form", "crop": 196, "mobile": 680, "desktop": 660},
    "fundraiser": {"src": "https://connect.squarepegpizzeria.com/public/fundraisers",
                   "title": "Square Peg Tuesday fundraiser request form", "crop": 196, "mobile": 680, "desktop": 660},
    "kids_class": {"src": "https://connect.squarepegpizzeria.com/public/kids-classes",
                   "title": "Square Peg kids pizza-making class request form",
                   "crop": 196, "mobile": 800, "desktop": 800},
}
EMBEDS["food_truck"] = EMBEDS["catering"]

LARGE_PARTY_FAQ = [
    ("What counts as a large party?", "Ten or more. At that point tables have to be moved and the kitchen wants a heads-up, so send a request rather than turning up and hoping. Birthdays, team dinners, showers, reunions, office parties — we’ll confirm what works for your group size and date."),
    ("Do all locations take large party reservations?", "Yes. Space is different at every Square Peg, so we’ll confirm the best setup for your group at the location you choose."),
    ("Can we plan the food ahead of time?", "Yes. Tell us what you have in mind in your request and we’ll plan it with you, so everything hits the table hot and together."),
    ("Do you have gluten-free or dairy-free options?", "Yes. We offer a 12″ gluten-free crust and vegan cheese. Mention any dietary needs in your request."),
    ("How far ahead should we book?", "As early as you can, especially for Friday and Saturday nights and during the holidays."),
    ("Would a fundraiser work better for our group?", "If you’re raising money for a school, team or nonprofit, a Tuesday Night Fundraiser earns 20% of food sales for your cause."),
]

CONTACT_TOPICS = [
    "General question", "Feedback about a visit", "Catering", "Large party reservation", "Food truck",
    "Kids pizza-making class", "Team night",
    "Fundraiser", "Gift cards", "Rewards / app help", "Jobs", "Media or partnership",
]

# ---------------------------------------------------------------------------
# Weekly entertainment (from squarepegpizzeria.com/entertainment). Day, event, time.
ENTERTAINMENT = {
    "plainville-ct": [("Mon", "Bingo", "6–8pm"), ("Wed", "Trivia", "6:30–8:30pm"), ("Fri", "DJ", "7–10pm")],
    "shelton-ct": [("Tue", "Bingo", "6–8pm")],
    # A 4th value is an optional start date: the event shows with a "from <date>" badge until
    # then, and the badge disappears on its own once the date passes (no rebuild needed).
    # Tidy up by deleting the 4th value whenever you're next in here.
    "vernon-ct": [("Wed", "Trivia", "6:30–8:30pm"), ("Sat", "Bingo", "6–8pm", "2026-09-26")],
    "east-hartford-ct": [("Thu", "Bingo", "6:30–8:30pm"), ("Sat", "Bingo", "6:30–8:30pm")],
    "glastonbury-ct": [("Wed", "What Trivia", "6:30–9pm")],
    "preston-ct": [("Thu", "Trivia", "7–9pm"), ("Sun", "Bingo", "6pm")],
    "storrs-ct": [("Wed", "Trivia", "6:30–8:30pm"), ("Fri", "DJ", "10pm–close"), ("Sat", "DJ", "10pm–close")],
    "delray-beach-fl": [("Sun", "Jackpot Bingo", "4–6pm"), ("Mon", "Bingo", "6:30–8:30pm"), ("Wed", "Trivia", "7–9pm")],
}

# Ongoing promotions (from squarepegpizzeria.com/promotions).
PROMOS = {
    "daily": [
        ("Tuesday", "Pasta Night", "$15", "After 5pm. Carb up, wind down."),
        ("Wednesday", "Wing Night", "$1 per wing", "After 5pm. You bring the appetite, we bring the heat."),
        ("Friday", "Wine Night", "½-price bottles", "After 5pm. Because you survived the week."),
    ],
    "lunch": [
        ("2 slices + drink", "Cheese or pepperoni."),
        ("1 slice + salad + drink", "Cheese or pepperoni, with a fresh salad."),
    ],
    "lunch_note": "$10 each. Monday–Friday, 11am–2pm where open, dine-in.",
    # Happy hour runs at every location with a bar (Bolton has none yet, so it's
    # gated on the location's "bar" flag). Deals aren't published yet — when they
    # are, add them as a list here and they'll render under the times.
    "happy_hour": {"days": "Every day", "time": "2–6pm", "deals": []},
    "app": [
        ("Refer a friend, get $10", "Invite a friend through the Square Peg app. When they join, a $10 reward lands in your app wallet. Limit one referral reward per month."),
        ("Rewards Club: $10 a month", "Pay $10 a month and get $20 in Square Peg credit, loaded automatically. Sign up in the app. Monthly credits expire in 30 days."),
        ("Load money, get rewarded", "Load $20, get $22. Load $50, get $55. Load $100, get $110. Bonus credit to use in the restaurant."),
    ],
    "punch": [
        ("Buy 6 pizzas, get a free large pizza", "Lunchtime only, until 3pm"),
        ("Buy 6 sandwiches, get the 7th free", "Lunchtime only, until 3pm"),
        ("Buy 6 desserts, get the 7th free", "Anytime"),
    ],
    "app_perks": ["$5 welcome reward", "App-only flash sales (lunch, dinner & more)", "Lunch specials & hero discounts", "Surprise drops & birthday perks"],
    "heroes": "Active duty service members, veterans and first responders (police, firefighters, EMTs) get 15% off their meal. Just show a valid military, veteran or first responder ID. You serve the community. Let us serve you.",
}

# ---------------------------------------------------------------- GAME DAY (football season)
# The page lives at /game-day/ all year, but the nav link, home banner and the specials
# themselves only show between these dates. The window is checked in the browser, so the page
# turns itself on and off without a rebuild. Next season: move both dates forward.
GAME_DAY = {
    "season_from": "2026-09-01",
    "season_to": "2027-02-15",          # a week after the Super Bowl
    "season_label": "2026–27 football season",
    "tagline": "Come for the game. Stay for the pizza.",
    # Headline deals, shown as a band. These run during games only.
    "band": [
        ("$4", "Green Tea shots", "During football games", "band-shot"),
        ("$7", "Game day cocktails", "During football games", "band-cocktail"),
        ("$4", "Miller Lite", "During football games", "band-miller"),
    ],
    "cocktails_price": "$7 each",
    "cocktails": [
        ("The Blitz", "Transfusion", ["Vodka", "Grape juice", "Fresh lime", "Ginger ale"], "Cherry garnish"),
        ("The Hail Mary", "Dark 'n' Stormy", ["Captain spiced rum", "Fresh lime", "Ginger beer"], "Lime garnish"),
        ("Sack Attack", "Blue margarita", ["Tequila", "Triple sec", "Fresh lime juice", "Blue curaçao"], "Lime garnish"),
        ("Touchdown Tea", "John Daly", ["Vodka", "Iced tea", "Lemonade"], "Lemon garnish"),
    ],
    "mocktails_price": "$5 each",
    "mocktails": [
        ("The Extra Point", "", ["Orange juice", "Pineapple juice", "Fresh lemon juice", "Club soda", "Grenadine"], "Cherry garnish"),
        ("The Rookie", "", ["Orange juice", "Cranberry", "Pineapple juice", "Sprite"], "Lime garnish"),
    ],
    # NFL Sunday Ticket for Business, via EverPass. Add "sunday_ticket": True to a location
    # in LOCATIONS as each store's equipment goes in.
    "sunday_ticket_note": "More Square Pegs will have the Sunday Ticket soon.",
    "pizza_price": "$15 small · $26 large",
    "pizzas": [
        ("The White Out", "gd-white-out", "Chicken bacon ranch",
         ["Parm cream", "Mozzarella", "Chicken", "Bacon", "Ranch drizzle", "Green onions"]),
        ("The Red Zone", "gd-red-zone", "Loaded red",
         ["Red sauce", "Mozzarella", "Pepperoni", "Sausage", "Roasted red peppers", "Ricotta"]),
    ],
}

# ---------------------------------------------------------------------------
# Ticketed events at a single location (paint nights, tastings, fundraisers).
#
# Keyed by location slug. Each event shows on that location's page from
# `announce` until the end of `date` (Eastern time), then hides itself — no
# rebuild, no one having to remember to take it down. Delete the entry
# whenever you're next in here.
#
#   date     ISO date of the event. Also the last day the block shows.
#   announce ISO date the block starts showing. Omit to show immediately.
#   meta     Short facts shown as a row: time, price, what's included.
#   url      Where tickets are sold. cta is the button label.
#   host     Optional credit for an outside host/partner.
# ---------------------------------------------------------------------------
EVENTS = {
    "shelton-ct": [
        {
            "title": "Charcuterie Board Paint & Sip",
            "date": "2026-10-21",
            "announce": "2026-09-24",
            "blurb": "Pick a design, paint your own wooden serving board, and take it home the "
                     "same night. Multiple designs to choose from and every material you need is "
                     "on the table — just bring yourself.",
            "meta": ["6:30 PM", "$35 per person", "Drink included", "Multiple designs"],
            "url": "https://paintsquarepeg.eventbrite.com",
            "cta": "Get tickets",
            "host": "Hosted with Paint Bar CT (@paintbarct)",
        },
    ],
}

# ---------------------------------------------------------------------------
# One-off entertainment on specific dates (a guest host, a holiday night).
#
# Unlike ENTERTAINMENT above, these don't recur — each is a single date and
# each card hides itself in the browser the day after it happens, so a passed
# date never sits on the page. Keyed by location slug.
#
#   (ISO date, what it is, time)
# ---------------------------------------------------------------------------
ENT_DATES = {
    "delray-beach-fl": [
        ("2026-10-03", "Karaoke with Trish", "6–10pm"),
        ("2026-10-16", "Karaoke with Trish", "6–10pm"),
        ("2026-10-30", "Karaoke with Trish", "6–10pm"),
    ],
}

# ---------------------------------------------------------------------------
# Limited-time offer menu — the monthly specials page at /monthly-specials/.
#
# The URL never changes, so every QR code, link and post keeps working. Each
# month: swap `month`, `ends`, the blurb and the items, drop the new photos in
# assets/img-src as lto-<slug>.webp, and rebuild.
#
# `ends` is the last day the menu shows. After that the page swaps itself to a
# short "next month is coming" message (checked in the browser, Eastern time),
# so a stale menu never sits there if the update runs late.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------- happy hour
# Keyed by location slug, so each Peg publishes its own menu as it's finalised.
# A location with no entry here falls back to the "ask your bartender" strip.
#
#   hours   — (days, time) rows for the badge
#   starts  — ISO date this menu goes live. A "starts <date>" flag shows on the
#             page up to the day before, then disappears on its own. Drop the key
#             once the menu has been running a while.
#   groups  — (heading, blurb, [(item, price, detail)]) under "drinks" and "food"
HAPPY_HOUR = {
    "delray-beach-fl": {
        "tagline": "Why limit happy to an hour?",
        "hours": [("Every day", "2–6pm"), ("Fri & Sat", "8:30pm–close")],
        "note": "Dine-in only.",
        "starts": "2026-10-05",
        "local": ["Funky Buddha Hop Gun IPA", "3 Sons Citrus Machine (hazy)", "3 Sons Lite Crispy Bois"],
        "drinks": [
            ("Our signatures", "The ones everybody orders twice.", [
                ("Fruitful Peg-arita", "$9", "Classic + your pick: strawberry, watermelon, blueberry, dragon fruit, passion fruit or coconut", "Fan fave"),
                ("Classic Peg-arita", "$7", "Tequila, triple sec, lemon, lime & agave", None),
                ("Cold Brew Martini", "$9", "Cold brew, vodka & Kahlúa. Add Baileys +$2", None),
            ]),
            ("Well drinks", "", [
                ("Well drinks", "$4", "Vodka · gin · rum · tequila · bourbon", None),
                ("Treat yourself", "+$2", "Tito’s, Smirnoff, Tanqueray, Hendrick’s, Captain Morgan, Casamigos, Maker’s Mark, Woodford Reserve", None),
            ]),
            ("Beer & wine", "", [
                ("Draft beer", "$4", "Miller Lite, Michelob Ultra, Peroni or 3 Sons Lite Crispy Bois", None),
                ("Draft pitcher", "$16", "Miller Lite, Michelob Ultra, Peroni or 3 Sons Lite Crispy Bois", None),
                ("Domestic bottles", "$4", "Budweiser, Coors Light, Michelob Ultra or Yuengling", None),
                ("Local IPA on tap", "$7", "Funky Buddha Hop Gun or 3 Sons Citrus Machine (hazy)", "Local"),
                ("House wine", "$6 / $9", "6oz or 9oz. Cabernet, Malbec, Pinot Noir, Pinot Grigio, Sauvignon Blanc or Chardonnay", None),
            ]),
        ],
        "food": [
            ("Wings", "Six wings, one flavor, zero regrets.", [
                ("6 wings", "$11", "Pick a flavor: BBQ, Hot Honey, Buffalo, Carolina Gold Mustard, or Peg Seasoning or Sweet & Smokey dry rub. Bleu cheese or ranch on the side.", None),
            ]),
            ("Starters & sides", "", [
                ("Loaded chips", "$8", "House-made chips with cheese, bacon & chives", None),
                ("Cheesy dough bites", "$7", "Warm, cheesy bites + house marinara for dipping", None),
                ("Fried mozzarella", "$8", "2 pieces, breaded & fried + house marinara for dipping", None),
                ("Pork meatball", "$8", "One giant house-made meatball, Pecorino Romano + house marinara", None),
                ("Pretzel", "$11", "Extra-large knot + queso or Carolina Gold mustard BBQ", None),
                ("Side salad", "$5", "Choice of House or Caesar, with house-made dressing", None),
            ]),
            ("Small pizza", "Our classic pies, sized for one. Gluten-free crust +$6.", [
                ("Small cheese pizza", "$8", "House-made red sauce, mozz + a sprinkle of Parm", None),
                ("Small 1-topping pizza", "$10", "The cheese pizza + your favorite topping", None),
            ]),
        ],
    },
}

# ---------------------------------------------------------------- Halloween
# The costume contest: the Monday of Halloween week through Halloween itself. In 2026
# Halloween is a Saturday, so the $5 kids menu is what earns the weeknights and
# Saturday mostly fills itself.
#
# The page reads these three dates and shows one of three states on its own:
#   before "starts"      -> counting down
#   starts .. ends       -> running now
#   after "ends"         -> wrapped, winners coming
# Nothing to switch on or off by hand.
HALLOWEEN = {
    "name": "Square Peg Costume Contest",
    "year": 2026,
    "starts": "2026-10-26",
    "ends": "2026-10-31",
    "when": "Monday, October 26 – Saturday, October 31",
    "hashtag": "#SquarePegCostume",
    "lede": "Six days of it. Come in costume, eat something, and get your picture "
            "taken in front of a wall of cheese pizza.",

    "prize": "$25 gift card",
    "prize_extra": "and your photo on our social media",
    "winners": "One winner at every Square Peg.",
    "judged": "Best costume, picked by the crew at your location after Halloween.",

    # Two ways in, so the families who will never post still get to enter.
    "enter": [
        ("Take the photo", "Get in front of the pizza wall, in costume. Any Square Peg, "
                           "any day of the week. Ask us and we’ll take it for you."),
        ("Post it and tag us", "Put it on Instagram or Facebook with #SquarePegCostume and tag "
                               "your Square Peg. Tagged posts are what we judge from."),
        ("That’s it", "We pick a best costume at each location once Halloween’s done, "
                      "and get in touch to hand over the card."),
    ],

    # Every item is $5 on its own — the groups are how it reads on the board, not a
    # three-course set. A kid can order any of them.
    "kids": {
        "price": "$5",
        "line": "Kids eat for $5 all six days.",
        "note": "Every item below is $5 each — order any of them.",
        # for print, where the dates sit in the header and each row shows its price
        "note_short": "Dine-in, all six days.",
        "menu": [
            ("Pizza", ["Two slices — cheese or pepperoni"]),
            ("Pasta, kid size", ["Mac and cheese", "Spaghetti with marinara",
                                 "Pasta alla vodka"]),
            ("Dessert", ["Fried dough with Nutella"]),
        ],
    },
    # Renames of drinks already on the menu, so the bar learns nothing new and the
    # kitchen orders nothing extra — only the name on the board changes.
    # CONFIRM WITH THE BAR before this goes live.
    "drinks": {
        "note": "Same drinks you already like, wearing a costume for the week.",
        "adults_price": "$9",
        "adults": [
            ("Vampire’s Kiss", "The Fruitful Peg-arita, made with strawberry."),
            ("Witch’s Brew", "The Fruitful Peg-arita, made with blueberry."),
            ("Zombie Cold Brew", "Our Cold Brew Martini. Cold brew, vodka and Kahlúa."),
            ("Jack-o’-Lantern Martini", "October’s Pumpkin Spice Martini."),
        ],
        # Nothing is added to either of these — same pour, different name on the
        # board, so no store has to stock or mix anything for the week.
        "kids": [
            ("Ghost Juice", "Square Peg Lemonade."),
            ("Monster Mash", "Any fountain soda. Mix them up!"),
        ],
    },

    "rules": [
        "Open to anyone who comes in during contest week, October 26–31, 2026.",
        "To be considered you have to post your photo and tag us — we judge from "
        "tagged posts on Instagram and Facebook. A photo we take for you still has "
        "to be posted and tagged by you.",
        "One winner per Square Peg location. Best costume, judged by our crew — "
        "it isn’t a random drawing.",
        "Entering means you’re OK with us sharing your photo on our screens, our "
        "social accounts and this website. For anyone under 18, a parent or "
        "guardian needs to be the one entering.",
        "Winners are contacted after October 31. Prize is a $25 Square Peg gift card, "
        "no cash value, plus your photo on our social accounts.",
        "Not sponsored, endorsed or administered by Instagram or Facebook.",
    ],
}

# The costume contest row on /links/ carries its own end date, because LINKS is
# defined before HALLOWEEN and cannot reference it. This makes the duplication
# safe: if the campaign moves and the links row doesn't, the build stops here
# rather than leaving a dead Halloween link in the Instagram bio for a month.
_pot = [r for r in LINKS if r[0] == "Square Peg Costume Contest"]
assert _pot, "The Square Peg Costume Contest row is missing from LINKS"
assert len(_pot[0]) == 6 and _pot[0][5] == HALLOWEEN["ends"], (
    f"The /links/ costume contest row expires {_pot[0][5] if len(_pot[0]) == 6 else 'never'}, "
    f"but HALLOWEEN['ends'] is {HALLOWEEN['ends']}. Make them match.")


LTO = {
    "month": "October",
    "year": "2026",
    "ends": "2026-10-31",
    "blurb": "Five things our kitchen only makes in October, plus two cocktails that taste "
             "like the season. Here until the 31st, then they're gone.",
    "sections": [
        ("Starter", [
            ("Fried Eggplant", "$12", "lto-eggplant",
             "Golden fried eggplant dusted in our Peg seasonings dry rub, with marinara for dipping."),
        ]),
        ("Sandwich", [
            ("Burrata Bliss", "$16", "lto-burrata",
             "Toasted garlic bread, fig jam, arugula and melted burrata. Our Italian take on a better grilled cheese."),
        ]),
        ("Signature brick oven pizza", [
            ("I Yuv You", "$18 small · $28 large", "lto-i-yuv-you",
             "The pizza our head chef makes for his own family. Red pie with mozzarella, pepperoni, "
             "fried eggplant, sliced roma tomatoes, red onions and parm."),
            ("The Bianca Bella", "$17 small · $27 large", "lto-bianca-bella",
             "A white pizza with mozzarella, parm cream, sausage, caramelized onions and fresh basil. "
             "Lives up to its name."),
        ]),
        ("Dessert", [
            ("Deep Fried Sandwich Cookies", "$12", "lto-cookies",
             "Five deep fried sandwich cookies, powdered sugar, chocolate sauce and a scoop of vanilla ice cream."),
        ]),
    ],
    # No photos for these — they render as copy-only cards.
    "cocktails": [
        ("Pumpkin Spice Martini", "$9",
         "Vanilla vodka, Kahlúa, Baileys, RumChata, pumpkin spice and cold brew, chilled, with whipped cream and caramel drizzle."),
        ("Fall Sangria", "$9",
         "Gooseneck Pinot Grigio, pear liqueur and apple cider in a salted caramel and cinnamon sugar rimmed glass."),
    ],
}


# ===========================================================================
# TOYS FOR TOTS — Square Peg as a drop-off location
# ===========================================================================
#
# NOT LIVE. The page is built, unlisted and noindex until Brian has the dates
# and the promotion settled. Flip TFT["live"] to True and rebuild to launch it;
# build.py refuses to launch while a placeholder is still unfilled, so the page
# cannot go public saying "dates to come".
#
# ON THE LOGO: the Toys for Tots bear-and-train logo is a registered trademark
# of the Marine Toys for Tots Foundation and is NOT on this page. Registered
# drop-off locations are sent approved artwork by their local coordinator —
# that is where the file comes from, not from saving an image off their
# website. Once Brian has it, it goes in src/img and gets added here.
#
# ON THE RULES BELOW: "new and unwrapped" is the Foundation's own universal
# requirement and is safe to state. The "please don't" list is the usual
# guidance but coordinators vary, so Brian should confirm it with his before
# this goes public. Marked with a comment where it matters.

TFT = {
    # Flip to True to launch. See the build-time guard in build.py.
    "live": False,

    "eyebrow": "Toys for Tots",
    "h1": "Drop a toy at Square Peg.",
    "lede": "Every Square Peg is a Toys for Tots drop-off point this holiday "
            "season. Bring a new, unwrapped toy, leave it in the box by the "
            "door, and the Marine Corps Reserve gets it to a child in the same "
            "community it was dropped off in.",

    # ---------------------------------------------------------------------
    # PLACEHOLDER 1 — THE DATES
    # Fill in "window" with the collection period, e.g. "November 14 – December 15".
    # Leave it empty and the page shows a visible placeholder card instead.
    # ---------------------------------------------------------------------
    "window": "",
    "window_note": "Drop off any time we're open — you don't need to be eating.",

    # ---------------------------------------------------------------------
    # THE PROMOTION — set Oct 2026
    #
    # ⚠ ONE THING TO SETTLE BEFORE LAUNCH: new Square Peg Rewards members also
    # get a $5 welcome reward. "Not combinable with any other offer" means a
    # guest who brings a toy AND joins on the same visit gets one $5, not two —
    # which is an argument at the till unless the staff know the answer. Tell
    # the GMs which way it goes.
    # ---------------------------------------------------------------------
    "offer_head": "$5 toward your meal, the day you drop off",
    "offer_body": "Bring in a toy and we'll take $5 off whatever you're eating "
                  "or taking home that day. Dine in or pick up, at any of the ten.",
    "offer_fine": "One $5 per guest, on the day you drop off the toy. Can't be "
                  "combined with any other offer, discount or reward.",

    "steps": [
        ("Pick up a toy",
         "New and unwrapped, in its original packaging. Anything from a board "
         "game to a basketball. Gifts for teenagers are what every campaign "
         "runs short of, so if you're stuck, that's where to aim."),
        ("Bring it in",
         "The collection box is by the door at all ten Square Pegs. Any day "
         "we're open, during normal hours. You don't have to stay, and you "
         "don't have to buy anything."),
        ("The Marines take it from there",
         "Local Marine Toys for Tots coordinators collect, sort and distribute "
         "every toy to families in the same area it was collected."),
    ],

    # The Foundation's own universal requirement. Safe to state as written.
    "yes": [
        "New toys, in the original packaging",
        "Books, board games, puzzles and art supplies",
        "Sports equipment and anything active",
        "Gifts for ages 12–18 — always the shortest category",
    ],
    # ⚠ CONFIRM WITH YOUR COORDINATOR before this page goes public. This is the
    # usual guidance but individual campaigns set their own rules.
    "no": [
        "Used, opened or hand-made toys",
        "Anything resembling a real weapon",
        "Food, sweets or anything perishable",
    ],

    # The Square Peg Rewards bar near the foot of the page. Wording follows the
    # menus: free, $5 welcome reward, points every visit, members-only deals.
    "rewards_head": "While you're here, join Square Peg Rewards.",
    "rewards_body": "It's free. A $5 welcome reward, points on every visit and "
                    "deals only members get.",
    "rewards_cta": "Get the app",

    "org_url": "https://www.toysfortots.org/",
    "chapter_url": "https://www.toysfortots.org/find-your-local-chapter/",
    # Attribution. Registered drop-off locations credit the program properly;
    # this is the line that does it.
    "credit": "Toys for Tots is a program of the U.S. Marine Corps Reserve, run "
              "by the Marine Toys for Tots Foundation. Square Peg Pizzeria is a "
              "drop-off location, not an affiliate of the Foundation.",
}

# ---- Corporate: events & bulk gift cards --------------------------------
# Two B2B pages that run holiday wording now and evergreen wording from
# Jan 1. Both copies ship in the HTML; the build hides whichever is out of
# season today and site.js re-checks against Eastern time on every load, so
# the swap happens on the day without anyone rebuilding or remembering.
#
# SWITCH is the last day the holiday wording runs. Move it a year each
# autumn — the build asserts it is in the future, so a stale date fails the
# build instead of quietly serving "book your holiday party" in March.
CORPORATE_SWITCH = "2026-12-31"

CORPORATE_EVENTS = {
    "holiday": {
        "eyebrow": "Corporate holiday parties · All 10 locations",
        "h1": "Host the holiday party at ours.",
        "lede": "Your team, your clients, or both. We give you the room, plan the "
                "food ahead, and run a tab you set the ceiling on. You turn up and "
                "talk to people.",
        "kicker": "December books up first. The good Thursdays go before Halloween.",
    },
    "evergreen": {
        "eyebrow": "Corporate events · All 10 locations",
        "h1": "Host it at ours.",
        "lede": "Client appreciation, a closed deal, a team that has had a long "
                "quarter. We give you the room, plan the food ahead, and run a tab "
                "you set the ceiling on. You turn up and talk to people.",
        "kicker": "Give us a couple of weeks and a rough headcount and the rest is ours.",
    },
    # Two genuinely different formats. The second one is the interesting one and
    # almost nobody offers it, so it gets equal billing rather than a footnote.
    "formats": [
        ("Everyone at once", "The sit-down",
         "One night, one long table or a room of your own. The food is planned "
         "before anyone arrives so it lands together instead of in waves, and "
         "nobody from your company has to get up and deal with the kitchen."),
        ("Come when you can", "The drop-in night",
         "Your clients can’t all make Thursday at seven, so don’t make them. Pick "
         "a night — or a whole week — tell us who’s invited, and they come by when "
         "it suits them. A drink and a pizza, eaten in or carried out, on your tab. "
         "You can be there the whole time or not at all."),
    ],
    "handled": [
        "A room of its own at some locations, a reserved section at others",
        "Food planned before the night, so it comes out together",
        "A tab with a ceiling you set — we stop there and tell you where it landed",
        "One invoice at the end. Nobody collects from anybody",
        "Gluten-free crust and vegan cheese on request, same as always",
    ],
    "steps": [
        ("Send the form", "A date, a rough headcount, and which Square Peg."),
        ("We call you", "We confirm the space, plan the food with you, and agree the tab."),
        ("Turn up", "Tables ready, tab open, nothing for you to run."),
    ],
    # Deliberately vague on which locations have a real room: it differs store to
    # store and a list on a web page goes stale the first time a dining room is
    # rearranged. The honest version is "tell us the number and we'll tell you where".
    "space": "Some of our locations have a room of their own. At the others we "
             "reserve a section and build it around your group. Tell us the "
             "headcount and the date and we’ll tell you which Square Peg fits — "
             "that one call saves a lot of guessing.",
    # Bolton is the only location without a bar. Saying so up front beats a
    # company booking a drinks night at the one place that can't pour.
    "bar_note": "Nine of the ten have a full bar. Bolton doesn’t — worth knowing "
                "if drinks are part of the night.",
}

CORPORATE_EVENTS_FAQ = [
    ("How many people can you take?",
     "It depends on the location. Some Square Pegs have a room of their own, others "
     "reserve a section of the dining room. Send the headcount and the date and we’ll "
     "tell you which one works rather than guessing on a web page."),
    ("Can we set a spending limit?",
     "Yes, and most companies do. You tell us the ceiling before the night, we run the "
     "tab against it, and we tell you where it landed. Nobody gets an awkward surprise."),
    ("Can guests take a pizza home instead of eating in?",
     "Yes — that’s the whole idea behind the drop-in night. They come by, have a drink, "
     "and take a pie home on the company."),
    ("Can we have the place to ourselves?",
     "Ask. It depends on the location and the night, and it’s a conversation rather than "
     "a yes or no on a web page."),
    ("Do you do this outside the holidays?",
     "Yes. December is busiest, but client appreciation, closing celebrations and team "
     "dinners run all year, and January through March is when we have the most room."),
    ("What about dietary needs?",
     "We have a 12″ gluten-free crust and vegan cheese. Mention it in the request and "
     "we’ll plan around it."),
    ("Can we get one invoice?",
     "Yes. One bill at the end, to the company. No splitting, no collecting."),
]

# PARKED, Oct 16 2026 — Brian took bulk gift cards off /corporate/, which is now
# only about hosting an event. Nothing on the site renders CORPORATE_GIFTS or
# CORPORATE_GIFTS_FAQ any more; both are left here intact so the programme can
# be switched back on without rewriting it.
#
# Bonus cards rather than a discount. Costs roughly the same but never marks the
# card down, and the bonus cards themselves bring extra people through the door —
# which a percentage off the invoice never does.
#
# "bonus" is cards given on top of the cards bought, so the headline percentage
# is bonus ÷ bought: 1/10, 3/25, 8/50.
CORPORATE_GIFTS = {
    "holiday": {
        "eyebrow": "Corporate gift cards · Bulk orders",
        "h1": "Give them something they’ll actually use.",
        "lede": "Your clients get a lot of branded water bottles in December. A Square "
                "Peg card gets spent — usually on a Friday, usually with their family, "
                "and they’ll remember who sent it.",
        "kicker": "Order with a week’s notice and they’ll be ready to collect.",
    },
    "evergreen": {
        "eyebrow": "Corporate gift cards · Bulk orders",
        "h1": "Give them something they’ll actually use.",
        "lede": "Closing gifts, referral thank-yous, a crew that pulled a long week. A "
                "Square Peg card gets spent. A branded water bottle goes in a drawer.",
        "kicker": "Order with a week’s notice and they’ll be ready to collect.",
    },
    "denominations": ["$25", "$50"],
    # (cards bought, bonus cards, headline)
    "tiers": [
        (10, 1, "10% extra"),
        (25, 3, "12% extra"),
        (50, 7, "14% extra"),
    ],
    "examples": [
        ("25 × $25", "$625", "28 cards", "$700 of Square Peg"),
        ("50 × $50", "$2,500", "57 cards", "$2,850 of Square Peg"),
    ],
    "uses": [
        ("Client thank-yous", "The one gift nobody re-gifts."),
        ("Closing gifts", "Realtors, agents, dealerships, anyone who shakes a hand at the end."),
        ("Referral thank-yous", "Cheaper than an ad and it earns the next one."),
        ("Staff rewards", "A spot bonus that doesn’t go through payroll."),
        ("Crew appreciation", "Contractors, trades, anyone who had a brutal week."),
        ("Patient and customer appreciation", "Medical, dental, veterinary — people remember dinner."),
    ],
    "how": [
        ("Tell us the numbers", "How many cards, and whether you want $25s, $50s or a mix."),
        ("We confirm and take payment", "One invoice to the company. We’ll tell you the bonus cards you’ve earned."),
        ("Collect them", "Ready at the Square Peg you choose, boxed and counted."),
    ],
    # ⚠ CONFIRM BEFORE PUSHING — do Toast gift cards redeem at all ten locations,
    # including Shelton and Delray Beach? The page says they do. If any store is on
    # a separate Toast account the claim is wrong and this line has to change.
    "scope": "Good at any Square Peg, on anything on the menu.",
    "min": 10,
}

CORPORATE_GIFTS_FAQ = [
    ("How does the bonus work?",
     "You pay for the cards you order and we add more on top. Ten cards earns one extra, "
     "twenty-five earns three, fifty earns seven. The cards themselves are never marked "
     "down — you just leave with more of them than you paid for."),
    ("What’s the minimum?",
     "Ten cards. Below that, buy them one at a time online like anyone else — the bonus "
     "is for the volume, not the paperwork."),
    ("Can we mix $25 and $50 cards?",
     "Yes. The bonus is counted on the total number of cards, and the bonus cards come in "
     "whichever denomination you’re mostly buying."),
    ("Can you put our company name on them?",
     "Ask when you send the request. Tell us what you had in mind and we’ll tell you "
     "honestly what we can and can’t do."),
    ("How long does it take?",
     "Give us about a week. In December, give us two — that’s the month everybody "
     "remembers gift cards at the same time."),
    ("Where do they work?",
     "Any Square Peg, on anything on the menu."),
    ("Can we get one invoice for accounting?",
     "Yes. One invoice to the company for the whole order."),
]

# ---- Gift card bounce-back: buy $100 in Nov/Dec, get $20 for January -----
# A bounce-back, not a discount. December gift card buyers are shopping for
# somebody else; the $20 is the only part of the transaction that is theirs,
# and it lands in the quietest six weeks of the year on purpose.
#
# Four windows, and the page tells the truth in all of them without anyone
# editing it: before it starts, while you can buy, while you can spend, and
# after. Dates are checked against each other at build time below.
GIFT_BOUNCE = {
    "buy_from": "2026-11-01",
    "buy_to": "2026-12-31",
    "use_from": "2027-01-01",
    "use_to": "2027-02-13",
    "buy_label": "November 1 – December 31",
    "use_label": "January 1 – February 13",
    "spend": "$100",
    "reward": "$20",
    "eyebrow": "November & December · In store · Everyone",
    "h1": "The gift card is for them. The $20 is for you.",
    "lede": "Every $100 in Square Peg gift cards you buy at any of our ten locations "
            "in November or December comes with a $20 voucher for you — to spend between "
            "January 1 and February 13, which is about when you’ll want it. No card to "
            "sign up for, no account needed.",
    "steps": [
        ("Buy $100 in gift cards", "At the register, at any Square Peg, any time in November or December. "
                                   "One card or several — it’s the $100 that counts."),
        ("Take your $20 voucher", "Handed to you at the register, there and then. Buy $300 in cards and "
                                  "you leave with three of them."),
        ("Spend it in the new year", "January 1 to February 13. Dine in, pick up, whatever you fancy."),
    ],
    "why": "Everyone buys gift cards in December and nobody buys anything in "
           "January. This is us closing that gap — and giving you a reason to "
           "come back when the decorations are down.",
    "join_head": "While you’re at it",
    "join_body": "You don’t need to be a member for any of this — the voucher is for "
                 "anyone buying. But if you aren’t in the app yet, joining is free, takes "
                 "a minute, and starts you with $5 off your next order on top.",
    "terms": [
        "$100 or more in gift cards, bought in person at a Square Peg location.",
        "One $20 voucher for every full $100 of gift cards on the same purchase. "
        "Buy $250, get two.",
        "Open to everyone. No loyalty membership needed.",
        "Gift cards bought online don’t qualify — it has to be in person at a location.",
        "The $20 is a voucher, not a gift card. It isn’t redeemable for cash and can’t be "
        "put toward buying more gift cards.",
        "Usable January 1 through February 13 only. It doesn’t carry over.",
        "Not valid with other offers. Tax and gratuity not included.",
        "Participating locations. Management may end the promotion at any time.",
    ],
}


# Same guard as the costume contest row above: LINKS is defined long before
# GIFT_BOUNCE and cannot reference it, so the end date is written twice. If the
# promotion's buy window ever moves and the /links/ row doesn't, the build stops
# here rather than leaving a dead offer in the Instagram bio through January.
_gcb = [r for r in LINKS if r[0] == "Holiday Gift Card Bonus"]
assert _gcb, "The Holiday Gift Card Bonus row is missing from LINKS"
assert len(_gcb[0]) == 6 and _gcb[0][5] == GIFT_BOUNCE["buy_to"], (
    f"The /links/ gift card bonus row expires {_gcb[0][5] if len(_gcb[0]) == 6 else 'never'}, "
    f"but GIFT_BOUNCE['buy_to'] is {GIFT_BOUNCE['buy_to']}. Make them match.")

# The bookable kids pizza-making class — a private party booking with a ten-child
# minimum, NOT the monthly open class that sells tickets through Eventbrite. Two
# products, two prices; keep them apart or the $10 open class and the $20 party
# class end up in the same sentence.
#
# Shelton's flyers sold this as two classes, "Little Peg" at $20 and "Big Peg" at
# $25. It is one class and an upgrade: the extra $5 buys $10 of arcade credit,
# which only works where there is an arcade.
PIZZA_CLASS = {
    "price": "$20",
    "upgrade_total": "$25",
    "upgrade_delta": "$5",
    "arcade_credit": "$10",
    "min_kids": 10,
    "price_note": "per child, plus tax and gratuity",
    "lede": "Your child stretches their own dough and tops it how they like it. The "
            "pizzas are then cooked in our brick oven. They leave with a full stomach "
            "and a certificate that says they did it.",
    "includes": [
        ("They make the pizza",
         "Cheese or pepperoni, stretched and topped by them, with one of our chefs "
         "showing them how."),
        ("Into the brick oven",
         "Their pizzas are then cooked in our brick oven by one of our chefs, while "
         "they watch."),
        ("A drink and a cookie",
         "A fountain drink each, and a warm chocolate chip cookie to finish."),
        ("A certificate",
         "Every child leaves with a certificate of completion, with their name on it."),
    ],
    "upgrade_head": "Add the arcade",
    "upgrade_body": "Five dollars more per child buys ten dollars of arcade games each "
                    "\u2014 so the party keeps going after the pizza comes out.",
    # Not every location has an arcade. Named locations stay off the page on
    # purpose — the class is for all ten, and a list here would read as the
    # upgrade being unavailable everywhere else rather than something to check.
    "arcade_note": "Not every location has an arcade. We\u2019ll confirm when we call.",
    "steps": [
        ("Send the form", "A date, how many children, and which Square Peg."),
        ("We call you back", "We confirm the date, go through allergies, and take it from there."),
        ("Turn up hungry", "We provide the aprons and chef hats. You bring the children."),
    ],
    "faq": [
        ("How many children do we need?",
         "Ten is the minimum for a class. There\u2019s no maximum we can\u2019t talk about "
         "\u2014 tell us the number and we\u2019ll tell you which location fits it."),
        ("What ages is it for?",
         "It works best for roughly 4 to 12. Younger children are welcome with a "
         "grown-up alongside them."),
        ("Can parents stay?",
         "Yes, and most do. Tell us how many adults are coming so we can set the room "
         "up properly \u2014 they can order off the regular menu while the class runs."),
        ("What about allergies?",
         "Tell us on the form or when we call. Gluten-free crust is available, and we "
         "will talk you through what we can and can\u2019t do for a specific allergy."),
        ("How far ahead should we book?",
         "A couple of weeks is comfortable. Weekends in December and around school "
         "holidays go first."),
    ],
}


# ---------------------------------------------------------------------------
# Team Night. Any team, any sport: play your game, come in wearing the uniform,
# and the whole table comes off by DISCOUNT. Dine in, any day.
#
# The discount lives here and nowhere else - page, flyer and TV slide all read
# it from this one line, because it is still being confirmed.
TEAM_NIGHT = {
    "discount": "10%",
    "lede": "Any team, any sport. Play your game, come straight in wearing your uniform, "
            "and we take 10% off the whole table. No card, no sign-up, no special "
            "night of the week \u2014 just turn up in uniform.",
    "steps": [
        ("Play your game",
         "Baseball, soccer, basketball, hockey, lacrosse, swim, cheer \u2014 if there "
         "was a game or a meet today, you qualify."),
        ("Come in your uniform",
         "Players in uniform, straight from the field. Muddy socks are part of it."),
        ("We take it off the bill",
         "Ten per cent off the whole table, not just the players. Tell your server "
         "when you sit down."),
    ],
    "sports": ["Baseball", "Softball", "Soccer", "Basketball", "Football", "Hockey",
               "Lacrosse", "Volleyball", "Field hockey", "Wrestling", "Swim",
               "Track", "Cross country", "Cheer", "Dance", "Gymnastics"],
    "rules": [
        "Dine in only \u2014 the uniform has to be in the room.",
        "Any day of the week, any Square Peg.",
        "One discount per table. Not combinable with any other deal or promotion.",
        "Alcohol is excluded.",
    ],
    "faq": [
        ("Does the whole table get it, or just the players?",
         "The whole table. Parents, grandparents, the sibling who sat through the "
         "whole game \u2014 ten per cent comes off the bill, not off one plate."),
        ("What counts as a team?",
         "Anything organised \u2014 little league, travel, rec league, school, club, "
         "adult league. If you play together and you have a uniform, you are a team."),
        ("Do we all have to come at once?",
         "No. Two players and a parent counts. If you are bringing the whole roster "
         "and the parents, call the location first so we can put tables together."),
        ("Which nights does it run?",
         "Any day we are open. It is tied to your game, not to our calendar."),
        ("Do adults count?",
         "Yes. Beer-league softball in a jersey is still a team in uniform."),
        ("Can we get it on takeout?",
         "No \u2014 this one is dine in only."),
    ],
}
